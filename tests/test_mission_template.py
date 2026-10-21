"""Ensure the reusable mission template differs only in its opening mission sentence."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSION_SENTENCE = "**<PROJECT_MISSION_SENTENCE>**"


def normalized_mission(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 4 or lines[0] != "# Mission" or not lines[2].startswith("**") or not lines[2].endswith("**"):
        raise AssertionError(f"{path.name} does not have the canonical mission heading and opening sentence")
    lines[2] = MISSION_SENTENCE
    return "\n".join(lines).rstrip() + "\n"


class MissionTemplateTests(unittest.TestCase):
    def test_mission_and_template_share_identical_operating_method(self):
        self.assertEqual(
            normalized_mission(ROOT / "MISSION.md"),
            normalized_mission(ROOT / "templates" / "MISSION.md"),
        )

    def test_template_has_only_one_explicit_replacement_instruction(self):
        template = (ROOT / "templates" / "MISSION.md").read_text(encoding="utf-8")
        self.assertEqual(template.count("REPLACE THIS SENTENCE"), 1)
        self.assertIn("Preserve the shared operating method below it", template)


if __name__ == "__main__":
    unittest.main()
