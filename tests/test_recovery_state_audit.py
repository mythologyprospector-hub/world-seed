"""Tests for the read-only recovery-state audit tool."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_recovery_state.py"
TEMPLATE = ROOT / "templates" / "recovery-project-state.template.json"


class RecoveryStateAuditTests(unittest.TestCase):
    def make_repo(self, parent: Path, origin: str = "https://github.com/owner/alpha.git") -> tuple[Path, str]:
        repo = parent / "repo"
        repo.mkdir()
        self.git(repo, "init", "-q")
        self.git(repo, "config", "user.name", "Test User")
        self.git(repo, "config", "user.email", "test@example.invalid")
        (repo / "tracked.txt").write_text("stable\n", encoding="utf-8")
        self.git(repo, "add", "tracked.txt")
        self.git(repo, "commit", "-qm", "initial")
        self.git(repo, "remote", "add", "origin", origin)
        head = self.git(repo, "rev-parse", "HEAD")
        return repo, head

    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def make_state(self, path: Path, commit: str, origin: str = "https://github.com/owner/alpha") -> bytes:
        state = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        state["project"]["name"] = "alpha"
        state["project"]["repository_url"] = origin
        state["record"]["describes_commit"] = commit
        state["record"]["freshness"] = "unknown"
        raw = (json.dumps(state, indent=2) + "\n").encode()
        path.write_bytes(raw)
        return raw

    def invoke(self, state: Path, repo: Path, output: Path, project: str = "alpha") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--project", project, "--state", str(state),
             "--repo", str(repo), "--output", str(output)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )

    def test_matching_clean_checkout_proposes_current_without_editing_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            repo, head = self.make_repo(parent)
            state_path = parent / "state.json"
            original = self.make_state(state_path, head)
            output = parent / "private" / "audit.json"
            result = self.invoke(state_path, repo, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["comparison"]["proposed_freshness"], "current")
            self.assertEqual(report["comparison"]["checks"]["repository_identity"]["status"], "match")
            self.assertEqual(report["comparison"]["checks"]["commit"]["status"], "match")
            self.assertEqual(state_path.read_bytes(), original)
            if os.name == "posix":
                self.assertEqual(output.stat().st_mode & 0o777, 0o600)
                self.assertEqual(output.parent.stat().st_mode & 0o777, 0o700)
            self.assertIn("does not verify tests", " ".join(report["limitations"]))
            suggestions = report["comparison"]["suggested_metadata_changes"]
            self.assertEqual([item["field"] for item in suggestions], ["record.freshness"])
            self.assertEqual(report["observed_repository"]["head_commit"], head)

    def test_dirty_checkout_is_not_current(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            repo, head = self.make_repo(parent)
            (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
            state = parent / "state.json"
            self.make_state(state, head)
            output = parent / "audit.json"
            result = self.invoke(state, repo, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(report["observed_repository"]["dirty"])
            self.assertEqual(report["comparison"]["proposed_freshness"], "possibly_stale")

    def test_commit_and_origin_mismatches_are_reported_separately(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            repo, _ = self.make_repo(parent, "https://github.com/elsewhere/other.git")
            state = parent / "state.json"
            self.make_state(state, "0" * 40)
            output = parent / "audit.json"
            result = self.invoke(state, repo, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            checks = json.loads(output.read_text())["comparison"]["checks"]
            self.assertEqual(checks["repository_identity"]["status"], "mismatch")
            self.assertEqual(checks["commit"]["status"], "mismatch")

    def test_ssh_origin_matches_https_repository_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            repo, head = self.make_repo(parent, "git@github.com:owner/alpha.git")
            state = parent / "state.json"
            self.make_state(state, head)
            output = parent / "audit.json"
            result = self.invoke(state, repo, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(report["comparison"]["checks"]["repository_identity"]["status"], "match")
            self.assertNotIn("git@", json.dumps(report))

    def test_wrong_project_and_invalid_state_fail_without_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            repo, head = self.make_repo(parent)
            state = parent / "state.json"
            original = self.make_state(state, head)
            output = parent / "audit.json"
            wrong = self.invoke(state, repo, output, project="beta")
            self.assertEqual(wrong.returncode, 2)
            self.assertFalse(output.exists())
            self.assertEqual(state.read_bytes(), original)
            state.write_text("{broken", encoding="utf-8")
            invalid = self.invoke(state, repo, output)
            self.assertEqual(invalid.returncode, 2)
            self.assertFalse(output.exists())

    def test_existing_report_is_never_overwritten_and_detached_head_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            repo, head = self.make_repo(parent)
            self.git(repo, "checkout", "--detach", "-q", head)
            state = parent / "state.json"
            self.make_state(state, head)
            output = parent / "audit.json"
            output.write_text("KEEP_ME", encoding="utf-8")
            result = self.invoke(state, repo, output)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output.read_text(), "KEEP_ME")
            output.unlink()
            retry = self.invoke(state, repo, output)
            self.assertEqual(retry.returncode, 0, retry.stderr)
            report = json.loads(output.read_text())
            self.assertTrue(report["observed_repository"]["detached_head"])
            self.assertIsNone(report["observed_repository"]["branch"])


if __name__ == "__main__":
    unittest.main()
