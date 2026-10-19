#!/usr/bin/env python3
"""Read selected repository governance documents and report structure, not body text.

This is a bounded content-inspection layer for the account auditor. It stores document
headings and blob hashes, never the source text, and remains a review aid rather than
a semantic, security, or completeness certification.
"""
from __future__ import annotations
import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
MAX_DOCUMENT_BYTES = 512_000
ROOT_DOC_PREFIXES = ("README.", "AGENTS.", "SECURITY.", "CONTRIBUTING.", "ARCHITECTURE.", "CODE_OF_CONDUCT.", "SUPPORT.")
DOCS_CANDIDATES = ("docs/README.md", "docs/architecture.md", "docs/ARCHITECTURE.md", "docs/overview.md", "docs/OVERVIEW.md")

def api_get(path: str, token: str):
    """Perform a GitHub API GET without logging credentials or response bodies."""
    request = Request(API_ROOT + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "world-seed-read-only-auditor",
    })
    with urlopen(request, timeout=20) as response:
        return json.load(response)

def _inspect_file(full_name: str, path: str, ref: str, token: str) -> dict:
    encoded_repo = quote(full_name, safe="/")
    encoded_path = quote(path, safe="/")
    encoded_ref = quote(ref, safe="")
    try:
        item = api_get(f"/repos/{encoded_repo}/contents/{encoded_path}?ref={encoded_ref}", token)
    except HTTPError as exc:
        if exc.code == 404:
            return {"path": path, "status": "not-found-or-not-visible"}
        raise
    if item.get("type") != "file":
        return {"path": path, "status": "not-a-file"}
    size = item.get("size")
    if not isinstance(size, int) or size > MAX_DOCUMENT_BYTES:
        return {"path": path, "status": "skipped-size-limit", "reported_bytes": size}
    if item.get("encoding") != "base64" or not isinstance(item.get("content"), str):
        return {"path": path, "status": "unsupported-content-response"}
    try:
        raw = base64.b64decode(item["content"], validate=False)
        content = raw.decode("utf-8")
    except (ValueError, UnicodeError):
        return {"path": path, "status": "unreadable-text"}
    headings = []
    for line in content.splitlines():
        match = re.match(r"^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            headings.append({"level": len(match.group(1)), "text": match.group(2).strip()[:180]})
    return {
        "path": path,
        "status": "inspected",
        "blob_sha": item.get("sha"),
        "bytes": len(raw),
        "heading_count": len(headings),
        "headings": headings[:100],
        "headings_truncated": len(headings) > 100,
        "body_retained": False,
    }

def inspect_documents(full_name: str, token: str, root_entry_names: list[str] | None = None) -> dict:
    """Inspect selected governance-document structure on the default branch."""
    encoded_repo = quote(full_name, safe="/")
    metadata = api_get(f"/repos/{encoded_repo}", token)
    branch = metadata.get("default_branch")
    if not branch:
        raise ValueError("repository default branch is unavailable")
    if root_entry_names is None:
        encoded_ref = quote(branch, safe="")
        root = api_get(f"/repos/{encoded_repo}/contents?ref={encoded_ref}", token)
        if not isinstance(root, list):
            raise ValueError("repository root response was not a directory listing")
        root_entry_names = [str(item.get("name", "")) for item in root]
    root_docs = sorted(
        name for name in root_entry_names
        if any(name.upper().startswith(prefix) for prefix in ROOT_DOC_PREFIXES)
        and "." in name
    )
    paths = list(root_docs)
    if any(name.casefold() == "docs" for name in root_entry_names):
        paths.extend(DOCS_CANDIDATES)
    unique_paths = list(dict.fromkeys(paths))
    inspected = []
    for path in unique_paths:
        try:
            inspected.append(_inspect_file(full_name, path, branch, token))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            inspected.append({"path": path, "status": "blocked", "reason": type(exc).__name__})
    present = [item for item in inspected if item["status"] == "inspected"]
    return {
        "schema_version": 1,
        "audit_type": "repository_governance_document_structure",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "repository": metadata.get("full_name", full_name),
        "default_branch": branch,
        "candidate_count": len(inspected),
        "inspected_count": len(present),
        "blocked_count": sum(item["status"] == "blocked" for item in inspected),
        "documents": inspected,
        "coverage": {
            "status": "bounded-structural-review",
            "body_text_retained": False,
            "semantic_quality_verified": False,
            "security_posture_verified": False,
            "note": "Only selected conventional governance documents and headings are inspected. A missing candidate may be absent or inaccessible; applicability is contextual. This is not a completeness or policy-compliance certification.",
        },
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
        report = inspect_documents(args.repo, token)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        print(f"BLOCKED: document inspection failed ({type(exc).__name__}); no clean result is implied.", file=sys.stderr)
        return 2
    print(f"Document structure report written for {report['repository']}: {report['inspected_count']} documents inspected; bodies not retained.")
    return 0 if report["blocked_count"] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
