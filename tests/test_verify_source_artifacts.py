"""Tests for local source-artifact integrity verification."""
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_source_artifacts import verify_source_artifacts


@unittest.skipUnless(subprocess.run(["git", "--version"], capture_output=True).returncode == 0, "git required")
class SourceArtifactVerificationTests(unittest.TestCase):
    def make_backup(self, root: Path, repositories=("owner/project",)):
        (root / "bundles").mkdir(parents=True)
        (root / "zips").mkdir()
        (root / "checkouts").mkdir()
        rows = ["owner\tvisibility\tarchived\tresult"]
        for repository in repositories:
            basename = repository.rsplit("/", 1)[1]
            source = root / f"working-{basename}"
            source.mkdir()
            subprocess.run(["git", "init", "-q", str(source)], check=True)
            subprocess.run(["git", "-C", str(source), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(source), "config", "user.name", "Test"], check=True)
            (source / "README.md").write_text("test source\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(source), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(source), "commit", "-qm", "test"], check=True)
            subprocess.run(["git", "-C", str(source), "bundle", "create", str(root / "bundles" / f"{basename}.bundle"), "--all"], check=True)
            with zipfile.ZipFile(root / "zips" / f"{basename}.zip", "w") as archive:
                archive.write(source / "README.md", "README.md")
            subprocess.run(["git", "clone", "-q", str(source), str(root / "checkouts" / basename)], check=True)
            rows.append(f"{repository}\tpublic\tFalse\tOK")
        (root / "manifest.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    def test_valid_bundle_zip_and_checkout_are_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_backup(root)
            report = verify_source_artifacts(root)
        self.assertEqual(report["overall_status"], "source-artifacts-verified")
        self.assertEqual(report["verified_repository_count"], 1)
        self.assertEqual(report["repository_results"][0]["bundle"]["status"], "verified")
        self.assertEqual(report["repository_results"][0]["source_zip"]["status"], "verified")
        self.assertEqual(report["repository_results"][0]["checkout"]["status"], "verified")
        self.assertIn("does not prove", report["note"])

    def test_bundle_ref_mismatch_with_checkout_is_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_backup(root)
            checkout = root / "checkouts" / "project"
            subprocess.run(
                ["git", "-C", str(checkout), "branch", "unexpected-local-branch"],
                check=True,
            )
            report = verify_source_artifacts(root)
        row = report["repository_results"][0]
        self.assertEqual(report["overall_status"], "partial")
        self.assertEqual(row["bundle"]["status"], "ref-mismatch")
        self.assertFalse(row["bundle"]["ref_match_with_checkout"])
        self.assertTrue(row["bundle"]["checkout_only_refs"])

    def test_corrupt_zip_is_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_backup(root)
            (root / "zips" / "project.zip").write_bytes(b"not a zip")
            report = verify_source_artifacts(root)
        self.assertEqual(report["overall_status"], "partial")
        self.assertEqual(report["repository_results"][0]["source_zip"]["status"], "invalid")

    def test_valid_zip_with_wrong_content_is_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_backup(root)
            with zipfile.ZipFile(root / "zips" / "project.zip", "w") as archive:
                archive.writestr("README.md", "different content\n")
            report = verify_source_artifacts(root)
        row = report["repository_results"][0]
        self.assertEqual(report["overall_status"], "partial")
        self.assertEqual(row["source_zip"]["status"], "tree-mismatch")
        self.assertFalse(row["source_zip"]["checkout_tree_match"])
        self.assertEqual(row["source_zip"]["content_mismatches"], ["README.md"])

    def test_duplicate_basenames_are_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bundles").mkdir()
            (root / "zips").mkdir()
            (root / "checkouts").mkdir()
            (root / "manifest.tsv").write_text(
                "owner\tvisibility\tarchived\tresult\n"
                "owner-a/project\tpublic\tFalse\tOK\n"
                "owner-b/project\tprivate\tFalse\tOK\n",
                encoding="utf-8",
            )
            report = verify_source_artifacts(root)
        self.assertEqual(report["overall_status"], "partial")
        self.assertEqual(report["repository_count"], 2)
        self.assertTrue(all(row["status"] == "ambiguous" for row in report["repository_results"]))

    def test_manifest_failure_does_not_claim_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_backup(root)
            manifest = root / "manifest.tsv"
            manifest.write_text(manifest.read_text().replace("\tOK\n", "\tFAILED\n"), encoding="utf-8")
            report = verify_source_artifacts(root)
        self.assertEqual(report["overall_status"], "partial")
        self.assertEqual(report["repository_results"][0]["status"], "manifest-failed")


if __name__ == "__main__":
    unittest.main()
