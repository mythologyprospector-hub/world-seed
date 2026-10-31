"""Tests for World Seed See privacy and command behavior."""

import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "world_seed_see.py"
SPEC = __import__("importlib.util", fromlist=["spec_from_file_location"]).spec_from_file_location("world_seed_see", SCRIPT)
MODULE = __import__("importlib.util", fromlist=["module_from_spec"]).module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class WorldSeedSeeTests(unittest.TestCase):
    def test_hidden_curiosity_mode_is_local_and_does_not_start_a_command(self):
        out = io.StringIO()
        with (
            patch.object(MODULE.sys, "argv", ["world_seed_see.py", "--moo"]),
            patch.object(MODULE, "gh") as gh,
            patch.object(MODULE.subprocess, "Popen") as popen,
            patch("sys.stdout", out),
        ):
            result = MODULE.main()
        self.assertEqual(result, 0)
        self.assertIn("FIELD CURIOSITY SOCIETY", out.getvalue())
        self.assertIn("specimen no. 0001", out.getvalue())
        gh.assert_not_called()
        popen.assert_not_called()

    def test_hidden_curiosity_mode_rejects_a_wrapped_command(self):
        err = io.StringIO()
        with (
            patch.object(MODULE.sys, "argv", ["world_seed_see.py", "--moo", "--", "echo", "unsafe"]),
            patch("sys.stderr", err),
            self.assertRaises(SystemExit) as raised,
        ):
            MODULE.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("cannot be combined", err.getvalue())

    def test_redacts_common_password_bearer_and_flag_shapes(self):
        value = "password=dummy-value Authorization: Bearer abcdefghijklmno --token command-secret"
        result = MODULE.redact(value)
        for secret in ("dummy-value", "abcdefghijklmno", "command-secret"):
            self.assertNotIn(secret, result)
        self.assertIn("[REDACTED]", result)

    def test_redacts_common_api_token_shapes(self):
        for token in ("ghp_" + "A" * 30, "sk-" + "B" * 30, "xoxb-" + "C" * 20, "npm_" + "D" * 30):
            with self.subTest(prefix=token.split("-")[0][:4]):
                self.assertNotIn(token, MODULE.redact(token))

    def test_refuses_public_destination_before_starting_command(self):
        out = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        err = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        response = subprocess.CompletedProcess([], 0, json.dumps({"isPrivate": False, "defaultBranchRef": {"name": "main"}}), "")
        with patch.object(MODULE, "gh", return_value=response), patch.object(MODULE, "upload") as upload, \
             patch.object(MODULE.subprocess, "Popen") as popen, patch.object(MODULE.sys, "argv", ["world_seed_see.py", "--", sys.executable, "-c", "print('SHOULD_NOT_RUN')"]), \
             patch("sys.stdout", out), patch("sys.stderr", err):
            result = MODULE.main()
        self.assertEqual(result, 125)
        err.flush()
        upload.assert_not_called()
        popen.assert_not_called()
        self.assertIn("not verified private", err.buffer.getvalue().decode())

    def test_initial_upload_failure_prevents_command_start(self):
        out = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        err = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        response = subprocess.CompletedProcess([], 0, json.dumps({"isPrivate": True, "defaultBranchRef": {"name": "main"}}), "")
        with patch.object(MODULE, "gh", return_value=response), patch.object(MODULE, "upload", side_effect=subprocess.CalledProcessError(1, ["gh"])) as upload, \
             patch.object(MODULE, "collect_shell_context", return_value={"timestamp_local": "00:00:00", "user": "test", "host": "test-host", "cwd": "/tmp/test", "git_branch": "test", "git_state": "clean"}), \
             patch.object(MODULE.subprocess, "Popen") as popen, patch.object(MODULE.sys, "argv", ["world_seed_see.py", "--", sys.executable, "-c", "print('SHOULD_NOT_RUN')"]), \
             patch("sys.stdout", out), patch("sys.stderr", err):
            result = MODULE.main()
        self.assertEqual(result, 125)
        upload.assert_called_once()
        popen.assert_not_called()

    def test_upload_refreshes_remote_sha_before_retrying_write_conflict(self):
        conflict = subprocess.CalledProcessError(
            1, ["gh"], stderr="gh: HTTP 409: Conflict"
        )
        current_sha = subprocess.CompletedProcess(["gh"], 0, "fresh-blob-sha\n", "")
        success = subprocess.CompletedProcess(
            ["gh"], 0, json.dumps({"content": {"sha": "new-blob-sha"}}), ""
        )
        with (
            patch.object(MODULE, "gh", side_effect=[conflict, current_sha, success]) as gh,
            patch.object(MODULE.time, "sleep") as sleep,
        ):
            result = MODULE.upload("terminal-live/run.txt", "report", "stale-blob-sha", "main")
        self.assertEqual(result, "new-blob-sha")
        self.assertEqual(gh.call_count, 3)
        self.assertEqual(
            gh.call_args_list[1].args[0],
            ["api", f"repos/{MODULE.REPO}/contents/terminal-live/run.txt", "--jq", ".sha"],
        )
        retry_request = json.loads(gh.call_args_list[2].kwargs["input_text"])
        self.assertEqual(retry_request["sha"], "fresh-blob-sha")
        sleep.assert_called_once_with(0.25)

    def test_upload_does_not_retry_non_conflict_failure(self):
        failure = subprocess.CalledProcessError(
            1, ["gh"], stderr="gh: HTTP 403: Forbidden"
        )
        with (
            patch.object(MODULE, "gh", side_effect=failure) as gh,
            patch.object(MODULE.time, "sleep") as sleep,
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                MODULE.upload("terminal-live/run.txt", "report", None, "main")
        gh.assert_called_once()
        sleep.assert_not_called()

    def test_publish_latest_updates_stable_pointer(self):
        response = subprocess.CompletedProcess([], 0, "old-blob-sha\n", "")
        with patch.object(MODULE, "gh", return_value=response) as gh, patch.object(MODULE, "upload", return_value="new-sha") as upload:
            MODULE.publish_latest("terminal-live/run.txt", "https://example.invalid/run.txt", "main")
        gh.assert_called_once_with(["api", f"repos/{MODULE.REPO}/contents/terminal-live/LATEST.txt", "--jq", ".sha"])
        args = upload.call_args.args
        self.assertEqual(args[0], "terminal-live/LATEST.txt")
        self.assertIn("terminal-live/run.txt", args[1])
        self.assertIn("https://example.invalid/run.txt", args[1])
        self.assertEqual(args[2], "old-blob-sha")
        self.assertEqual(args[3], "main")

    def test_publish_latest_uses_requested_pointer_path(self):
        response = subprocess.CompletedProcess([], 0, "old-blob-sha\n", "")
        with patch.object(MODULE, "gh", return_value=response) as gh, patch.object(MODULE, "upload", return_value="new-sha") as upload:
            MODULE.publish_latest("terminal-live/run.txt", "https://example.invalid/run.txt", "main", pointer_path="terminal-live/LATEST-SEE.txt")
        gh.assert_called_once_with(["api", f"repos/{MODULE.REPO}/contents/terminal-live/LATEST-SEE.txt", "--jq", ".sha"])
        self.assertEqual(upload.call_args.args[0], "terminal-live/LATEST-SEE.txt")

    def test_collect_shell_context_includes_prompt_dashboard_fields(self):
        context = MODULE.collect_shell_context()
        for key in ("timestamp_local", "user", "host", "cwd", "git_branch", "git_state"):
            self.assertIn(key, context)
            self.assertTrue(context[key])
        rendered = MODULE.format_shell_context("test context", context)
        self.assertIn("User/host:", rendered)
        self.assertIn("Working directory:", rendered)
        self.assertIn("Git branch:", rendered)
        self.assertIn("Git working tree:", rendered)

    def test_streams_bounded_output_and_preserves_exit_code(self):
        reports = []
        def fake_upload(path, body, sha, branch):
            reports.append((path, body, sha, branch))
            return f"sha-{len(reports)}"
        response = subprocess.CompletedProcess([], 0, json.dumps({"isPrivate": True, "defaultBranchRef": {"name": "test-branch"}}), "")
        out = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        err = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        command = [sys.executable, "-c", "import sys; print('SYNTHETIC_OK'); print('x' * 3000); sys.exit(7)"]
        with patch.object(MODULE, "gh", return_value=response), patch.object(MODULE, "upload", side_effect=fake_upload), \
             patch.object(MODULE.sys, "argv", ["world_seed_see.py", "--limit-bytes", "1024", "--", *command]), \
             patch("sys.stdout", out), patch("sys.stderr", err):
            result = MODULE.main()
        self.assertEqual(result, 7)
        self.assertGreaterEqual(len(reports), 2)
        self.assertTrue(all(item[3] == "test-branch" for item in reports))
        final_report = reports[-1][1]
        self.assertIn("SYNTHETIC_OK", final_report)
        self.assertIn("[OUTPUT TRUNCATED LOCALLY]", final_report)
        self.assertIn("Exit code: 7", final_report)
        self.assertIn(str(Path.cwd()), final_report)
        self.assertIn("shell context at wrapper start", final_report)
        self.assertIn("current shell/repository context", final_report)
        self.assertIn("Git working tree:", final_report)
        self.assertIn("SYNTHETIC_OK", out.buffer.getvalue().decode())

    def test_upload_sends_json_body_via_stdin_without_payload_in_arguments(self):
            body = "private synthetic report body"
            response = subprocess.CompletedProcess([], 0, json.dumps({"content": {"sha": "blob-sha"}}), "")
            with patch.object(MODULE, "gh", return_value=response) as gh:
                result = MODULE.upload("terminal-live/report.txt", body, "old-sha", "main")

            self.assertEqual(result, "blob-sha")
            args = gh.call_args.args[0]
            self.assertEqual(args, [
                "api", "--method", "PUT",
                f"repos/{MODULE.REPO}/contents/terminal-live/report.txt",
                "--input", "-",
            ])
            self.assertNotIn(body, " ".join(args))
            self.assertNotIn("content=", " ".join(args))
            request = json.loads(gh.call_args.kwargs["input_text"])
            self.assertEqual(request, {
                "message": "Refresh live terminal snapshot",
                "content": MODULE.base64.b64encode(body.encode()).decode("ascii"),
                "branch": "main",
                "sha": "old-sha",
            })

    def test_gh_forwards_input_text_to_process_stdin(self):
            request_body = '{"content":"synthetic"}'
            with patch.object(MODULE.subprocess, "run") as run:
                MODULE.gh(["api", "--input", "-"], input_text=request_body)
            run.assert_called_once_with(
                ["gh", "api", "--input", "-"],
                input=request_body,
                text=True,
                capture_output=True,
                check=True,
            )

    def test_upload_diagnostic_does_not_echo_payload_or_credentials(self):
            sensitive_text = "report-body-secret ghp_abcdefghijklmnopqrstuvwxyz123456"
            error = subprocess.CalledProcessError(
                1, ["gh", "api", "--input", "-"], stderr=sensitive_text,
            )
            diagnostic = MODULE.safe_diagnostic(error, "Snapshot upload")
            self.assertIn("exit status 1", diagnostic)
            self.assertNotIn("report-body-secret", diagnostic)
            self.assertNotIn("ghp_", diagnostic)
            self.assertNotIn(sensitive_text, diagnostic)
            launch_error = OSError(f"failed with {sensitive_text}")
            self.assertNotIn(sensitive_text, MODULE.safe_diagnostic(launch_error, "GitHub CLI access check"))


if __name__ == "__main__":
    unittest.main()
