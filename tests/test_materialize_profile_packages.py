"""Exercise safe materialization of generic package templates using temporary directories."""
import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "materialize_profile_packages.py"
SPEC = importlib.util.spec_from_file_location("materialize_profile_packages", MODULE_PATH)
assert SPEC and SPEC.loader
MATERIALIZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MATERIALIZER)


class MaterializeProfilePackagesTests(unittest.TestCase):
    def test_creates_both_packages_with_private_permissions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            operator = root / "operator"
            personal = root / "personal"
            result = MATERIALIZER.materialize(ROOT / "templates", operator, personal)

            self.assertEqual(set(result), {"operator-profile", "personal-data"})
            self.assertEqual(set(result["operator-profile"]), {"README.md", "manifest.json", "PREFERENCES.md"})
            self.assertEqual(set(result["personal-data"]), {"README.md", "manifest.json"})
            self.assertEqual(
                (operator / "manifest.json").read_text(encoding="utf-8"),
                (ROOT / "templates/operator-profile/manifest.json").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (personal / "manifest.json").read_text(encoding="utf-8"),
                (ROOT / "templates/personal-data/manifest.json").read_text(encoding="utf-8"),
            )
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(operator.stat().st_mode), 0o700)
                self.assertEqual(stat.S_IMODE(personal.stat().st_mode), 0o700)
                for path in list(operator.iterdir()) + list(personal.iterdir()):
                    self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_second_run_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            operator, personal = root / "operator", root / "personal"
            MATERIALIZER.materialize(ROOT / "templates", operator, personal)
            result = MATERIALIZER.materialize(ROOT / "templates", operator, personal)
            self.assertEqual(result, {"operator-profile": [], "personal-data": []})

    def test_conflicting_existing_file_aborts_before_creating_other_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            operator, personal = root / "operator", root / "personal"
            operator.mkdir(mode=0o700)
            if os.name == "posix":
                os.chmod(operator, 0o700)
            (operator / "PREFERENCES.md").write_text("owner data must survive\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "refusing changes"):
                MATERIALIZER.materialize(ROOT / "templates", operator, personal)
            self.assertEqual(
                (operator / "PREFERENCES.md").read_text(encoding="utf-8"),
                "owner data must survive\n",
            )
            self.assertFalse(personal.exists())

    def test_refuses_non_private_existing_destination(self):
        if os.name != "posix":
            self.skipTest("POSIX permission bits are unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            operator, personal = root / "operator", root / "personal"
            operator.mkdir(mode=0o755)
            os.chmod(operator, 0o755)
            with self.assertRaisesRegex(ValueError, "not private"):
                MATERIALIZER.materialize(ROOT / "templates", operator, personal)
            self.assertFalse(personal.exists())

    def test_refuses_overlapping_destinations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "must be distinct"):
                MATERIALIZER.materialize(ROOT / "templates", root / "package", root / "package" / "child")


if __name__ == "__main__":
    unittest.main()
