import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "world_seed_see.py"
SPEC = importlib.util.spec_from_file_location("world_seed_see", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class WorldSeedSeeTests(unittest.TestCase):
    def test_redacts_common_password_and_bearer_shapes(self):
        value = "pass" + "word=" + "dummy-value " + "Authorization: Bearer " + "abcdefghijklmno"
        result = MODULE.redact(value)
        self.assertNotIn("dummy-value", result)
        self.assertNotIn("abcdefghijklmno", result)
        self.assertIn("[REDACTED]", result)

    def test_redacts_github_token_shape(self):
        value = "ghp_" + "A" * 30
        result = MODULE.redact(value)
        self.assertNotIn(value, result)
        self.assertIn("[REDACTED_GITHUB_TOKEN]", result)


if __name__ == "__main__":
    unittest.main()
