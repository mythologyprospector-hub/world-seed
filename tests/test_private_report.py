"""Tests that local audit reports are created with private file permissions."""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "private_report.py"
SPEC = importlib.util.spec_from_file_location("private_report", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PrivateReportTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "POSIX file permission bits required")
    def test_report_is_owner_read_write_only(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "nested" / "report.json"
            MODULE.write_private_json(target, {"private": True})
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"private": True})

    @unittest.skipUnless(os.name == "posix", "POSIX file permission bits required")
    def test_existing_report_permissions_are_restricted(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "report.json"
            target.write_text("old", encoding="utf-8")
            target.chmod(0o644)
            MODULE.write_private_json(target, {"private": True})
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
