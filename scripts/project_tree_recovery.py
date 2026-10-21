#!/usr/bin/env python3
"""Capture and restore a bounded project tree into a new isolated destination.

Git metadata is intentionally separate: .git entries are recorded as exclusions.
Only explicitly selected top-level roots are included; unsafe selected paths fail closed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
from typing import Sequence

MANIFEST_NAME = "project-tree-recovery.json"
SECRET_WORDS = ("secret", "credential", "token", "password", "private-key", "apikey", "api-key", ".env")
HASH_LENGTH = 64


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(value: str) -> bool:
    if not value or "\\" in value or "\x00" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and all(part not in ("", ".", "..") for part in value.split("/"))
        and str(path) == value
        and value != MANIFEST_NAME
    )


def secret_like(value: str) -> bool:
    folded = value.casefold()
    return any(word in folded for word in SECRET_WORDS)


def _inventory_tree(source: Path, includes: set[str], excluded: set[str]) -> tuple[list[dict[str, object]], list[str], list[dict[str, str]], list[dict[str, str]]]:
    files: list[dict[str, object]] = []
    directories: list[str] = []
    exclusions: list[dict[str, str]] = []
    selected_top = {item.split("/", 1)[0] for item in includes}
    not_captured = [
        {"path": item.name, "reason": "not selected by explicit capture roots"}
        for item in sorted(source.iterdir(), key=lambda item: item.name)
        if item.name not in selected_top and item.name != ".git" and item.name not in {value.split("/", 1)[0] for value in excluded}
    ]
    for current, dirnames, filenames in os.walk(source, topdown=True, followlinks=False):
        current_path = Path(current)
        relative_dir = current_path.relative_to(source).as_posix()
        if relative_dir == ".":
            relative_dir = ""
        if relative_dir and not any(root == relative_dir or root.startswith(relative_dir + "/") or relative_dir.startswith(root + "/") for root in includes):
            dirnames[:] = []
            continue
        kept_dirs: list[str] = []
        for name in sorted(dirnames):
            path = current_path / name
            rel = (Path(relative_dir) / name).as_posix() if relative_dir else name
            if name == ".git":
                exclusions.append({"path": rel, "reason": "Git history and metadata are a separate recovery category"})
                continue
            if any(rel == item or rel.startswith(item + "/") for item in excluded):
                if rel in excluded:
                    exclusions.append({"path": rel, "reason": "explicitly excluded by operator"})
                continue
            selected = any(rel == item or rel.startswith(item + "/") for item in includes)
            ancestor_of_selection = any(item.startswith(rel + "/") for item in includes)
            if not selected and not ancestor_of_selection:
                continue
            if path.is_symlink():
                raise ValueError(f"symlink directory is not allowed: {rel}")
            if not path.is_dir():
                raise ValueError(f"non-directory entry in directory inventory: {rel}")
            if secret_like(rel):
                raise ValueError(f"credential-like path requires review and cannot be captured: {rel}")
            kept_dirs.append(name)
            directories.append(rel)
        dirnames[:] = kept_dirs
        for name in sorted(filenames):
            path = current_path / name
            rel = (Path(relative_dir) / name).as_posix() if relative_dir else name
            if not safe_relative(rel):
                raise ValueError(f"unsafe relative path: {rel!r}")
            if name == ".git":
                exclusions.append({"path": rel, "reason": "Git metadata pointer is a separate recovery category"})
                continue
            if any(rel == item or rel.startswith(item + "/") for item in excluded):
                if rel in excluded:
                    exclusions.append({"path": rel, "reason": "explicitly excluded by operator"})
                continue
            if not any(rel == item or rel.startswith(item + "/") for item in includes):
                continue
            if secret_like(rel):
                raise ValueError(f"credential-like path requires review and cannot be captured: {rel}")
            if path.is_symlink():
                raise ValueError(f"symlink file is not allowed: {rel}")
            try:
                mode = path.lstat().st_mode
            except OSError as exc:
                raise ValueError(f"cannot inspect path {rel}: {exc}") from exc
            if not stat.S_ISREG(mode):
                raise ValueError(f"special files are not allowed: {rel}")
            files.append({
                "path": rel,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "executable": bool(mode & 0o111),
            })
    return sorted(files, key=lambda item: str(item["path"])), sorted(set(directories)), sorted(exclusions, key=lambda item: item["path"]), not_captured


def _check_destination_separation(source: Path, destination: Path, label: str) -> None:
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError(f"{label} and source/payload must not contain one another")


def capture(source: Path, output: Path, includes: Sequence[str], excludes: Sequence[str] = ()) -> dict[str, object]:
    source = source.expanduser().absolute()
    output = output.expanduser().absolute()
    if source.is_symlink() or not source.is_dir():
        raise ValueError("source must be an existing, non-symlink directory")
    if output.exists() or output.is_symlink():
        raise ValueError("payload output must not already exist")
    _check_destination_separation(source, output, "payload output")
    selected = set(includes)
    excluded = set(excludes)
    if not selected or len(selected) != len(list(includes)) or any(not safe_relative(item) or len(item.split("/")) != 1 or ".git" in item.split("/") or secret_like(item) for item in selected):
        raise ValueError("provide unique explicit direct-child file/directory roots; do not include Git metadata or credential-like paths")
    if len(excluded) != len(list(excludes)) or any(not safe_relative(item) for item in excluded):
        raise ValueError("exclusions must be unique safe relative paths; repeat --exclude for each exact path")
    if any(any(root == item or root.startswith(item + "/") for item in excluded) for root in selected):
        raise ValueError("an include root conflicts with an exclusion")
    for item in selected:
        path = source / item
        if path.is_symlink() or not path.exists() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"include root must exist and be a regular file or directory, not a symlink: {item}")
    files, directories, exclusions, not_captured = _inventory_tree(source, selected, excluded)
    if not files:
        raise ValueError("refusing to create an empty file payload")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".project-tree-capture-", dir=output.parent))
    try:
        if os.name == "posix":
            os.chmod(staging, 0o700)
        for directory in directories:
            (staging / directory).mkdir(parents=True, exist_ok=True)
        for item in files:
            relative = str(item["path"])
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, target, follow_symlinks=False)
            if os.name == "posix":
                os.chmod(target, 0o700 if item["executable"] else 0o600)
            if target.is_symlink() or target.stat().st_size != item["size_bytes"] or sha256_file(target) != item["sha256"]:
                raise ValueError(f"captured file verification failed: {relative}")
        manifest: dict[str, object] = {
            "schema_version": 1,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "capture_scope": "recursive regular files beneath explicitly selected roots only; .git excluded; exclusions and unselected top-level entries recorded; credential-like paths and symlinks refused",
            "git_history": "excluded; recover separately with a Git bundle/clone and isolated ref verification",
            "files": files,
            "directories": directories,
            "exclusions": exclusions,
            "not_captured": not_captured,
        }
        manifest_path = staging / MANIFEST_NAME
        with manifest_path.open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2, sort_keys=True)
            stream.write("\n")
        if os.name == "posix":
            os.chmod(manifest_path, 0o600)
        os.rename(staging, output)
        return manifest
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _validate_manifest(payload: Path) -> tuple[dict[str, object], dict[str, dict[str, object]], list[str]]:
    manifest_path = payload / MANIFEST_NAME
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("payload manifest must be a regular file")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("payload manifest is unreadable or invalid JSON") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("unsupported payload manifest schema")
    files = manifest.get("files")
    directories = manifest.get("directories")
    if not isinstance(files, list) or not files or not isinstance(directories, list):
        raise ValueError("manifest must contain non-empty files and a directory inventory")
    expected: dict[str, dict[str, object]] = {}
    folded: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("invalid file inventory entry")
        name, digest, size, executable = item.get("path"), item.get("sha256"), item.get("size_bytes"), item.get("executable")
        if not isinstance(name, str) or not safe_relative(name) or name in expected or name.casefold() in folded:
            raise ValueError("unsafe, duplicate, or case-colliding file path in manifest")
        if secret_like(name):
            raise ValueError(f"credential-like path in manifest: {name}")
        if not isinstance(digest, str) or len(digest) != HASH_LENGTH or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError(f"invalid file hash in manifest: {name}")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0 or not isinstance(executable, bool):
            raise ValueError(f"invalid file metadata in manifest: {name}")
        expected[name] = item
        folded.add(name.casefold())
    safe_dirs: list[str] = []
    for name in directories:
        if not isinstance(name, str) or not safe_relative(name) or name in safe_dirs or name.casefold() in folded:
            raise ValueError("unsafe, duplicate, or colliding directory path in manifest")
        if secret_like(name):
            raise ValueError(f"credential-like directory in manifest: {name}")
        safe_dirs.append(name)
        folded.add(name.casefold())
    return manifest, expected, safe_dirs


def _walk_payload(payload: Path) -> set[str]:
    found: set[str] = {MANIFEST_NAME}
    for current, dirnames, filenames in os.walk(payload, topdown=True, followlinks=False):
        base = Path(current)
        for name in list(dirnames):
            path = base / name
            if path.is_symlink() or not path.is_dir():
                raise ValueError(f"payload contains unsafe directory entry: {path.relative_to(payload)}")
            found.add(path.relative_to(payload).as_posix())
        for name in filenames:
            path = base / name
            rel = path.relative_to(payload).as_posix()
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"payload contains unsafe file entry: {rel}")
            found.add(rel)
    return found


def restore(payload: Path, destination: Path) -> dict[str, object]:
    payload = payload.expanduser().absolute()
    destination = destination.expanduser().absolute()
    if payload.is_symlink() or not payload.is_dir():
        raise ValueError("payload must be an existing, non-symlink directory")
    if destination.exists() or destination.is_symlink():
        raise ValueError("restore destination must not already exist; refusing to overwrite")
    _check_destination_separation(payload, destination, "restore destination")
    manifest, expected, directories = _validate_manifest(payload)
    expected_paths = set(expected) | set(directories) | {MANIFEST_NAME}
    actual_paths = _walk_payload(payload)
    if actual_paths != expected_paths:
        raise ValueError(f"payload entries differ from manifest; missing={sorted(expected_paths-actual_paths)}, unexpected={sorted(actual_paths-expected_paths)}")
    for name, item in expected.items():
        path = payload / name
        if path.stat().st_size != item["size_bytes"] or sha256_file(path) != item["sha256"]:
            raise ValueError(f"payload verification failed: {name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".project-tree-restore-", dir=destination.parent))
    try:
        if os.name == "posix":
            os.chmod(staging, 0o700)
        for directory in directories:
            (staging / directory).mkdir(parents=True, exist_ok=True)
        for name, item in sorted(expected.items()):
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(payload / name, target, follow_symlinks=False)
            if os.name == "posix":
                os.chmod(target, 0o700 if item["executable"] else 0o600)
        for name, item in expected.items():
            target = staging / name
            if target.is_symlink() or target.stat().st_size != item["size_bytes"] or sha256_file(target) != item["sha256"]:
                raise ValueError(f"restored file verification failed: {name}")
        for directory in directories:
            if not (staging / directory).is_dir():
                raise ValueError(f"restored directory missing: {directory}")
        os.rename(staging, destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture and restore a manifest-backed project tree.")
    commands = parser.add_subparsers(dest="command", required=True)
    capture_parser = commands.add_parser("capture", help="capture a project tree into a new private payload")
    capture_parser.add_argument("--source", type=Path, required=True)
    capture_parser.add_argument("--output", type=Path, required=True)
    capture_parser.add_argument("--include", action="append", required=True, help="explicit direct-child file/directory root to capture recursively; repeat for every approved root")
    capture_parser.add_argument("--exclude", action="append", default=[], help="exact relative path to exclude; repeat as needed")
    restore_parser = commands.add_parser("restore", help="verify and restore into a new isolated destination")
    restore_parser.add_argument("--payload", type=Path, required=True)
    restore_parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            manifest = capture(args.source, args.output, args.include, args.exclude)
            print(f"PROJECT_TREE_CAPTURE=VERIFIED files={len(manifest['files'])} directories={len(manifest['directories'])} exclusions={len(manifest['exclusions'])} not_selected={len(manifest['not_captured'])}")
            print("Git history remains separate; review every exclusion before relying on this payload.")
        else:
            manifest = restore(args.payload, args.destination)
            print(f"PROJECT_TREE_RESTORE=VERIFIED files={len(manifest['files'])} directories={len(manifest['directories'])}")
            print("This verifies restored tree bytes, not Git history or GitHub-only records.")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
