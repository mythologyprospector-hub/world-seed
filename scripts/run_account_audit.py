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
from audit_branch_safeguards import inspect_branch_safeguards


def build_report(token: str, owner_filter: str | None = None) -> dict:
    """Collect inventory, root-layout signals, and bounded governance-document structure without changing GitHub."""
    inventory = collect_inventory(token, owner_filter)
    results = []
    blocked = []
    document_blocked = []
    safeguard_results = []
    for repository in inventory["repositories"]:
        full_name = repository["full_name"]
        safeguards = inspect_branch_safeguards(full_name, repository.get("default_branch"), token)
        safeguard_results.append(safeguards)
        try:
            layout = inspect_layout(full_name, token)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            blocked.append({"repository": full_name, "reason": type(exc).__name__})
            results.append({"repository": full_name, "inventory": repository, "layout": None, "documents": None, "branch_safeguards": safeguards, "inspection_status": "blocked", "document_inspection_status": "not-attempted"})
            continue
        document_status = "blocked"
        documents = None
        try:
            documents = inspect_documents(full_name, token, layout.get("root_entry_names", []))
            # Missing conventional paths are expected probes, not failed inspections.
            # Other non-inspected statuses (blocked, too large, unreadable, etc.)
            # still make coverage partial. This status does not certify completeness.
            document_results = documents.get("documents", [])
            incomplete = any(
                item.get("status") not in {"inspected", "not-found-or-not-visible"}
                for item in document_results
                if isinstance(item, dict)
            )
            document_status = "partial" if incomplete or documents.get("blocked_count", 0) else "inspected"
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            document_status = "blocked"
            document_blocked.append({"repository": full_name, "reason": type(exc).__name__, "stage": "document-inspection"})
        results.append({"repository": full_name, "inventory": repository, "layout": layout, "documents": documents, "branch_safeguards": safeguards, "inspection_status": "inspected", "document_inspection_status": document_status})
    return {
        "schema_version": 1,
        "audit_type": "account_visible_repository_baseline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authenticated_identity": inventory["authenticated_identity"],
        "requested_owner_filter": owner_filter,
        "repository_count_discovered": inventory["repository_count"],
        "pages_fetched": inventory.get("pages_fetched"),
        "pagination_complete": inventory.get("pagination_complete") is True,
        "repository_count_inspected": sum(item["inspection_status"] == "inspected" for item in results),
        "repository_count_blocked": len(blocked),
        "document_inspections_blocked": len(document_blocked),
        "branch_safeguard_repositories_inspected": len(safeguard_results),
        "branch_safeguard_repositories_with_unverified_controls": sum(
            any((item.get(control) or {}).get("status") in {"unverified", "error"}
                for control in ("classic_branch_protection", "repository_rulesets", "organization_rulesets"))
            for item in safeguard_results
        ),
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
            "cross_repository_contract_inventory_verified": False,
            "security_posture_verified": False,
            "note": "This covers only repositories visible to the token. Compare with an authoritative expected inventory and verify private/organization access before claiming completeness.",
        },
        "review_policy": "Presence signals are prompts for human/AI review, not automatic defects; applicability depends on project purpose and documented exceptions.",
        "repositories": results,
        "blocked_inspections": blocked + document_blocked,
    }



def attach_expected_inventory_reconciliation(report: dict, expected: dict) -> dict:
    """Record inventory reconciliation without upgrading overall backup coverage."""
    from reconcile_expected_inventory import reconcile_expected_inventory

    reconciliation = reconcile_expected_inventory(report, expected)
    coverage = report["coverage"]
    coverage["expected_inventory_reconciliation"] = reconciliation
    coverage["repository_inventory_reconciliation_status"] = reconciliation["status"]
    coverage["repository_inventory_verified"] = reconciliation["repository_inventory_verified"]
    # Inventory equality is one narrow dimension; it cannot certify the full
    # account backup, settings, metadata, binaries, or an actual recovery drill.
    coverage["account_completeness_verified"] = False
    coverage["status"] = "partial-unverified"
    coverage["note"] = (
        f"Repository inventory reconciliation: {reconciliation['status']}. "
        "Full account backup and recovery completeness remains unverified; "
        "repository contents, operating records, settings, binary artifacts, "
        "and isolated restoration require separate evidence."
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", help="Keep only repositories owned by this user or organization login")
    parser.add_argument("--output", required=True, type=Path, help="Access-controlled local report path")
    parser.add_argument("--ledger-db", type=Path, help="Optional private SQLite findings ledger path outside this public repository")
    parser.add_argument("--expected-inventory", type=Path, help="Optional authoritative private JSON inventory outside this public repository")
    parser.add_argument("--expected-contracts", type=Path, help="Optional private JSON cross-repository contract inventory outside this public repository")
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
        if args.expected_inventory:
            expected_path = args.expected_inventory.expanduser().resolve()
            if expected_path == seed_root or seed_root in expected_path.parents:
                raise ValueError("expected inventory must be outside the public world-seed repository")
            expected = json.loads(expected_path.read_text(encoding="utf-8"))
            report = attach_expected_inventory_reconciliation(report, expected)
        if args.expected_contracts:
            contracts_path = args.expected_contracts.expanduser().resolve()
            if contracts_path == seed_root or seed_root in contracts_path.parents:
                raise ValueError("expected contracts inventory must be outside the public world-seed repository")
            from inspect_cross_repository_contracts import inspect_expected_contracts
            expected_contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
            contract_report = inspect_expected_contracts(report, expected_contracts, token)
            report["cross_repository_contracts"] = contract_report
            report["coverage"]["cross_repository_contracts_checked"] = True
            report["coverage"]["cross_repository_contract_inventory_verified"] = contract_report["cross_repository_contract_inventory_verified"]
        output.parent.mkdir(parents=True, exist_ok=True)
        write_private_json(output, report)
        ledger_summary = None
        if args.ledger_db:
            from audit_findings_ledger import open_ledger
            from audit_report_findings import ingest_report
            ledger_path = args.ledger_db.expanduser().resolve()
            if ledger_path == seed_root or seed_root in ledger_path.parents:
                raise ValueError("ledger database must be outside the public world-seed repository")
            ledger_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with open_ledger(ledger_path) as connection:
                ledger_summary = ingest_report(connection, report)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        print(f"BLOCKED: baseline scan failed ({type(exc).__name__}); no clean result is implied.", file=sys.stderr)
        return 2
    document_status = report["coverage"]["document_inspection_status_counts"]
    print(f"Baseline report written to the chosen local path: {report['repository_count_inspected']} layouts inspected, {report['repository_count_blocked']} layout inspections blocked; document inspections: {document_status['inspected']} complete, {document_status['partial']} partial, {document_status['blocked']} blocked. Coverage remains partial-unverified.")
    if args.ledger_db:
        print(f"Private findings ledger updated: {ledger_summary['observations_upserted']} current observations; {ledger_summary['verified_resolutions_reopened_by_new_evidence']} previously resolved findings reopened; no absent findings auto-resolved.")
    return 0 if not report["repository_count_blocked"] and not report["document_inspections_blocked"] and not document_status["partial"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
