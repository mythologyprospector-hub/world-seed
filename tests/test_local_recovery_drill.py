"""Tests for the bounded local Git recovery drill."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_local_recovery_drill.py"


class LocalRecoveryDrillTests(unittest.TestCase):
    def test_drill_restores_known_checkpoint_after_controlled_damage(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["overall_status"], "passed")
        self.assertTrue(report["fresh_clone_matches_checkpoint"])
        self.assertTrue(report["controlled_damage_observed"])
        self.assertEqual(report["working_tree_restore"], "passed")
        self.assertTrue(report["restored_working_tree_clean"])
        self.assertTrue(report["limitations"])

    def test_report_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "report.json"
            target.write_text("preserve me", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(target)],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), "preserve me")


if __name__ == "__main__":
    unittest.main()
