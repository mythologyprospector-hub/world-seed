"""Regression tests for local handoff backup destination safety."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class HandoffBackupSafetyTests(unittest.TestCase):
    def test_refuses_dangling_symlink_destination_without_creating_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            gh = bin_dir / "gh"
            gh.write_text(
                "#!/usr/bin/env bash\n"
                'if [[ "$1" == "auth" && "$2" == "status" ]]; then exit 0; fi\n'
                "exit 99\n",
                encoding="utf-8",
            )
            gh.chmod(0o755)

            target = root / "sensitive-backup-location"
            destination = root / "backup-link"
            destination.symlink_to(target, target_is_directory=True)
            script = (
                Path(__file__).resolve().parents[1]
                / "scripts"
                / "prepare_local_handoff_backup.sh"
            )
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"

            result = subprocess.run(
                ["bash", str(script), "example-owner", str(destination)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(target.exists(), "refused destination must not create the symlink target")
            self.assertIn("destination already exists", result.stderr)


if __name__ == "__main__":
    unittest.main()
