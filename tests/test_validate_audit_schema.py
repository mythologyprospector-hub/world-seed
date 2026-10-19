"""Full JSON Schema validation tests for audit finding records."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_audit_schema.py"
SPEC = importlib.util.spec_from_file_location("validate_audit_schema", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class FullAuditSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "schemas" / "audit-finding.schema.json").read_text(encoding="utf-8"))
        cls.template = json.loads((ROOT / "templates" / "audit-finding.template.json").read_text(encoding="utf-8"))

    def test_canonical_template_passes_full_schema(self):
        self.assertEqual(VALIDATOR.validate_record(self.template, self.schema), [])

    def test_unexpected_field_is_rejected(self):
        record = dict(self.template)
        record["surprise"] = True
        self.assertTrue(any("Additional properties are not allowed" in error for error in VALIDATOR.validate_record(record, self.schema)))

    def test_invalid_datetime_is_rejected(self):
        record = dict(self.template)
        record["first_observed"] = "yesterday"
        self.assertTrue(any("first_observed" in error for error in VALIDATOR.validate_record(record, self.schema)))

    def test_verified_resolved_requires_evidence_and_timestamp(self):
        record = json.loads(json.dumps(self.template))
        record["status"] = "verified-resolved"
        record["verification"] = {"verified": True, "evidence": []}
        errors = VALIDATOR.validate_record(record, self.schema)
        self.assertTrue(any("verified_at" in error for error in errors))
        self.assertTrue(any("evidence" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
