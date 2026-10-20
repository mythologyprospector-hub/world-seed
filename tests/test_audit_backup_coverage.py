"""Tests for conservative backup coverage reporting."""
import os
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_backup_coverage import audit_backup_coverage, main


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

    def test_partial_operating_record_export_is_evidence_but_not_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "records").mkdir()
            (root / "records" / "manifest.tsv").write_text(
                "repository\tfile\tresult\tendpoint_status\nowner/project\trecords.json\tPARTIAL\tpartial\n",
                encoding="utf-8",
            )
            result = audit_backup_coverage(root)
        category = result["categories"]["issues_pull_requests_comments_reviews_releases_actions_metadata"]
        self.assertEqual(category["status"], "partial")
        self.assertEqual(category["endpoint_exports_ok"], 0)
        self.assertEqual(category["endpoint_exports_failed"], 1)
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

    @unittest.skipUnless(os.name == "posix", "POSIX file mode semantics required")
    def test_cli_writes_coverage_report_owner_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "backup"
            root.mkdir()
            output = Path(tmp) / "coverage.json"
            with patch.object(sys, "argv", ["audit_backup_coverage.py", "--backup-dir", str(root), "--output", str(output)]):
                self.assertEqual(main(), 0)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)

    def test_cli_refuses_symlink_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "backup"
            root.mkdir()
            target = Path(tmp) / "target.json"
            target.write_text("preserve", encoding="utf-8")
            link = Path(tmp) / "coverage.json"
            link.symlink_to(target)
            with patch.object(sys, "argv", ["audit_backup_coverage.py", "--backup-dir", str(root), "--output", str(link)]):
                with self.assertRaises(SystemExit) as raised:
                    main()
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(target.read_text(encoding="utf-8"), "preserve")


    def test_cli_refuses_report_inside_public_seed_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "backup"
            root.mkdir()
            repo_root = Path(__file__).resolve().parents[1]
            output = repo_root / ".coverage-report-must-not-be-created.json"
            with patch.object(sys, "argv", ["audit_backup_coverage.py", "--backup-dir", str(root), "--output", str(output)]):
                with self.assertRaises(SystemExit) as raised:
                    main()
            self.assertEqual(raised.exception.code, 2)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
