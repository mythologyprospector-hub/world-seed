"""Tests for structural comparison of partial account baseline reports."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
MODULE_PATH = ROOT / "scripts" / "compare_audit_baselines.py"
SPEC = importlib.util.spec_from_file_location("compare_audit_baselines", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def report(repositories, generated_at):
    return {
        "schema_version": 1,
        "audit_type": "account_visible_repository_baseline",
        "generated_at": generated_at,
        "coverage": {"status": "partial-unverified"},
        "repositories": repositories,
    }


def repo(name, branch="main", headings=None):
    return {
        "repository": name,
        "inventory": {"visibility": "private", "default_branch": branch, "archived": False, "fork": False},
        "layout": {"root_entry_names": ["README.md"], "signals": {"readme_present": True}},
        "documents": {"documents": [{"path": "README.md", "status": "inspected", "blob_sha": "abc", "headings": headings or [{"level": 1, "text": "Project"}]}]},
        "document_inspection_status": "inspected",
    }


class BaselineComparisonTests(unittest.TestCase):
    def test_reports_added_removed_changed_and_unchanged(self):
        previous = report([repo("org/kept"), repo("org/changed"), repo("org/removed")], "old")
        current = report([repo("org/kept"), repo("org/changed", branch="trunk"), repo("org/added")], "new")
        result = MODULE.compare_reports(previous, current)
        self.assertEqual(result["added_repositories"], ["org/added"])
        self.assertEqual(result["removed_repositories"], ["org/removed"])
        self.assertEqual(result["changed_repositories"], [{"repository": "org/changed", "changed_fields": ["default_branch"]}])
        self.assertEqual(result["counts"]["unchanged"], 1)

    def test_heading_change_is_detected_without_document_body(self):
        previous = report([repo("org/project", headings=[{"level": 1, "text": "Old"}])], "old")
        current = report([repo("org/project", headings=[{"level": 1, "text": "New"}])], "new")
        result = MODULE.compare_reports(previous, current)
        self.assertIn("documents", result["changed_repositories"][0]["changed_fields"])

    def test_duplicate_repository_is_rejected(self):
        duplicate = report([repo("org/project"), repo("org/project")], "old")
        with self.assertRaisesRegex(ValueError, "duplicate repository"):
            MODULE.compare_reports(duplicate, report([], "new"))

    def test_comparison_never_claims_complete_coverage(self):
        result = MODULE.compare_reports(report([], "old"), report([], "new"))
        self.assertEqual(result["coverage"]["status"], "partial-unverified")
        self.assertFalse(result["coverage"]["account_completeness_verified"])


if __name__ == "__main__":
    unittest.main()
