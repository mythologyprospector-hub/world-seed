#!/usr/bin/env python3
"""Collect an allowlisted, local-only machine readiness report.

The collector prints JSON or writes to an explicitly selected local file. It
never uploads data, reads credential files, inspects environment-variable
values, or executes authentication commands.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOL_CHECKS: dict[str, list[str]] = {
    "git": ["git", "--version"],
    "gh": ["gh", "--version"],
    "python3": [sys.executable, "--version"],
    "codex": ["codex", "--version"],
}


def command_version(command: list[str]) -> dict[str, Any]:
    """Return availability and one bounded version line."""
    executable = shutil.which(command[0])
    if not executable:
        return {"available": False}
    try:
        result = subprocess.run(
            [executable, *command[1:]],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"available": True, "version_check": "failed"}
    output = (result.stdout or result.stderr).splitlines()
    version = output[0].strip()[:160] if output else ""
    return {
        "available": True,
        "version": version,
        "version_check": "ok" if result.returncode == 0 else "failed",
    }


def git_value(root: Path, args: list[str]) -> str:
    """Run a bounded, read-only Git query."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def discover_repositories(root: Path) -> list[dict[str, Any]]:
    """Inspect immediate child Git checkouts without exposing remotes or file names."""
    repositories: list[dict[str, Any]] = []
    if not root.is_dir():
        return repositories
    for candidate in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not candidate.is_dir() or not (candidate / ".git").exists():
            continue
        branch = git_value(candidate, ["rev-parse", "--abbrev-ref", "HEAD"])
        tracked_changes = git_value(
            candidate, ["status", "--porcelain", "--untracked-files=no"]
        )
        repositories.append({
            "name": candidate.name,
            "path": str(candidate),
            "branch": branch or None,
            "tracked_changes_present": bool(tracked_changes),
        })
    return repositories


def collect(
    include_repositories: bool = False, projects_root: Path | None = None
) -> dict[str, Any]:
    """Build an allowlisted report without reading secret values or credential files."""
    report: dict[str, Any] = {
        "schema_version": 1,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine_architecture": platform.machine(),
            "python_version": platform.python_version(),
        },
        "tools": {name: command_version(command) for name, command in TOOL_CHECKS.items()},
        "privacy": {
            "mode": "local_report_only",
            "uploaded": False,
            "credential_files_read": False,
            "environment_variable_values_read": False,
            "remote_urls_collected": False,
        },
    }
    if include_repositories:
        root = projects_root or (Path.home() / "projects")
        report["repositories"] = discover_repositories(root)
        report["repository_scan_root"] = str(root)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-repositories",
        action="store_true",
        help="Include names and local paths of Git checkouts under the projects root.",
    )
    parser.add_argument(
        "--projects-root",
        type=Path,
        help="Clone directory; used only with --include-repositories (default: ~/projects).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON to this path instead of stdout. Existing files are never overwritten.",
    )
    args = parser.parse_args()

    if args.output and args.output.exists():
        parser.error(f"refusing to overwrite existing output file: {args.output}")

    report = collect(args.include_repositories, args.projects_root)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        try:
            # The report may contain private repository names and local paths.
            # Enforce owner-only permissions regardless of the caller's umask,
            # and O_EXCL closes the race between the earlier check and creation.
            descriptor = os.open(
                args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
            )
        except FileExistsError:
            parser.error(f"refusing to overwrite existing output file: {args.output}")
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(rendered)
        print(f"Wrote local report: {args.output}")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
