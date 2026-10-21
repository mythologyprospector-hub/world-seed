"""Tests for explicit selective recovery capture and restore."""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("selective_recovery", ROOT / "scripts" / "selective_recovery.py")
assert SPEC and SPEC.loader
RECOVERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECOVERY)

GENERATOR_SPEC = importlib.util.spec_from_file_location("create_project", ROOT / "scripts" / "create_project.py")
assert GENERATOR_SPEC and GENERATOR_SPEC.loader
GENERATOR = importlib.util.module_from_spec(GENERATOR_SPEC)
GENERATOR_SPEC.loader.exec_module(GENERATOR)

LIBRARY_SPEC = importlib.util.spec_from_file_location("project_library", ROOT / "scripts" / "project_library.py")
assert LIBRARY_SPEC and LIBRARY_SPEC.loader
LIBRARY = importlib.util.module_from_spec(LIBRARY_SPEC)
LIBRARY_SPEC.loader.exec_module(LIBRARY)


class SelectiveRecoveryTests(unittest.TestCase):
    def test_capture_restore_and_hashes_match_in_new_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "README.md").write_bytes(b"# hello\n")
            (source / "notes.txt").write_bytes(b"unique user data\x00\xff")
            (source / "ignored.bin").write_bytes(b"not selected")
            payload = root / "private" / "payload"
            manifest = RECOVERY.capture(source, payload, ["README.md", "notes.txt"])
            self.assertEqual([item["path"] for item in manifest["files"]], ["README.md", "notes.txt"])
            self.assertFalse((payload / "ignored.bin").exists())
            destination = root / "restored"
            RECOVERY.restore(payload, destination)
            for name in ("README.md", "notes.txt"):
                self.assertEqual((destination / name).read_bytes(), (source / name).read_bytes())
                self.assertEqual(RECOVERY.sha256_file(destination / name),
                                 next(item["sha256"] for item in manifest["files"] if item["path"] == name))
            self.assertFalse((destination / "world-seed-manifest.json").exists())
            if os.name == "posix":
                self.assertEqual(payload.stat().st_mode & 0o777, 0o700)
                self.assertEqual((payload / "notes.txt").stat().st_mode & 0o777, 0o600)

    def test_safe_name_rejects_portable_path_separators(self):
        self.assertFalse(RECOVERY.safe_name("nested/name.txt"))
        self.assertFalse(RECOVERY.safe_name("nested\\\\name.txt"))
        self.assertTrue(RECOVERY.safe_name("world-seed-manifest.json"))

    def test_safe_name_rejects_nul_character(self):
        self.assertFalse(RECOVERY.safe_name("bad\x00name"))

    def test_capture_requires_explicit_safe_regular_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "README.md").write_text("ok", encoding="utf-8")
            (source / "token.txt").write_text("never capture", encoding="utf-8")
            with self.assertRaises(ValueError):
                RECOVERY.capture(source, root / "out1", ["../outside"])
            with self.assertRaises(ValueError):
                RECOVERY.capture(source, root / "out2", ["token.txt"])
            with self.assertRaises(ValueError):
                RECOVERY.capture(source, root / "out3", ["missing.txt"])
            with self.assertRaises(ValueError):
                RECOVERY.capture(source, root / "out4", ["README.md", "README.md"])

    def test_capture_refuses_symlinks_and_existing_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            external = root / "external.txt"
            external.write_text("outside", encoding="utf-8")
            try:
                (source / "README.md").symlink_to(external)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on this platform")
            with self.assertRaises(ValueError):
                RECOVERY.capture(source, root / "payload", ["README.md"])
            existing = root / "existing"
            existing.mkdir()
            with self.assertRaises(ValueError):
                RECOVERY.capture(source, existing, ["README.md"])

    def test_restore_refuses_existing_destination_and_corrupt_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "README.md").write_text("safe", encoding="utf-8")
            payload = root / "payload"
            RECOVERY.capture(source, payload, ["README.md"])
            existing = root / "existing"
            existing.mkdir()
            (existing / "keep.txt").write_text("do not overwrite", encoding="utf-8")
            with self.assertRaises(ValueError):
                RECOVERY.restore(payload, existing)
            self.assertEqual((existing / "keep.txt").read_text(), "do not overwrite")
            (payload / "README.md").write_text("tampered", encoding="utf-8")
            with self.assertRaises(ValueError):
                RECOVERY.restore(payload, root / "restored")
            self.assertFalse((root / "restored").exists())

    def test_restore_rejects_manifest_path_traversal_and_unexpected_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "README.md").write_text("safe", encoding="utf-8")
            payload = root / "payload"
            RECOVERY.capture(source, payload, ["README.md"])
            manifest_path = payload / RECOVERY.PAYLOAD_MANIFEST
            manifest = json.loads(manifest_path.read_text())
            manifest["files"][0]["path"] = "../outside"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(ValueError):
                RECOVERY.restore(payload, root / "restored")
            manifest["files"][0]["path"] = "README.md"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (payload / "unexpected.txt").write_text("extra", encoding="utf-8")
            with self.assertRaises(ValueError):
                RECOVERY.restore(payload, root / "restored")

    def test_capture_does_not_modify_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "README.md").write_bytes(b"original")
            before = {path.name: path.read_bytes() for path in source.iterdir()}
            RECOVERY.capture(source, root / "payload", ["README.md"])
            self.assertEqual(before, {path.name: path.read_bytes() for path in source.iterdir()})


    def test_generated_project_manifest_survives_recovery_and_catalog_verifies(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_root = root / "source-projects"
            source_root.mkdir()
            source = GENERATOR.create_project(
                ROOT,
                "recovery-fixture",
                "Prove generated projects survive verified recovery.",
                source_root / "recovery-fixture",
                revision="c" * 40,
            )
            included = [*GENERATOR.PROJECT_FILES, "world-seed-manifest.json"]
            payload = root / "private-payload"
            RECOVERY.capture(source, payload, included)
            payload_manifest = json.loads(
                (payload / RECOVERY.PAYLOAD_MANIFEST).read_text(encoding="utf-8")
            )
            self.assertEqual({entry["path"] for entry in payload_manifest["files"]}, set(included))

            restored_root = root / "restored-projects"
            restored = restored_root / "recovery-fixture"
            RECOVERY.restore(payload, restored)
            for name in included:
                self.assertEqual((restored / name).read_bytes(), (source / name).read_bytes(), name)

            catalog = LIBRARY.build_catalog([restored_root])
            self.assertEqual(catalog["project_count"], 1)
            record = catalog["projects"][0]
            self.assertEqual(record["status"], "generated-files-match")
            self.assertEqual(record["verification"], "generated-files-match-manifest")
            self.assertEqual(record["source_revision"], "c" * 40)
            self.assertEqual(
                json.loads((restored / "world-seed-manifest.json").read_text(encoding="utf-8"))["generated_files"],
                sorted(GENERATOR.PROJECT_FILES),
            )


if __name__ == "__main__":
    unittest.main()
