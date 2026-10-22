"""Regression checks for the versioned recovery project-state contract.

These tests use only the Python standard library so the focused CI job remains
dependency-free. Full JSON Schema validation can be performed with the
repository's development dependency when available.
"""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "recovery-project-state.schema.json"
TEMPLATE_PATH = ROOT / "templates" / "recovery-project-state.template.json"


class RecoveryProjectStateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))

    def test_schema_is_versioned_and_rejects_unknown_top_level_fields(self) -> None:
        self.assertEqual(self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(self.schema["properties"]["schema_version"]["const"], 1)
        self.assertFalse(self.schema["additionalProperties"])
        self.assertTrue({
            "project", "record", "canon", "verification", "decisions",
            "current_work", "next_action", "retrieval",
        }.issubset(self.schema["required"]))

    def test_template_contains_all_required_sections(self) -> None:
        self.assertEqual(self.template["schema_version"], 1)
        self.assertEqual(
            set(self.schema["required"]),
            set(self.template),
        )
        for section in self.schema["required"]:
            if section != "schema_version":
                self.assertIn(section, self.template)

    def test_template_marks_unverified_facts_unknown_instead_of_claiming_success(self) -> None:
        self.assertEqual(self.template["record"]["freshness"], "unknown")
        self.assertEqual(self.template["record"]["describes_commit"], "unknown")
        self.assertEqual(self.template["verification"][0]["result"], "not_run")
        self.assertEqual(self.template["verification"][0]["commit"], "unknown")
        self.assertIn("not evidence", self.template["verification"][0]["scope_limitations"][0])
        self.assertEqual(self.template["next_action"]["authorization"], "safe_with_existing_authority")

    def test_decisions_and_next_action_preserve_authorization_boundaries(self) -> None:
        self.assertEqual(
            set(self.template["decisions"]),
            {"accepted", "rejected", "open", "superseded"},
        )
        self.assertIn(
            self.template["next_action"]["authorization"],
            {"safe_with_existing_authority", "requires_human_approval", "unknown"},
        )
        serialized = json.dumps(self.template).lower()
        for forbidden in ("api_key", "private_key", "access_token", "secret_value"):
            self.assertNotIn(forbidden, serialized)

    def test_schema_defines_evidence_and_freshness_fields(self) -> None:
        self.assertIn("freshness", self.schema["properties"]["record"]["required"])
        self.assertIn("provenance", self.schema["properties"]["record"]["required"])
        verification = self.schema["properties"]["verification"]["items"]["properties"]
        self.assertIn("commit", verification)
        self.assertIn("evidence", verification)
        self.assertIn("scope_limitations", verification)
        self.assertIn("authorization", self.schema["properties"]["next_action"]["properties"])


if __name__ == "__main__":
    unittest.main()
