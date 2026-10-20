"""Tests for conservative backup coverage reporting."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_backup_coverage import audit_backup_coverage


class BackupCoverageTests(unittest.TestCase):
    def test_missing_backup_is_incomplete_and_unverified(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = audit_backup_coverage(Path(tmp))
        self.assertEqual(result["overall_status"], "incomplete-unverified")
        self.assertEqual(result["categories"]["repository_inventory"]["status"], "missing")
        self.assertEqual(result["categories"]["isolated_recovery_drill"]["status"], "not-tested")
        self.assertEqual(result["categories"]["repository_and_organization_settings_permissions"]["status"], "unverified")

    def test_source_only_backup_does_not_imply_operating_records_or_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "manifest.tsv").write_text(
                "owner\tvisibility\tarchived\tresult\nowner/project\tpublic\tFalse\tOK\n",
                encoding="utf-8",
            )
            (root / "bundles").mkdir()
            (root / "bundles" / "project.bundle").write_bytes(b"not-validated-here")
            (root / "zips").mkdir()
            (root / "zips" / "project.zip").write_bytes(b"not-validated-here")
            (root / "checkouts").mkdir()
            (root / "checkouts" / "project").mkdir()
            result = audit_backup_coverage(root)
        categories = result["categories"]
        self.assertEqual(categories["git_source_and_history"]["status"], "present")
        self.assertEqual(categories["issues_pull_requests_comments_reviews_releases_actions_metadata"]["status"], "unverified")
        self.assertEqual(categories["actions_binary_artifact_contents"]["status"], "unverified")
        self.assertEqual(categories["isolated_recovery_drill"]["status"], "not-tested")
        self.assertEqual(result["overall_status"], "incomplete-unverified")

    def test_operating_record_export_does_not_claim_full_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "records").mkdir()
            (root / "records" / "manifest.tsv").write_text(
                "repository\tresource\tresult\nowner/project\tissues\tOK\n",
                encoding="utf-8",
            )
            result = audit_backup_coverage(root)
        self.assertEqual(
            result["categories"]["issues_pull_requests_comments_reviews_releases_actions_metadata"]["status"],
            "partial",
        )
        self.assertEqual(result["overall_status"], "incomplete-unverified")

    def test_governance_export_is_detected_but_does_not_certify_all_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "manifest.tsv").write_text(
                "owner\tvisibility\tarchived\tresult\nowner/project\tprivate\tFalse\tOK\n",
                encoding="utf-8",
            )
            governance = root / "records" / "governance"
            governance.mkdir(parents=True)
            (governance / "governance-owner_project.json").write_text(
                '{"repository":"owner/project","overall_status":"captured","controls":{}}',
                encoding="utf-8",
            )
            result = audit_backup_coverage(root)
        categories = result["categories"]
        self.assertEqual(categories["branch_protection_and_ruleset_exports"]["status"], "present")
        self.assertEqual(categories["branch_protection_and_ruleset_exports"]["export_count"], 1)
        self.assertEqual(categories["repository_and_organization_settings_permissions"]["status"], "partial")
        self.assertEqual(result["overall_status"], "incomplete-unverified")


if __name__ == "__main__":
    unittest.main()
