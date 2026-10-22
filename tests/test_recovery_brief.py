"""Tests for local recovery-brief rendering."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_recovery_brief.py"
TEMPLATE = ROOT / "templates" / "recovery-project-state.template.json"


class RecoveryBriefTests(unittest.TestCase):
    def make_state(self, path: Path) -> None:
        state = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        state["project"]["name"] = "alpha"
        state["project"]["repository_url"] = "https://private-user:private-password@github.com/owner/alpha?private-query=yes#fragment"
        state["project"]["purpose"] = "A test project purpose."
        state["record"]["freshness"] = "possibly_stale"
        state["record"]["describes_commit"] = "a" * 40
        state["canon"]["summary"] = "Read the canonical rules first."
        state["canon"]["authoritative_documents"] = [
            {"title": "Canon", "location": "CANON.md", "authority": "canonical"}
        ]
        state["decisions"]["accepted"] = [{
            "statement": "Do not overwrite existing state.",
            "status": "explicitly_accepted",
            "provenance": "Human decision",
            "scope": "Local recovery files",
            "evidence": ["decision-note.md"],
        }]
        state["verification"] = [{
            "claim": "Focused tests passed",
            "commit": "b" * 40,
            "method": "python -m unittest",
            "result": "pass",
            "checked_at": "2026-10-21T12:00:00Z",
            "evidence": ["Actions run 123"],
            "scope_limitations": ["Only the listed suite was run."],
        }]
        path.write_text(json.dumps(state), encoding="utf-8")

    def invoke(self, state: Path, project: str = "alpha") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--project", project, "--state", str(state)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )

    def test_brief_includes_state_and_warns_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / "state.json"
            self.make_state(state_path)
            result = self.invoke(state_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("# Recovery Brief — alpha", result.stdout)
            self.assertIn("**possibly_stale**", result.stdout)
            self.assertIn("Freshness warning", result.stdout)
            self.assertIn("Do not overwrite existing state.", result.stdout)
            self.assertIn("One proposed next action", result.stdout)
            self.assertIn("does not grant authority", result.stdout)

    def test_verification_commit_mismatch_is_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / "state.json"
            self.make_state(state_path)
            result = self.invoke(state_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("verification commit differs", result.stdout)
            self.assertIn("Only the listed suite was run.", result.stdout)

    def test_repository_url_credentials_and_query_are_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / "state.json"
            self.make_state(state_path)
            result = self.invoke(state_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("https://github.com/owner/alpha", result.stdout)
            for secret_like in ("private-user", "private-password", "private-query", "fragment"):
                self.assertNotIn(secret_like, result.stdout)

    def test_wrong_project_fails_without_rendering_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / "state.json"
            self.make_state(state_path)
            result = self.invoke(state_path, project="wrong")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
