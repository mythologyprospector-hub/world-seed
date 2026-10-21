"""Tests for the private, schema-validated findings ledger."""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
MODULE_PATH = ROOT / "scripts" / "audit_findings_ledger.py"
SPEC = importlib.util.spec_from_file_location("audit_findings_ledger", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FindingsLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db_path = Path(self.temporary.name) / "private" / "findings.sqlite3"
        self.connection = MODULE.open_ledger(self.db_path)
        self.addCleanup(self.connection.close)
        self.template = json.loads((ROOT / "templates" / "audit-finding.template.json").read_text(encoding="utf-8"))

    @unittest.skipUnless(os.name == "posix", "POSIX file permission bits required")
    def test_database_is_owner_only(self):
        self.assertEqual(self.db_path.stat().st_mode & 0o777, 0o600)

    def test_upsert_and_query_by_status_and_severity(self):
        record = dict(self.template)
        record["finding_id"] = "AUDIT-LEDGER-001"
        record["severity"] = "high"
        MODULE.upsert_record(self.connection, record)
        self.assertEqual(MODULE.get_record(self.connection, record["finding_id"]), record)
        self.assertEqual(len(MODULE.query_records(self.connection, status="observed")), 1)
        self.assertEqual(len(MODULE.query_records(self.connection, severity="critical")), 0)

    def test_upsert_replaces_existing_record_without_duplicate(self):
        record = dict(self.template)
        record["finding_id"] = "AUDIT-LEDGER-002"
        MODULE.upsert_record(self.connection, record)
        revised = dict(record)
        revised["title"] = "Revised title"
        MODULE.upsert_record(self.connection, revised)
        self.assertEqual(len(MODULE.query_records(self.connection)), 1)
        self.assertEqual(MODULE.get_record(self.connection, revised["finding_id"])["title"], "Revised title")

    def test_invalid_record_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "fails schema validation"):
            MODULE.upsert_record(self.connection, {"finding_id": "broken"})

    def test_database_inside_public_seed_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside the public"):
            MODULE.open_ledger(ROOT / "should-not-be-created.sqlite3")


if __name__ == "__main__":
    unittest.main()
