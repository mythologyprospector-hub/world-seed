#!/usr/bin/env python3
"""Build a private, metadata-only catalog of local project directories."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Sequence

MANIFEST_NAME = "world-seed-manifest.json"
SHA256_LENGTH = 64


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_project(path: Path) -> dict[str, object]:
    """Describe one directory without reading arbitrary project contents."""
    record: dict[str, object] = {
        "name": path.name,
        "path": str(path.resolve()),
        "status": "unmanaged-directory",
        "manifest_present": False,
        "verification": "not-applicable",
    }
    manifest_path = path / MANIFEST_NAME
    if not manifest_path.exists():
        return record
    record["manifest_present"] = True
    if manifest_path.is_symlink() or not manifest_path.is_file():
        record.update(status="invalid-manifest", verification="manifest-not-regular-file")
        return record
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        record.update(status="invalid-manifest", verification="manifest-unreadable-or-invalid-json")
        return record
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        record.update(status="invalid-manifest", verification="unsupported-manifest-schema")
        return record
    generated_files = manifest.get("generated_files")
    if (
        not isinstance(generated_files, list)
        or not generated_files
        or any(not isinstance(name, str) or not name or Path(name).is_absolute()
               or ".." in Path(name).parts or len(Path(name).parts) != 1
               for name in generated_files)
        or len(set(generated_files)) != len(generated_files)
    ):
        record.update(status="invalid-manifest", verification="unsafe-or-invalid-generated-file-list")
        return record

    record["project_name"] = str(manifest.get("project_name", path.name))
    record["mission"] = str(manifest.get("mission", ""))
    record["template_version"] = str(manifest.get("template_version", "unknown"))
    record["source_revision"] = str(manifest.get("source_revision", "unknown"))
    record["generated_file_count"] = len(generated_files)
    missing = []
    unsafe = []
    actual_hashes: dict[str, str] = {}
    for name in sorted(generated_files):
        file_path = path / name
        if file_path.is_symlink():
            unsafe.append(name)
        elif not file_path.is_file():
            missing.append(name)
        else:
            try:
                actual_hashes[name] = sha256_file(file_path)
            except OSError:
                missing.append(name)
    if unsafe:
        record.update(status="unsafe-project-files", verification="symlink-generated-files", unsafe_files=unsafe)
        return record
    if missing:
        record.update(status="missing-generated-files", verification="missing-or-unreadable", missing_files=missing)
        return record

    expected_hashes = manifest.get("generated_file_sha256")
    if not isinstance(expected_hashes, dict):
        record.update(status="cataloged-legacy-unverified", verification="manifest-has-no-file-hashes")
        return record
    if set(expected_hashes) != set(generated_files) or any(
        not isinstance(expected_hashes.get(name), str)
        or len(expected_hashes[name]) != SHA256_LENGTH
        or any(char not in "0123456789abcdef" for char in expected_hashes[name])
        for name in generated_files
    ):
        record.update(status="invalid-manifest", verification="invalid-hash-inventory")
        return record
    changed = [name for name in sorted(generated_files) if actual_hashes[name] != expected_hashes[name]]
    if changed:
        record.update(status="generated-files-drift", verification="hash-mismatch", changed_files=changed)
    else:
        record.update(status="generated-files-match", verification="generated-files-match-manifest")
    return record


def build_catalog(roots: Sequence[Path]) -> dict[str, object]:
    projects: list[dict[str, object]] = []
    normalized_roots: list[Path] = []
    for raw_root in roots:
        if raw_root.is_symlink():
            raise ValueError(f"catalog root must not be a symbolic link: {raw_root}")
        root = raw_root.expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"catalog root is not a directory: {root}")
        if root not in normalized_roots:
            normalized_roots.append(root)
    for root in normalized_roots:
        for child in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
            if child.is_symlink() or not child.is_dir():
                continue
            projects.append(inspect_project(child))
    projects.sort(key=lambda item: (str(item.get("name", "")).casefold(), str(item.get("path", ""))))
    return {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "catalog_roots": [str(root) for root in normalized_roots],
        "project_count": len(projects),
        "status_counts": {
            status: sum(project.get("status") == status for project in projects)
            for status in sorted({str(project.get("status")) for project in projects})
        },
        "projects": projects,
        "recovery_claim": "none; catalog status is not proof of backup or successful restoration",
    }


def write_private_json(destination: Path, payload: dict[str, object]) -> None:
    """Atomically write a JSON report with owner-only permissions."""
    if destination.is_symlink():
        raise ValueError(f"output must not be a symbolic link: {destination}")
    destination = destination.expanduser().absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not stat.S_ISREG(destination.stat().st_mode):
        raise ValueError(f"output must be a regular file: {destination}")
    fd, temporary_name = tempfile.mkstemp(prefix=".project-library-", dir=destination.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, destination)
        os.chmod(destination, 0o600)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Catalog local project directories without changing them.")
    parser.add_argument("--root", action="append", required=True, type=Path,
                        help="parent directory to scan one level deep; may be repeated")
    parser.add_argument("--output", required=True, type=Path,
                        help="private JSON catalog path outside every scanned root")
    args = parser.parse_args(argv)
    try:
        roots = [path.expanduser().resolve() for path in args.root]
        output = args.output.expanduser().resolve()
        for root in roots:
            if output == root or root in output.parents:
                raise ValueError("catalog output must be outside every scanned root")
        catalog = build_catalog(args.root)
        write_private_json(args.output, catalog)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Catalog written: {args.output.expanduser().absolute()}")
    print(f"Directories cataloged: {catalog['project_count']}")
    print("This is an inventory only; it does not back up, modify, or certify recovery of any project.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
