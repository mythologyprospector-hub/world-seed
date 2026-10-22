"""Tests for conservative recovery-state refresh proposals."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "propose_recovery_state_refresh.py"
TEMPLATE = ROOT / "templates" / "recovery-project-state.template.json"


class RecoveryStateRefreshProposalTests(unittest.TestCase):
    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def make_repo(self, parent: Path) -> tuple[Path, str]:
        repo = parent / "repo"
        repo.mkdir()
        self.git(repo, "init", "-q")
        self.git(repo, "config", "user.name", "Test User")
        self.git(repo, "config", "user.email", "test@example.invalid")
        (repo / "tracked.txt").write_text("stable\n", encoding="utf-8")
        self.git(repo, "add", "tracked.txt")
        self.git(repo, "commit", "-qm", "initial")
        self.git(repo, "remote", "add", "origin", "https://github.com/owner/alpha.git")
        return repo, self.git(repo, "rev-parse", "HEAD")

    def make_state(self, path: Path, commit: str) -> bytes:
        state = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        state["project"]["name"] = "alpha"
        state["project"]["repository_url"] = "https://github.com/owner/alpha"
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

    def test_candidate_changes_only_freshness_and_preserves_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            repo, head = self.make_repo(parent)
            state_path = parent / "state.json"
            original_bytes = self.make_state(state_path, head)
            original = json.loads(original_bytes)
            output = parent / "private" / "candidate.json"

            result = self.invoke(state_path, repo, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            candidate = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(candidate["record"]["freshness"], "current")
            self.assertEqual(candidate["record"]["describes_commit"], head)
            original["record"]["freshness"] = candidate["record"]["freshness"]
            self.assertEqual(candidate, original)
            self.assertEqual(state_path.read_bytes(), original_bytes)
            if os.name == "posix":
                self.assertEqual(output.stat().st_mode & 0o777, 0o600)
                self.assertEqual(output.parent.stat().st_mode & 0o777, 0o700)

    def test_dirty_checkout_proposes_stale_without_changing_described_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            repo, head = self.make_repo(parent)
            (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
            state_path = parent / "state.json"
            self.make_state(state_path, head)
            output = parent / "candidate.json"

            result = self.invoke(state_path, repo, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            candidate = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(candidate["record"]["freshness"], "possibly_stale")
            self.assertEqual(candidate["record"]["describes_commit"], head)

    def test_invalid_project_fails_without_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            repo, head = self.make_repo(parent)
            state_path = parent / "state.json"
            self.make_state(state_path, head)
            output = parent / "candidate.json"

            result = self.invoke(state_path, repo, output, project="wrong")
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())

    def test_existing_candidate_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            repo, head = self.make_repo(parent)
            state_path = parent / "state.json"
            self.make_state(state_path, head)
            output = parent / "candidate.json"
            output.write_text("KEEP_ME", encoding="utf-8")

            result = self.invoke(state_path, repo, output)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "KEEP_ME")


if __name__ == "__main__":
    unittest.main()
