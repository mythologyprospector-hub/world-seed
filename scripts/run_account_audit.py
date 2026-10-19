#!/usr/bin/env python3
"""Run a read-only baseline scan of visible repositories, layouts, and governance-document structure.

This is a partial baseline audit, not a completeness or security certification.
Reports can reveal private repository names and structure; store them outside public repositories.
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

from audit_account_inventory import collect_inventory
from inspect_repository_layout import inspect_layout
from inspect_repository_documents import inspect_documents


def build_report(token: str, owner_filter: str | None = None) -> dict:
    """Collect inventory, root-layout signals, and bounded governance-document structure without changing GitHub."""
    inventory = collect_inventory(token, owner_filter)
    results = []
    blocked = []
    document_blocked = []
    for repository in inventory["repositories"]:
        full_name = repository["full_name"]
        try:
            layout = inspect_layout(full_name, token)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            blocked.append({"repository": full_name, "reason": type(exc).__name__})
            results.append({"repository": full_name, "inventory": repository, "layout": None, "documents": None, "inspection_status": "blocked", "document_inspection_status": "not-attempted"})
            continue
        document_status = "blocked"
        documents = None
        try:
            documents = inspect_documents(full_name, token, layout.get("root_entry_names", []))
            candidate_count = documents.get("candidate_count", documents.get("inspected_count", 0))
            inspected_count = documents.get("inspected_count", 0)
            document_status = "partial" if documents.get("blocked_count", 0) or inspected_count < candidate_count else "inspected"
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            document_status = "blocked"
            document_blocked.append({"repository": full_name, "reason": type(exc).__name__, "stage": "document-inspection"})
        results.append({"repository": full_name, "inventory": repository, "layout": layout, "documents": documents, "inspection_status": "inspected", "document_inspection_status": document_status})
    return {
        "schema_version": 1,
        "audit_type": "account_visible_repository_baseline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authenticated_identity": inventory["authenticated_identity"],
        "requested_owner_filter": owner_filter,
        "repository_count_discovered": inventory["repository_count"],
        "repository_count_inspected": sum(item["inspection_status"] == "inspected" for item in results),
        "repository_count_blocked": len(blocked),
        "document_inspections_blocked": len(document_blocked),
        "coverage": {
            "status": "partial-unverified",
            "account_completeness_verified": False,
            "repository_contents_inspected": "selected governance document headings and hashes; full document bodies are not retained",
            "document_inspection_status_counts": {
                "inspected": sum(item.get("document_inspection_status") == "inspected" for item in results),
                "partial": sum(item.get("document_inspection_status") == "partial" for item in results),
                "blocked": sum(item.get("document_inspection_status") == "blocked" for item in results),
                "not_attempted": sum(item.get("document_inspection_status") == "not-attempted" for item in results),
            },
            "cross_repository_contracts_checked": False,
            "security_posture_verified": False,
            "note": "This covers only repositories visible to the token. Compare with an authoritative expected inventory and verify private/organization access before claiming completeness.",
        },
        "review_policy": "Presence signals are prompts for human/AI review, not automatic defects; applicability depends on project purpose and documented exceptions.",
        "repositories": results,
        "blocked_inspections": blocked + document_blocked,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", help="Keep only repositories owned by this user or organization login")
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
    try:
        report = build_report(token, args.owner)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        print(f"BLOCKED: baseline scan failed ({type(exc).__name__}); no clean result is implied.", file=sys.stderr)
        return 2
    document_status = report["coverage"]["document_inspection_status_counts"]
    print(f"Baseline report written to the chosen local path: {report['repository_count_inspected']} layouts inspected, {report['repository_count_blocked']} layout inspections blocked; document inspections: {document_status['inspected']} complete, {document_status['partial']} partial, {document_status['blocked']} blocked. Coverage remains partial-unverified.")
    return 0 if not report["repository_count_blocked"] and not report["document_inspections_blocked"] and not document_status["partial"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
