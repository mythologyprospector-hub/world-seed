"""Mock-only tests for guarded Intake Dock GitHub repository provisioning."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("provision_intake_dock", ROOT / "scripts" / "provision_intake_dock.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeGitHub:
    def __init__(self, login="mythologyprospector-hub", existing=None, create_response=None):
        self.login = login
        self.existing = existing
        self.create_response = create_response
        self.calls = []

    def authenticated_login(self):
        self.calls.append(("identity",))
        return self.login

    def get_repository(self, full_name):
        self.calls.append(("get", full_name))
        if self.existing is None:
            raise MODULE.RepositoryNotFound(full_name)
        return self.existing

    def create_private_repository(self, name):
        self.calls.append(("create", name))
        if self.create_response is None:
            self.create_response = {"full_name": f"{self.login}/{name}", "private": True}
            self.existing = self.create_response
        return self.create_response


class ProvisioningTests(unittest.TestCase):
    def test_dry_run_makes_no_remote_calls(self):
        client = FakeGitHub()
        result = MODULE.provision(client, "mythologyprospector-hub", "intake-dock")
        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["remote_calls_made"], "false")
        self.assertEqual(client.calls, [])

    def test_live_operation_requires_exact_confirmation_before_any_call(self):
        client = FakeGitHub()
        with self.assertRaisesRegex(ValueError, "confirm-target"):
            MODULE.provision(client, "mythologyprospector-hub", "intake-dock", apply=True)
        self.assertEqual(client.calls, [])

    def test_wrong_authenticated_owner_fails_before_repo_lookup(self):
        client = FakeGitHub(login="someone-else")
        with self.assertRaisesRegex(ValueError, "authenticated personal account"):
            MODULE.provision(client, "mythologyprospector-hub", "intake-dock", apply=True,
                             confirmed_target="mythologyprospector-hub/intake-dock")
        self.assertEqual(client.calls, [("identity",)])

    def test_creates_private_repo_and_rereads_to_verify(self):
        client = FakeGitHub()
        result = MODULE.provision(client, "mythologyprospector-hub", "intake-dock", apply=True,
                                  confirmed_target="mythologyprospector-hub/intake-dock")
        self.assertEqual(result["status"], "created-and-verified-private")
        self.assertEqual(client.calls, [
            ("identity",), ("get", "mythologyprospector-hub/intake-dock"),
            ("create", "intake-dock"), ("get", "mythologyprospector-hub/intake-dock"),
        ])

    def test_existing_private_repo_is_idempotently_verified(self):
        target = {"full_name": "mythologyprospector-hub/intake-dock", "private": True}
        client = FakeGitHub(existing=target)
        result = MODULE.provision(client, "mythologyprospector-hub", "intake-dock", apply=True,
                                  confirmed_target="mythologyprospector-hub/intake-dock")
        self.assertEqual(result["status"], "existing-private-verified")
        self.assertNotIn(("create", "intake-dock"), client.calls)

    def test_existing_public_repo_is_not_changed(self):
        public = {"full_name": "mythologyprospector-hub/intake-dock", "private": False}
        client = FakeGitHub(existing=public)
        with self.assertRaisesRegex(ValueError, "not private"):
            MODULE.provision(client, "mythologyprospector-hub", "intake-dock", apply=True,
                             confirmed_target="mythologyprospector-hub/intake-dock")
        self.assertNotIn(("create", "intake-dock"), client.calls)

    def test_wrong_repository_response_is_refused(self):
        client = FakeGitHub(create_response={"full_name": "someone-else/intake-dock", "private": True})
        with self.assertRaisesRegex(ValueError, "exact requested target"):
            MODULE.provision(client, "mythologyprospector-hub", "intake-dock", apply=True,
                             confirmed_target="mythologyprospector-hub/intake-dock")

    def test_invalid_names_and_path_traversal_are_refused(self):
        client = FakeGitHub()
        for owner, name in [("owner/repo", "intake-dock"), ("owner", "../dock"),
                            ("owner", "MixedCase"), ("", "dock")]:
            with self.subTest(owner=owner, name=name):
                with self.assertRaises(ValueError):
                    MODULE.provision(client, owner, name)
        self.assertEqual(client.calls, [])


if __name__ == "__main__":
    unittest.main()
