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
            record = records[0]
            self.assertEqual(record["exit_code"], 0)
            self.assertIn("OUT_OK", record["stdout"])
            self.assertIn("ERR_OK", record["stderr"])
            self.assertTrue(record["started_at"])
            self.assertTrue(record["ended_at"])
            self.assertIn("cwd", record)
            self.assertIn("git_branch", record)
            self.assertIn("command", record)

    def test_preserves_nonzero_exit_code_and_records_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_dir = Path(temp) / "journal"
            result = self.invoke(log_dir, "--", sys.executable, "-c", "print('FAIL_MARKER'); raise SystemExit(7)")
            self.assertEqual(result.returncode, 7)
            _, records = self.records(log_dir)
            self.assertEqual(records[0]["exit_code"], 7)
            self.assertIn("FAIL_MARKER", records[0]["stdout"])

    def test_appends_multiple_commands_as_separate_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_dir = Path(temp) / "journal"
            first = self.invoke(log_dir, "--", sys.executable, "-c", "print('FIRST')")
            second = self.invoke(log_dir, "--", sys.executable, "-c", "print('SECOND')")
            self.assertEqual((first.returncode, second.returncode), (0, 0))
            _, records = self.records(log_dir)
            self.assertEqual(len(records), 2)
            self.assertIn("FIRST", records[0]["stdout"])
            self.assertIn("SECOND", records[1]["stdout"])

    def test_shell_mode_captures_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_dir = Path(temp) / "journal"
            result = self.invoke(log_dir, "--shell", "printf 'SHELL_OK\\n' | tr a-z A-Z")
            self.assertEqual(result.returncode, 0)
            self.assertIn("SHELL_OK", result.stdout)
            _, records = self.records(log_dir)
            self.assertIn("SHELL_OK", records[0]["stdout"])
            self.assertIsInstance(records[0]["command"], dict)

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
