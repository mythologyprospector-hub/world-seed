"""Fixture tests for repository layout inspection."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "inspect_repository_layout.py"
SPEC = importlib.util.spec_from_file_location("inspect_repository_layout", MODULE_PATH)
assert SPEC and SPEC.loader
INSPECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSPECTOR)

class LayoutInspectionTests(unittest.TestCase):
    def test_reports_presence_signals_without_claiming_full_coverage(self):
        metadata = {"full_name": "example/project", "visibility": "private", "private": True, "default_branch": "main"}
        root = [
            {"name": "README.md", "type": "file"},
            {"name": "AGENTS.md", "type": "file"},
            {"name": "tests", "type": "dir"},
            {"name": ".github", "type": "dir"},
        ]
        workflows = [{"name": "checks.yml", "type": "file"}, {"name": "notes.txt", "type": "file"}]
        with patch.object(INSPECTOR, "api_get", side_effect=[metadata, root, workflows]):
            report = INSPECTOR.inspect_layout("example/project", "test-token")
        self.assertTrue(report["signals"]["readme_present"])
        self.assertTrue(report["signals"]["builder_instructions_present"])
        self.assertEqual(report["signals"]["workflow_file_count"], 1)
        self.assertIn("No file contents", report["coverage"])

    def test_missing_workflow_directory_is_not_a_failed_clean_check(self):
        metadata = {"full_name": "example/project", "visibility": "public", "private": False, "default_branch": "main"}
        root = [{"name": "README.md", "type": "file"}]
        with patch.object(INSPECTOR, "api_get", side_effect=[metadata, root]):
            report = INSPECTOR.inspect_layout("example/project", "test-token")
        self.assertEqual(report["signals"]["workflow_directory_status"], "not-inspected")
        self.assertIsNone(report["signals"]["workflow_file_count"])

if __name__ == "__main__":
    unittest.main()
