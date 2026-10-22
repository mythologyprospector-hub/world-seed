"""Tests for the local Project Library catalog."""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("project_library", ROOT / "scripts" / "project_library.py")
assert SPEC and SPEC.loader
LIBRARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LIBRARY)


class ProjectLibraryTests(unittest.TestCase):
    def make_project(self, root: Path, name: str = "sample-project") -> Path:
        project = root / name
        project.mkdir()
        contents = {"README.md": "# Sample\n", "MISSION.md": "A mission.\n"}
        for filename, content in contents.items():
            (project / filename).write_text(content, encoding="utf-8")
        manifest = {
            "schema_version": 1,
            "project_name": name,
            "mission": "A mission.",
            "template_version": "1.0.0",
            "source_revision": "a" * 40,
            "generated_files": sorted(contents),
            "generated_file_sha256": {
                filename: __import__("hashlib").sha256(content.encode()).hexdigest()
                for filename, content in contents.items()
            },
            "manifest_excludes_itself": True,
        }
        (project / "world-seed-manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return project

    def test_catalog_verifies_manifest_hashes_without_modifying_project(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "projects"
            root.mkdir()
            project = self.make_project(root)
            before = {p.name: p.read_bytes() for p in project.iterdir()}
            catalog = LIBRARY.build_catalog([root])
            record = catalog["projects"][0]
            self.assertEqual(record["status"], "generated-files-match")
            self.assertEqual(record["verification"], "generated-files-match-manifest")
            self.assertEqual(catalog["recovery_claim"], "none; catalog status is not proof of backup or successful restoration")
            self.assertEqual(before, {p.name: p.read_bytes() for p in project.iterdir()})

    def test_catalog_accepts_schema_two_manifest_with_validation_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = self.make_project(root)
            manifest_path = project / "world-seed-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["schema_version"] = 2
            manifest["template_version"] = "1.2.0"
            manifest["validation_results"] = {
                "status": "passed",
                "checks": [{"id": "required_file_inventory", "status": "passed", "detail": "fixture"}],
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            record = LIBRARY.build_catalog([root])["projects"][0]
            self.assertEqual(record["status"], "generated-files-match")
            self.assertEqual(record["verification"], "generated-files-match-manifest")

    def test_modified_generated_file_is_reported_as_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = self.make_project(root)
            (project / "README.md").write_text("# Changed\n", encoding="utf-8")
            record = LIBRARY.build_catalog([root])["projects"][0]
            self.assertEqual(record["status"], "generated-files-drift")
            self.assertIn("README.md", record["changed_files"])

    def test_missing_generated_file_is_not_called_recoverable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = self.make_project(root)
            (project / "MISSION.md").unlink()
            record = LIBRARY.build_catalog([root])["projects"][0]
            self.assertEqual(record["status"], "missing-generated-files")
            self.assertIn("MISSION.md", record["missing_files"])

    def test_legacy_manifest_without_hashes_is_cataloged_but_unverified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = self.make_project(root)
            manifest_path = project / "world-seed-manifest.json"
            manifest = json.loads(manifest_path.read_text())
            del manifest["generated_file_sha256"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            record = LIBRARY.build_catalog([root])["projects"][0]
            self.assertEqual(record["status"], "cataloged-legacy-unverified")

    def test_invalid_path_inventory_and_symlinked_generated_file_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = self.make_project(root)
            manifest_path = project / "world-seed-manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["generated_files"] = ["../outside.txt"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(LIBRARY.build_catalog([root])["projects"][0]["status"], "invalid-manifest")

            manifest["generated_files"] = ["README.md", "MISSION.md"]
            manifest["generated_file_sha256"] = {
                filename: "0" * 64 for filename in manifest["generated_files"]
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (project / "README.md").unlink()
            outside = root / "outside.txt"
            outside.write_text("not project content", encoding="utf-8")
            try:
                (project / "README.md").symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on this platform")
            self.assertEqual(LIBRARY.build_catalog([root])["projects"][0]["status"], "unsafe-project-files")

    def test_unmanaged_directories_are_listed_without_scanning_contents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            unmanaged = root / "other-project"
            unmanaged.mkdir()
            (unmanaged / "private-data.txt").write_text("must not be read", encoding="utf-8")
            record = LIBRARY.build_catalog([root])["projects"][0]
            self.assertEqual(record["status"], "unmanaged-directory")
            self.assertNotIn("private-data.txt", json.dumps(record))
            self.assertNotIn("must not be read", json.dumps(record))

    def test_symlinked_child_directories_are_skipped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            external = root / "external"
            external.mkdir()
            self.make_project(external, "private-project")
            scan_root = root / "scan"
            scan_root.mkdir()
            try:
                (scan_root / "linked-project").symlink_to(external / "private-project", target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on this platform")
            self.assertEqual(LIBRARY.build_catalog([scan_root])["project_count"], 0)

    def test_catalog_report_is_owner_only_and_atomically_replaceable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "catalog.json"
            LIBRARY.write_private_json(output, {"schema_version": 1})
            self.assertEqual(json.loads(output.read_text())["schema_version"], 1)
            if os.name == "posix":
                self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            LIBRARY.write_private_json(output, {"schema_version": 2})
            self.assertEqual(json.loads(output.read_text())["schema_version"], 2)

    def test_symlink_output_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.json"
            target.write_text("preserve", encoding="utf-8")
            link = root / "link.json"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on this platform")
            with self.assertRaises(ValueError):
                LIBRARY.write_private_json(link, {"schema_version": 1})
            self.assertEqual(target.read_text(encoding="utf-8"), "preserve")


if __name__ == "__main__":
    unittest.main()
