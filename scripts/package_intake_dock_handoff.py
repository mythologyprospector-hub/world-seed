#!/usr/bin/env python3
"""Build a local, manifest-backed Intake Dock handoff package from explicit files.

This tool never uploads, deletes, moves, or modifies source files. It refuses
symlinks, unsafe names, likely credential files, oversized inputs, and outputs
that already exist. A successful package is not permission to transmit it.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Sequence
import zipfile

LANE_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,98}[a-z0-9])?\Z")
MAX_FILE_BYTES = 50 * 1024 * 1024
SECRET_NAMES = {
    ".env", ".env.local", ".npmrc", ".pypirc", "credentials", "credentials.json",
    "id_rsa", "id_ed25519", "known_hosts", "secrets.json", "token",
}
SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".kdbx")
PRIVATE_KEY_MARKERS = (
    b"-----BEGIN PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
    b"-----BEGIN EC PRIVATE KEY-----",
)
GITHUB_TOKEN_PATTERN = re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}")


def _safe_source(path: Path) -> tuple[Path, bytes]:
    source = path.expanduser().absolute()
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"input must be a regular non-symlink file: {path.name}")
    if source.name in {".", ".."} or "/" in source.name or "\\" in source.name:
        raise ValueError("input filename is unsafe")
    lowered = source.name.lower()
    if lowered in SECRET_NAMES or lowered.endswith(SECRET_SUFFIXES):
        raise ValueError(f"credential-like filename refused: {source.name}")
    info = source.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"input is not a regular file: {source.name}")
    if info.st_size > MAX_FILE_BYTES:
        raise ValueError(f"input exceeds {MAX_FILE_BYTES} bytes: {source.name}")
    data = source.read_bytes()
    if any(marker in data for marker in PRIVATE_KEY_MARKERS) or GITHUB_TOKEN_PATTERN.search(data):
        raise ValueError(f"content resembles a private key or GitHub token: {source.name}")
    return source, data


def build_package(files: Sequence[Path], output: Path, lane: str, target_repo: str) -> dict[str, object]:
    if not LANE_PATTERN.fullmatch(lane):
        raise ValueError("lane must be a lowercase repository-style slug")
    if not re.fullmatch(r"[A-Za-z0-9-]+/[a-z0-9](?:[a-z0-9-]{0,98}[a-z0-9])?", target_repo):
        raise ValueError("target must be an explicit OWNER/repository slug")
    if not files:
        raise ValueError("provide at least one explicit --file")
    output = output.expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("output already exists; refusing to overwrite")
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise ValueError("output parent must already exist and must not be a symlink")

    prepared: list[tuple[Path, bytes]] = []
    names: set[str] = set()
    for path in files:
        source, data = _safe_source(path)
        if source.name in names:
            raise ValueError(f"duplicate basename would collide in package: {source.name}")
        names.add(source.name)
        prepared.append((source, data))

    entries = []
    for source, data in sorted(prepared, key=lambda item: item[0].name):
        entries.append({
            "path": f"projects/{lane}/incoming/{source.name}",
            "source_name": source.name,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source_mtime_utc": datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat(),
        })
    manifest = {
        "schema_version": 1,
        "package_type": "intake-dock-handoff",
        "target_repository": target_repo,
        "lane": lane,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": entries,
        "transfer_status": "not_uploaded",
        "source_files_modified": False,
    }

    # Create exclusively, then verify the archive can be read and all hashes match.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(output, flags, 0o600)
    os.close(descriptor)
    try:
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            data_by_name = {source.name: data for source, data in prepared}
            for entry in entries:
                archive.writestr(entry["path"], data_by_name[entry["source_name"]])
        with zipfile.ZipFile(output, "r") as archive:
            if archive.testzip() is not None:
                raise ValueError("package ZIP integrity check failed")
            loaded = json.loads(archive.read("manifest.json"))
            for entry in loaded["files"]:
                actual = archive.read(entry["path"])
                if len(actual) != entry["size_bytes"] or hashlib.sha256(actual).hexdigest() != entry["sha256"]:
                    raise ValueError(f"package post-write hash verification failed: {entry['source_name']}")
    except Exception:
        try:
            output.unlink()
        except OSError:
            pass
        raise
    if os.name == "posix":
        os.chmod(output, 0o600)
    return {"output": str(output), "files": len(entries), "target_repository": target_repo, "lane": lane,
            "transfer_status": "not_uploaded", "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", action="append", type=Path, required=True, help="explicit source file; repeat for each file")
    parser.add_argument("--output", type=Path, required=True, help="new output ZIP path; must not already exist")
    parser.add_argument("--target", required=True, help="explicit target OWNER/repository")
    parser.add_argument("--lane", required=True, help="explicit project lane slug")
    args = parser.parse_args(argv)
    try:
        result = build_package(args.file, args.output, args.lane, args.target)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    print("LOCAL PACKAGE ONLY: no source files were moved or changed; nothing was uploaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
