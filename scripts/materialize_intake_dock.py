#!/usr/bin/env python3
"""Initialize a private local Intake Dock without overwriting supplied material."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
from typing import Sequence

DOCK_FILES = ("README.md", "DROP_HERE.md", "manifest.json")
DOCK_DIRS = ("incoming", "originals", "working-copies", "outputs")


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


def materialize(template_root: Path, destination: Path) -> dict[str, object]:
    templates = load_templates(template_root)
    destination = destination.expanduser().absolute()
    if destination.is_symlink():
        raise ValueError("Intake Dock destination must not be a symlink")
    if destination.exists() and not destination.is_dir():
        raise ValueError("Intake Dock destination exists but is not a directory")
    if destination.exists() and os.name == "posix":
        mode = stat.S_IMODE(destination.stat().st_mode)
        if mode & 0o077:
            raise ValueError(f"Intake Dock destination is not private (mode {mode:04o}); secure it before retrying")

    missing_files: list[str] = []
    missing_dirs: list[str] = []
    if destination.exists():
        for name in DOCK_FILES:
            target = destination / name
            if target.is_symlink():
                raise ValueError(f"refusing symlink at Intake Dock template file: {name}")
            if target.exists():
                if not target.is_file() or target.read_bytes() != templates[name]:
                    raise ValueError(f"existing file differs from template; preserving it and refusing changes: {name}")
            else:
                missing_files.append(name)
        for name in DOCK_DIRS:
            target = destination / name
            if target.is_symlink():
                raise ValueError(f"refusing symlink at Intake Dock directory: {name}")
            if target.exists():
                if not target.is_dir():
                    raise ValueError(f"expected a directory but found another file type: {name}")
                if os.name == "posix" and stat.S_IMODE(target.stat().st_mode) & 0o077:
                    raise ValueError(f"Intake Dock subdirectory is not private: {name}")
            else:
                missing_dirs.append(name)
    else:
        missing_files = list(DOCK_FILES)
        missing_dirs = list(DOCK_DIRS)

    created_files: list[Path] = []
    created_dirs: list[Path] = []
    try:
        if not destination.exists():
            destination.mkdir(parents=True, mode=0o700)
            created_dirs.append(destination)
        if os.name == "posix":
            os.chmod(destination, 0o700)
        for name in missing_dirs:
            path = destination / name
            path.mkdir(mode=0o700)
            created_dirs.append(path)
            if os.name == "posix":
                os.chmod(path, 0o700)
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

    return {"files_added": missing_files, "directories_added": missing_dirs, "destination": str(destination)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize a local private Intake Dock; no GitHub access or upload.")
    parser.add_argument("--template-root", type=Path, default=Path(__file__).resolve().parents[1] / "templates" / "intake-dock")
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = materialize(args.template_root, args.destination)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Intake Dock initialized locally: files added={len(result['files_added'])}; directories added={len(result['directories_added'])}.")
    print("Existing unrelated material was preserved. No GitHub repository was created and no data was uploaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
