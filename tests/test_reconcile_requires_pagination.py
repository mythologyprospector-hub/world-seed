import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reconcile_expected_inventory import reconcile_expected_inventory


class PaginationEvidenceTests(unittest.TestCase):
    def test_exact_names_without_pagination_evidence_are_not_verified(self):
        expected = {
            "schema_version": 1,
            "authoritative": True,
            "reviewed_at": "2026-10-20T00:00:00Z",
            "repositories": ["owner/one"],
        }
        report = {"repositories": [{"full_name": "owner/one"}]}
        result = reconcile_expected_inventory(report, expected)
        self.assertFalse(result["repository_inventory_verified"])
        self.assertFalse(result["pagination_complete"])
        self.assertEqual(result["status"], "partial-unverified")


if __name__ == "__main__":
    unittest.main()
