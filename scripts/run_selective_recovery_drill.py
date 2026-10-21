#!/usr/bin/env python3
"""Exercise the selective-recovery CLI end to end using disposable synthetic files only."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(*args: str) -> str:
    result = subprocess.run(
        [sys.executable, *args], capture_output=True, text=True, check=False, timeout=30
    )
    if result.returncode:
        raise RuntimeError((result.stdout + "\n" + result.stderr).strip()[-3000:])
    return result.stdout


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    cli = Path(__file__).with_name("selective_recovery.py").resolve()
    with tempfile.TemporaryDirectory(prefix="world-seed-selective-drill-") as temp:
        root = Path(temp)
        source = root / "fixture-source"
        source.mkdir()
        expected = {
            "README.md": b"# Disposable fixture\n",
            "sample.bin": bytes(range(256)) + b"\x00\xff",
        }
        for name, content in expected.items():
            (source / name).write_bytes(content)
        (source / "omitted.txt").write_text("must not be captured", encoding="utf-8")
        before = {p.name: sha256(p) for p in source.iterdir() if p.is_file()}
        payload = root / "private-payload"
        restored = root / "fresh-restore"

        capture_output = run(
            str(cli), "capture", "--source", str(source), "--output", str(payload),
            "--include", "README.md", "--include", "sample.bin",
        )
        manifest = json.loads((payload / "recovery-payload.json").read_text(encoding="utf-8"))
        if {entry["path"] for entry in manifest["files"]} != set(expected):
            raise RuntimeError("payload inventory does not match the explicit include list")
        if (payload / "omitted.txt").exists():
            raise RuntimeError("unselected file unexpectedly entered the payload")

        restore_output = run(
            str(cli), "restore", "--payload", str(payload), "--destination", str(restored)
        )
        for name, content in expected.items():
            target = restored / name
            if target.read_bytes() != content or sha256(target) != sha256(source / name):
                raise RuntimeError(f"independent restored-byte comparison failed: {name}")
        after = {p.name: sha256(p) for p in source.iterdir() if p.is_file()}
        if before != after:
            raise RuntimeError("source fixture changed during capture/restore")

        print("SELECTIVE_RECOVERY_CLI_DRILL=PASSED")
        print("scope=temporary synthetic files; no real projects or network")
        print("checks=explicit selection, binary bytes, payload inventory, independent SHA-256, source unchanged")
        print(capture_output.strip())
        print(restore_output.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
