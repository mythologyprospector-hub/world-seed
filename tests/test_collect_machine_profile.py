"""Tests for the safe, local-only machine discovery collector."""
import importlib.util
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "collect_machine_profile.py"
SPEC = importlib.util.spec_from_file_location("collect_machine_profile", MODULE_PATH)
assert SPEC and SPEC.loader
COLLECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COLLECTOR)


class CollectMachineProfileTests(unittest.TestCase):
    def test_runtime_facts_are_allowlisted_and_include_uv_and_python(self):
        with patch.object(COLLECTOR, "command_version", return_value={"available": False}), \
             patch.object(COLLECTOR, "gnome_terminal_facts", return_value={"settings": {"verified": False}}), \
             patch.object(COLLECTOR, "current_checkout_facts", return_value={"verified": False}):
            report = COLLECTOR.collect()
        self.assertIn("uv", report["runtime"])
        self.assertEqual(report["runtime"]["python"]["executable"], str(Path(COLLECTOR.sys.executable).resolve()))
        self.assertIn(report["runtime"]["python"]["environment"], {
            "project_virtual_environment", "virtual_environment", "system_or_base_python"
        })
        self.assertFalse(report["privacy"]["environment_variable_values_read"])
        self.assertNotIn("environment", report["privacy"])

    def test_uv_probe_records_resolved_executable_and_version(self):
        result = type("Result", (), {"stdout": "uv 0.9.0\n", "stderr": "", "returncode": 0})()
        with patch.object(COLLECTOR.shutil, "which", return_value="/usr/bin/uv"), \
             patch.object(COLLECTOR.subprocess, "run", return_value=result):
            found = COLLECTOR.command_version(["uv", "--version"])
        self.assertEqual(found["executable"], "/usr/bin/uv")
        self.assertEqual(found["version"], "uv 0.9.0")

    def test_gnome_profile_queries_capture_only_approved_fields(self):
        profile_id = "12345678-1234-1234-1234-123456789abc"
        values = {
            ("org.gnome.Terminal.ProfilesList", "list"): "['" + profile_id + "']",
            ("org.gnome.Terminal.ProfilesList", "default"): "'" + profile_id + "'",
            (f"org.gnome.Terminal.Legacy.Profile:/org/gnome/terminal/legacy/profiles:/:{profile_id}/", "visible-name"): "'Work'",
            (f"org.gnome.Terminal.Legacy.Profile:/org/gnome/terminal/legacy/profiles:/:{profile_id}/", "use-custom-command"): "true",
            (f"org.gnome.Terminal.Legacy.Profile:/org/gnome/terminal/legacy/profiles:/:{profile_id}/", "custom-command"): "'zsh -l'",
        }
        seen = []
        def respond(args):
            seen.append(args)
            return {
                 "available": True, "verified": True,
                 "value": values[(args[2], args[3])],
             } if args[0] == "gsettings" else {"available": True, "verified": True, "value": "42"}
        with patch.object(COLLECTOR.shutil, "which", side_effect=lambda name: "/usr/bin/gnome-terminal" if name == "gnome-terminal" else None), \
             patch.object(COLLECTOR, "query", side_effect=respond):
            found = COLLECTOR.gnome_terminal_facts()
        self.assertEqual(found["settings"]["default_profile_uuid"], profile_id)
        self.assertEqual(found["settings"]["profiles"], [{
            "uuid": profile_id, "name": "Work", "custom_command_enabled": True,
            "custom_command": "zsh -l",
        }])
        self.assertNotIn("remote", found)
        profile_schema = f"org.gnome.Terminal.Legacy.Profile:/org/gnome/terminal/legacy/profiles:/:{profile_id}/"
        self.assertIn(["gsettings", "get", "org.gnome.Terminal.ProfilesList", "list"], seen)
        self.assertIn(["gsettings", "get", "org.gnome.Terminal.ProfilesList", "default"], seen)
        self.assertIn(["gsettings", "get", profile_schema, "visible-name"], seen)
        self.assertIn(["gsettings", "get", profile_schema, "use-custom-command"], seen)
        self.assertIn(["gsettings", "get", profile_schema, "custom-command"], seen)
        self.assertTrue(all(args[1] == "get" for args in seen if args[0] == "gsettings"))

    def test_incomplete_gnome_discovery_is_not_verified(self):
        profile_ids = [f"12345678-1234-1234-1234-{index:012d}" for index in range(33)]
        def respond(args):
            if args[2:] == ["org.gnome.Terminal.ProfilesList", "list"]:
                return {"available": True, "verified": True, "value": repr(profile_ids)}
            if args[2:] == ["org.gnome.Terminal.ProfilesList", "default"]:
                return {"available": True, "verified": True, "value": repr(profile_ids[0])}
            key = args[3]
            return {"available": True, "verified": True, "value": "'Name'" if key == "visible-name" else "false"}
        with patch.object(COLLECTOR.shutil, "which", side_effect=lambda name: "/usr/bin/gnome-terminal" if name == "gnome-terminal" else None), \
             patch.object(COLLECTOR, "query", side_effect=respond):
            found = COLLECTOR.gnome_terminal_facts()
        self.assertFalse(found["settings"]["verified"])
        self.assertFalse(found["settings"]["complete"])
        self.assertTrue(found["settings"]["limit_reached"])
        self.assertEqual(len(found["settings"]["profiles"]), 32)

        with patch.object(COLLECTOR.shutil, "which", side_effect=lambda name: "/usr/bin/gnome-terminal" if name == "gnome-terminal" else None), \
             patch.object(COLLECTOR, "query", side_effect=[
                 {"available": True, "verified": True, "value": "['12345678-1234-1234-1234-123456789abc']", "truncated": True},
                 {"available": True, "verified": True, "value": "'12345678-1234-1234-1234-123456789abc'"},
             ]):
            truncated = COLLECTOR.gnome_terminal_facts()
        self.assertFalse(truncated["settings"]["verified"])
        self.assertTrue(truncated["settings"]["truncated"])

        profile_id = "12345678-1234-1234-1234-123456789abc"
        def profile_output(args):
            if args[2:] == ["org.gnome.Terminal.ProfilesList", "list"]:
                return {"available": True, "verified": True, "value": repr([profile_id])}
            if args[2:] == ["org.gnome.Terminal.ProfilesList", "default"]:
                return {"available": True, "verified": True, "value": repr(profile_id)}
            if args[3] == "visible-name":
                return {"available": True, "verified": True, "value": "'Name'", "truncated": True}
            return {"available": True, "verified": True, "value": "false"}
        with patch.object(COLLECTOR.shutil, "which", side_effect=lambda name: "/usr/bin/gnome-terminal" if name == "gnome-terminal" else None), \
             patch.object(COLLECTOR, "query", side_effect=profile_output):
            clipped_profile = COLLECTOR.gnome_terminal_facts()
        self.assertFalse(clipped_profile["settings"]["verified"])
        self.assertTrue(clipped_profile["settings"]["truncated"])

    def test_failed_git_status_is_unverified_and_hides_status_output(self):
        outputs = [
            {"verified": True, "value": "/private/project", "truncated": False},
            {"verified": True, "value": "main", "truncated": False},
            {"verified": False},
        ]
        with patch.object(COLLECTOR, "git_query", side_effect=outputs):
            found = COLLECTOR.current_checkout_facts()
        self.assertFalse(found["verified"])
        self.assertNotIn("state", found)
        self.assertNotIn("filename", json.dumps(found))

    def test_empty_successful_git_status_is_clean(self):
        outputs = [
            {"verified": True, "value": "/private/project", "truncated": False},
            {"verified": True, "value": "main", "truncated": False},
            {"verified": True, "value": "", "truncated": False},
        ]
        with patch.object(COLLECTOR, "git_query", side_effect=outputs):
            found = COLLECTOR.current_checkout_facts()
        self.assertTrue(found["verified"])
        self.assertEqual(found["state"], "clean")

    def test_project_venv_classification_uses_checkout_root_from_subdirectory(self):
        root = Path("/project").resolve()
        with patch.object(COLLECTOR.sys, "executable", str(root / ".venv/bin/python")), \
             patch.object(COLLECTOR.sys, "prefix", str(root / ".venv")), \
             patch.object(COLLECTOR.sys, "base_prefix", "/usr"), \
             patch.object(COLLECTOR.Path, "cwd", return_value=root / "src/subdir"), \
             patch.object(COLLECTOR, "git_query", return_value={"verified": True, "value": str(root)}):
            found = COLLECTOR.python_facts()
        self.assertEqual(found["environment"], "project_virtual_environment")
        self.assertTrue(found["environment_verified"])

    def test_privacy_boundary_excludes_secret_sources_and_arbitrary_contents(self):
        class NoEnvironmentReads:
            def __getitem__(self, _key):
                raise AssertionError("collector attempted to read an environment value")

            def get(self, *_args, **_kwargs):
                raise AssertionError("collector attempted to read an environment value")

            def __contains__(self, _key):
                raise AssertionError("collector attempted to inspect environment values")

        with patch.object(COLLECTOR, "command_version", return_value={"available": False}), \
             patch.object(COLLECTOR, "gnome_terminal_facts", return_value={"settings": {"verified": False}}), \
             patch.object(COLLECTOR, "current_checkout_facts", return_value={"verified": False}), \
             patch.object(COLLECTOR, "git_query", return_value={"verified": False}), \
             patch.object(COLLECTOR.os, "environ", NoEnvironmentReads()):
            report = COLLECTOR.collect()
        rendered = json.dumps(report).lower()
        for forbidden in ("gh_token", "github_token", "git@", "https://", "tracked.txt"):
            self.assertNotIn(forbidden, rendered)
        self.assertFalse(report["privacy"]["environment_variable_values_read"])
        self.assertFalse(report["privacy"]["credential_files_read"])
        self.assertFalse(report["privacy"]["remote_urls_collected"])

    def test_missing_gnome_tools_and_settings_are_unverified(self):
        with patch.object(COLLECTOR.shutil, "which", return_value=None):
            found = COLLECTOR.gnome_terminal_facts()
        self.assertFalse(found["gnome_terminal"]["available"])
        self.assertFalse(found["settings"]["verified"])

    def test_gsettings_failure_does_not_expose_raw_output_or_guess(self):
        with patch.object(COLLECTOR.shutil, "which", side_effect=lambda name: "/usr/bin/gnome-terminal" if name == "gnome-terminal" else None), \
             patch.object(COLLECTOR, "query", return_value={"available": True, "verified": False}):
            found = COLLECTOR.gnome_terminal_facts()
        self.assertFalse(found["settings"]["verified"])
        self.assertNotIn("profiles", found["settings"])

    def test_gsettings_query_timeout_and_nonzero_exit_hide_raw_output(self):
        failed = type("Result", (), {"returncode": 1, "stdout": "secret path", "stderr": "secret detail"})()
        with patch.object(COLLECTOR.shutil, "which", return_value="/usr/bin/gsettings"), \
             patch.object(COLLECTOR.subprocess, "run", return_value=failed):
            nonzero = COLLECTOR.query(["gsettings", "get", "schema", "key"])
        self.assertEqual(nonzero, {"available": True, "verified": False})
        with patch.object(COLLECTOR.shutil, "which", return_value="/usr/bin/gsettings"), \
             patch.object(COLLECTOR.subprocess, "run", side_effect=COLLECTOR.subprocess.TimeoutExpired("gsettings", 3)):
            timeout = COLLECTOR.query(["gsettings", "get", "schema", "key"])
        self.assertEqual(timeout, {"available": True, "verified": False})

    def test_gnome_terminal_server_process_match_is_verified_running(self):
        result = type("Result", (), {"returncode": 0, "stdout": "4821\n", "stderr": "private detail"})()
        with patch.object(COLLECTOR.shutil, "which", return_value="/usr/bin/pgrep"), \
             patch.object(COLLECTOR.subprocess, "run", return_value=result) as run:
            found = COLLECTOR.process_status(["pgrep", "-x", "gnome-terminal-server"])
        self.assertEqual(found, {"available": True, "running": True, "verified": True})
        self.assertEqual(run.call_args.args[0], ["/usr/bin/pgrep", "-x", "gnome-terminal-server"])

    def test_gnome_terminal_server_no_match_is_verified_not_running(self):
        result = type("Result", (), {"returncode": 1, "stdout": "", "stderr": "no process"})()
        with patch.object(COLLECTOR.shutil, "which", return_value="/usr/bin/pgrep"), \
             patch.object(COLLECTOR.subprocess, "run", return_value=result):
            found = COLLECTOR.process_status(["pgrep", "-x", "gnome-terminal-server"])
        self.assertEqual(found, {"available": True, "running": False, "verified": True})

    def test_gnome_terminal_facts_preserves_verified_process_state(self):
        with patch.object(COLLECTOR.shutil, "which", side_effect=lambda name: "/usr/bin/gnome-terminal" if name == "gnome-terminal" else None), \
             patch.object(COLLECTOR, "process_status", return_value={"available": True, "running": False, "verified": True}), \
             patch.object(COLLECTOR, "query", return_value={"available": False}):
            found = COLLECTOR.gnome_terminal_facts()
        self.assertEqual(found["gnome_terminal_server_process"], {
            "available": True, "running": False, "verified": True,
        })

    def test_gnome_terminal_server_probe_failures_remain_unknown_and_private(self):
        command = ["pgrep", "-x", "gnome-terminal-server"]
        with patch.object(COLLECTOR.shutil, "which", return_value=None):
            missing = COLLECTOR.process_status(command)
        self.assertEqual(missing, {"available": False, "running": None, "verified": False})

        with patch.object(COLLECTOR.shutil, "which", return_value="/usr/bin/pgrep"), \
             patch.object(COLLECTOR.subprocess, "run", side_effect=COLLECTOR.subprocess.TimeoutExpired("pgrep", 3)):
            timed_out = COLLECTOR.process_status(command)
        self.assertEqual(timed_out, {"available": True, "running": None, "verified": False})

        failed = type("Result", (), {"returncode": 2, "stdout": "private stdout", "stderr": "private stderr"})()
        with patch.object(COLLECTOR.shutil, "which", return_value="/usr/bin/pgrep"), \
             patch.object(COLLECTOR.subprocess, "run", return_value=failed):
            other_failure = COLLECTOR.process_status(command)
        self.assertEqual(other_failure, {"available": True, "running": None, "verified": False})
        self.assertNotIn("private", json.dumps([missing, timed_out, other_failure]))

    def test_command_version_output_is_bounded(self):
        result = type("Result", (), {"stdout": "x" * (COLLECTOR.MAX_COMMAND_OUTPUT + 100), "stderr": "", "returncode": 0})()
        with patch.object(COLLECTOR.shutil, "which", return_value="/bin/tool"), \
             patch.object(COLLECTOR.subprocess, "run", return_value=result):
            found = COLLECTOR.command_version(["tool", "--version"])
        self.assertEqual(len(found["version"]), 160)

    def test_default_report_omits_repository_names_and_paths(self):
        with patch.object(COLLECTOR, "command_version", return_value={"available": False}):
            report = COLLECTOR.collect()
        self.assertNotIn("repositories", report)
        self.assertNotIn("repository_scan_root", report)
        self.assertFalse(report["privacy"]["uploaded"])
        self.assertFalse(report["privacy"]["credential_files_read"])

    def test_repository_scan_reports_only_top_level_git_checkouts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "example-private-repo"
            repo.mkdir()
            (repo / ".git").mkdir()
            (root / "not-a-repo").mkdir()
            with patch.object(COLLECTOR, "git_value", side_effect=["main", " M tracked.txt"]):
                found = COLLECTOR.discover_repositories(root)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["name"], "example-private-repo")
        self.assertEqual(found[0]["branch"], "main")
        self.assertTrue(found[0]["tracked_changes_present"])
        self.assertNotIn("remote", found[0])

    def test_report_is_json_serializable(self):
        with patch.object(COLLECTOR, "command_version", return_value={"available": False}):
            rendered = json.dumps(COLLECTOR.collect())
        self.assertIn('"schema_version": 1', rendered)

    def test_output_refuses_to_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report.json"
            output.write_text("keep", encoding="utf-8")
            with patch.object(COLLECTOR.sys, "argv", ["collect_machine_profile.py", "--output", str(output)]):
                with self.assertRaises(SystemExit) as raised:
                    COLLECTOR.main()
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")

    @unittest.skipUnless(os.name == "posix", "POSIX file mode semantics required")
    def test_saved_report_has_owner_only_permissions(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "private" / "report.json"
            with patch.object(COLLECTOR, "command_version", return_value={"available": False}):
                with patch.object(COLLECTOR.sys, "argv", ["collect_machine_profile.py", "--output", str(output)]):
                    self.assertEqual(COLLECTOR.main(), 0)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertIn('"schema_version": 1', output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
