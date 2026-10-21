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


if __name__ == "__main__":
    unittest.main()
