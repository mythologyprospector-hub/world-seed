#!/usr/bin/env python3
"""Read-only audit of a recovery-state JSON record against a local Git checkout.

The state input is never modified. The report is written to a new private file.
This command performs no network access and does not verify tests or hosted CI.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "recovery-project-state.schema.json"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def safe_slug(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value) or value in {".", ".."}:
        raise ValueError("project must be a 1-80 character repository-style slug")
    return value


def run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=10,
    )
    if completed.returncode:
        raise ValueError(f"git {' '.join(args[:2])} failed (exit {completed.returncode})")
    return completed.stdout.strip()


def redact_url(value: str) -> str:
    """Remove URL userinfo before any URL is written to the report."""
    try:
        parsed = urlsplit(value)
        if parsed.scheme and parsed.netloc:
            host = parsed.hostname or ""
            if parsed.port:
                host = f"{host}:{parsed.port}"
            return urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))
    except ValueError:
        pass
    return "[unparseable-or-non-url-origin]"


def normalize_url(value: str) -> str:
    safe = redact_url(value.strip())
    parsed = urlsplit(safe)
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", "")).rstrip("/")


def load_state(path: Path, project: str) -> dict[str, Any]:
    try:
        value = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read state JSON ({type(exc).__name__})") from exc
    if not isinstance(value, dict):
        raise ValueError("state JSON must be an object")
    try:
        import jsonschema
    except ImportError as exc:
        raise ValueError("state validation requires requirements-dev.txt in the project virtual environment") from exc
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        errors = sorted(validator.iter_errors(value), key=lambda err: list(err.absolute_path))
    except (OSError, UnicodeError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
        raise ValueError(f"cannot load or use state schema ({type(exc).__name__})") from exc
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "<root>"
        raise ValueError(f"state failed schema validation at {location}: {first.message}")
    if value["project"]["name"] != project:
        raise ValueError("state project.name must exactly match --project")
    return value


def inspect_git(repo: Path) -> dict[str, Any]:
    if not repo.exists() or not repo.is_dir():
        raise ValueError("repository path does not exist or is not a directory")
    root = Path(run_git(repo, "rev-parse", "--show-toplevel")).resolve()
    head = run_git(root, "rev-parse", "HEAD")
    branch_result = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "--quiet", "--short", "HEAD"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=10,
    )
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
    origin_result = subprocess.run(
        ["git", "-C", str(root), "remote", "get-url", "origin"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=10,
    )
    origin = redact_url(origin_result.stdout.strip()) if origin_result.returncode == 0 else None
    status = run_git(root, "status", "--porcelain=v1", "--untracked-files=normal")
    return {
        "git_root_local_path": str(root),
        "origin_url_redacted": origin,
        "head_commit": head,
        "branch": branch,
        "detached_head": branch is None,
        "dirty": bool(status),
        "origin_available": origin is not None,
    }


def compare(state: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    recorded_url = state["project"]["repository_url"]
    observed_url = observed["origin_url_redacted"]
    recorded_commit = state["record"]["describes_commit"]
    checks: dict[str, dict[str, str]] = {}

    if not observed_url:
        checks["repository_identity"] = {"status": "unknown", "detail": "No origin remote is configured."}
    elif normalize_url(recorded_url) == normalize_url(observed_url):
        checks["repository_identity"] = {"status": "match", "detail": "Recorded URL matches the redacted local origin."}
    else:
        checks["repository_identity"] = {"status": "mismatch", "detail": "Recorded repository URL differs from local origin."}

    if recorded_commit == "unknown":
        checks["commit"] = {"status": "unknown", "detail": "State does not record a commit SHA."}
    elif recorded_commit == observed["head_commit"]:
        checks["commit"] = {"status": "match", "detail": "Recorded commit matches local HEAD."}
    else:
        checks["commit"] = {"status": "mismatch", "detail": "Recorded commit differs from local HEAD."}

    checks["working_tree"] = {
        "status": "mismatch" if observed["dirty"] else "clean",
        "detail": "Working tree has tracked or untracked changes." if observed["dirty"] else "Working tree reports no tracked or untracked changes.",
    }

    problems = [
        key for key in ("repository_identity", "commit")
        if checks[key]["status"] != "match"
    ]
    if observed["dirty"]:
        problems.append("working_tree")
    if problems:
        proposed_freshness = "possibly_stale" if any(
            checks[key]["status"] == "mismatch" for key in problems
        ) or observed["dirty"] else "unknown"
    else:
        proposed_freshness = "current"

    return {
        "checks": checks,
        "proposed_freshness": proposed_freshness,
        "freshness_reason": (
            "Proposed current only because repository identity and commit match and the working tree is clean."
            if proposed_freshness == "current"
            else "Not current: at least one identity, commit, cleanliness, or evidence check is unresolved."
        ),
        "suggested_metadata_changes": [
            {
                "field": "record.freshness",
                "suggested_value": proposed_freshness,
                "reason": "Derived from local Git comparisons only; review before editing the source state record.",
            },
            {
                "field": "record.describes_commit",
                "suggested_value": observed["head_commit"],
                "reason": "Local HEAD observed; changing the record to this commit is a human-reviewed proposal, not an automatic update.",
            },
        ],
    }


def write_new_private(path: Path, payload: dict[str, Any]) -> None:
    path = path.expanduser()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ValueError("refusing to overwrite an existing report file") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="exact project slug from state.project.name")
    parser.add_argument("--state", required=True, type=Path, help="existing recovery-state JSON file")
    parser.add_argument("--repo", required=True, type=Path, help="local Git checkout to inspect")
    parser.add_argument("--output", required=True, type=Path, help="new audit report path; must not exist")
    args = parser.parse_args()
    try:
        project = safe_slug(args.project)
        state_path = args.state.expanduser().resolve()
        output_path = args.output.expanduser().resolve()
        if state_path == output_path:
            raise ValueError("report output must not be the state input path")
        state = load_state(state_path, project)
        observed = inspect_git(args.repo.expanduser())
        comparison = compare(state, observed)
        report = {
            "report_schema_version": 1,
            "created_at": utc_now(),
            "project": project,
            "state_record": {
                "repository_url": state["project"]["repository_url"],
                "describes_commit": state["record"]["describes_commit"],
                "freshness": state["record"]["freshness"],
                "input_unchanged_by_design": True,
            },
            "observed_repository": observed,
            "comparison": comparison,
            "limitations": [
                "This report is based on local JSON and Git metadata only.",
                "It does not verify tests, GitHub Actions, remote freshness, authorization, or human-authored claims.",
                "A proposed freshness value is advisory and does not modify the source state record.",
                "The origin URL is redacted for URL user information; inspect output before sharing.",
            ],
        }
        write_new_private(output_path, report)
        print(f"Recovery-state audit written: {output_path}")
        print(f"Repository identity: {comparison['checks']['repository_identity']['status']}")
        print(f"Commit comparison: {comparison['checks']['commit']['status']}")
        print(f"Working tree: {comparison['checks']['working_tree']['status']}")
        print(f"Proposed freshness: {comparison['proposed_freshness']}")
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"[recovery-state-audit] ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
