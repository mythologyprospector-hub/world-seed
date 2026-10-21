"""Tests for private, idempotent local Intake Dock initialization."""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("materialize_intake_dock", ROOT / "scripts" / "materialize_intake_dock.py")
assert SPEC and SPEC.loader
DOCK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOCK)


class IntakeDockMaterializerTests(unittest.TestCase):
    def test_initializes_private_structure_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            destination = root / "dock"
            result = DOCK.materialize(ROOT / "templates" / "intake-dock", destination)
            self.assertEqual(set(result["files_added"]), set(DOCK.DOCK_FILES))
            self.assertEqual(set(result["directories_added"]), set(DOCK.DOCK_DIRS))
            manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["package_type"], "intake-dock")
            self.assertEqual(manifest["remote_provisioning"], "not_implemented")
            if os.name == "posix":
                self.assertEqual(destination.stat().st_mode & 0o777, 0o700)
                self.assertEqual((destination / "incoming").stat().st_mode & 0o777, 0o700)
                self.assertEqual((destination / "README.md").stat().st_mode & 0o777, 0o600)

    def test_rerun_is_idempotent_and_preserves_owner_material(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "dock"
            DOCK.materialize(ROOT / "templates" / "intake-dock", destination)
            extra = destination / "incoming" / "owner-export.txt"
            extra.write_text("preserve me", encoding="utf-8")
            result = DOCK.materialize(ROOT / "templates" / "intake-dock", destination)
            self.assertEqual(result["files_added"], [])
            self.assertEqual(result["directories_added"], [])
            self.assertEqual(extra.read_text(encoding="utf-8"), "preserve me")

    def test_conflicting_template_file_is_preserved_and_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "dock"
            destination.mkdir(mode=0o700)
            if os.name == "posix":
                os.chmod(destination, 0o700)
            conflict = destination / "README.md"
            conflict.write_text("owner-authored content", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differs from template"):
                DOCK.materialize(ROOT / "templates" / "intake-dock", destination)
            self.assertEqual(conflict.read_text(encoding="utf-8"), "owner-authored content")

    def test_refuses_insecure_existing_destination(self):
        if os.name != "posix":
            self.skipTest("POSIX permissions are not available")
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "dock"
            destination.mkdir(mode=0o755)
            with self.assertRaisesRegex(ValueError, "not private"):
                DOCK.materialize(ROOT / "templates" / "intake-dock", destination)

    def test_refuses_symlink_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            actual = root / "actual"
            actual.mkdir()
            link = root / "link"
            try:
                link.symlink_to(actual, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "must not be a symlink"):
                DOCK.materialize(ROOT / "templates" / "intake-dock", link)

    def test_refuses_template_conflict_before_creating_missing_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            destination = root / "dock"
            destination.mkdir(mode=0o700)
            if os.name == "posix":
                os.chmod(destination, 0o700)
            (destination / "README.md").write_text("different", encoding="utf-8")
            with self.assertRaises(ValueError):
                DOCK.materialize(ROOT / "templates" / "intake-dock", destination)
            self.assertFalse((destination / "incoming").exists())


if __name__ == "__main__":
    unittest.main()
