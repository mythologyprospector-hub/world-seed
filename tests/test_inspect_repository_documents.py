"""Fixture tests for bounded repository governance-document inspection."""
import base64
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "inspect_repository_documents.py"
SPEC = importlib.util.spec_from_file_location("inspect_repository_documents", MODULE_PATH)
assert SPEC and SPEC.loader
INSPECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSPECTOR)


class RepositoryDocumentInspectionTests(unittest.TestCase):
    def test_reports_headings_without_retaining_document_body(self):
        source = "# Project\n\n## Purpose\nPrivate body text.\n"
        response = {
            "type": "file",
            "size": len(source.encode("utf-8")),
            "encoding": "base64",
            "content": base64.b64encode(source.encode("utf-8")).decode("ascii"),
            "sha": "fixture-sha",
        }

        def fake_get(path, token):
            if path == "/repos/example/project":
                return {"full_name": "example/project", "default_branch": "main"}
            if path == "/repos/example/project/contents/README.md?ref=main":
                return response
            raise AssertionError(f"Unexpected API path: {path}")

        with patch.object(INSPECTOR, "api_get", side_effect=fake_get):
            report = INSPECTOR.inspect_documents("example/project", "fixture-token", ["README.md"])

        self.assertEqual(report["inspected_count"], 1)
        self.assertEqual(report["documents"][0]["headings"], [
            {"level": 1, "text": "Project"},
            {"level": 2, "text": "Purpose"},
        ])
        self.assertFalse(report["documents"][0]["body_retained"])
        self.assertNotIn("Private body text", str(report))

    def test_oversized_document_is_skipped(self):
        response = {"type": "file", "size": INSPECTOR.MAX_DOCUMENT_BYTES + 1, "sha": "large-sha"}

        def fake_get(path, token):
            if path == "/repos/example/project":
                return {"full_name": "example/project", "default_branch": "main"}
            if path == "/repos/example/project/contents/README.md?ref=main":
                return response
            raise AssertionError(f"Unexpected API path: {path}")

        with patch.object(INSPECTOR, "api_get", side_effect=fake_get):
            report = INSPECTOR.inspect_documents("example/project", "fixture-token", ["README.md"])

        self.assertEqual(report["documents"][0]["status"], "skipped-size-limit")
        self.assertFalse(report["coverage"]["semantic_quality_verified"])


if __name__ == "__main__":
    unittest.main()
