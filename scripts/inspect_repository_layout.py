#!/usr/bin/env python3
"""Inspect repository entry names and workflow presence without reading file contents."""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from private_report import write_private_json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"

def api_get(path: str, token: str):
    """Perform a GitHub API GET without printing credentials or response bodies."""
    request = Request(API_ROOT + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "world-seed-read-only-auditor",
    })
    with urlopen(request, timeout=20) as response:
        return json.load(response)

def inspect_layout(full_name: str, token: str) -> dict:
    """Return a cautious, metadata-only layout report for one repository."""
    encoded = quote(full_name, safe="/")
    metadata = api_get(f"/repos/{encoded}", token)
    branch = metadata.get("default_branch")
    if not branch:
        raise ValueError("repository default branch is unavailable")
    ref = quote(branch, safe="")
    root = api_get(f"/repos/{encoded}/contents?ref={ref}", token)
    if not isinstance(root, list):
        raise ValueError("repository root response was not a directory listing")
    names = sorted((str(item.get("name", "")) for item in root), key=str.casefold)
    upper = {name.upper() for name in names}
    workflows_status = "not-inspected"
    workflow_count = None
    if any(item.get("name") == ".github" and item.get("type") == "dir" for item in root):
        try:
            workflows = api_get(f"/repos/{encoded}/contents/.github/workflows?ref={ref}", token)
            if isinstance(workflows, list):
                workflow_count = sum(1 for item in workflows if item.get("type") == "file" and str(item.get("name", "")).lower().endswith((".yml", ".yaml")))
                workflows_status = "inspected"
            else:
                workflows_status = "blocked-unexpected-response"
        except HTTPError as exc:
            workflows_status = "directory-not-found" if exc.code == 404 else "blocked-http-error"
        except (URLError, TimeoutError, OSError):
            workflows_status = "blocked-network-error"
    return {
        "schema_version": 1,
        "audit_type": "repository_root_layout",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "repository": metadata.get("full_name", full_name),
        "visibility": metadata.get("visibility") or ("private" if metadata.get("private") else "public"),
        "default_branch": branch,
        "root_entry_names": names,
        "signals": {
            "readme_present": any(name.startswith("README.") for name in upper),
            "builder_instructions_present": "AGENTS.MD" in upper,
            "security_policy_present": "SECURITY.MD" in upper,
            "contribution_guide_present": any(name.startswith("CONTRIBUTING.") for name in upper),
            "license_candidate_present": any(name.startswith("LICENSE") for name in upper),
            "test_directory_present": bool({"TEST", "TESTS"} & upper),
            "workflow_directory_status": workflows_status,
            "workflow_file_count": workflow_count,
        },
        "interpretation": "These are review signals, not automatic defects. Applicability depends on repository purpose, risk, and documented exceptions.",
        "coverage": "Root and workflow entry names only. No file contents, branch protections, secrets, workflow execution history, or cross-repository contracts were inspected.",
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="Repository as owner/name")
    parser.add_argument("--output", required=True, type=Path, help="Access-controlled local report path")
    args = parser.parse_args(argv)
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("BLOCKED: set GH_TOKEN or GITHUB_TOKEN in the environment; do not pass tokens as arguments.", file=sys.stderr)
        return 2
    output = args.output.expanduser().resolve()
    seed_root = Path(__file__).resolve().parents[1]
    if output == seed_root or seed_root in output.parents:
        print("BLOCKED: write the report outside the public world-seed repository.", file=sys.stderr)
        return 2
    if "/" not in args.repo or any(not part for part in args.repo.split("/", 1)):
        print("BLOCKED: --repo must be owner/name.", file=sys.stderr)
        return 2
    try:
        report = inspect_layout(args.repo, token)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        print(f"BLOCKED: inspection failed ({type(exc).__name__}); no clean result is implied.", file=sys.stderr)
        return 2
    print(f"Layout report written to the chosen local path for {report['repository']}; content coverage remains limited.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
