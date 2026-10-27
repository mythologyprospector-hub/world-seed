#!/usr/bin/env python3
"""Collect an allowlisted, local-only machine readiness report.

The collector prints JSON or writes to an explicitly selected local file. It
never uploads data, reads credential files, inspects environment-variable
values, or executes authentication commands.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import platform
import re
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

COMMAND_TIMEOUT_SECONDS = 3
MAX_COMMAND_OUTPUT = 4096


def command_version(command: list[str]) -> dict[str, Any]:
    """Return availability and one bounded version line."""
    executable = shutil.which(command[0])
    if not executable:
        return {"available": False}
    executable = str(Path(executable).resolve())
    try:
        result = subprocess.run(
            [executable, *command[1:]],
            check=False,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"available": True, "version_check": "failed"}
    output = (result.stdout or result.stderr)[:MAX_COMMAND_OUTPUT].splitlines()
    version = output[0].strip()[:160] if output else ""
    return {
        "available": True,
        "executable": executable,
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
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout[:MAX_COMMAND_OUTPUT].strip() if result.returncode == 0 else ""


def git_query(root: Path, args: list[str]) -> dict[str, Any]:
    """Return success separately from a possibly empty, minimal Git response."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], check=False, capture_output=True,
            text=True, timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"verified": False}
    if result.returncode != 0:
        return {"verified": False}
    output = result.stdout or ""
    return {
        "verified": True,
        "truncated": len(output) > MAX_COMMAND_OUTPUT,
        "value": output[:MAX_COMMAND_OUTPUT].strip(),
    }


def query(command: list[str]) -> dict[str, Any]:
    """Run a bounded read-only local query; never expose its raw failure output."""
    executable = shutil.which(command[0])
    if not executable:
        return {"available": False}
    try:
        result = subprocess.run(
            [executable, *command[1:]], check=False, capture_output=True,
            text=True, timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"available": True, "verified": False}
    if result.returncode:
        return {"available": True, "verified": False}
    output = result.stdout or ""
    return {
        "available": True,
        "verified": True,
        "truncated": len(output) > MAX_COMMAND_OUTPUT,
        "value": output[:MAX_COMMAND_OUTPUT].strip(),
    }


def process_status(command: list[str]) -> dict[str, Any]:
    """Check an exact process query without returning its output or errors."""
    executable = shutil.which(command[0])
    if not executable:
        return {"available": False, "running": None, "verified": False}
    try:
        result = subprocess.run(
            [executable, *command[1:]], check=False, capture_output=True,
            text=True, timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"available": True, "running": None, "verified": False}
    if result.returncode == 0 and (result.stdout or "").strip():
        return {"available": True, "running": True, "verified": True}
    if result.returncode == 1:
        return {"available": True, "running": False, "verified": True}
    return {"available": True, "running": None, "verified": False}


def python_facts() -> dict[str, Any]:
    executable = str(Path(sys.executable).resolve())
    prefix = Path(sys.prefix).resolve()
    base_prefix = Path(sys.base_prefix).resolve()
    in_venv = prefix != base_prefix
    interpreter_path = Path(sys.executable).absolute()
    root_query = git_query(Path.cwd(), ["rev-parse", "--show-toplevel"])
    checkout_root = Path(root_query["value"]).resolve() if root_query["verified"] and root_query["value"] else None
    project_venv = (
        in_venv
        and checkout_root is not None
        and (checkout_root / ".venv").resolve() == prefix
        and interpreter_path.is_relative_to(prefix)
    )
    return {
        "executable": executable,
        "version": platform.python_version(),
        "environment": "project_virtual_environment" if project_venv else ("virtual_environment" if in_venv else "system_or_base_python"),
        "environment_verified": project_venv or not in_venv,
    }


