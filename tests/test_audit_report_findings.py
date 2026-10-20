"""Evidence-to-ledger integration tests."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_findings_ledger import open_ledger, get_record, upsert_record
from audit_report_findings import derive_findings, ingest_report


class ReportFindingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.connection = open_ledger(Path(self.tmp.name) / "private.sqlite3")
        self.addCleanup(self.connection.close)
        self.report = {
            "generated_at": "2026-10-20T00:00:00+00:00",
            "coverage": {"account_completeness_verified": False,
                         "cross_repository_contracts_checked": False,
                         "security_posture_verified": False, "note": "Partial inventory only."},
            "repositories": [{"repository": "example/private-repo", "branch_safeguards": {
                "classic_branch_protection": {"status": "unverified"},
                "repository_rulesets": {"status": "observed", "count": 0},
                "organization_rulesets": {"status": "error"}}}],
            "blocked_inspections": [],
        }

    def test_stable_coverage_and_repository_findings(self):
        first = derive_findings(self.report)
        second = derive_findings(self.report)
        self.assertEqual([x["finding_id"] for x in first], [x["finding_id"] for x in second])
        ids = {x["finding_id"] for x in first}
        self.assertIn("AUDIT-COVERAGE-ACCOUNT-COMPLETENESS", ids)
        self.assertIn("AUDIT-COVERAGE-CROSS-REPOSITORY-CONTRACTS", ids)
        self.assertIn("AUDIT-COVERAGE-SECURITY-POSTURE", ids)
        self.assertIn("AUDIT-BRANCH-SAFEGUARDS-EXAMPLE-PRIVATE-REPO", ids)

    def test_ingestion_preserves_first_observed_and_appends_evidence(self):
        ingest_report(self.connection, self.report)
        prior = get_record(self.connection, "AUDIT-COVERAGE-ACCOUNT-COMPLETENESS")
        later = dict(self.report)
        later["generated_at"] = "2026-10-21T00:00:00+00:00"
        ingest_report(self.connection, later)
        current = get_record(self.connection, prior["finding_id"])
        self.assertEqual(current["first_observed"], prior["first_observed"])
        self.assertEqual(current["last_reviewed"], later["generated_at"])
        self.assertEqual(len(current["evidence"]), 2)

    def test_absence_does_not_resolve_finding(self):
        ingest_report(self.connection, self.report)
        fid = "AUDIT-COVERAGE-ACCOUNT-COMPLETENESS"
        ingest_report(self.connection, {"generated_at": "2026-10-21T00:00:00+00:00",
            "coverage": {"account_completeness_verified": True,
                         "cross_repository_contracts_checked": True, "security_posture_verified": True},
            "repositories": [], "blocked_inspections": []})
        self.assertEqual(get_record(self.connection, fid)["status"], "observed")

    def test_new_observation_reopens_verified_resolution(self):
        ingest_report(self.connection, self.report)
        record = get_record(self.connection, "AUDIT-COVERAGE-ACCOUNT-COMPLETENESS")
        record["status"] = "verified-resolved"
        record["verification"] = {"verified": True, "evidence": ["inventory reconciled"],
                                  "verified_at": "2026-10-20T01:00:00+00:00", "verified_by": "reviewer"}
        upsert_record(self.connection, record)
        later = dict(self.report)
        later["generated_at"] = "2026-10-21T00:00:00+00:00"
        result = ingest_report(self.connection, later)
        current = get_record(self.connection, record["finding_id"])
        self.assertEqual(current["status"], "reopened")
        self.assertEqual(result["verified_resolutions_reopened_by_new_evidence"], 1)
        self.assertFalse(current["verification"]["verified"])


if __name__ == "__main__":
    unittest.main()
