#!/usr/bin/env python3
"""Collect a private, read-only inventory of repositories visible to a GitHub token.

The report may contain private repository names. Write it only to an approved,
access-controlled location; never commit it to a public seed repository.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from private_report import write_private_json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
PAGE_SIZE = 100
MAX_PAGES = 1000


def api_get(path: str, token: str):
    """GET one GitHub API endpoint without printing credentials or response bodies."""
    request = Request(
        API_ROOT + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "world-seed-read-only-auditor",
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def collect_inventory(token: str, owner_filter: str | None = None) -> dict:
    """Return visible repository metadata, explicitly not a completeness claim."""
    identity = api_get("/user", token)
    repositories = []
    for page in range(1, MAX_PAGES + 1):
        query = f"/user/repos?affiliation=owner%2Ccollaborator%2Corganization_member&per_page={PAGE_SIZE}&page={page}&sort=full_name&direction=asc"
        batch = api_get(query, token)
        if not isinstance(batch, list):
            raise ValueError("GitHub repository endpoint returned an unexpected response shape")
        for item in batch:
            repository_owner = (item.get("owner") or {}).get("login", "")
            if owner_filter and repository_owner.casefold() != owner_filter.casefold():
                continue
            repositories.append({
                "full_name": item.get("full_name"),
                "owner": repository_owner,
                "visibility": item.get("visibility") or ("private" if item.get("private") else "public"),
                "default_branch": item.get("default_branch"),
                "archived": bool(item.get("archived", False)),
                "fork": bool(item.get("fork", False)),
                "updated_at": item.get("updated_at"),
                "html_url": item.get("html_url"),
            })
        if len(batch) < PAGE_SIZE:
            break
    else:
        raise RuntimeError(f"Repository pagination exceeded safety limit ({MAX_PAGES} pages)")

    repositories.sort(key=lambda item: (item["full_name"] or "").casefold())
    return {
        "schema_version": 1,
        "audit_type": "accessible_repository_inventory",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "authenticated_identity": identity.get("login"),
        "requested_owner_filter": owner_filter,
        "source": "GitHub REST API GET /user/repos with owner, collaborator, and organization-member affiliations",
        "repository_count": len(repositories),
        "visibility_counts": {
            visibility: sum(1 for item in repositories if item["visibility"] == visibility)
            for visibility in ("public", "private", "internal")
        },
        "coverage": {
            "status": "partial-unverified",
            "meaning": "Only repositories visible to this token and affiliation query are included.",
            "account_completeness_verified": False,
            "repository_contents_inspected": False,
            "cross_repository_contracts_checked": False,
            "private_repositories_may_be_missing": True,
            "note": "Compare against an authoritative expected inventory and verify token/organization access before treating this list as complete.",
        },
        "repositories": repositories,
    }


def main(argv: list[str] | None = None) -> int:
    """Collect inventory to an explicitly chosen local path; perform no writes to GitHub."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", help="Keep only repositories owned by this user or organization login")
    parser.add_argument("--output", required=True, type=Path, help="Local report path; choose access-controlled storage")
    args = parser.parse_args(argv)
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("BLOCKED: set GH_TOKEN or GITHUB_TOKEN in the environment; do not pass tokens as command-line arguments.", file=sys.stderr)
        return 2
    output_path = args.output.expanduser().resolve()
    seed_root = Path(__file__).resolve().parents[1]
    if output_path == seed_root or seed_root in output_path.parents:
        print("BLOCKED: report output must be outside the world-seed repository to protect private repository metadata.", file=sys.stderr)
        return 2
    try:
        report = collect_inventory(token, args.owner)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        print(f"BLOCKED: inventory collection failed ({type(exc).__name__}); no completeness claim is possible.", file=sys.stderr)
        return 2
    print(f"Inventory written to the chosen local path; visible repositories: {report['repository_count']}. Coverage: partial-unverified.")
    print("The report can contain private repository names. Keep it outside public repositories and do not commit it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
