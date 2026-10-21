"""Synthetic end-to-end Intake Dock package-to-repository drill; never uses GitHub."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PACKAGER = load_module("package_intake_dock_handoff", "scripts/package_intake_dock_handoff.py")
TRANSFER = load_module("transfer_intake_dock_handoff", "scripts/transfer_intake_dock_handoff.py")


def git(args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


class LocalPrivateRepo:
    """Implements the transfer interface using a persistent local bare Git repository."""

    def __init__(self, root):
        self.root = Path(root)
        self.remote = self.root / "fake-private-dock.git"
        self.calls = []
        self.login = "owner"
        self._initialize_remote()

    def _initialize_remote(self):
        git(["init", "--bare", str(self.remote)])
        seed = self.root / "seed-checkout"
        git(["init", "-b", "main", str(seed)])
        git(["-C", str(seed), "config", "user.name", "Synthetic Drill"])
        git(["-C", str(seed), "config", "user.email", "synthetic@example.invalid"])
        (seed / "README.md").write_text("Synthetic private Intake Dock\n", encoding="utf-8")
        git(["-C", str(seed), "add", "README.md"])
        git(["-C", str(seed), "commit", "-m", "Initialize synthetic Dock"])
        git(["-C", str(seed), "remote", "add", "origin", str(self.remote)])
        git(["-C", str(seed), "push", "--set-upstream", "origin", "main"])

    def authenticated_login(self):
        self.calls.append("identity")
        return self.login

    def get_repository(self, target):
        self.calls.append(("metadata", target))
        return {"full_name": target, "private": True, "default_branch": "main"}

    def clone(self, target, destination):
        self.calls.append(("clone", target))
        git(["clone", str(self.remote), str(destination)])

    def git(self, repo, args, allow_failure=False):
        self.calls.append(("git", tuple(args)))
        result = subprocess.run(["git", "-C", str(repo), *args], check=False,
                                capture_output=True, text=True)
        if result.returncode and not allow_failure:
            raise RuntimeError("local synthetic git command failed")
        return result


class SyntheticHandoffDrillTests(unittest.TestCase):
    def test_package_transfer_receipt_and_idempotent_rerun(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "approved-synthetic-notes.txt"
            original = b"SYNTHETIC ONLY: no private user data.\n"
            source.write_bytes(original)
            package_path = root / "synthetic-handoff.zip"

            packed = PACKAGER.build_package(
                [source], package_path, "episteme", "owner/episteme"
            )
            self.assertEqual(packed["transfer_status"], "not_uploaded")
            self.assertEqual(source.read_bytes(), original)

            client = LocalPrivateRepo(root)
            transferred = TRANSFER.transfer(
                package_path, "owner/episteme", apply=True,
                confirmed_target="owner/episteme", client=client,
            )
            self.assertEqual(transferred["status"], "transferred-and-committed")
            self.assertEqual(source.read_bytes(), original)

            verification = root / "verification-checkout"
            git(["clone", str(client.remote), str(verification)])
            incoming = verification / "projects/episteme/incoming/approved-synthetic-notes.txt"
            self.assertEqual(incoming.read_bytes(), original)
            receipt_path = verification / transferred["receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["target_repository"], "owner/episteme")
            self.assertEqual(receipt["lane"], "episteme")
            self.assertEqual(receipt["transfer_status"], "received")
            self.assertEqual(receipt["source_package_sha256"], packed["sha256"])
            with zipfile.ZipFile(package_path) as archive:
                manifest = json.loads(archive.read("manifest.json"))
            self.assertEqual(receipt["files"][0]["sha256"], manifest["files"][0]["sha256"])

            again = TRANSFER.transfer(
                package_path, "owner/episteme", apply=True,
                confirmed_target="owner/episteme", client=client,
            )
            self.assertEqual(again["status"], "already-present")
            self.assertEqual(source.read_bytes(), original)

    def test_wrong_owner_is_refused_before_repository_lookup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "notes.txt"
            source.write_text("synthetic", encoding="utf-8")
            package_path = root / "handoff.zip"
            PACKAGER.build_package([source], package_path, "episteme", "owner/episteme")
            client = LocalPrivateRepo(root)
            client.login = "unrelated-account"
            with self.assertRaisesRegex(ValueError, "authenticated personal GitHub"):
                TRANSFER.transfer(package_path, "owner/episteme", apply=True,
                                  confirmed_target="owner/episteme", client=client)
            self.assertEqual([call for call in client.calls if isinstance(call, tuple) and call[0] == "metadata"], [])


if __name__ == "__main__":
    unittest.main()
