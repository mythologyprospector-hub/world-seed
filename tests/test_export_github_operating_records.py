"""Fixture tests for the read-only GitHub operating-record exporter."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
MODULE_PATH = SCRIPTS_DIR / "export_github_operating_records.py"
SPEC = importlib.util.spec_from_file_location("export_github_operating_records", MODULE_PATH)
assert SPEC and SPEC.loader
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)


class OperatingRecordExporterTests(unittest.TestCase):
    def test_collection_paginates_until_a_short_page(self):
        first = [{"id": index} for index in range(EXPORTER.PAGE_SIZE)]
        second = [{"id": EXPORTER.PAGE_SIZE}]
        with patch.object(EXPORTER, "_get", side_effect=[first, second]) as getter:
            records = EXPORTER._collection("/repos/example/project/issues", "test-token")
        self.assertEqual(len(records), EXPORTER.PAGE_SIZE + 1)
        self.assertEqual(getter.call_count, 2)
        self.assertIn("page=1", getter.call_args_list[0].args[0])
        self.assertIn("page=2", getter.call_args_list[1].args[0])

    def test_invalid_repository_is_rejected_before_network_access(self):
        with patch.object(EXPORTER, "_get") as getter:
            with self.assertRaises(ValueError):
                EXPORTER.export_repository("not-a-repository", "test-token")
        getter.assert_not_called()

    def test_not_found_is_not_reported_as_proof_of_absence(self):
        error = HTTPError("https://api.github.com/example", 404, "Not Found", {}, None)
        with patch.object(EXPORTER, "_get", side_effect=error):
            result = EXPORTER._capture("test", lambda: EXPORTER._get("/example", "token"))
        self.assertEqual(result["status"], "not-found-or-not-visible")
        self.assertIsNone(result["records"])

    def test_successful_empty_collections_remain_partial_coverage(self):
        def fake_get(path, token):
            if path == "/repos/example/project":
                return {"full_name": "example/project", "default_branch": "main"}
            if "/actions/runs" in path:
                return {"total_count": 0, "workflow_runs": []}
            return []
        with patch.object(EXPORTER, "_get", side_effect=fake_get):
            report = EXPORTER.export_repository("example/project", "test-token")
        self.assertEqual(report["coverage_status"], "partial")
        self.assertEqual(report["endpoints"]["issues_including_pull_request_issue_records"]["status"], "captured")
        self.assertEqual(report["workflow_runs_and_artifact_metadata"]["status"], "captured")
        self.assertEqual(report["binary_content"]["actions_artifacts"], "not-downloaded")
        self.assertEqual(report["binary_content"]["discussions"], "not-attempted")

    def test_pull_request_reviews_and_artifact_metadata_are_collected(self):
        def fake_get(path, token):
            if path == "/repos/example/project":
                return {"full_name": "example/project", "default_branch": "main"}
            if path.startswith("/repos/example/project/issues?"):
                return []
            if path.startswith("/repos/example/project/issues/comments?"):
                return []
            if path.startswith("/repos/example/project/pulls?"):
                return [{"number": 7}]
            if path == "/repos/example/project/pulls/7/reviews?per_page=100&page=1":
                return [{"id": 70}]
            if path == "/repos/example/project/pulls/7/comments?per_page=100&page=1":
                return [{"id": 71}]
            if path.startswith("/repos/example/project/releases?"):
                return []
            if path.startswith("/repos/example/project/actions/runs?"):
                return {"total_count": 1, "workflow_runs": [{"id": 80}]}
            if path == "/repos/example/project/actions/runs/80/artifacts?per_page=100&page=1":
                return {"total_count": 1, "artifacts": [{"id": 81}]}
            return []
        with patch.object(EXPORTER, "_get", side_effect=fake_get):
            report = EXPORTER.export_repository("example/project", "test-token")
        self.assertEqual(report["pull_request_reviews_and_inline_comments"]["status"], "captured")
        self.assertEqual(report["workflow_runs_and_artifact_metadata"]["status"], "captured")
        detail = report["pull_request_reviews_and_inline_comments"]["records"][0]
        self.assertEqual(detail["reviews"]["count"], 1)
        self.assertEqual(detail["inline_comments"]["count"], 1)
        run_detail = report["workflow_runs_and_artifact_metadata"]["records"][0]
        self.assertEqual(run_detail["artifacts"]["count"], 1)
        self.assertEqual(report["coverage_status"], "partial")


if __name__ == "__main__":
    unittest.main()