def gnome_terminal_facts() -> dict[str, Any]:
    terminal = shutil.which("gnome-terminal")
    server = shutil.which("gnome-terminal-server")
    process = process_status(["pgrep", "-x", "gnome-terminal-server"])
    result: dict[str, Any] = {
        "gnome_terminal": {"available": bool(terminal), "path": terminal},
        "gnome_terminal_server_executable": {"available": bool(server), "path": server},
        "gnome_terminal_server_process": {
            "available": process.get("available", False),
            "running": process.get("running"),
            "verified": process.get("verified", False),
        },
        "settings": {"available": False, "verified": False},
    }
    if not terminal:
        return result
    profiles = query(["gsettings", "get", "org.gnome.Terminal.ProfilesList", "list"])
    default = query(["gsettings", "get", "org.gnome.Terminal.ProfilesList", "default"])
    if not profiles.get("verified") or profiles.get("truncated") or not default.get("verified") or default.get("truncated"):
        result["settings"].update({
            "available": profiles.get("available", False) or default.get("available", False),
            "truncated": bool(profiles.get("truncated") or default.get("truncated")),
            "complete": False,
        })
        return result
    # `gsettings get ... list` prints a GVariant array of quoted UUID strings.
    try:
        uuids = ast.literal_eval(profiles["value"])
        default_uuid = ast.literal_eval(default["value"])
    except (ValueError, SyntaxError, TypeError):
        result["settings"]["complete"] = False
        return result
    uuid_pattern = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z")
    if (not isinstance(uuids, list) or not uuids or
            any(not isinstance(uuid, str) or not uuid_pattern.fullmatch(uuid) for uuid in uuids) or
            not isinstance(default_uuid, str) or not uuid_pattern.fullmatch(default_uuid) or
            default_uuid not in uuids):
        result["settings"]["complete"] = False
        return result
    profile_facts = []
    complete = len(uuids) <= 32
    truncated = False
    for uuid in uuids[:32]:
        # GSettings accepts schema:path as one schema identifier; the path is
        # relocatable for each profile and ends in the profile UUID component.
        schema = f"org.gnome.Terminal.Legacy.Profile:/org/gnome/terminal/legacy/profiles:/:{uuid}/"
        name = query(["gsettings", "get", schema, "visible-name"])
        enabled = query(["gsettings", "get", schema, "use-custom-command"])
        truncated = truncated or bool(name.get("truncated") or enabled.get("truncated"))
        name_value = _variant_string(name.get("value")) if name.get("verified") and not name.get("truncated") else None
        enabled_value = _variant_bool(enabled.get("value")) if enabled.get("verified") and not enabled.get("truncated") else None
        item: dict[str, Any] = {"uuid": uuid, "name": name_value}
        item["custom_command_enabled"] = enabled_value
        complete = complete and name_value is not None and enabled_value is not None
        if item["custom_command_enabled"] is True:
            custom = query(["gsettings", "get", schema, "custom-command"])
            truncated = truncated or bool(custom.get("truncated"))
            custom_value = _variant_string(custom.get("value")) if custom.get("verified") and not custom.get("truncated") else None
            item["custom_command"] = custom_value
            complete = complete and custom_value is not None
        profile_facts.append(item)
    result["settings"] = {
        "available": True,
        "verified": complete,
        "complete": complete,
        "truncated": truncated,
        "limit_reached": len(uuids) > 32,
        "default_profile_uuid": default_uuid,
        "profiles": profile_facts,
    }
    return result


def _variant_string(value: str | None) -> str | None:
    """Decode the simple quoted string form returned by gsettings."""
    if not value or len(value) > MAX_COMMAND_OUTPUT:
        return None
    try:
        decoded = ast.literal_eval(value)
    except (ValueError, SyntaxError, TypeError):
        return None
    return decoded if isinstance(decoded, str) else None


def _variant_bool(value: str | None) -> bool | None:
    if value == "true":
        return True
    if value == "false":
        return False
    return None


def current_checkout_facts() -> dict[str, Any]:
    """Return minimal status for the checkout containing the current directory."""
    root_query = git_query(Path.cwd(), ["rev-parse", "--show-toplevel"])
    root_value = root_query.get("value")
    if not root_query.get("verified") or not root_value:
        return {"verified": False}
    root = Path(root_value)
    branch_query = git_query(root, ["branch", "--show-current"])
    branch = branch_query.get("value")
    if not branch_query.get("verified") or not branch:
        return {"verified": False, "root": str(root)}
    status = git_query(root, ["status", "--porcelain", "--untracked-files=all"])
    if not status.get("verified"):
        return {"verified": False, "root": str(root), "branch": branch}
    return {
        "verified": True,
        "root": str(root),
        "branch": branch,
        "state": "dirty" if status["value"] else "clean",
    }


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
        "runtime": {
            "uv": command_version(["uv", "--version"]),
            "python": python_facts(),
        },
        "gnome_terminal": gnome_terminal_facts(),
        "current_checkout": current_checkout_facts(),
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
