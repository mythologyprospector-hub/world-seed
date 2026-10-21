#!/usr/bin/env python3
"""Capture and restore an explicit, bounded set of project files without overwriting data."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Sequence

PAYLOAD_MANIFEST = "recovery-payload.json"
SECRET_WORDS = ("secret", "credential", "token", "password", "private-key", "apikey", "api-key", ".env")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(name: str) -> bool:
    path = Path(name)
    folded = name.casefold()
    return (
        bool(name)
        and not path.is_absolute()
        and len(path.parts) == 1
        and "/" not in name
        and "\\" not in name
        and name not in {".", "..", PAYLOAD_MANIFEST}
        and not name.startswith(".")
        and not any(word in folded for word in SECRET_WORDS)
        and "\x00" not in name
    )


def capture(source: Path, output: Path, includes: Sequence[str]) -> dict[str, object]:
    source = source.expanduser().absolute()
    output = output.expanduser().absolute()
    if source.is_symlink() or not source.is_dir():
        raise ValueError("source must be an existing, non-symlink directory")
    if output.exists() or output.is_symlink():
        raise ValueError("payload output must not already exist")
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("payload output and source must not contain one another")
    names = list(includes)
    if not names or len(names) != len(set(names)) or any(not safe_name(name) for name in names):
        raise ValueError("include explicit, unique, safe direct-child filenames; no secrets, hidden files, or manifests")
    files: list[dict[str, str | int]] = []
    for name in sorted(names):
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"requested file is missing, not regular, or a symlink: {name}")
        info = path.stat()
        files.append({"path": name, "sha256": sha256_file(path), "size_bytes": info.st_size})
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".recovery-capture-", dir=output.parent))
    try:
        if os.name == "posix":
            os.chmod(temporary, 0o700)
        for item in files:
            shutil.copyfile(source / str(item["path"]), temporary / str(item["path"]), follow_symlinks=False)
            if os.name == "posix":
                os.chmod(temporary / str(item["path"]), 0o600)
            copied = temporary / str(item["path"])
            if copied.is_symlink() or not copied.is_file():
                raise ValueError(f"captured file is not a regular file: {item['path']}")
            if copied.stat().st_size != item["size_bytes"] or sha256_file(copied) != item["sha256"]:
                raise ValueError(f"captured file verification failed: {item['path']}")
        project_manifest = source / "world-seed-manifest.json"
        source_revision = "unknown"
        if project_manifest.is_file() and not project_manifest.is_symlink():
            try:
                candidate = json.loads(project_manifest.read_text(encoding="utf-8"))
                if isinstance(candidate, dict) and isinstance(candidate.get("source_revision"), str):
                    source_revision = candidate["source_revision"]
            except (OSError, UnicodeError, json.JSONDecodeError):
                pass
        manifest = {
            "schema_version": 1,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_revision": source_revision,
            "capture_scope": "explicit direct-child regular files only; not a complete project backup",
            "files": files,
        }
        manifest_path = temporary / PAYLOAD_MANIFEST
        with manifest_path.open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2, sort_keys=True)
            stream.write("\n")
        if os.name == "posix":
            os.chmod(manifest_path, 0o600)
        os.rename(temporary, output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return manifest


def restore(payload: Path, destination: Path) -> dict[str, object]:
    payload = payload.expanduser().absolute()
    destination = destination.expanduser().absolute()
    if payload.is_symlink() or not payload.is_dir():
        raise ValueError("payload must be an existing, non-symlink directory")
    if destination.exists() or destination.is_symlink():
        raise ValueError("restore destination must not already exist; refusing to overwrite")
    if payload == destination or payload in destination.parents or destination in payload.parents:
        raise ValueError("payload and destination must not contain one another")
    manifest_path = payload / PAYLOAD_MANIFEST
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("payload manifest must be a regular file")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("payload manifest is unreadable or invalid JSON") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("unsupported payload manifest schema")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("payload must list at least one file")
    expected: dict[str, dict[str, object]] = {}
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("invalid file inventory entry")
        name, digest, size = item.get("path"), item.get("sha256"), item.get("size_bytes")
        if not isinstance(name, str) or not safe_name(name) or name in expected:
            raise ValueError("unsafe or duplicate file path in manifest")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise ValueError("invalid file hash in manifest")
        if not isinstance(size, int) or size < 0:
            raise ValueError("invalid file size in manifest")
        expected[name] = item
    actual_names = {p.name for p in payload.iterdir()}
    if actual_names != set(expected) | {PAYLOAD_MANIFEST}:
        raise ValueError("payload contains missing or unexpected files; refusing restore")
    for name, item in expected.items():
        path = payload / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"payload file is missing, not regular, or a symlink: {name}")
        if path.stat().st_size != item["size_bytes"] or sha256_file(path) != item["sha256"]:
            raise ValueError(f"payload verification failed: {name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".recovery-restore-", dir=destination.parent))
    try:
        if os.name == "posix":
            os.chmod(staging, 0o700)
        for name in sorted(expected):
            shutil.copyfile(payload / name, staging / name, follow_symlinks=False)
            if os.name == "posix":
                os.chmod(staging / name, 0o600)
        for name, item in expected.items():
            restored = staging / name
            if restored.is_symlink() or sha256_file(restored) != item["sha256"]:
                raise ValueError(f"restored file verification failed: {name}")
        os.rename(staging, destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture or restore an explicit selective recovery payload.")
    commands = parser.add_subparsers(dest="command", required=True)
    capture_parser = commands.add_parser("capture", help="capture explicit files into a new private payload directory")
    capture_parser.add_argument("--source", type=Path, required=True)
    capture_parser.add_argument("--output", type=Path, required=True)
    capture_parser.add_argument("--include", action="append", required=True, help="one direct-child filename; repeat for each file")
    restore_parser = commands.add_parser("restore", help="verify a payload and restore into a new destination")
    restore_parser.add_argument("--payload", type=Path, required=True)
    restore_parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            manifest = capture(args.source, args.output, args.include)
            print(f"Selective payload captured: {args.output.expanduser().absolute()}")
            print(f"Files captured: {len(manifest['files'])}")
        else:
            manifest = restore(args.payload, args.destination)
            print(f"Selective payload restored and verified: {args.destination.expanduser().absolute()}")
            print(f"Files restored: {len(manifest['files'])}")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print("Scope is explicit files only; this is not a complete project or GitHub-account backup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
