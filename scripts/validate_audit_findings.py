#!/usr/bin/env python3
"""Validate portable audit finding JSON records without third-party dependencies."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = {
    "finding_id", "title", "scope", "severity", "confidence", "status",
    "affected_assets", "impact", "evidence", "owner", "first_observed",
    "last_reviewed", "remediation", "verification",
}
SCOPES = {"repository", "cross-repository", "account"}
SEVERITIES = {"critical", "high", "medium", "low"}
CONFIDENCE = {"confirmed", "high", "medium", "low", "suspected"}
STATUSES = {
    "observed", "triaged", "accepted-risk", "planned", "in-progress",
    "fixed-unverified", "verified-resolved", "blocked", "reopened",
}


def validate_record(record: object, source: str = "record") -> list[str]:
    """Return validation errors for one finding record."""
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{source}: top-level JSON value must be an object"]
    missing = sorted(REQUIRED - record.keys())
    if missing:
        errors.append(f"{source}: missing required fields: {', '.join(missing)}")
    for field, allowed in (("scope", SCOPES), ("severity", SEVERITIES), ("confidence", CONFIDENCE), ("status", STATUSES)):
        if field in record and record[field] not in allowed:
            errors.append(f"{source}: invalid {field} value")
    finding_id = record.get("finding_id")
    if isinstance(finding_id, str) and (not finding_id.startswith("AUDIT-") or len(finding_id) <= 6):
        errors.append(f"{source}: finding_id must start with AUDIT- and include a stable suffix")
    for field in ("title", "impact", "owner"):
        if field in record and (not isinstance(record[field], str) or not record[field].strip()):
            errors.append(f"{source}: {field} must be a non-empty string")
    assets = record.get("affected_assets")
    if "affected_assets" in record and (not isinstance(assets, list) or not assets or not all(isinstance(x, str) and x.strip() for x in assets)):
        errors.append(f"{source}: affected_assets must be a non-empty list of names")
    evidence = record.get("evidence")
    if "evidence" in record:
        if not isinstance(evidence, list):
            errors.append(f"{source}: evidence must be a list")
        else:
            for index, item in enumerate(evidence):
                if not isinstance(item, dict) or not isinstance(item.get("description"), str) or not item.get("description", "").strip() or not isinstance(item.get("observed_at"), str):
                    errors.append(f"{source}: evidence item {index} needs description and observed_at")
    remediation = record.get("remediation")
    if "remediation" in record and (not isinstance(remediation, dict) or not isinstance(remediation.get("next_action"), str) or not remediation.get("next_action", "").strip()):
        errors.append(f"{source}: remediation.next_action must be a non-empty string")
    verification = record.get("verification")
    if "verification" in record and (not isinstance(verification, dict) or not isinstance(verification.get("verified"), bool) or not isinstance(verification.get("evidence"), list)):
        errors.append(f"{source}: verification needs a boolean verified flag and an evidence list")
    if record.get("status") == "verified-resolved" and isinstance(verification, dict):
        if verification.get("verified") is not True or not verification.get("evidence") or not verification.get("verified_at"):
            errors.append(f"{source}: verified-resolved requires verified=true, verification evidence, and verified_at")
    if record.get("status") == "accepted-risk" and isinstance(remediation, dict):
        if not str(remediation.get("accepted_risk_rationale") or "").strip() or not remediation.get("review_by"):
            errors.append(f"{source}: accepted-risk requires a rationale and review_by date")
    return errors


def main(argv: list[str] | None = None) -> int:
    """Validate one or more JSON finding records or templates."""
    paths = [Path(item) for item in (argv if argv is not None else sys.argv[1:])]
    if not paths:
        print("Usage: python scripts/validate_audit_findings.py FINDING.json [...]")
        return 2
    errors: list[str] = []
    checked = 0
    for path in paths:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: could not read valid JSON ({type(exc).__name__})")
            continue
        checked += 1
        errors.extend(validate_record(record, str(path)))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} issue(s) across {checked} record(s).")
        return 1
    print(f"PASS: {checked} audit finding record(s) validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
