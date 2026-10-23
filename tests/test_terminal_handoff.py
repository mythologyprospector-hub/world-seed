"""Tests for explicit terminal-output handoff and privacy boundaries."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "terminal_handoff.py"


class TerminalHandoffTests(unittest.TestCase):
    def run_cli(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True, text=True, check=False, env=env,
        )

    def make_journal(self, root: Path, *, stdout: str, stderr: str = "", exit_code: int = 0) -> Path:
        lane = root / "demo-project"
        lane.mkdir(parents=True)
        journal = lane / "2026-01-01.jsonl"
        sid = "11111111-2222-4333-8444-555555555555"
        records = [
            {"schema_version": 2, "session_id": sid, "project": "demo-project", "cwd": "/tmp/demo-project",
             "repository_root": "/tmp/demo-project", "git_branch": "test-branch", "git_dirty": False,
             "command": ["python", "-c", "print('ok')"], "event": "command_started",
             "sequence": 0, "recorded_at": "2026-01-01T00:00:00+00:00"},
        ]
        if stdout:
            records.append({"session_id": sid, "event": "output", "sequence": 1, "stream": "stdout", "text": stdout})
        if stderr:
            records.append({"session_id": sid, "event": "output", "sequence": 2, "stream": "stderr", "text": stderr})
        records.append({"session_id": sid, "event": "command_finished", "sequence": 3,
                        "recorded_at": "2026-01-01T00:00:01+00:00", "exit_code": exit_code})
        journal.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
        return journal

    def test_prepare_redacts_and_does_not_upload(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            journal_root = root / "journals"
            self.make_journal(journal_root, stdout="tests passed\nAPI_KEY=ghp_abcdefghijklmnopqrstuvwxyz123456\n")
            outbox = root / "outbox"
            result = self.run_cli("prepare", "--project", "demo-project",
                                  "--journal-root", str(journal_root), "--outbox", str(outbox))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("NOT uploaded", result.stdout)
            report_path = next(outbox.glob("*.json"))
            self.assertEqual(report_path.stat().st_mode & 0o777, 0o600)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("tests passed", report["stdout"])
            self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyz123456", report["stdout"])
            self.assertTrue(report["redactions_applied"])
            self.assertEqual(report["exit_code"], 0)

    def test_prepare_bounds_output_and_marks_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            journal_root = root / "journals"
            self.make_journal(journal_root, stdout="x" * 10000)
            result = self.run_cli("prepare", "--project", "demo-project",
                                  "--journal-root", str(journal_root), "--outbox", str(root / "outbox"),
                                  "--max-output-bytes", "1024")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(next((root / "outbox").glob("*.json")).read_text(encoding="utf-8"))
            self.assertTrue(report["truncated"])
            self.assertLess(len(report["stdout"].encode()), 1024)

    def test_publish_requires_explicit_confirmation_and_outbox_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outbox = root / "outbox"
            outbox.mkdir()
            report = outbox / "report.json"
            report.write_text(json.dumps({"handoff_schema": "world-seed-terminal-output-handoff/v1"}))
            result = self.run_cli("publish", "--report", str(report), "--outbox", str(outbox))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--confirm-publish", result.stderr)
            elsewhere = root / "elsewhere.json"
            elsewhere.write_text(report.read_text())
            result = self.run_cli("publish", "--report", str(elsewhere), "--outbox", str(outbox),
                                  "--confirm-publish")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("inside the configured local outbox", result.stderr)

    def test_publish_refuses_nonapproved_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outbox = root / "outbox"
            outbox.mkdir()
            report = outbox / "report.json"
            report.write_text(json.dumps({"handoff_schema": "world-seed-terminal-output-handoff/v1"}))
            result = self.run_cli("publish", "--report", str(report), "--outbox", str(outbox),
                                  "--repo", "somewhere/public-repo", "--confirm-publish")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not the approved repository", result.stderr)

    def test_public_destination_refusal_with_fake_gh(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outbox = root / "outbox"
            outbox.mkdir()
            report = outbox / "report.json"
            report.write_text(json.dumps({"handoff_schema": "world-seed-terminal-output-handoff/v1"}))
            fakebin = root / "bin"
            fakebin.mkdir()
            gh = fakebin / "gh"
            gh.write_text("#!/bin/sh\nprintf 'false\\tmain\\n'\n")
            gh.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(fakebin) + os.pathsep + env.get("PATH", "")
            result = self.run_cli("publish", "--report", str(report), "--outbox", str(outbox),
                                  "--confirm-publish", env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("did not verify as private", result.stderr)



    def test_publish_success_writes_receipt_from_github_response(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outbox = root / "outbox"
            outbox.mkdir()
            report = outbox / "report.json"
            report.write_text(json.dumps({
                "handoff_schema": "world-seed-terminal-output-handoff/v1",
                "session_id": "test-session",
            }), encoding="utf-8")
            fakebin = root / "bin"
            fakebin.mkdir()
            gh = fakebin / "gh"
            gh.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "if sys.argv[1:3] == ['repo', 'view']:\n"
                " print('true\\tmain')\n"
                "elif sys.argv[1] == 'api':\n"
                " print(json.dumps({'content': {'html_url': 'https://github.com/mythologyprospector-hub/miracle-depot/blob/main/terminal-handoffs/report.json'}, 'commit': {'sha': 'a' * 40}}))\n"
                "else:\n"
                " sys.exit(2)\n",
                encoding="utf-8",
            )
            gh.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(fakebin) + os.pathsep + env.get("PATH", "")
            result = self.run_cli("publish", "--report", str(report), "--outbox", str(outbox),
                                  "--confirm-publish", env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("https://github.com/mythologyprospector-hub/miracle-depot/blob/main/terminal-handoffs/report.json", result.stdout)
            receipt = json.loads(report.with_suffix(".receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["commit_sha"], "a" * 40)
            self.assertEqual(receipt["repository"], "mythologyprospector-hub/miracle-depot")

if __name__ == "__main__":
    unittest.main()
