"""Sanity checks for the portable audit-finding contract."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class AuditContractTests(unittest.TestCase):
    def test_schema_is_valid_json_and_declares_lifecycle(self):
        schema = json.loads((ROOT / "schemas" / "audit-finding.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["title"], "World-seed audit finding")
        self.assertIn("verified-resolved", schema["properties"]["status"]["enum"])
        self.assertTrue(schema["allOf"])

    def test_template_is_valid_json_and_has_required_fields(self):
        schema = json.loads((ROOT / "schemas" / "audit-finding.schema.json").read_text(encoding="utf-8"))
        template = json.loads((ROOT / "templates" / "audit-finding.template.json").read_text(encoding="utf-8"))
        self.assertTrue(set(schema["required"]).issubset(template))
        self.assertEqual(template["status"], "observed")
        self.assertFalse(template["verification"]["verified"])

if __name__ == "__main__":
    unittest.main()
