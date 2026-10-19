"""Fixture tests for the authenticated inventory collector."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_account_inventory.py"
SPEC = importlib.util.spec_from_file_location("audit_account_inventory", MODULE_PATH)
assert SPEC and SPEC.loader
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)

class InventoryTests(unittest.TestCase):
    def test_inventory_marks_coverage_unverified(self):
        visible_repo = {
            "full_name": "example/project", "owner": {"login": "example"},
            "visibility": "private", "private": True, "default_branch": "main",
            "archived": False, "fork": False, "updated_at": "2026-01-01T00:00:00Z",
            "html_url": "https://github.com/example/project",
        }
        with patch.object(AUDITOR, "api_get", side_effect=[{"login": "builder"}, [visible_repo], []]):
            report = AUDITOR.collect_inventory("test-token")
        self.assertEqual(report["repository_count"], 1)
        self.assertEqual(report["visibility_counts"]["private"], 1)
        self.assertEqual(report["coverage"]["status"], "partial-unverified")
        self.assertFalse(report["coverage"]["account_completeness_verified"])

    def test_owner_filter_limits_results(self):
        one = {"full_name": "wanted/repo", "owner": {"login": "wanted"}, "visibility": "public"}
        two = {"full_name": "other/repo", "owner": {"login": "other"}, "visibility": "public"}
        with patch.object(AUDITOR, "api_get", side_effect=[{"login": "builder"}, [one, two], []]):
            report = AUDITOR.collect_inventory("test-token", "wanted")
        self.assertEqual([item["full_name"] for item in report["repositories"]], ["wanted/repo"])

if __name__ == "__main__":
    unittest.main()
