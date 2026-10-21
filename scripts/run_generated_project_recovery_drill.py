#!/usr/bin/env python3
"""Generate, capture, restore, and recatalog one disposable World Seed project."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def run(*args: str) -> str:
    result = subprocess.run([sys.executable, *args], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError((result.stdout + "\n" + result.stderr)[-5000:])
    return result.stdout


def catalog_record(catalog_path: Path, project_name: str) -> dict[str, object]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    matches = [item for item in catalog["projects"] if item["name"] == project_name]
    if len(matches) != 1:
        raise RuntimeError(f"expected one catalog record for {project_name}, found {len(matches)}")
    return matches[0]


def main() -> int:
    seed_root = Path(__file__).resolve().parents[1]
    generator = seed_root / "scripts" / "create_project.py"
    library = seed_root / "scripts" / "project_library.py"
    recovery = seed_root / "scripts" / "project_tree_recovery.py"
    project_name = "disposable-recovery-fixture"

    with tempfile.TemporaryDirectory(prefix="world-seed-generated-recovery-") as temporary:
        root = Path(temporary)
        source_parent = root / "source-projects"
        restored_parent = root / "restored-projects"
        source_parent.mkdir()
        restored_parent.mkdir()
        source = source_parent / project_name
        restored = restored_parent / project_name
        payload = root / "private-payload"
        source_catalog = root / "source-catalog.json"
        restored_catalog = root / "restored-catalog.json"

        run(
            str(generator), "--name", project_name,
            "--mission", "Prove a generated project can be recovered without losing its manifest.",
            "--destination", str(source),
            "--source-revision", "a" * 40,
        )
        original_manifest = json.loads((source / "world-seed-manifest.json").read_text(encoding="utf-8"))
        generated_files = original_manifest.get("generated_files")
        if not isinstance(generated_files, list) or not generated_files:
            raise RuntimeError("generated project manifest has no generated-file inventory")

        # Add representative owner userdata not listed among generated template files.
        (source / "user-data.bin").write_bytes(bytes(range(256)) + b"\x00\xff")
        notes = source / "notes"
        notes.mkdir()
        (notes / "operator-note.md").write_text("Synthetic user-authored note; preserve it.\n", encoding="utf-8")
        before = snapshot(source)

        run(str(library), "--root", str(source_parent), "--output", str(source_catalog))
        source_record = catalog_record(source_catalog, project_name)
        if source_record.get("status") != "generated-files-match":
            raise RuntimeError(f"source project did not catalog as generated-files-match: {source_record.get('status')}")

        capture_args = [
            str(recovery), "capture", "--source", str(source), "--output", str(payload),
        ]
        for name in generated_files:
            capture_args.extend(["--include", name])
        capture_args.extend([
            "--include", "world-seed-manifest.json",
            "--include", "user-data.bin",
            "--include", "notes",
        ])
        run(*capture_args)

        recovery_manifest = json.loads((payload / "project-tree-recovery.json").read_text(encoding="utf-8"))
        expected_paths = set(before)
        captured_paths = {entry["path"] for entry in recovery_manifest["files"]}
        if captured_paths != expected_paths:
            raise RuntimeError(
                f"capture inventory mismatch: missing={sorted(expected_paths - captured_paths)} "
                f"unexpected={sorted(captured_paths - expected_paths)}"
            )

        run(str(recovery), "restore", "--payload", str(payload), "--destination", str(restored))
        after_source = snapshot(source)
        restored_snapshot = snapshot(restored)
        if before != after_source:
            raise RuntimeError("source project changed during capture/restore")
        if before != restored_snapshot:
            raise RuntimeError("restored project bytes differ from the source project")
        restored_manifest = json.loads((restored / "world-seed-manifest.json").read_text(encoding="utf-8"))
        if restored_manifest != original_manifest:
            raise RuntimeError("World Seed project manifest did not survive capture/restore unchanged")
        if (restored / "user-data.bin").read_bytes() != (source / "user-data.bin").read_bytes():
            raise RuntimeError("synthetic binary userdata did not survive capture/restore")
        if (restored / "notes" / "operator-note.md").read_bytes() != (source / "notes" / "operator-note.md").read_bytes():
            raise RuntimeError("synthetic nested user note did not survive capture/restore")

        run(str(library), "--root", str(restored_parent), "--output", str(restored_catalog))
        restored_record = catalog_record(restored_catalog, project_name)
        if restored_record.get("status") != "generated-files-match":
            raise RuntimeError(
                f"restored project did not catalog as generated-files-match: {restored_record.get('status')}"
            )

        print("GENERATED_PROJECT_RECOVERY_DRILL=PASSED")
        print("scope=temporary generated project; synthetic userdata; no live project or network")
        print("checks=generator, project manifest preservation, nested note, binary bytes, independent tree hashes, source unchanged, restored catalog generated-files-match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
