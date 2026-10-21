"""Unit tests for the world-seed structural validator."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_seed.py"
SPEC = importlib.util.spec_from_file_location("validate_seed", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

class ValidateSeedTests(unittest.TestCase):
    def test_missing_required_file_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            errors = VALIDATOR.validate(Path(temporary))
        self.assertTrue(any("required file missing: README.md" in item for item in errors))

    def test_missing_mission_document_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            errors = VALIDATOR.validate(Path(temporary))
        self.assertTrue(any("required file missing: MISSION.md" in item for item in errors))

    def test_missing_project_seed_absorption_contract_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            errors = VALIDATOR.validate(Path(temporary))
        self.assertTrue(any("required file missing: PROJECT_SEED_ABSORPTION.md" in item for item in errors))

    def test_broken_local_link_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("# Title\n\n[Missing](missing.md)\n", encoding="utf-8")
            errors = VALIDATOR.validate(root)
        self.assertTrue(any("broken local link" in item for item in errors))

    def test_valid_local_link_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("# Title\n\n[Other](other.md)\n", encoding="utf-8")
            (root / "other.md").write_text("# Other\n", encoding="utf-8")
            errors = VALIDATOR.validate(root)
        self.assertFalse(any("broken local link" in item for item in errors))

    def test_empty_markdown_link_target_does_not_crash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("# Title\n\n[Empty]()\n", encoding="utf-8")
            errors = VALIDATOR.validate(root)
        self.assertFalse(any("broken local link" in item for item in errors))

    def test_link_examples_inside_fenced_code_are_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fence = chr(96) * 3
            example = "# Title\n\n" + fence + "md\n[Example](missing-file.md)\n" + fence + "\n"
            (root / "README.md").write_text(example, encoding="utf-8")
            errors = VALIDATOR.validate(root)
        self.assertFalse(any("broken local link" in item for item in errors))

if __name__ == "__main__":
    unittest.main()
