"""Tests for metadata-only terminal journal recovery capsules."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_recovery_capsule.py"


class RecoveryCapsuleTests(unittest.TestCase):
    def write_journal(self, root: Path, project: str, records: list[dict[str, object]]) -> Path:
        directory = root / project
        directory.mkdir(parents=True)
        path = directory / "2026-10-22.jsonl"
        path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
        return path

    def invoke(self, root: Path, project: str, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--project", project, "--journal-root", str(root), "--output", str(output)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_capsule_contains_metadata_but_no_commands_or_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "journal"
            self.write_journal(root, "alpha", [
                {"schema_version": 2, "session_id": "session-1", "project": "alpha",
                 "event": "command_started", "recorded_at": "2026-10-22T10:00:00Z",
                 "command": ["echo", "SENSITIVE_COMMAND"], "cwd": "/private/path",
                 "git_branch": "feat/example", "git_dirty": False},
                {"schema_version": 2, "session_id": "session-1", "project": "alpha",
                 "event": "output", "sequence": 1, "stream": "stdout", "text": "SENSITIVE_OUTPUT"},
                {"schema_version": 2, "session_id": "session-1", "project": "alpha",
                 "event": "command_finished", "recorded_at": "2026-10-22T10:00:01Z",
                 "exit_code": 0, "interrupted": False, "stdout_bytes": 16, "stderr_bytes": 0,
                 "stdout_sha256": "abc", "stderr_sha256": "def", "journal_errors": []},
            ])
            output = Path(temp) / "capsule.json"
            result = self.invoke(root, "alpha", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            capsule_text = output.read_text(encoding="utf-8")
            capsule = json.loads(capsule_text)
            self.assertNotIn("SENSITIVE_COMMAND", capsule_text)
            self.assertNotIn("SENSITIVE_OUTPUT", capsule_text)
            self.assertNotIn("/private/path", capsule_text)
            self.assertEqual(capsule["project"], "alpha")
            self.assertEqual(capsule["sessions"][0]["exit_code"], 0)
            self.assertEqual(capsule["sessions"][0]["completion"], "recorded")
            self.assertFalse(capsule["source"]["stdout_stderr_text_included"])
            self.assertFalse(capsule["source"]["network_transfer_performed"])

    def test_missing_completion_is_not_reported_as_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "journal"
            self.write_journal(root, "alpha", [
                {"session_id": "partial", "project": "alpha", "event": "command_started",
                 "recorded_at": "2026-10-22T10:00:00Z", "git_branch": "main"},
            ])
            from importlib.util import module_from_spec, spec_from_file_location
            spec = spec_from_file_location("capsule_script", SCRIPT)
            module = module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)
            result = module.build_capsule("alpha", root)
            self.assertEqual(result["sessions"][0]["completion"], "incomplete_or_unrecorded")
            self.assertIsNone(result["sessions"][0]["exit_code"])

    def test_project_isolation_and_bad_project_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "journal"
            self.write_journal(root, "alpha", [
                {"session_id": "a", "project": "alpha", "event": "command_started",
                 "recorded_at": "2026-10-22T10:00:00Z"},
            ])
            self.write_journal(root, "beta", [
                {"session_id": "b", "project": "beta", "event": "command_started",
                 "recorded_at": "2026-10-22T10:00:00Z"},
            ])
            output = Path(temp) / "alpha.json"
            result = self.invoke(root, "alpha", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            capsule = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual([s["session_id"] for s in capsule["sessions"]], ["a"])
            rejected = self.invoke(root, "../beta", Path(temp) / "bad.json")
            self.assertEqual(rejected.returncode, 2)
            self.assertFalse((Path(temp) / "bad.json").exists())

    def test_output_is_private_and_existing_file_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "journal"
            self.write_journal(root, "alpha", [])
            output = Path(temp) / "private" / "capsule.json"
            result = self.invoke(root, "alpha", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            if os.name == "posix":
                self.assertEqual(output.stat().st_mode & 0o777, 0o600)
                self.assertEqual(output.parent.stat().st_mode & 0o777, 0o700)
            output.write_text("DO_NOT_OVERWRITE", encoding="utf-8")
            second = self.invoke(root, "alpha", output)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "DO_NOT_OVERWRITE")

    def test_malformed_records_are_reported_as_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "journal"
            directory = root / "alpha"
            directory.mkdir(parents=True)
            (directory / "broken.jsonl").write_text("{not json}\n", encoding="utf-8")
            output = Path(temp) / "capsule.json"
            result = self.invoke(root, "alpha", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            capsule = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(capsule["warnings"])


if __name__ == "__main__":
    unittest.main()
