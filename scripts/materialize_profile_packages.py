#!/usr/bin/env python3
"""Safely initialize private operator and personal-data package directories from generic templates."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import stat
from typing import Sequence

PACKAGE_FILES = {
    "operator-profile": ("README.md", "manifest.json", "PREFERENCES.md"),
    "personal-data": ("README.md", "manifest.json"),
}


def load_templates(root: Path) -> dict[str, dict[str, bytes]]:
    root = root.expanduser().absolute()
    packages: dict[str, dict[str, bytes]] = {}
    for package, names in PACKAGE_FILES.items():
        source = root / package
        if source.is_symlink() or not source.is_dir():
            raise ValueError(f"template directory is missing or unsafe: {package}")
        files: dict[str, bytes] = {}
        for name in names:
            path = source / name
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"template file is missing or unsafe: {package}/{name}")
            files[name] = path.read_bytes()
        try:
            manifest = json.loads(files["manifest.json"].decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"template manifest is invalid JSON: {package}") from exc
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or manifest.get("package_type") != package:
            raise ValueError(f"template manifest has the wrong schema or package type: {package}")
        packages[package] = files
    return packages


def normalize_destinations(operator: Path, personal: Path) -> dict[str, Path]:
    destinations = {
        "operator-profile": operator.expanduser().absolute(),
        "personal-data": personal.expanduser().absolute(),
    }
    resolved = {name: path.resolve(strict=False) for name, path in destinations.items()}
    first, second = resolved.values()
    if first == second or first in second.parents or second in first.parents:
        raise ValueError("package destinations must be distinct and must not contain one another")
    return destinations


def preflight(destinations: dict[str, Path], packages: dict[str, dict[str, bytes]]) -> dict[str, list[str]]:
    pending: dict[str, list[str]] = {}
    for package, destination in destinations.items():
        if destination.is_symlink():
            raise ValueError(f"destination must not be a symlink: {destination}")
        if destination.exists() and not destination.is_dir():
            raise ValueError(f"destination exists but is not a directory: {destination}")
        if destination.exists() and os.name == "posix":
            mode = stat.S_IMODE(destination.stat().st_mode)
            if mode & 0o077:
                raise ValueError(
                    f"existing destination is not private (mode {mode:04o}); "
                    f"secure it before retrying: {destination}"
                )
        missing: list[str] = []
        if destination.exists():
            for name, expected in packages[package].items():
                target = destination / name
                if target.is_symlink():
                    raise ValueError(f"refusing symlink at package file: {target}")
                if target.exists():
                    if not target.is_file() or target.read_bytes() != expected:
                        raise ValueError(
                            f"existing file differs from template; preserving it and refusing changes: {target}"
                        )
                else:
                    missing.append(name)
        else:
            missing.extend(packages[package])
        pending[package] = missing
    return pending


def materialize(
    template_root: Path, operator_destination: Path, personal_destination: Path
) -> dict[str, list[str]]:
    packages = load_templates(template_root)
    destinations = normalize_destinations(operator_destination, personal_destination)
    pending = preflight(destinations, packages)

    created_files: list[Path] = []
    created_directories: list[Path] = []
    try:
        for package, destination in destinations.items():
            if not destination.exists():
                destination.mkdir(parents=True, mode=0o700)
                created_directories.append(destination)
                if os.name == "posix":
                    os.chmod(destination, 0o700)
            for name in pending[package]:
                target = destination / name
                descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                created_files.append(target)
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(packages[package][name])
                if os.name == "posix":
                    os.chmod(target, 0o600)
                if target.read_bytes() != packages[package][name]:
                    raise ValueError(f"post-write verification failed: {target}")
    except Exception:
        for path in reversed(created_files):
            try:
                path.unlink()
            except OSError:
                pass
        for path in reversed(created_directories):
            try:
                path.rmdir()
            except OSError:
                pass
        raise
    return pending


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Initialize two private package directories without overwriting existing material."
    )
    parser.add_argument("--template-root", type=Path, default=Path(__file__).resolve().parents[1] / "templates")
    parser.add_argument("--operator-destination", type=Path, required=True)
    parser.add_argument("--personal-data-destination", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        pending = materialize(
            args.template_root, args.operator_destination, args.personal_data_destination
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    for package, names in pending.items():
        print(f"{package}: initialized; template files added={len(names)}; existing files preserved")
    print("No personal records were collected or restored. Template initialization is not a backup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
