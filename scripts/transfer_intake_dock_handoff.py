#!/usr/bin/env python3
"""Validate and explicitly transfer a manifest-backed Intake Dock package.

Default mode is local validation/planning only. Live transfer requires --apply
and an exact --confirm-target OWNER/REPOSITORY. It writes only new or byte-identical
files under the named project's incoming/ and inventory/ paths; conflicting
remote content is never overwritten. This is not a complete secret scanner.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from typing import Any, Protocol, Sequence
import zipfile

MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_PACKAGE_BYTES = 200 * 1024 * 1024
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
PRIVATE_KEY_MARKERS = (b"-----BEGIN PRIVATE KEY-----", b"-----BEGIN RSA PRIVATE KEY-----", b"-----BEGIN OPENSSH PRIVATE KEY-----", b"-----BEGIN EC PRIVATE KEY-----")
GITHUB_TOKEN_PATTERN = re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}")
LANE_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,98}[a-z0-9])?\Z")
TARGET_PATTERN = re.compile(r"[A-Za-z0-9-]+/[a-z0-9](?:[a-z0-9-]{0,98}[a-z0-9])?\Z")


class TransferError(ValueError):
    """A package or target violates the transfer contract."""


class GitHubClient(Protocol):
    def authenticated_login(self) -> str: ...
    def get_repository(self, target: str) -> dict[str, Any]: ...


def validate_package(package_path: Path, target: str) -> dict[str, Any]:
    """Validate package structure, intended target, paths, sizes, and all hashes."""
    if not TARGET_PATTERN.fullmatch(target):
        raise TransferError("target must be an explicit OWNER/repository slug")
    package_path = package_path.expanduser().absolute()
    if package_path.is_symlink() or not package_path.is_file():
        raise TransferError("package must be a regular non-symlink file")
    if package_path.stat().st_size > MAX_PACKAGE_BYTES:
        raise TransferError("package exceeds the maximum compressed size")

    try:
        archive = zipfile.ZipFile(package_path, "r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise TransferError("package is not a valid ZIP archive") from exc
    with archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        if len(names) != len(set(names)):
            raise TransferError("package contains duplicate ZIP entries")
        if sum(item.file_size for item in infos) > MAX_PACKAGE_BYTES + MAX_MANIFEST_BYTES:
            raise TransferError("uncompressed package content exceeds the maximum size")
        info_by_name = {item.filename: item for item in infos}
        if "manifest.json" not in names:
            raise TransferError("package manifest.json is missing")
        if info_by_name["manifest.json"].file_size > MAX_MANIFEST_BYTES:
            raise TransferError("package manifest exceeds the maximum size")
        try:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError, KeyError) as exc:
            raise TransferError("package manifest is invalid JSON") from exc
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or manifest.get("package_type") != "intake-dock-handoff":
            raise TransferError("unsupported handoff manifest schema")
        if manifest.get("target_repository", "").casefold() != target.casefold():
            raise TransferError("package target does not match the explicitly confirmed target")
        lane = manifest.get("lane")
        if not isinstance(lane, str) or not LANE_PATTERN.fullmatch(lane):
            raise TransferError("manifest contains an invalid project lane")
        if manifest.get("transfer_status") != "not_uploaded":
            raise TransferError("package is not marked as a fresh local handoff")
        entries = manifest.get("files")
        if not isinstance(entries, list) or not entries:
            raise TransferError("manifest must contain at least one file")
        expected_paths = {"manifest.json"}
        seen_sources: set[str] = set()
        total = 0
        verified: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                raise TransferError("manifest file entry is invalid")
            source_name = entry.get("source_name")
            relative = entry.get("path")
            if not isinstance(source_name, str) or source_name in {"", ".", ".."} or "/" in source_name or "\\" in source_name:
                raise TransferError("manifest contains an unsafe source filename")
            if source_name in seen_sources:
                raise TransferError("manifest contains duplicate source filenames")
            seen_sources.add(source_name)
            expected = f"projects/{lane}/incoming/{source_name}"
            if relative != expected:
                raise TransferError("manifest destination path does not match the selected lane")
            pure = PurePosixPath(relative)
            if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts) or "\\" in relative:
                raise TransferError("manifest contains an unsafe destination path")
            if relative not in names:
                raise TransferError(f"package is missing declared file: {source_name}")
            if info_by_name[relative].file_size > MAX_FILE_BYTES:
                raise TransferError(f"file exceeds the size limit: {source_name}")
            data = archive.read(relative)
            if any(marker in data for marker in PRIVATE_KEY_MARKERS) or GITHUB_TOKEN_PATTERN.search(data):
                raise TransferError(f"content resembles a private key or GitHub token: {source_name}")
            size = entry.get("size_bytes")
            digest = entry.get("sha256")
            if not isinstance(size, int) or size < 0 or size > MAX_FILE_BYTES or len(data) != size:
                raise TransferError(f"size mismatch or limit exceeded: {source_name}")
            if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest) or hashlib.sha256(data).hexdigest() != digest:
                raise TransferError(f"SHA-256 mismatch: {source_name}")
            total += size
            verified.append({"path": relative, "source_name": source_name, "data": data, "size_bytes": size, "sha256": digest})
        if total > MAX_PACKAGE_BYTES:
            raise TransferError("uncompressed package content exceeds the maximum size")
        if set(names) != expected_paths.union(entry["path"] for entry in entries):
            raise TransferError("package contains undeclared ZIP entries")
        if archive.testzip() is not None:
            raise TransferError("ZIP integrity test failed")
    return {"target_repository": target, "lane": lane, "files": verified, "manifest": manifest,
            "package_sha256": hashlib.sha256(package_path.read_bytes()).hexdigest()}


class GhGitClient:
    """Bounded subprocess adapter; never displays tokens or arbitrary CLI output."""

    @staticmethod
    def _run(args: list[str], *, cwd: Path | None = None, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(args, cwd=cwd, check=False, capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(f"transfer command failed: {type(exc).__name__}") from exc
        if result.returncode and not allow_failure:
            detail = " (HTTP 404)" if re.search(r"\b404\b", result.stderr or "") else ""
            raise RuntimeError(f"transfer command failed{detail}; inspect gh auth status and git access")
        return result

    def authenticated_login(self) -> str:
        result = self._run(["gh", "api", "user"])
        try:
            value = json.loads(result.stdout)
            login = value["login"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise RuntimeError("GitHub did not return the authenticated login") from exc
        if not isinstance(login, str) or not login:
            raise RuntimeError("GitHub did not return the authenticated login")
        return login

    def get_repository(self, target: str) -> dict[str, Any]:
        result = self._run(["gh", "api", f"repos/{target}"])
        try:
            value = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("GitHub returned invalid repository metadata") from exc
        if not isinstance(value, dict):
            raise RuntimeError("GitHub returned invalid repository metadata")
        return value

    def clone(self, target: str, destination: Path) -> None:
        self._run(["gh", "repo", "clone", target, str(destination)])

    def git(self, repo: Path, args: list[str], *, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
        return self._run(["git", "-C", str(repo), *args], allow_failure=allow_failure)


def _ensure_safe_parents(root: Path, relative: str) -> Path:
    target = root / PurePosixPath(relative)
    current = root
    for part in PurePosixPath(relative).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise TransferError(f"remote repository contains a symlink in destination path: {relative}")
        if current.exists() and not current.is_dir():
            raise TransferError(f"remote repository has a non-directory destination parent: {relative}")
    if target.is_symlink():
        raise TransferError(f"remote destination is a symlink: {relative}")
    return target


def transfer(package_path: Path, target: str, *, apply: bool = False,
             confirmed_target: str | None = None, client: Any | None = None) -> dict[str, Any]:
    package = validate_package(package_path, target)
    if not apply:
        return {"status": "planned", "target_repository": target, "lane": package["lane"],
                "files": len(package["files"]), "package_sha256": package["package_sha256"],
                "remote_calls_made": False}
    if confirmed_target != target:
        raise TransferError(f"live transfer requires --confirm-target {target}")
    client = client or GhGitClient()
    owner = target.split("/", 1)[0]
    if client.authenticated_login().casefold() != owner.casefold():
        raise TransferError("target owner must match the authenticated personal GitHub account")
    repository = client.get_repository(target)
    if str(repository.get("full_name", "")).casefold() != target.casefold():
        raise TransferError("GitHub returned a repository other than the exact target")
    if repository.get("private") is not True:
        raise TransferError("target repository is not private; refusing transfer")

    lane = package["lane"]
    receipt_rel = f"projects/{lane}/inventory/handoff-{package['package_sha256']}.json"
    receipt = {
        "schema_version": 1,
        "package_type": "intake-dock-receipt",
        "source_package_sha256": package["package_sha256"],
        "target_repository": target,
        "lane": lane,
        "files": [{k: v for k, v in entry.items() if k != "data"} for entry in package["files"]],
        "transfer_status": "received",
    }
    receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")

    with tempfile.TemporaryDirectory(prefix="intake-dock-transfer-") as temporary:
        checkout = Path(temporary) / "repo"
        client.clone(target, checkout)
        default_branch = repository.get("default_branch")
        head_check = client.git(checkout, ["rev-parse", "--verify", "HEAD"], allow_failure=True)
        if head_check.returncode == 0:
            if isinstance(default_branch, str) and default_branch:
                client.git(checkout, ["checkout", "--quiet", default_branch])
                branch = default_branch
            else:
                branch_result = client.git(checkout, ["symbolic-ref", "--short", "HEAD"])
                branch = branch_result.stdout.strip()
                if not branch:
                    raise RuntimeError("could not identify the existing repository branch")
        else:
            # A newly provisioned private repo can be empty even if GitHub
            # already reports its intended default-branch name.
            client.git(checkout, ["symbolic-ref", "HEAD", "refs/heads/main"])
            branch = "main"

        pending: list[str] = []
        for entry in package["files"]:
            path = _ensure_safe_parents(checkout, entry["path"])
            if path.exists():
                if not path.is_file() or path.read_bytes() != entry["data"]:
                    raise TransferError(f"remote path already exists with different content; refusing overwrite: {entry['path']}")
            else:
                path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                if path.parent.is_symlink():
                    raise TransferError(f"unsafe parent path: {entry['path']}")
                with path.open("xb") as stream:
                    stream.write(entry["data"])
                if os.name == "posix":
                    os.chmod(path, 0o600)
                pending.append(entry["path"])

        receipt_path = _ensure_safe_parents(checkout, receipt_rel)
        if receipt_path.exists():
            if not receipt_path.is_file() or receipt_path.read_bytes() != receipt_bytes:
                raise TransferError("receipt path already exists with different content; refusing overwrite")
        else:
            receipt_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with receipt_path.open("xb") as stream:
                stream.write(receipt_bytes)
            if os.name == "posix":
                os.chmod(receipt_path, 0o600)
            pending.append(receipt_rel)

        if not pending:
            return {"status": "already-present", "target_repository": target, "lane": lane,
                    "files": len(package["files"]), "receipt": receipt_rel, "remote_calls_made": True}
        client.git(checkout, ["config", "user.name", "Intake Dock Transfer"])
        client.git(checkout, ["config", "user.email", "noreply@github.com"])
        client.git(checkout, ["add", "--", *pending])
        client.git(checkout, ["commit", "-m", f"Receive Intake Dock handoff for {lane}"])
        client.git(checkout, ["push", "--set-upstream", "origin", branch])
        return {"status": "transferred-and-committed", "target_repository": target, "lane": lane,
                "files": len(package["files"]), "receipt": receipt_rel, "remote_calls_made": True}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--apply", action="store_true", help="perform GitHub and git operations")
    parser.add_argument("--confirm-target", help="repeat exact OWNER/REPOSITORY to authorize live transfer")
    args = parser.parse_args(argv)
    try:
        result = transfer(args.package, args.target, apply=args.apply, confirmed_target=args.confirm_target)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    if result["status"] == "planned":
        print("PLAN ONLY: no GitHub or git network calls were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
