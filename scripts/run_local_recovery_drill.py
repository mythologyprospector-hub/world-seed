#!/usr/bin/env python3
"""Run a network-free, disposable Git source-recovery drill.

This proves only that a local Git bundle can restore a known checkpoint into a
fresh clone and that a damaged working tree can be reset to that checkpoint.
It does not test GitHub metadata, credentials, settings, or whole-account recovery.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def run(command: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, check=False, timeout=30
    )
    if result.returncode:
        detail = (result.stdout + "\n" + result.stderr).strip()[-2000:]
        raise RuntimeError(f"command failed ({result.returncode}): {command[0]} {detail}")
    return result.stdout.strip()


def drill() -> dict:
    with tempfile.TemporaryDirectory(prefix="world-seed-recovery-drill-") as tmp:
        root = Path(tmp)
        source = root / "fixture-source"
        source.mkdir()
        run(["git", "init", "-q", str(source)])
        run(["git", "config", "user.name", "World Seed Recovery Drill"], cwd=source)
        run(["git", "config", "user.email", "recovery-drill@example.invalid"], cwd=source)
        expected = source / "CANARY.txt"
        expected.write_text("checkpoint-content-v1\n", encoding="utf-8")
        run(["git", "add", "CANARY.txt"], cwd=source)
        run(["git", "commit", "-qm", "Create known-good recovery checkpoint"], cwd=source)
        checkpoint = run(["git", "rev-parse", "HEAD"], cwd=source)
        bundle = root / "fixture.bundle"
        run(["git", "bundle", "create", str(bundle), "--all"], cwd=source)
        run(["git", "bundle", "verify", str(bundle)], cwd=source)

        restored = root / "restored-from-bundle"
        run(["git", "clone", "-q", str(bundle), str(restored)])
        restored_head = run(["git", "rev-parse", "HEAD"], cwd=restored)
        bundle_restore_passed = restored_head == checkpoint

        canary = restored / "CANARY.txt"
        canary.write_text("deliberately-damaged-content\n", encoding="utf-8")
        damaged = canary.read_text(encoding="utf-8") != "checkpoint-content-v1\n"
        run(["git", "restore", "--source", checkpoint, "--worktree", "--", "CANARY.txt"], cwd=restored)
        recovered_content = canary.read_text(encoding="utf-8")
        working_tree_clean = run(["git", "status", "--porcelain"], cwd=restored) == ""
        file_restore_passed = recovered_content == "checkpoint-content-v1\n" and working_tree_clean

        return {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": "passed" if bundle_restore_passed and damaged and file_restore_passed else "failed",
            "scope": "temporary local Git fixture only; no network or real project data",
            "checkpoint_commit": checkpoint,
            "bundle_integrity": "passed",
            "fresh_clone_matches_checkpoint": bundle_restore_passed,
            "controlled_damage_observed": damaged,
            "working_tree_restore": "passed" if file_restore_passed else "failed",
            "restored_working_tree_clean": working_tree_clean,
            "limitations": [
                "Does not prove all intended repositories or refs were captured.",
                "Does not cover GitHub issues, pull requests, comments, Actions artifacts, releases, or settings.",
                "Does not test project-specific build/tests or whole-account reconstruction.",
                "Uses a synthetic temporary repository; production recovery still requires a drill against a real disposable project and independently stored backup.",
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON report path; parent must already exist.")
    args = parser.parse_args()
    try:
        report = drill()
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            target = args.output.expanduser()
            if not target.parent.is_dir():
                parser.error("output parent directory must already exist")
            if target.exists() or target.is_symlink():
                parser.error("output already exists; refusing to overwrite")
            old_umask = os.umask(0o077)
            try:
                target.write_text(rendered, encoding="utf-8")
                target.chmod(0o600)
            finally:
                os.umask(old_umask)
        print(rendered, end="")
        return 0 if report["overall_status"] == "passed" else 1
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": "failed",
            "error": type(exc).__name__,
            "note": "Drill failed; no recovery success is claimed.",
        }, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
