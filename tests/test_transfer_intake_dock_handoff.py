"""Tests for fail-closed Intake Dock package validation and transfer gates."""
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("transfer_intake_dock_handoff", ROOT / "scripts" / "transfer_intake_dock_handoff.py")
assert SPEC and SPEC.loader
TRANSFER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRANSFER)


def make_package(root: Path, *, target="owner/episteme", lane="episteme", files=None):
    files = files or [("notes.txt", b"synthetic notes")]
    entries = []
    payload = {}
    import hashlib
    for name, data in files:
        relative = f"projects/{lane}/incoming/{name}"
        payload[relative] = data
        entries.append({"path": relative, "source_name": name, "size_bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(), "source_mtime_utc": "2026-01-01T00:00:00+00:00"})
    manifest = {"schema_version": 1, "package_type": "intake-dock-handoff", "target_repository": target,
                "lane": lane, "created_at_utc": "2026-01-01T00:00:00+00:00",
                "files": entries, "transfer_status": "not_uploaded", "source_files_modified": False}
    output = root / "handoff.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        for name, data in payload.items():
            archive.writestr(name, data)
    return output, manifest, payload


class FakeClient:
    def __init__(self):
        self.calls = []
        self.login = "owner"
    def authenticated_login(self):
        self.calls.append("identity")
        return self.login
    def get_repository(self, target):
        self.calls.append(("repository", target))
        return {"full_name": target, "private": True, "default_branch": "main"}
    def clone(self, target, destination):
        self.calls.append(("clone", target))
        destination.mkdir()
        import subprocess
        subprocess.run(["git", "init", "-b", "main", str(destination)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(destination), "config", "user.name", "test"], check=True)
        subprocess.run(["git", "-C", str(destination), "config", "user.email", "test@example.invalid"], check=True)
        remote = destination.parent / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(destination), "remote", "add", "origin", str(remote)], check=True)
        (destination / "README.md").write_text("existing repository content", encoding="utf-8")
        subprocess.run(["git", "-C", str(destination), "add", "README.md"], check=True)
        subprocess.run(["git", "-C", str(destination), "commit", "-m", "seed"], check=True, capture_output=True)
    def git(self, repo, args, allow_failure=False):
        self.calls.append(("git", tuple(args)))
        import subprocess
        return subprocess.run(["git", "-C", str(repo), *args], check=not allow_failure, capture_output=True, text=True)


class TransferPackageTests(unittest.TestCase):
    def test_default_is_local_plan_and_makes_no_remote_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            package, _, _ = make_package(Path(temp))
            client = FakeClient()
            result = TRANSFER.transfer(package, "owner/episteme", client=client)
            self.assertEqual(result["status"], "planned")
            self.assertFalse(result["remote_calls_made"])
            self.assertEqual(client.calls, [])

    def test_requires_exact_confirmation_before_remote_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            package, _, _ = make_package(Path(temp))
            client = FakeClient()
            with self.assertRaisesRegex(ValueError, "confirm-target"):
                TRANSFER.transfer(package, "owner/episteme", apply=True, client=client)
            self.assertEqual(client.calls, [])

    def test_rejects_package_for_different_target(self):
        with tempfile.TemporaryDirectory() as temp:
            package, _, _ = make_package(Path(temp))
            with self.assertRaisesRegex(ValueError, "does not match"):
                TRANSFER.transfer(package, "owner/other")

    def test_rejects_tampered_payload_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            package, manifest, payload = make_package(Path(temp))
            payload_path = next(iter(payload))
            with zipfile.ZipFile(package, "a") as archive:
                archive.writestr(payload_path, b"tampered")
            with self.assertRaisesRegex(ValueError, "duplicate ZIP entries"):
                TRANSFER.validate_package(package, "owner/episteme")


    def test_rejects_secret_material_even_if_package_manifest_hashes_match(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package, _, _ = make_package(root, files=[("notes.txt", ("ghp_" + "A" * 36).encode())])
            with self.assertRaisesRegex(ValueError, "GitHub token"):
                TRANSFER.validate_package(package, "owner/episteme")

    def test_refuses_unsafe_manifest_path(self):
        with tempfile.TemporaryDirectory() as temp:
            package, manifest, payload = make_package(Path(temp))
            manifest["files"][0]["path"] = "../notes.txt"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("manifest.json", json.dumps(manifest))
                archive.writestr("../notes.txt", b"synthetic notes")
            with self.assertRaisesRegex(ValueError, "unsafe destination path|does not match"):
                TRANSFER.validate_package(package, "owner/episteme")

    def test_refuses_public_repository_before_clone(self):
        with tempfile.TemporaryDirectory() as temp:
            package, _, _ = make_package(Path(temp))
            client = FakeClient()
            client.get_repository = lambda target: {"full_name": target, "private": False, "default_branch": "main"}
            with self.assertRaisesRegex(ValueError, "not private"):
                TRANSFER.transfer(package, "owner/episteme", apply=True,
                                  confirmed_target="owner/episteme", client=client)
            self.assertEqual(client.calls, ["identity"])

    def test_transfer_writes_lane_and_receipt_without_overwriting_existing_files(self):
        with tempfile.TemporaryDirectory() as temp:
            package, _, payload = make_package(Path(temp))
            client = FakeClient()
            result = TRANSFER.transfer(package, "owner/episteme", apply=True,
                                       confirmed_target="owner/episteme", client=client)
            self.assertEqual(result["status"], "transferred-and-committed")
            self.assertEqual(result["files"], 1)
            self.assertTrue(any(call[0] == "git" and call[1][0] == "push" for call in client.calls if isinstance(call, tuple)))
            self.assertEqual(len(payload), 1)

    def test_conflicting_existing_remote_path_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            package, _, _ = make_package(Path(temp))
            client = FakeClient()
            original_clone = client.clone
            def clone_with_conflict(target, destination):
                original_clone(target, destination)
                path = destination / "projects/episteme/incoming/notes.txt"
                path.parent.mkdir(parents=True)
                path.write_text("different", encoding="utf-8")
                import subprocess
                subprocess.run(["git", "-C", str(destination), "add", str(path)], check=True)
                subprocess.run(["git", "-C", str(destination), "commit", "-m", "conflict"], check=True, capture_output=True)
            client.clone = clone_with_conflict
            with self.assertRaisesRegex(ValueError, "refusing overwrite"):
                TRANSFER.transfer(package, "owner/episteme", apply=True,
                                  confirmed_target="owner/episteme", client=client)

    def test_existing_non_private_or_wrong_owner_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            package, _, _ = make_package(Path(temp))
            client = FakeClient()
            client.login = "someone-else"
            with self.assertRaisesRegex(ValueError, "authenticated personal GitHub"):
                TRANSFER.transfer(package, "owner/episteme", apply=True,
                                  confirmed_target="owner/episteme", client=client)
            self.assertEqual(client.calls, ["identity"])


if __name__ == "__main__":
    unittest.main()
