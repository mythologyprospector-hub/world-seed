import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reconcile_expected_inventory import reconcile_expected_inventory


class ReconciliationInputValidationTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            "schema_version": 1,
            "authoritative": True,
            "reviewed_at": "2026-10-20T00:00:00Z",
            "repositories": ["owner/one"],
        }

    def test_bad_expected_names_are_rejected(self):
        for names in (["bad"], ["owner/repo/extra"], [" owner/repo"], ["owner/a", "OWNER/A"]):
            with self.subTest(names=names), self.assertRaises(ValueError):
                reconcile_expected_inventory({"repositories": []}, dict(self.expected, repositories=names))

    def test_bad_observed_reports_are_rejected(self):
        reports = (None, {"repositories": "bad"}, {"repositories": ["bad"]},
                   {"repositories": [{}]}, {"repositories": [{"full_name": "owner/repo/extra"}]},
                   {"repositories": [{"full_name": "owner/repo", "inventory": "bad"}]})
        for report in reports:
            with self.subTest(report=report), self.assertRaises(ValueError):
                reconcile_expected_inventory(report, self.expected)


if __name__ == "__main__":
    unittest.main()
