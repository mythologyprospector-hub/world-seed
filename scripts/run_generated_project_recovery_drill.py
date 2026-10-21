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
        if path.is_file()
        and not path.is_symlink()
        and ".git" not in path.relative_to(root).parts
    }


def run(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        [args[0], *args[1:]], cwd=cwd, capture_output=True, text=True, timeout=30
    )
    if result.returncode:
        raise RuntimeError((result.stdout + "\n" + result.stderr)[-5000:])
    return result.stdout.strip()


def run_python(*args: str) -> str:
    return run(sys.executable, *args)


def catalog_record(catalog_path: Path, project_name: str) -> dict[str, object]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    matches = [item for item in catalog["projects"] if item["name"] == project_name]
    if len(matches) != 1:
        raise RuntimeError(f"expected one catalog record for {project_name}, found {len(matches)}")
    return matches[0]


def overlay_tree(source_tree: Path, git_checkout: Path) -> None:
    """Overlay captured working-tree files without copying the separate .git directory."""
    for path in sorted(source_tree.rglob("*")):
        relative = path.relative_to(source_tree)
        target = git_checkout / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file() and not path.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())


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
        restored_tree = root / "restored-tree"
        restored_git = restored_parent / project_name
        payload = root / "private-payload"
        bundle = root / "project-history.bundle"
        source_catalog = root / "source-catalog.json"
        restored_catalog = root / "restored-catalog.json"

        run_python(
            str(generator), "--name", project_name,
            "--mission", "Prove a generated project can be recovered without losing its manifest.",
            "--destination", str(source),
            "--source-revision", "a" * 40,
        )
        original_manifest = json.loads((source / "world-seed-manifest.json").read_text(encoding="utf-8"))
        generated_files = original_manifest.get("generated_files")
        if not isinstance(generated_files, list) or not generated_files:
            raise RuntimeError("generated project manifest has no generated-file inventory")

        # Create a real local Git checkpoint, then keep user edits/data outside that checkpoint.
        working_notes = source / "operator-working-notes.md"
        working_notes.write_text("committed baseline note\n", encoding="utf-8")
        run("git", "init", "-q", str(source))
        run("git", "config", "user.name", "World Seed Generated Recovery Drill", cwd=source)
        run("git", "config", "user.email", "generated-recovery@example.invalid", cwd=source)
        run("git", "add", ".", cwd=source)
        run("git", "commit", "-qm", "Checkpoint generated project", cwd=source)
        checkpoint = run("git", "rev-parse", "HEAD", cwd=source)
        run("git", "bundle", "create", str(bundle), "--all", cwd=source)
        run("git", "bundle", "verify", str(bundle), cwd=source)

        # Deliberately create an uncommitted tracked edit and untracked user data.
        working_notes.write_text("edited after checkpoint; recover this working-tree change.\n", encoding="utf-8")
        (source / "user-data.bin").write_bytes(bytes(range(256)) + b"\x00\xff")
        notes = source / "notes"
        notes.mkdir()
        (notes / "operator-note.md").write_text("Synthetic user-authored note; preserve it.\n", encoding="utf-8")
        source_status_before = run("git", "status", "--porcelain", cwd=source)
        before = snapshot(source)

        run_python(str(library), "--root", str(source_parent), "--output", str(source_catalog))
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
            "--include", "operator-working-notes.md",
            "--include", "user-data.bin",
            "--include", "notes",
        ])
        run_python(*capture_args)

        recovery_manifest = json.loads((payload / "project-tree-recovery.json").read_text(encoding="utf-8"))
        expected_paths = set(before)
        captured_paths = {entry["path"] for entry in recovery_manifest["files"]}
        if captured_paths != expected_paths:
            raise RuntimeError(
                f"capture inventory mismatch: missing={sorted(expected_paths - captured_paths)} "
                f"unexpected={sorted(captured_paths - expected_paths)}"
            )
        if not any(entry["path"] == ".git" for entry in recovery_manifest["exclusions"]):
            raise RuntimeError("Git metadata was not explicitly recorded as a separate recovery category")

        run_python(str(recovery), "restore", "--payload", str(payload), "--destination", str(restored_tree))
        restored_tree_snapshot = snapshot(restored_tree)
        if before != restored_tree_snapshot:
            raise RuntimeError("restored project-tree bytes differ from the source project")
        restored_manifest = json.loads((restored_tree / "world-seed-manifest.json").read_text(encoding="utf-8"))
        if restored_manifest != original_manifest:
            raise RuntimeError("World Seed project manifest did not survive capture/restore unchanged")
        if (restored_tree / "user-data.bin").read_bytes() != (source / "user-data.bin").read_bytes():
            raise RuntimeError("synthetic binary userdata did not survive capture/restore")
        if (restored_tree / "notes" / "operator-note.md").read_bytes() != (source / "notes" / "operator-note.md").read_bytes():
            raise RuntimeError("synthetic nested user note did not survive capture/restore")

        # Restore Git history separately, then overlay the recovered working tree.
        run("git", "clone", "-q", str(bundle), str(restored_git))
        restored_head = run("git", "rev-parse", "HEAD", cwd=restored_git)
        if restored_head != checkpoint:
            raise RuntimeError("Git bundle restore did not preserve the checkpoint commit")
        overlay_tree(restored_tree, restored_git)
        if snapshot(restored_git) != before:
            raise RuntimeError("combined Git-history plus working-tree restore differs from source")
        restored_status = run("git", "status", "--porcelain", cwd=restored_git)
        if restored_status != source_status_before:
            raise RuntimeError("restored working-tree/index status differs from the source status")
        if run("git", "rev-parse", "HEAD", cwd=source) != checkpoint:
            raise RuntimeError("source Git checkpoint changed during recovery")
        if run("git", "status", "--porcelain", cwd=source) != source_status_before:
            raise RuntimeError("source Git working-tree status changed during recovery")

        run_python(str(library), "--root", str(restored_parent), "--output", str(restored_catalog))
        restored_record = catalog_record(restored_catalog, project_name)
        if restored_record.get("status") != "generated-files-match":
            raise RuntimeError(
                f"restored project did not catalog as generated-files-match: {restored_record.get('status')}"
            )

        # Exercise the separate operator-profile and personal-data packages with synthetic records.
        profile_materializer = seed_root / "scripts" / "materialize_profile_packages.py"
        profile_source = root / "private-packages"
        operator_package = profile_source / "operator-profile"
        personal_package = profile_source / "personal-data"
        run_python(
            str(profile_materializer),
            "--template-root", str(seed_root / "templates"),
            "--operator-destination", str(operator_package),
            "--personal-data-destination", str(personal_package),
        )
        (operator_package / "PREFERENCES.md").write_text(
            "# Synthetic operator preferences\\nUse concise status updates.\\n",
            encoding="utf-8",
        )
        (personal_package / "family-records.md").write_text(
            "# Synthetic personal record\\nFixture-only data; not a real person.\\n",
            encoding="utf-8",
        )
        profile_before = snapshot(profile_source)
        profile_payload = root / "private-profile-payload"
        profile_restored = root / "restored-private-packages"
        run_python(
            str(recovery), "capture", "--source", str(profile_source),
            "--output", str(profile_payload),
            "--include", "operator-profile", "--include", "personal-data",
        )
        profile_manifest = json.loads(
            (profile_payload / "project-tree-recovery.json").read_text(encoding="utf-8")
        )
        if {entry["path"] for entry in profile_manifest["files"]} != set(profile_before):
            raise RuntimeError("private profile package capture inventory mismatch")
        run_python(
            str(recovery), "restore", "--payload", str(profile_payload),
            "--destination", str(profile_restored),
        )
        if snapshot(profile_restored) != profile_before:
            raise RuntimeError("private operator/personal-data package restore mismatch")
        if snapshot(profile_source) != profile_before:
            raise RuntimeError("private package source changed during recovery")
        if (profile_restored / "operator-profile" / "PREFERENCES.md").read_text(encoding="utf-8") != (
            operator_package / "PREFERENCES.md"
        ).read_text(encoding="utf-8"):
            raise RuntimeError("operator preferences did not survive recovery")
        if (profile_restored / "personal-data" / "family-records.md").read_text(encoding="utf-8") != (
            personal_package / "family-records.md"
        ).read_text(encoding="utf-8"):
            raise RuntimeError("personal-data fixture did not survive recovery")

        print("GENERATED_PROJECT_RECOVERY_DRILL=PASSED")
        print("scope=temporary generated project and private package fixtures; local Git bundle; synthetic working-tree changes/userdata; no live project or network")
        print("checks=project manifest, Git checkpoint/history, uncommitted tracked edit, untracked binary/nested userdata, operator preferences, personal-data package, independent hashes, source unchanged, restored catalog generated-files-match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
