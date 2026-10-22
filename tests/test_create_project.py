"""Tests for World Seed's portable project generator."""
import importlib.util
import json
import hashlib
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "create_project.py"
SPEC = importlib.util.spec_from_file_location("create_project", MODULE_PATH)
assert SPEC and SPEC.loader
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class CreateProjectTests(unittest.TestCase):
    def test_installed_release_directory_preserves_commit_provenance_without_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            revision = "d" * 40
            release = Path(temporary) / revision
            release.mkdir()
            self.assertEqual(GENERATOR.source_revision(release), revision)

    def test_generates_complete_bundle_and_provenance_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "example-project"
            created = GENERATOR.create_project(
                ROOT,
                "example-project",
                "Help people solve a useful problem.",
                destination,
                revision="a" * 40,
            )
            self.assertEqual(created, destination)
            manifest = json.loads((created / "world-seed-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["project_name"], "example-project")
            self.assertEqual(manifest["mission"], "Help people solve a useful problem.")
            self.assertEqual(manifest["template_version"], "1.1.0")
            self.assertEqual(manifest["source_revision"], "a" * 40)
            self.assertTrue(manifest["manifest_excludes_itself"])
            self.assertEqual(set(manifest["generated_files"]), set(GENERATOR.PROJECT_FILES))
            self.assertEqual(set(manifest["generated_file_sha256"]), set(GENERATOR.PROJECT_FILES))
            for name in GENERATOR.PROJECT_FILES:
                self.assertTrue((created / name).is_file(), name)
                expected = hashlib.sha256((created / name).read_bytes()).hexdigest()
                self.assertEqual(manifest["generated_file_sha256"][name], expected)
            self.assertTrue((created / "world-seed-manifest.json").is_file())
            license_text = (created / "LICENSE").read_text(encoding="utf-8")
            self.assertIn("<YEAR>", license_text)
            self.assertIn("<COPYRIGHT HOLDER>", license_text)

    def test_generated_builder_guidance_requires_real_project_work_and_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            created = GENERATOR.create_project(
                ROOT,
                "quality-project",
                "Deliver a useful result.",
                Path(temporary) / "quality-project",
                revision="e" * 40,
            )
            guidance = (created / "AGENTS.md").read_text(encoding="utf-8")
            for requirement in (
                "First-build protocol",
                "Build a complete first slice",
                "Test the behavior",
                "Make it reproducible",
                "Review the whole project",
                "Do not stop after creating its documents",
                "Do not call the project useful, complete, or recovery-worthy",
            ):
                self.assertIn("social preview", (created / "DOCS.md").read_text(encoding="utf-8").lower())
                self.assertIn(requirement, guidance)

    def test_custom_mission_replaces_marker_and_readme_placeholders(self):
        with tempfile.TemporaryDirectory() as temporary:
            created = GENERATOR.create_project(
                ROOT,
                "bright-idea",
                "Make useful knowledge easier to discover.",
                Path(temporary) / "bright-idea",
                revision="b" * 40,
            )
            mission = (created / "MISSION.md").read_text(encoding="utf-8")
            readme = (created / "README.md").read_text(encoding="utf-8")
            self.assertIn("**Make useful knowledge easier to discover.**", mission)
            self.assertNotIn(GENERATOR.MISSION_MARKER, mission)
            self.assertIn("# bright-idea", readme)
            self.assertIn("Make useful knowledge easier to discover.", readme)
            self.assertNotIn("{{PROJECT_NAME}}", readme)
            self.assertNotIn("{{MISSION}}", readme)

    def test_existing_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "keep-me"
            destination.mkdir()
            marker = destination / "owner-data.txt"
            marker.write_text("preserve", encoding="utf-8")
            with self.assertRaises(GENERATOR.ProjectGenerationError):
                GENERATOR.create_project(ROOT, "keep-me", "A mission.", destination)
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")

    def test_symbolic_link_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "preserve-me"
            target.mkdir()
            (target / "marker.txt").write_text("preserve", encoding="utf-8")
            link = root / "project-link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(GENERATOR.ProjectGenerationError):
                GENERATOR.create_project(ROOT, "project-link", "A mission.", link)
            self.assertEqual((target / "marker.txt").read_text(encoding="utf-8"), "preserve")

    def test_invalid_name_and_blank_mission_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "new-project"
            with self.assertRaises(GENERATOR.ProjectGenerationError):
                GENERATOR.create_project(ROOT, "Not A Slug", "A mission.", destination)
            with self.assertRaises(GENERATOR.ProjectGenerationError):
                GENERATOR.create_project(ROOT, "new-project", "   ", destination)

    def test_multiline_mission_and_invalid_revision_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "new-project"
            with self.assertRaises(GENERATOR.ProjectGenerationError):
                GENERATOR.create_project(ROOT, "new-project", "First line" + chr(10) + "Second line", destination)
            with self.assertRaises(GENERATOR.ProjectGenerationError):
                GENERATOR.create_project(ROOT, "new-project", "A mission.", destination, revision="not-a-sha")

    def test_output_must_be_outside_factory_source_checkout(self):
        with self.assertRaises(GENERATOR.ProjectGenerationError):
            GENERATOR.create_project(
                ROOT,
                "unsafe-output",
                "A mission.",
                ROOT / "generated" / "unsafe-output",
            )

    def test_portable_bundle_does_not_embed_operator_machine_or_secret_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            created = GENERATOR.create_project(
                ROOT,
                "portable-project",
                "A portable mission.",
                Path(temporary) / "portable-project",
                revision="c" * 40,
            )
            bundle = "\n".join(
                (created / name).read_text(encoding="utf-8")
                for name in GENERATOR.PROJECT_FILES
            )
            self.assertNotIn("mythos1", bundle)
            self.assertNotIn("/srv/organs", bundle)
            self.assertNotIn("PROJECT_SEED_SYNC_TOKEN", bundle)
            self.assertNotIn("BEGIN PRIVATE KEY", bundle)


if __name__ == "__main__":
    unittest.main()
