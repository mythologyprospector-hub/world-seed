"""Tests for expected-inventory reconciliation."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reconcile_expected_inventory import reconcile_expected_inventory


class ExpectedInventoryTests(unittest.TestCase):
    def setUp(self):
        self.expected = {"schema_version": 1, "authoritative": True,
                         "reviewed_at": "2026-10-20T00:00:00+00:00",
                         "repositories": ["owner/public", "owner/private"]}

    def test_exact_authoritative_match_without_filter_verifies_inventory_only(self):
        report = {"repositories": [{"full_name": "owner/public"}, {"full_name": "owner/private"}],
                  "requested_owner_filter": None}
        result = reconcile_expected_inventory(report, self.expected)
        self.assertTrue(result["repository_inventory_verified"])
        self.assertFalse(result["repository_inventory_verified"])
        self.assertFalse(result["account_completeness_verified"])
        self.assertEqual(result["status"], "verified-match")
        self.assertIn("full account backup/recovery completeness is not", result["note"])

    def test_missing_and_unexpected_repositories_prevent_verification(self):
        report = {"repositories": [{"full_name": "owner/public"}, {"full_name": "other/extra"}],
                  "requested_owner_filter": None}
        result = reconcile_expected_inventory(report, self.expected)
        self.assertFalse(result["repository_inventory_verified"])
        self.assertFalse(result["account_completeness_verified"])
        self.assertEqual(result["missing_from_observed"], ["owner/private"])
        self.assertEqual(result["unexpected_in_observed"], ["other/extra"])

    def test_owner_filter_and_non_authoritative_list_never_verify(self):
        report = {"repositories": [{"full_name": "owner/public"}, {"full_name": "owner/private"}],
                  "requested_owner_filter": "owner"}
        self.assertFalse(reconcile_expected_inventory(report, self.expected)["repository_inventory_verified"])
        expected = dict(self.expected, authoritative=False)
        report["requested_owner_filter"] = None
        self.assertFalse(reconcile_expected_inventory(report, expected)["repository_inventory_verified"])

    def test_canonical_template_is_valid_but_not_authoritative(self):
        template = json.loads((Path(__file__).resolve().parents[1] / "templates" / "expected-inventory.template.json").read_text(encoding="utf-8"))
        report = {"repositories": [], "requested_owner_filter": None}
        result = reconcile_expected_inventory(report, template)
        self.assertFalse(template["authoritative"])
        self.assertFalse(result["account_completeness_verified"])

    def test_duplicate_or_malformed_expected_names_rejected(self):
        with self.assertRaises(ValueError):
            reconcile_expected_inventory({"repositories": []}, dict(self.expected, repositories=["owner/a", "OWNER/A"]))
        with self.assertRaises(ValueError):
            reconcile_expected_inventory({"repositories": []}, dict(self.expected, repositories=["not-a-repo"]))


if __name__ == "__main__":
    unittest.main()
