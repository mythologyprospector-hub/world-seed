"""Validate generic package templates without using real operator or personal data."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPERATOR = ROOT / "templates" / "operator-profile"
PERSONAL = ROOT / "templates" / "personal-data"


class ProfilePackageTemplateTests(unittest.TestCase):
    def test_all_expected_template_files_exist(self):
        expected = {
            OPERATOR / "README.md",
            OPERATOR / "manifest.json",
            OPERATOR / "PREFERENCES.md",
            PERSONAL / "README.md",
            PERSONAL / "manifest.json",
        }
        for path in expected:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertTrue(path.is_file())

    def test_operator_manifest_is_valid_and_points_to_preferences(self):
        manifest = json.loads((OPERATOR / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["package_type"], "operator-profile")
        self.assertEqual(manifest["sensitivity"], "private")
        self.assertEqual(manifest["included_sections"], ["PREFERENCES.md"])
        self.assertEqual(manifest["intended_operator"], "unknown")
        self.assertIn("provenance", manifest)

    def test_personal_data_manifest_starts_empty_and_private(self):
        manifest = json.loads((PERSONAL / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["package_type"], "personal-data")
        self.assertEqual(manifest["sensitivity"], "highly-private")
        self.assertEqual(manifest["records"], [])
        self.assertEqual(manifest["intended_owner"], "unknown")
        self.assertIn("provenance", manifest)

    def test_templates_warn_against_secrets_and_overwriting(self):
        operator = (OPERATOR / "README.md").read_text(encoding="utf-8")
        preferences = (OPERATOR / "PREFERENCES.md").read_text(encoding="utf-8")
        personal = (PERSONAL / "README.md").read_text(encoding="utf-8")
        self.assertIn("must refuse to overwrite", operator)
        self.assertIn("Do not store credentials", preferences)
        self.assertIn("Preserve original exports", personal)
        self.assertIn("must not overwrite existing records", personal)


if __name__ == "__main__":
    unittest.main()
