#!/usr/bin/env python3
"""Compare two partial account-baseline reports without overstating audit coverage."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from private_report import write_private_json

ROOT = Path(__file__).resolve().parents[1]
REPO_FIELDS = ("visibility", "default_branch", "archived", "fork")


def _index(report: object, label: str) -> dict[str, dict]:
    """Validate the report envelope and index its repository records by full name."""
    if not isinstance(report, dict) or report.get("audit_type") != "account_visible_repository_baseline":
        raise ValueError(f"{label}: expected an account_visible_repository_baseline report")
    if report.get("schema_version") != 1 or not isinstance(report.get("repositories"), list):
        raise ValueError(f"{label}: unsupported schema version or missing repositories list")
    indexed = {}
    for item in report["repositories"]:
        if not isinstance(item, dict) or not isinstance(item.get("repository"), str) or not item["repository"].strip():
            raise ValueError(f"{label}: each repository record needs a full repository name")
        name = item["repository"]
        if name in indexed:
            raise ValueError(f"{label}: duplicate repository record: {name}")
        indexed[name] = item
    return indexed


def _fingerprint(item: dict) -> dict:
    """Extract comparable signals only; do not retain document bodies or secrets."""
    inventory = item.get("inventory") or {}
    layout = item.get("layout") or {}
    documents = item.get("documents") or {}
    document_signals = {}
    for document in documents.get("documents", []):
        if not isinstance(document, dict) or not isinstance(document.get("path"), str):
            continue
        document_signals[document["path"]] = {
            "status": document.get("status"),
            "blob_sha": document.get("blob_sha"),
            "headings": document.get("headings"),
            "headings_truncated": document.get("headings_truncated"),
        }
    result = {field: inventory.get(field) for field in REPO_FIELDS}
    result["root_entry_names"] = layout.get("root_entry_names")
    result["signals"] = layout.get("signals")
    result["document_inspection_status"] = item.get("document_inspection_status")
    result["documents"] = document_signals
    return result


def compare_reports(previous: object, current: object) -> dict:
    """Produce a deterministic structural delta while preserving both reports' coverage limits."""
    before = _index(previous, "previous")
    after = _index(current, "current")
    previous_report = previous
    current_report = current
    old_names = set(before)
    new_names = set(after)
    added = sorted(new_names - old_names, key=str.casefold)
    removed = sorted(old_names - new_names, key=str.casefold)
    changed = []
    unchanged = 0
    for name in sorted(old_names & new_names, key=str.casefold):
        old_fp = _fingerprint(before[name])
        new_fp = _fingerprint(after[name])
        fields = sorted(field for field in old_fp if old_fp[field] != new_fp[field])
        if fields:
            changed.append({"repository": name, "changed_fields": fields})
        else:
            unchanged += 1
    old_coverage = previous_report.get("coverage") if isinstance(previous_report, dict) else None
    new_coverage = current_report.get("coverage") if isinstance(current_report, dict) else None
    return {
        "schema_version": 1,
        "audit_type": "account_baseline_comparison",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "previous_generated_at": previous_report.get("generated_at"),
        "current_generated_at": current_report.get("generated_at"),
        "counts": {
            "previous_repositories": len(before),
            "current_repositories": len(after),
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "unchanged": unchanged,
        },
        "added_repositories": added,
        "removed_repositories": removed,
        "changed_repositories": changed,
        "coverage": {
            "previous": old_coverage,
            "current": new_coverage,
            "status": "partial-unverified",
            "account_completeness_verified": False,
            "note": "A delta compares only records present in each supplied report. It does not prove account completeness, explain why a repository disappeared, or certify semantic correctness.",
        },
    }


def main(argv: list[str] | None = None) -> int:
    """Compare two JSON baselines and write the private comparison report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", required=True, type=Path, help="Previous baseline JSON")
    parser.add_argument("--current", required=True, type=Path, help="Current baseline JSON")
    parser.add_argument("--output", required=True, type=Path, help="Private output path outside this public repository")
    args = parser.parse_args(argv)
    output = args.output.expanduser().resolve()
    if output == ROOT or ROOT in output.parents:
        print("BLOCKED: write the comparison outside the public world-seed repository.", file=sys.stderr)
        return 2
    try:
        previous = json.loads(args.previous.expanduser().read_text(encoding="utf-8"))
        current = json.loads(args.current.expanduser().read_text(encoding="utf-8"))
        report = compare_reports(previous, current)
        write_private_json(output, report)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"BLOCKED: baseline comparison failed ({type(exc).__name__}); no clean result is implied.", file=sys.stderr)
        return 2
    counts = report["counts"]
    print(f"Comparison written privately: +{counts['added']} added, -{counts['removed']} removed, {counts['changed']} changed, {counts['unchanged']} unchanged. Coverage remains partial-unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
