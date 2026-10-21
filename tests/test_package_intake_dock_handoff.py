"""Tests for safe, local-only Intake Dock handoff packaging."""
import importlib.util
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_intake_dock_handoff", ROOT / "scripts" / "package_intake_dock_handoff.py")
assert SPEC and SPEC.loader
PKG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PKG)


class HandoffPackageTests(unittest.TestCase):
    def test_packages_explicit_files_with_hashes_and_preserves_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "notes.txt"
            second = root / "source.py"
            first.write_text("original notes\n", encoding="utf-8")
            second.write_text("print('synthetic')\n", encoding="utf-8")
            before = (first.read_bytes(), second.read_bytes())
            output = root / "handoff.zip"
            result = PKG.build_package([second, first], output, "episteme", "owner/episteme")
            self.assertEqual(result["files"], 2)
            self.assertEqual(result["transfer_status"], "not_uploaded")
            self.assertEqual((first.read_bytes(), second.read_bytes()), before)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            with zipfile.ZipFile(output) as archive:
                manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual(manifest["target_repository"], "owner/episteme")
                self.assertEqual(manifest["transfer_status"], "not_uploaded")
                self.assertEqual(len(manifest["files"]), 2)
                for entry in manifest["files"]:
                    data = archive.read(entry["path"])
                    import hashlib
                    self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])

    def test_refuses_existing_output_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "notes.txt"
            source.write_text("source", encoding="utf-8")
            output = root / "handoff.zip"
            output.write_text("owner file", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                PKG.build_package([source], output, "episteme", "owner/episteme")
            self.assertEqual(output.read_text(encoding="utf-8"), "owner file")

    def test_refuses_credential_filenames_and_token_material(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            envfile = root / ".env"
            envfile.write_text("not a real secret", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "credential-like filename"):
                PKG.build_package([envfile], root / "out.zip", "episteme", "owner/episteme")
            tokenfile = root / "sample.txt"
            tokenfile.write_text("ghp_" + "A" * 36, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "GitHub token"):
                PKG.build_package([tokenfile], root / "out2.zip", "episteme", "owner/episteme")

    def test_refuses_private_key_material(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "notes.txt"
            source.write_text("-----BEGIN OPENSSH PRIVATE KEY-----", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "private key"):
                PKG.build_package([source], root / "out.zip", "episteme", "owner/episteme")

    def test_refuses_symlink_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            actual = root / "actual.txt"
            actual.write_text("data", encoding="utf-8")
            link = root / "link.txt"
            try:
                link.symlink_to(actual)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "non-symlink"):
                PKG.build_package([link], root / "out.zip", "episteme", "owner/episteme")

    def test_refuses_duplicate_names_and_invalid_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = root / "a"
            bdir = root / "sub"
            bdir.mkdir()
            b = bdir / "a"
            a.write_text("A", encoding="utf-8")
            b.write_text("B", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate basename"):
                PKG.build_package([a, b], root / "out.zip", "episteme", "owner/episteme")
            with self.assertRaisesRegex(ValueError, "target"):
                PKG.build_package([a], root / "out2.zip", "episteme", "../repo")

    def test_refuses_empty_input_and_invalid_lane(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, "at least one"):
                PKG.build_package([], root / "out.zip", "episteme", "owner/episteme")
            source = root / "a"
            source.write_text("A", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "lane"):
                PKG.build_package([source], root / "out.zip", "../episteme", "owner/episteme")


if __name__ == "__main__":
    unittest.main()
