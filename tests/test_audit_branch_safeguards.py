"""Fixture tests for branch-protection and ruleset inspection."""
import importlib.util
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_branch_safeguards.py"
SPEC = importlib.util.spec_from_file_location("audit_branch_safeguards", MODULE_PATH)
assert SPEC and SPEC.loader
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)


def http_error(code):
    return HTTPError("https://api.github.com/test", code, "test", None, None)


class BranchSafeguardTests(unittest.TestCase):
    def test_classic_404_is_not_reported_as_effective_absence(self):
        def fake_get(path, token):
            if "/branches/main/protection" in path:
                raise http_error(404)
            if "/rulesets?" in path:
                return []
            if path == "/users/example":
                return {"type": "User"}
            raise AssertionError(path)

        with patch.object(AUDITOR, "api_get", side_effect=fake_get):
            result = AUDITOR.inspect_branch_safeguards("example/project", "main", "test-token")
        self.assertEqual(result["classic_branch_protection"]["status"], "not-reported")
        self.assertEqual(result["repository_rulesets"]["count"], 0)
        self.assertEqual(result["organization_rulesets"]["status"], "not-applicable")
        self.assertIn("verify", result["interpretation"])

    def test_forbidden_protection_endpoint_remains_unverified(self):
        def fake_get(path, token):
            if "/branches/main/protection" in path:
                raise http_error(403)
            if "/rulesets?" in path:
                return []
            if path == "/users/example":
                return {"type": "User"}
            raise AssertionError(path)

        with patch.object(AUDITOR, "api_get", side_effect=fake_get):
            result = AUDITOR.inspect_branch_safeguards("example/project", "main", "test-token")
        self.assertEqual(result["classic_branch_protection"]["status"], "unverified")
        self.assertIn("partial", result["interpretation"])

    def test_unverified_controls_create_follow_up_and_never_certify_gate(self):
        plan = AUDITOR.build_policy_follow_up({
            "classic_branch_protection": {"status": "unverified"},
            "repository_rulesets": {"status": "unverified"},
            "organization_rulesets": {"status": "unverified"},
        })
        self.assertEqual(plan["status"], "review-required")
        self.assertFalse(plan["effective_human_gate_certified"])
        self.assertTrue(any(item["action"] == "Resolve settings coverage gaps" for item in plan["next_actions"]))
        self.assertTrue(any(item["priority"] == "approval-required" for item in plan["next_actions"]))

    def test_no_reported_protection_creates_proposal_not_automatic_change(self):
        plan = AUDITOR.build_policy_follow_up({
            "classic_branch_protection": {"status": "not-reported"},
            "repository_rulesets": {"status": "observed", "count": 0},
            "organization_rulesets": {"status": "observed", "count": 0},
        })
        self.assertTrue(any(item["action"] == "Prepare a branch-protection proposal" for item in plan["next_actions"]))
        self.assertFalse(plan["effective_human_gate_certified"])

    def test_missing_default_branch_is_unverified(self):
        result = AUDITOR.inspect_branch_safeguards("example/project", None, "test-token")
        self.assertEqual(result["classic_branch_protection"]["status"], "unverified")
        self.assertEqual(result["repository_rulesets"]["status"], "unverified")

    def test_organization_rulesets_are_paginated(self):
        first_page = [
            {"id": index, "name": f"Rule {index}", "target": "branch", "enforcement": "active"}
            for index in range(100)
        ]
        second_page = [{"id": 101, "name": "Last rule", "target": "branch", "enforcement": "active"}]

        def fake_get(path, token):
            if "/branches/main/protection" in path:
                raise http_error(404)
            if "/repos/example/project/rulesets?" in path:
                return []
            if path == "/users/example":
                return {"type": "Organization"}
            if "/orgs/example/rulesets?per_page=100&page=1" in path:
                return first_page
            if "/orgs/example/rulesets?per_page=100&page=2" in path:
                return second_page
            raise AssertionError(path)

        with patch.object(AUDITOR, "api_get", side_effect=fake_get):
            result = AUDITOR.inspect_branch_safeguards("example/project", "main", "test-token")
        self.assertEqual(result["organization_rulesets"]["status"], "observed")
        self.assertEqual(result["organization_rulesets"]["count"], 101)

    def test_configured_classic_protection_is_summarized(self):
        def fake_get(path, token):
            if "/branches/main/protection" in path:
                return {
                    "required_status_checks": {"contexts": ["tests"]},
                    "required_pull_request_reviews": {"required_approving_review_count": 1},
                    "restrictions": None,
                    "enforce_admins": {"enabled": True},
                    "allow_force_pushes": {"enabled": False},
                    "allow_deletions": {"enabled": False},
                    "required_conversation_resolution": {"enabled": True},
                }
            if "/rulesets?" in path:
                return [{"id": 5, "name": "Protect main", "target": "branch", "enforcement": "active"}]
            if path == "/users/example":
                return {"type": "User"}
            raise AssertionError(path)

        with patch.object(AUDITOR, "api_get", side_effect=fake_get):
            result = AUDITOR.inspect_branch_safeguards("example/project", "main", "test-token")
        self.assertEqual(result["classic_branch_protection"]["status"], "observed")
        self.assertEqual(result["classic_branch_protection"]["required_status_checks"]["contexts"], ["tests"])
        self.assertEqual(result["repository_rulesets"]["count"], 1)


if __name__ == "__main__":
    unittest.main()
