"""Tests for recursive, manifest-backed project-tree recovery."""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("project_tree_recovery", ROOT / "scripts" / "project_tree_recovery.py")
assert SPEC and SPEC.loader
RECOVERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECOVERY)


class ProjectTreeRecoveryTests(unittest.TestCase):
    def test_nested_binary_empty_directories_and_executable_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "src" / "nested").mkdir(parents=True)
            (source / "assets").mkdir()
            (source / "empty" / "inside").mkdir(parents=True)
            (source / "README.md").write_bytes(b"# test\n")
            (source / "src" / "nested" / "module.py").write_bytes(b"print('hello')\n")
            (source / "assets" / "sample.bin").write_bytes(bytes(range(256)) + b"\x00\xff")
            executable = source / "run.sh"
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o755)
            (source / ".git").mkdir()
            (source / ".git" / "private-history").write_text("excluded separately", encoding="utf-8")
            before = {
                p.relative_to(source).as_posix(): RECOVERY.sha256_file(p)
                for p in source.rglob("*") if p.is_file() and ".git" not in p.parts
            }

            payload = root / "private" / "payload"
            manifest = RECOVERY.capture(source, payload, ["README.md", "src", "assets", "empty", "run.sh"])
            self.assertEqual(len(manifest["files"]), 4)
            self.assertIn("empty/inside", manifest["directories"])
            self.assertEqual(manifest["exclusions"], [{
                "path": ".git",
                "reason": "Git history and metadata are a separate recovery category",
            }])
            self.assertFalse((payload / ".git").exists())

            restored = root / "restored"
            RECOVERY.restore(payload, restored)
            after = {
                p.relative_to(restored).as_posix(): RECOVERY.sha256_file(p)
                for p in restored.rglob("*") if p.is_file()
            }
            self.assertEqual(before, after)
            self.assertTrue((restored / "empty" / "inside").is_dir())
            self.assertTrue((restored / "run.sh").stat().st_mode & 0o111)
            self.assertFalse((restored / ".git").exists())
            if os.name == "posix":
                self.assertEqual(payload.stat().st_mode & 0o777, 0o700)
                self.assertEqual((payload / "README.md").stat().st_mode & 0o777, 0o600)

    def test_exact_explicit_exclusion_is_recorded_and_not_copied(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "src").mkdir(parents=True)
            (source / "README.md").write_text("keep", encoding="utf-8")
            (source / "src" / "generated.txt").write_text("exclude", encoding="utf-8")
            (source / "not-selected.txt").write_text("not selected", encoding="utf-8")
            payload = root / "payload"
            manifest = RECOVERY.capture(source, payload, ["README.md", "src"], ["src/generated.txt"])
            self.assertEqual(manifest["exclusions"], [{
                "path": "src/generated.txt",
                "reason": "explicitly excluded by operator",
            }])
            self.assertFalse((payload / "src" / "generated.txt").exists())
            self.assertTrue((payload / "src").is_dir())
            self.assertEqual(manifest["not_captured"], [{"path": "not-selected.txt", "reason": "not selected by explicit capture roots"}])

    def test_capture_refuses_symlinks_and_credential_like_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "README.md").write_text("safe", encoding="utf-8")
            (source / ".env.local").write_text("secret", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "credential-like"):
                RECOVERY.capture(source, root / "payload-secret", [".env.local"])
            (source / ".env.local").unlink()
            try:
                (source / "link.txt").symlink_to(source / "README.md")
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on this platform")
            with self.assertRaisesRegex(ValueError, "symlink"):
                RECOVERY.capture(source, root / "payload-link", ["README.md", "link.txt"])

    def test_capture_rejects_path_traversal_and_overlapping_destinations(self):
        self.assertFalse(RECOVERY.safe_relative("../outside"))
        self.assertFalse(RECOVERY.safe_relative("nested\\outside"))
        self.assertTrue(RECOVERY.safe_relative("nested/inside.txt"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "nested").mkdir(parents=True)
            (source / "nested" / "file.txt").write_text("ok", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not contain one another"):
                RECOVERY.capture(source, source / "payload", ["nested"])
            with self.assertRaisesRegex(ValueError, "direct-child file/directory roots"):
                RECOVERY.capture(source, root / "payload", ["../outside"])

    def test_restore_rejects_tampering_unexpected_entries_and_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "nested").mkdir(parents=True)
            (source / "nested" / "file.txt").write_text("original", encoding="utf-8")
            payload = root / "payload"
            RECOVERY.capture(source, payload, ["nested"])
            existing = root / "existing"
            existing.mkdir()
            (existing / "keep.txt").write_text("untouched", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not already exist"):
                RECOVERY.restore(payload, existing)
            self.assertEqual((existing / "keep.txt").read_text(encoding="utf-8"), "untouched")

            (payload / "nested" / "file.txt").write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "payload verification failed"):
                RECOVERY.restore(payload, root / "tampered-restore")
            self.assertFalse((root / "tampered-restore").exists())

            (payload / "nested" / "file.txt").write_text("original", encoding="utf-8")
            (payload / "unexpected.txt").write_text("extra", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "entries differ from manifest"):
                RECOVERY.restore(payload, root / "unexpected-restore")
            self.assertFalse((root / "unexpected-restore").exists())

    def test_manifest_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "README.md").write_text("safe", encoding="utf-8")
            payload = root / "payload"
            RECOVERY.capture(source, payload, ["README.md"])
            path = payload / RECOVERY.MANIFEST_NAME
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["files"][0]["path"] = "../outside"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsafe, duplicate"):
                RECOVERY.restore(payload, root / "restore")
            self.assertFalse((root / "restore").exists())


if __name__ == "__main__":
    unittest.main()
