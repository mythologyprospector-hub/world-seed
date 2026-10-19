"""Tests for audit finding lifecycle invariants."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_audit_findings.py"
SPEC = importlib.util.spec_from_file_location("validate_audit_findings", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

class AuditFindingValidationTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / "templates" / "audit-finding.template.json").read_text(encoding="utf-8"))

    def test_template_passes(self):
        self.assertEqual(VALIDATOR.validate_record(self.record), [])

    def test_resolved_finding_requires_verification_evidence(self):
        self.record["status"] = "verified-resolved"
        errors = VALIDATOR.validate_record(self.record)
        self.assertTrue(any("verified-resolved requires" in error for error in errors))

    def test_accepted_risk_requires_rationale_and_review_date(self):
        self.record["status"] = "accepted-risk"
        errors = VALIDATOR.validate_record(self.record)
        self.assertTrue(any("accepted-risk requires" in error for error in errors))

    def test_unknown_lifecycle_state_is_rejected(self):
        self.record["status"] = "done"
        errors = VALIDATOR.validate_record(self.record)
        self.assertTrue(any("invalid status" in error for error in errors))

if __name__ == "__main__":
    unittest.main()
