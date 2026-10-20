"""Keep operator-specific identity and machine data out of the distributable seed."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTABLE_DOCS = (
    "AGENTS.md",
    "AUDIT_SYSTEM.md",
    "AUTOMATION.md",
    "BASH_PROMPT.md",
    "BOOTSTRAP.md",
    "CONSISTENCY_STANDARD.md",
    "CONSTITUTION.md",
    "HUMAN.md",
    "LICENSE",
    "MACHINE_PROFILE.md",
    "MISSION.md",
    "ONBOARDING_PROMPT.md",
    "PROFILE_PACKAGES.md",
    "scripts/prepare_local_handoff_backup.sh",
    "README.md",
    "RECOVERY.md",
    "REPOSITORY_MODEL.md",
    "profiles/ACCOUNT_PROFILE.template.md",
    "templates/MISSION.md",
)
EMAIL_PATTERN = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
OPERATOR_MARKERS = re.compile(r"James Earl Stambaugh|jimmydev|mythologyprospector-hub|Copyright \\(c\\) 2026 James", re.IGNORECASE)


class PortableProfileBoundaryTests(unittest.TestCase):
    def test_profiles_directory_contains_only_the_generic_template(self):
        profile_files = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "profiles").rglob("*")
            if path.is_file()
        }
        self.assertEqual(profile_files, {"profiles/ACCOUNT_PROFILE.template.md"})

    def test_portable_documents_do_not_embed_email_addresses(self):
        for relative in PORTABLE_DOCS:
            with self.subTest(path=relative):
                content = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIsNone(EMAIL_PATTERN.search(content))

    def test_portable_documents_do_not_embed_operator_identity(self):
        for relative in PORTABLE_DOCS:
            with self.subTest(path=relative):
                content = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIsNone(OPERATOR_MARKERS.search(content))

    def test_license_uses_replaceable_portable_holder(self):
        content = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("<YEAR>", content)
        self.assertIn("<COPYRIGHT HOLDER>", content)

    def test_human_guidance_uses_the_profile_loading_contract(self):
        content = (ROOT / "HUMAN.md").read_text(encoding="utf-8")
        self.assertIn("PROFILE_PACKAGES.md", content)


if __name__ == "__main__":
    unittest.main()
