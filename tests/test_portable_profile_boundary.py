"""Keep source-operator identity out of portable operating instructions."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTABLE_DOCS = (
    "AGENTS.md",
    "BOOTSTRAP.md",
    "CONSTITUTION.md",
    "HUMAN.md",
    "MACHINE_PROFILE.md",
    "MISSION.md",
    "ONBOARDING_PROMPT.md",
    "README.md",
    "REPOSITORY_MODEL.md",
    "templates/MISSION.md",
)


class PortableProfileBoundaryTests(unittest.TestCase):
    def test_portable_documents_do_not_hardcode_the_source_operator(self):
        for relative in PORTABLE_DOCS:
            with self.subTest(path=relative):
                content = (ROOT / relative).read_text(encoding="utf-8")
                self.assertNotIn("Jimmy", content)
                self.assertNotIn("profiles/jimmy.md", content)

    def test_human_guidance_uses_the_profile_loading_contract(self):
        content = (ROOT / "HUMAN.md").read_text(encoding="utf-8")
        self.assertIn("PROFILE_PACKAGES.md", content)
        self.assertNotIn("Read profiles/jimmy.md", content)


if __name__ == "__main__":
    unittest.main()
