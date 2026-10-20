"""Tests for explicit cross-repository contract inspection."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from inspect_cross_repository_contracts import (
    inspect_expected_contracts,
    validate_expected_contracts,
)


class CrossRepositoryContractTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            "schema_version": 1,
            "authoritative": True,
            "reviewed_at": "2026-10-20T00:00:00+00:00",
            "contracts": [{
                "contract_id": "runtime-api",
                "producer": "owner/organs",
                "consumer": "owner/world",
                "path": "docs/API.md",
            }],
        }
        self.report = {
            "requested_owner_filter": None,
            "repositories": [
                {"full_name": "owner/organs"},
                {"full_name": "owner/world"},
            ],
        }

    def test_canonical_template_is_valid_but_not_authoritative(self):
        template = json.loads((Path(__file__).resolve().parents[1] / "templates" / "expected-contracts.template.json").read_text(encoding="utf-8"))
        self.assertFalse(template["authoritative"])
        self.assertEqual(len(validate_expected_contracts(template)), 1)

    def test_inventory_requires_authority_review_and_contract(self):
        with self.assertRaises(ValueError):
            validate_expected_contracts({"schema_version": 1, "contracts": []})
        with self.assertRaises(ValueError):
            validate_expected_contracts(dict(self.expected, contracts=[
                dict(self.expected["contracts"][0], path="../private.txt")
            ]))
        with self.assertRaises(ValueError):
            validate_expected_contracts(dict(self.expected, contracts=[
                self.expected["contracts"][0], self.expected["contracts"][0]
            ]))

    @patch("inspect_cross_repository_contracts._api_get")
    def test_present_artifact_verifies_presence_not_compatibility(self, api_get):
        api_get.side_effect = [
            {"default_branch": "main"},
            {"type": "file", "sha": "abc123"},
        ]
        result = inspect_expected_contracts(self.report, self.expected, "token")
        self.assertTrue(result["cross_repository_contract_inventory_verified"])
        self.assertEqual(result["contracts"][0]["artifact_status"], "present")
        self.assertIsNone(result["contracts"][0].get("content"))
        self.assertIn("does not validate consumer usage", result["note"])

    @patch("inspect_cross_repository_contracts._api_get")
    def test_missing_consumer_is_unverified_not_absent_contract(self, api_get):
        report = dict(self.report, repositories=[{"full_name": "owner/organs"}])
        result = inspect_expected_contracts(report, self.expected, "token")
        self.assertFalse(result["cross_repository_contract_inventory_verified"])
        self.assertEqual(result["contracts"][0]["reason"], "producer-or-consumer-not-observed")
        api_get.assert_not_called()

    @patch("inspect_cross_repository_contracts._api_get")
    def test_filtered_or_non_authoritative_report_never_verifies(self, api_get):
        api_get.side_effect = [
            {"default_branch": "main"},
            {"type": "file", "sha": "abc123"},
        ]
        report = dict(self.report, requested_owner_filter="owner")
        result = inspect_expected_contracts(report, self.expected, "token")
        self.assertFalse(result["cross_repository_contract_inventory_verified"])


if __name__ == "__main__":
    unittest.main()
