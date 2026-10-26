"""Tests for explicit, local-only interactive terminal handoff preparation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_interactive_handoff.py"
SESSION = "5f664a7f-8c3f-4b32-8835-5d9cf0e46c9c"


class InteractiveHandoffTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True, check=False)

    def fixture(self, root: Path, output: str) -> Path:
        interactive = root / "interactive"
        interactive.mkdir(parents=True)
        path = interactive / "2026-10-26.jsonl"
        records = [
            {"session_id": SESSION, "event": "session_started", "sequence": 0,
             "recorded_at": "2026-10-26T10:00:00+00:00", "cwd": "/home/test/project",
             "shell": "/bin/bash"},
            {"session_id": SESSION, "event": "terminal_output", "sequence": 1,
             "recorded_at": "2026-10-26T10:00:01+00:00", "text": output},
            {"session_id": SESSION, "event": "session_finished", "sequence": 2,
             "recorded_at": "2026-10-26T10:00:02+00:00", "exit_code": 0,
             "interrupted": False, "error": None},
        ]
        path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
        return path

    def test_prepare_redacts_bounds_and_does_not_upload(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root, "synthetic success\nAPI_KEY=not-a-real-secret-value\n")
            outbox = root / "outbox"
            result = self.run_cli("--session", SESSION, "--journal-root", str(root),
                                  "--outbox", str(outbox))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("NOT uploaded", result.stdout)
            report_path = outbox / f"interactive-handoff-{SESSION}.json"
            self.assertEqual(report_path.stat().st_mode & 0o777, 0o600)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["handoff_schema"], "world-seed-terminal-output-handoff/v1")
            self.assertIn("synthetic success", report["stdout"])
            self.assertNotIn("not-a-real-secret-value", report["stdout"])
            self.assertTrue(report["redactions_applied"])
            self.assertEqual(report["exit_code"], 0)
            self.assertEqual(report["completion"], "recorded")
            self.assertEqual(report["repository"], "project")

    def test_requires_exact_existing_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root, "synthetic only\n")
            result = self.run_cli("--session", "00000000-0000-4000-8000-000000000000",
                                  "--journal-root", str(root), "--outbox", str(root / "outbox"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("exact session ID was not found", result.stderr)

    def test_marks_truncated_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root, "x" * 5000)
            outbox = root / "outbox"
            result = self.run_cli("--session", SESSION, "--journal-root", str(root),
                                  "--outbox", str(outbox), "--max-output-bytes", "1024")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((outbox / f"interactive-handoff-{SESSION}.json").read_text())
            self.assertTrue(report["truncated"])
            self.assertLessEqual(len(report["stdout"].encode()), 1024)

    def test_rejects_malformed_journal_instead_of_claiming_zero_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            journal = self.fixture(root, "synthetic output\\n")
            with journal.open("a", encoding="utf-8") as stream:
                stream.write("{malformed json\\n")
            outbox = root / "outbox"
            result = self.run_cli("--session", SESSION, "--journal-root", str(root),
                                  "--outbox", str(outbox))
            self.assertEqual(result.returncode, 2)
            self.assertIn("malformed JSONL record", result.stderr)
            self.assertFalse(outbox.exists() and list(outbox.glob("*.json")))

if __name__ == "__main__":
    unittest.main()
