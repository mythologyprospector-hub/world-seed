"""Tests for the safe, local-only machine discovery collector."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "collect_machine_profile.py"
SPEC = importlib.util.spec_from_file_location("collect_machine_profile", MODULE_PATH)
assert SPEC and SPEC.loader
COLLECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COLLECTOR)


class CollectMachineProfileTests(unittest.TestCase):
    def test_default_report_omits_repository_names_and_paths(self):
        with patch.object(COLLECTOR, "command_version", return_value={"available": False}):
            report = COLLECTOR.collect()
        self.assertNotIn("repositories", report)
        self.assertNotIn("repository_scan_root", report)
        self.assertFalse(report["privacy"]["uploaded"])
        self.assertFalse(report["privacy"]["credential_files_read"])

    def test_repository_scan_reports_only_top_level_git_checkouts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "example-private-repo"
            repo.mkdir()
            (repo / ".git").mkdir()
            (root / "not-a-repo").mkdir()
            with patch.object(COLLECTOR, "git_value", side_effect=["main", " M tracked.txt"]):
                found = COLLECTOR.discover_repositories(root)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["name"], "example-private-repo")
        self.assertEqual(found[0]["branch"], "main")
        self.assertTrue(found[0]["tracked_changes_present"])
        self.assertNotIn("remote", found[0])

    def test_report_is_json_serializable(self):
        with patch.object(COLLECTOR, "command_version", return_value={"available": False}):
            rendered = json.dumps(COLLECTOR.collect())
        self.assertIn('"schema_version": 1', rendered)

    def test_output_refuses_to_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report.json"
            output.write_text("keep", encoding="utf-8")
            with patch.object(COLLECTOR.sys, "argv", ["collect_machine_profile.py", "--output", str(output)]):
                with self.assertRaises(SystemExit) as raised:
                    COLLECTOR.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(output.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
