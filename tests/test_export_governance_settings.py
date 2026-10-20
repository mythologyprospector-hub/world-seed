"""Fixture tests for private governance settings export."""
import importlib.util
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "export_governance_settings.py"
SPEC = importlib.util.spec_from_file_location("export_governance_settings", MODULE_PATH)
assert SPEC and SPEC.loader
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)


def http_error(code):
    return HTTPError("https://api.github.com/test", code, "test", None, None)


class GovernanceExportTests(unittest.TestCase):
    def test_forbidden_endpoint_is_unverified_not_absent(self):
        with patch.object(EXPORTER, "api_get", side_effect=http_error(403)):
            result = EXPORTER.read_endpoint("/repos/example/project/branches/main/protection", "token")
        self.assertEqual(result["status"], "unverified")
        self.assertEqual(result["http_status"], 403)

    def test_404_is_not_reported_not_proof_of_absence(self):
        with patch.object(EXPORTER, "api_get", side_effect=http_error(404)):
            result = EXPORTER.read_endpoint("/repos/example/project/branches/main/protection", "token")
        self.assertEqual(result["status"], "not-reported")
        self.assertIn("not proof", result["evidence"])

    def test_full_classic_payload_and_ruleset_details_are_preserved(self):
        protection = {
            "required_status_checks": {"contexts": ["Validate seed structure and tests"]},
            "required_pull_request_reviews": {"required_approving_review_count": 0},
            "enforce_admins": {"enabled": True},
            "allow_force_pushes": {"enabled": False},
            "allow_deletions": {"enabled": False},
        }
        ruleset = {
            "id": 17, "name": "Protect main", "target": "branch",
            "enforcement": "active", "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"]}},
            "bypass_actors": [], "rules": [{"type": "required_signatures"}],
        }

        def fake_get(path, token):
            if path == "/repos/example/project":
                return {"default_branch": "main", "private": True}
            if path == "/repos/example/project/branches/main/protection":
                return protection
            if path == "/repos/example/project/rulesets?per_page=100&page=1":
                return [{"id": 17, "name": "Protect main", "target": "branch", "enforcement": "active"}]
            if path == "/repos/example/project/rulesets/17":
                return ruleset
            if path == "/users/example":
                return {"type": "User"}
            raise AssertionError(path)

        with patch.object(EXPORTER, "api_get", side_effect=fake_get):
            result = EXPORTER.export_governance("example/project", "token")
        self.assertEqual(result["overall_status"], "captured")
        self.assertEqual(
            result["controls"]["classic_default_branch_protection"]["data"],
            protection,
        )
        saved = result["controls"]["repository_rulesets"]["rulesets"][0]["detail"]["data"]
        self.assertEqual(saved["rules"], [{"type": "required_signatures"}])
        self.assertEqual(result["controls"]["organization_rulesets"]["status"], "not-applicable")

    def test_ruleset_detail_denial_makes_export_partial(self):
        def fake_get(path, token):
            if path == "/repos/example/project":
                return {"default_branch": "main"}
            if path == "/repos/example/project/branches/main/protection":
                raise http_error(403)
            if path == "/repos/example/project/rulesets?per_page=100&page=1":
                return [{"id": 17, "name": "Protect main"}]
            if path == "/repos/example/project/rulesets/17":
                raise http_error(403)
            if path == "/users/example":
                return {"type": "Organization"}
            if path == "/orgs/example/rulesets?per_page=100&page=1":
                return []
            raise AssertionError(path)

        with patch.object(EXPORTER, "api_get", side_effect=fake_get):
            result = EXPORTER.export_governance("example/project", "token")
        self.assertEqual(result["overall_status"], "partial")
        self.assertEqual(result["controls"]["classic_default_branch_protection"]["status"], "unverified")
        self.assertEqual(result["controls"]["repository_rulesets"]["status"], "partial")
        self.assertEqual(result["controls"]["organization_rulesets"]["status"], "captured")


if __name__ == "__main__":
    unittest.main()
