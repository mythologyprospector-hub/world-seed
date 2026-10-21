#!/usr/bin/env python3
"""Run the project-tree recovery CLI against a temporary nested synthetic fixture."""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str) -> str:
    result = subprocess.run([sys.executable, *args], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError((result.stdout + "\n" + result.stderr)[-4000:])
    return result.stdout


def main() -> int:
    cli = Path(__file__).with_name("project_tree_recovery.py").resolve()
    with tempfile.TemporaryDirectory(prefix="world-seed-project-tree-drill-") as temporary:
        root = Path(temporary)
        source = root / "source"
        (source / "src" / "nested").mkdir(parents=True)
        (source / "empty" / "kept").mkdir(parents=True)
        (source / ".git").mkdir()
        expected = {
            "README.md": b"# synthetic tree\n",
            "src/nested/module.py": b"payload = b'\\x00\\xff'\n",
            "assets.bin": bytes(range(256)) + b"\x00\xff",
        }
        for name, data in expected.items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (source / ".git" / "must-not-copy").write_text("separate Git recovery", encoding="utf-8")
        (source / "omit.txt").write_text("explicitly excluded", encoding="utf-8")
        before = {name: sha(source / name) for name in expected}
        payload, restored = root / "private-payload", root / "restored"
        capture_output = run(str(cli), "capture", "--source", str(source), "--output", str(payload), "--exclude", "omit.txt")
        manifest = json.loads((payload / "project-tree-recovery.json").read_text(encoding="utf-8"))
        if {entry["path"] for entry in manifest["files"]} != set(expected):
            raise RuntimeError("manifest file inventory differs from expected fixture")
        if not any(entry["path"] == ".git" for entry in manifest["exclusions"]):
            raise RuntimeError("Git metadata exclusion was not recorded")
        if not any(entry["path"] == "omit.txt" for entry in manifest["exclusions"]):
            raise RuntimeError("explicit exclusion was not recorded")
        restore_output = run(str(cli), "restore", "--payload", str(payload), "--destination", str(restored))
        after = {name: sha(restored / name) for name in expected}
        if before != after:
            raise RuntimeError("independent SHA-256 comparison failed")
        if not (restored / "empty" / "kept").is_dir():
            raise RuntimeError("empty nested directory was not restored")
        if (restored / ".git").exists() or (restored / "omit.txt").exists():
            raise RuntimeError("excluded content appeared in restored tree")
        print("PROJECT_TREE_RECOVERY_CLI_DRILL=PASSED")
        print("scope=temporary synthetic fixture; no live project or network")
        print("checks=nested paths, binary bytes, empty directories, explicit exclusions, .git separation, independent SHA-256")
        print(capture_output.strip())
        print(restore_output.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
