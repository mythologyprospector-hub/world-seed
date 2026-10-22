"""Tests for the durable local terminal journal."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "terminal_journal.py"


class TerminalJournalTests(unittest.TestCase):
    def invoke(self, log_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--log-dir", str(log_dir), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def records(self, log_dir: Path) -> tuple[Path, list[dict[str, object]]]:
        files = list(log_dir.rglob("*.jsonl"))
        self.assertEqual(len(files), 1, f"expected one journal file, got {files}")
        return files[0], [json.loads(line) for line in files[0].read_text(encoding="utf-8").splitlines()]

    def events(self, records: list[dict[str, object]], name: str) -> list[dict[str, object]]:
        return [record for record in records if record["event"] == name]

    def output(self, records: list[dict[str, object]], stream: str) -> str:
        return "".join(
            str(record["text"])
            for record in records
            if record["event"] == "output" and record["stream"] == stream
        )

    def test_captures_stdout_stderr_and_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_dir = Path(temp) / "journal"
            result = self.invoke(
                log_dir, "--", sys.executable, "-c",
                "import sys; print('OUT_OK'); print('ERR_OK', file=sys.stderr)",
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("OUT_OK", result.stdout)
            self.assertIn("ERR_OK", result.stderr)
            _, records = self.records(log_dir)
            started = self.events(records, "command_started")[0]
            finished = self.events(records, "command_finished")[0]
            self.assertIn("OUT_OK", self.output(records, "stdout"))
            self.assertIn("ERR_OK", self.output(records, "stderr"))
            self.assertTrue(started["recorded_at"])
            self.assertTrue(finished["recorded_at"])
            self.assertIn("cwd", started)
            self.assertIn("git_branch", started)
            self.assertIn("command", started)
            self.assertEqual(finished["exit_code"], 0)
            self.assertEqual(finished["stdout_bytes"], len(self.output(records, "stdout").encode()))
            self.assertTrue(finished["stdout_sha256"])

    def test_output_is_journaled_before_command_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_dir = Path(temp) / "journal"
            result = self.invoke(
                log_dir, "--", sys.executable, "-c",
                "import time; print('EARLY_MARKER', flush=True); time.sleep(0.2); print('LATE_MARKER')",
            )
            self.assertEqual(result.returncode, 0)
            _, records = self.records(log_dir)
            output_positions = [i for i, record in enumerate(records) if record["event"] == "output"]
            finish_positions = [i for i, record in enumerate(records) if record["event"] == "command_finished"]
            self.assertTrue(output_positions)
            self.assertTrue(finish_positions)
            self.assertLess(max(output_positions), finish_positions[0])
            self.assertIn("EARLY_MARKER", self.output(records, "stdout"))
            self.assertIn("LATE_MARKER", self.output(records, "stdout"))

    def test_preserves_nonzero_exit_code_and_records_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_dir = Path(temp) / "journal"
            result = self.invoke(log_dir, "--", sys.executable, "-c", "print('FAIL_MARKER'); raise SystemExit(7)")
            self.assertEqual(result.returncode, 7)
            _, records = self.records(log_dir)
            finished = self.events(records, "command_finished")[0]
            self.assertEqual(finished["exit_code"], 7)
            self.assertIn("FAIL_MARKER", self.output(records, "stdout"))

    def test_appends_multiple_commands_as_separate_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_dir = Path(temp) / "journal"
            first = self.invoke(log_dir, "--", sys.executable, "-c", "print('FIRST')")
            second = self.invoke(log_dir, "--", sys.executable, "-c", "print('SECOND')")
            self.assertEqual((first.returncode, second.returncode), (0, 0))
            _, records = self.records(log_dir)
            starts = self.events(records, "command_started")
            finishes = self.events(records, "command_finished")
            self.assertEqual(len(starts), 2)
            self.assertEqual(len(finishes), 2)
            self.assertNotEqual(starts[0]["session_id"], starts[1]["session_id"])
            self.assertIn("FIRST", self.output(records, "stdout"))
            self.assertIn("SECOND", self.output(records, "stdout"))

    def test_shell_mode_captures_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_dir = Path(temp) / "journal"
            result = self.invoke(log_dir, "--shell", "printf 'SHELL_OK\\n' | tr a-z A-Z")
            self.assertEqual(result.returncode, 0)
            self.assertIn("SHELL_OK", result.stdout)
            _, records = self.records(log_dir)
            self.assertIn("SHELL_OK", self.output(records, "stdout"))
            self.assertIsInstance(self.events(records, "command_started")[0]["command"], dict)

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits required")
    def test_journal_and_directory_permissions_are_private(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_dir = Path(temp) / "journal"
            result = self.invoke(log_dir, "--", sys.executable, "-c", "print('PRIVATE')")
            self.assertEqual(result.returncode, 0)
            path, _ = self.records(log_dir)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)

    def test_project_name_is_separated_and_invalid_names_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_dir = Path(temp) / "journal"
            result = self.invoke(
                log_dir, "--project", "other-project", "--", sys.executable, "-c", "print('LANE')"
            )
            self.assertEqual(result.returncode, 0)
            self.assertTrue((log_dir / "other-project").is_dir())
            invalid = self.invoke(
                log_dir, "--project", "../escape", "--", sys.executable, "-c", "print('NO')"
            )
            self.assertEqual(invalid.returncode, 2)
            self.assertFalse((Path(temp) / "escape").exists())


if __name__ == "__main__":
    unittest.main()
