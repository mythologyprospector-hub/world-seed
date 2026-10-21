from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "scripts" / "install_local_factory.sh"


class LocalFactoryInstallerTests(unittest.TestCase):
    def test_installer_passes_bash_syntax_check(self) -> None:
        result = subprocess.run(["bash", "-n", str(INSTALLER)], check=False, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_installer_declares_safe_first_layer_boundaries(self) -> None:
        source = INSTALLER.read_text(encoding="utf-8")
        self.assertIn("status --porcelain --untracked-files=normal", source)
        self.assertIn("refusing to overwrite", source)
        self.assertIn("chmod 600", source)
        self.assertIn("remote_delivery", source)
        self.assertIn("api_bus_changes", source)
        self.assertIn('git -C "$SOURCE_ROOT" archive "$REV"', source)
        self.assertNotIn("gh auth token", source)
        self.assertNotIn("git push", source)

    @unittest.skipUnless(shutil.which("git") and shutil.which("python3"), "git/python3 required")
    def test_installs_into_isolated_home_without_network_or_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout = root / "checkout"
            shutil.copytree(REPO_ROOT, checkout, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
            subprocess.run(["git", "init", "-q", str(checkout)], check=True)
            subprocess.run(["git", "-C", str(checkout), "config", "user.email", "factory-test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(checkout), "config", "user.name", "Factory Test"], check=True)
            subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
            subprocess.run(["git", "-C", str(checkout), "commit", "-qm", "fixture"], check=True)

            fake_bin = root / "fake-bin"
            fake_bin.mkdir()
            fake_uv = fake_bin / "uv"
            fake_uv.write_text(
                "#!/usr/bin/env bash\n"
                "set -e\n"
                "if [[ \"$1\" == \"venv\" ]]; then\n"
                "  shift; [[ \"$1\" != \"--python\" ]] || shift 2\n"
                "  exec python3 -m venv \"$1\"\n"
                "fi\n"
                "if [[ \"$1\" == \"pip\" && \"$2\" == \"install\" ]]; then exit 0; fi\n"
                "exit 2\n",
                encoding="utf-8",
            )
            fake_uv.chmod(0o755)
            home = root / "home"
            home.mkdir()
            factory_home = root / "installed-factory"
            state_home = root / "private-state"
            environment = os.environ.copy()
            environment.pop("WORLD_SEED_OPERATOR_PROFILE_DESTINATION", None)
            environment.pop("WORLD_SEED_PERSONAL_DATA_DESTINATION", None)
            environment.pop("WORLD_SEED_INTAKE_DOCK_DESTINATION", None)
            environment.pop("WORLD_SEED_INTAKE_DOCK_LANE", None)
            environment.update({
                "HOME": str(home),
                "PATH": f"{fake_bin}:{environment['PATH']}",
                "WORLD_SEED_FACTORY_HOME": str(factory_home),
                "WORLD_SEED_STATE_HOME": str(state_home),
            })
            result = subprocess.run(
                ["bash", str(checkout / "scripts" / "install_local_factory.sh")],
                cwd=checkout, env=environment, check=False, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((factory_home / "current" / "scripts" / "collect_machine_profile.py").is_file())
            self.assertTrue((factory_home / "current" / "scripts" / "export_github_operating_records.py").is_file())
            self.assertTrue((factory_home / "current" / ".venv" / "bin" / "python").is_file())
            reports = list(state_home.glob("machine-profile-*.json"))
            manifests = list(state_home.glob("install-*.tsv"))
            self.assertEqual(len(reports), 1)
            self.assertEqual(len(manifests), 1)
            self.assertEqual(reports[0].stat().st_mode & 0o777, 0o600)
            self.assertEqual(manifests[0].stat().st_mode & 0o777, 0o600)
            self.assertEqual(state_home.stat().st_mode & 0o777, 0o700)
            self.assertIn("remote_delivery\tnot_configured", manifests[0].read_text(encoding="utf-8"))
            self.assertIn("profile_packages\tnot_configured", manifests[0].read_text(encoding="utf-8"))

            # A second run reuses the exact release and initializes only explicitly selected destinations.
            operator_destination = root / "private-operator-profile"
            personal_destination = root / "private-personal-data"
            second_state_home = root / "private-state-with-packages"
            configured_environment = environment.copy()
            configured_environment.update({
                "WORLD_SEED_STATE_HOME": str(second_state_home),
                "WORLD_SEED_OPERATOR_PROFILE_DESTINATION": str(operator_destination),
                "WORLD_SEED_PERSONAL_DATA_DESTINATION": str(personal_destination),
                "WORLD_SEED_INTAKE_DOCK_DESTINATION": str(root / "private-intake-dock"),
                "WORLD_SEED_INTAKE_DOCK_LANE": "episteme",
            })
            configured_result = subprocess.run(
                ["bash", str(checkout / "scripts" / "install_local_factory.sh")],
                cwd=checkout, env=configured_environment, check=False,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(configured_result.returncode, 0, configured_result.stdout + configured_result.stderr)
            self.assertTrue((operator_destination / "PREFERENCES.md").is_file())
            self.assertTrue((personal_destination / "manifest.json").is_file())
            dock_destination = root / "private-intake-dock"
            self.assertTrue((dock_destination / "projects" / "episteme" / "incoming").is_dir())
            self.assertTrue((dock_destination / "projects" / "episteme" / "inventory").is_dir())
            configured_manifests = list(second_state_home.glob("install-*.tsv"))
            self.assertEqual(len(configured_manifests), 1)
            configured_manifest = configured_manifests[0].read_text(encoding="utf-8")
            self.assertIn("profile_packages\tmaterialized", configured_manifest)
            self.assertIn("intake_dock\tmaterialized_local_only", configured_manifest)

            incomplete_environment = configured_environment.copy()
            incomplete_environment.pop("WORLD_SEED_INTAKE_DOCK_LANE", None)
            incomplete_environment["WORLD_SEED_STATE_HOME"] = str(root / "state-incomplete-dock")
            incomplete = subprocess.run(
                ["bash", str(checkout / "scripts" / "install_local_factory.sh")],
                cwd=checkout, env=incomplete_environment, check=False,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(incomplete.returncode, 2)
            self.assertIn("set both WORLD_SEED_INTAKE_DOCK_DESTINATION and WORLD_SEED_INTAKE_DOCK_LANE", incomplete.stderr)


if __name__ == "__main__":
    unittest.main()
