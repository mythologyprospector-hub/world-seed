"""Fixture tests for the combined account baseline scan."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_account_audit.py"
SPEC = importlib.util.spec_from_file_location("run_account_audit", MODULE_PATH)
assert SPEC and SPEC.loader
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)

class AccountBaselineTests(unittest.TestCase):
    def test_combines_inventory_and_layout_without_claiming_completeness(self):
        inventory = {
            "authenticated_identity": "builder",
            "requested_owner_filter": "example",
            "repository_count": 1,
            "repositories": [{"full_name": "example/project", "visibility": "private"}],
            "coverage": {"status": "partial-unverified"},
        }
        layout = {"repository": "example/project", "signals": {"readme_present": True}, "coverage": "entry names only"}
        with patch.object(AUDITOR, "collect_inventory", return_value=inventory), patch.object(AUDITOR, "inspect_layout", return_value=layout):
            report = AUDITOR.build_report("test-token", "example")
        self.assertEqual(report["repository_count_inspected"], 1)
        self.assertEqual(report["repository_count_blocked"], 0)
        self.assertFalse(report["coverage"]["account_completeness_verified"])
        self.assertFalse(report["coverage"]["cross_repository_contracts_checked"])

    def test_blocked_repository_is_counted_and_not_silently_omitted(self):
        inventory = {
            "authenticated_identity": "builder", "requested_owner_filter": None,
            "repository_count": 1, "repositories": [{"full_name": "example/private"}],
            "coverage": {"status": "partial-unverified"},
        }
        with patch.object(AUDITOR, "collect_inventory", return_value=inventory), patch.object(AUDITOR, "inspect_layout", side_effect=PermissionError()):
            report = AUDITOR.build_report("test-token")
        self.assertEqual(report["repository_count_blocked"], 1)
        self.assertEqual(report["repositories"][0]["inspection_status"], "blocked")
        self.assertEqual(report["blocked_inspections"][0]["repository"], "example/private")

if __name__ == "__main__":
    unittest.main()
