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
             patch.object(MODULE.subprocess, "Popen") as popen, patch.object(MODULE.sys, "argv", ["world_seed_see.py", "--", sys.executable, "-c", "print('SHOULD_NOT_RUN')"]), \
             patch("sys.stdout", out), patch("sys.stderr", err):
            result = MODULE.main()
        self.assertEqual(result, 125)
        upload.assert_called_once()
        popen.assert_not_called()

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
        self.assertNotIn(str(Path.cwd()), final_report)
        self.assertIn("SYNTHETIC_OK", out.buffer.getvalue().decode())


if __name__ == "__main__":
    unittest.main()
