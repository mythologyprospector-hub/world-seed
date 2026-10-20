"""Keep source-operator identity and machine details out of the distributable seed."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTABLE_DOCS = (
    "AGENTS.md",
    "BOOTSTRAP.md",
    "BASH_PROMPT.md",
    "CONSTITUTION.md",
    "HUMAN.md",
    "MACHINE_PROFILE.md",
    "MISSION.md",
    "ONBOARDING_PROMPT.md",
    "PROFILE_PACKAGES.md",
    "README.md",
    "REPOSITORY_MODEL.md",
    "profiles/ACCOUNT_PROFILE.template.md",
    "templates/MISSION.md",
)

SOURCE_OPERATOR_MARKERS = (
    "James Earl Stambaugh III",
    "mythologyprospector@gmail.com",
    "mythos1",
    "Bucky",
    "/srv/organs",
    "teresa-oracle",
    "profiles/jimmy.md",
)


class PortableProfileBoundaryTests(unittest.TestCase):
    def test_operator_specific_profile_is_not_bundled(self):
        self.assertFalse((ROOT / "profiles" / "jimmy.md").exists())

    def test_portable_documents_do_not_hardcode_source_operator_details(self):
        for relative in PORTABLE_DOCS:
            with self.subTest(path=relative):
                content = (ROOT / relative).read_text(encoding="utf-8")
                self.assertNotIn("Jimmy", content)
                for marker in SOURCE_OPERATOR_MARKERS:
                    with self.subTest(path=relative, marker=marker):
                        self.assertNotIn(marker, content)

    def test_human_guidance_uses_the_profile_loading_contract(self):
        content = (ROOT / "HUMAN.md").read_text(encoding="utf-8")
        self.assertIn("PROFILE_PACKAGES.md", content)
        self.assertNotIn("Read profiles/jimmy.md", content)


if __name__ == "__main__":
    unittest.main()
