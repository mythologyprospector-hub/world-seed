#!/usr/bin/env python3
"""Initialize a private local Intake Dock lane without overwriting supplied material."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
from typing import Sequence

DOCK_FILES = ("README.md", "DROP_HERE.md", "manifest.json")
LANE_DIRS = ("incoming", "inventory", "working", "reports")
LANE_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,98}[a-z0-9])?\Z")


def load_templates(template_root: Path) -> dict[str, bytes]:
    root = template_root.expanduser().absolute()
    files: dict[str, bytes] = {}
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Intake Dock template root is missing or unsafe")
    for name in DOCK_FILES:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Intake Dock template file is missing or unsafe: {name}")
        files[name] = path.read_bytes()
    try:
        manifest = json.loads(files["manifest.json"].decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Intake Dock template manifest is invalid JSON") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or manifest.get("package_type") != "intake-dock":
        raise ValueError("Intake Dock template manifest has the wrong schema or package type")
    return files


def _private_directory(path: Path, label: str) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing symlink at {label}")
    if path.exists():
        if not path.is_dir():
            raise ValueError(f"expected a directory at {label}")
        if os.name == "posix" and stat.S_IMODE(path.stat().st_mode) & 0o077:
            raise ValueError(f"{label} is not private; secure it before retrying")


def materialize(template_root: Path, destination: Path, lane: str) -> dict[str, object]:
    if not LANE_PATTERN.fullmatch(lane):
        raise ValueError("lane must be a lowercase repository-style slug (letters, digits, hyphens)")
    templates = load_templates(template_root)
    destination = destination.expanduser().absolute()
    if destination.exists():
        _private_directory(destination, "Intake Dock destination")
    else:
        parent = destination.parent
        if not parent.is_dir() or parent.is_symlink():
            raise ValueError("Intake Dock parent must already exist and must not be a symlink")
        if os.name == "posix" and stat.S_IMODE(parent.stat().st_mode) & 0o077:
            raise ValueError("Intake Dock parent is not private; choose a private parent or secure it first")

    lane_root = destination / "projects" / lane
    expected_dirs = [destination, destination / "projects", lane_root, *(lane_root / name for name in LANE_DIRS)]
    for directory in expected_dirs:
        if directory.exists():
            _private_directory(directory, f"Intake Dock directory: {directory.relative_to(destination)}")

    missing_files: list[str] = []
    for name in DOCK_FILES:
        target = destination / name
        if target.is_symlink():
            raise ValueError(f"refusing symlink at Intake Dock template file: {name}")
        if target.exists():
            if not target.is_file() or target.read_bytes() != templates[name]:
                raise ValueError(f"existing file differs from template; preserving it and refusing changes: {name}")
        else:
            missing_files.append(name)

    missing_dirs = [str(directory.relative_to(destination)) for directory in expected_dirs if not directory.exists()]
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    try:
        for directory in expected_dirs:
            if not directory.exists():
                directory.mkdir(mode=0o700)
                created_dirs.append(directory)
            if os.name == "posix":
                os.chmod(directory, 0o700)
        for name in missing_files:
            path = destination / name
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created_files.append(path)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(templates[name])
            if os.name == "posix":
                os.chmod(path, 0o600)
            if path.read_bytes() != templates[name]:
                raise ValueError(f"post-write verification failed: {name}")
    except Exception:
        for path in reversed(created_files):
            try:
                path.unlink()
            except OSError:
                pass
        for path in reversed(created_dirs):
            try:
                path.rmdir()
            except OSError:
                pass
        raise

    return {"files_added": missing_files, "directories_added": missing_dirs, "destination": str(destination), "lane": lane}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize a local private Intake Dock lane; no GitHub access or upload.")
    parser.add_argument("--template-root", type=Path, default=Path(__file__).resolve().parents[1] / "templates" / "intake-dock")
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--lane", required=True, help="explicit lowercase repository-style project lane slug")
    args = parser.parse_args(argv)
    try:
        result = materialize(args.template_root, args.destination, args.lane)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Intake Dock initialized locally for lane {result['lane']}: files added={len(result['files_added'])}; directories added={len(result['directories_added'])}.")
    print("Existing unrelated material was preserved. No GitHub repository was created and no data was uploaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
