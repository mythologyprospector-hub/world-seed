"""Compare observed repositories with an explicitly authoritative private inventory."""
from __future__ import annotations
from datetime import datetime, timezone


def reconcile_expected_inventory(observed_report: dict, expected: dict) -> dict:
    """Reconcile exact names without treating token visibility alone as completeness."""
    if not isinstance(expected, dict) or expected.get("schema_version") != 1:
        raise ValueError("expected inventory must be an object with schema_version=1")
    names = expected.get("repositories")
    if not isinstance(names, list) or not names:
        raise ValueError("expected inventory repositories must be a non-empty list")
    for name in names:
        if (not isinstance(name, str) or name != name.strip()
                or len(name.split("/")) != 2 or not all(name.split("/"))):
            raise ValueError("expected inventory names must be trimmed owner/repository strings")
    normalized = [name.casefold() for name in names]
    if len(set(normalized)) != len(normalized):
        raise ValueError("expected inventory contains duplicate repository names")
    if not isinstance(expected.get("authoritative"), bool):
        raise ValueError("expected inventory must explicitly declare authoritative true or false")
    if not isinstance(expected.get("reviewed_at"), str) or not expected["reviewed_at"].strip():
        raise ValueError("expected inventory must include reviewed_at")
    if not isinstance(observed_report, dict):
        raise ValueError("observed report must be an object")
    observed = observed_report.get("repositories", [])
    if not isinstance(observed, list):
        raise ValueError("observed report repositories must be a list")
    observed_names = []
    for item in observed:
        if not isinstance(item, dict):
            raise ValueError("observed repository entries must be objects")
        inventory = item.get("inventory") or {}
        if not isinstance(inventory, dict):
            raise ValueError("observed repository inventory field must be an object")
        name = item.get("full_name") or item.get("repository") or inventory.get("full_name")
        if not isinstance(name, str) or name != name.strip() or len(name.split("/")) != 2 or not all(name.split("/")):
            raise ValueError("observed repository entry must contain a valid owner/repository name")
        observed_names.append(name)
    observed_set = {name.casefold() for name in observed_names}
    expected_set = set(normalized)
    missing = sorted((name for name in names if name.casefold() not in observed_set), key=str.casefold)
    unexpected = sorted((name for name in observed_names if name.casefold() not in expected_set), key=str.casefold)
    matches = not missing and not unexpected and len(observed_names) == len(observed_set)
    pagination_complete = observed_report.get("pagination_complete") is True
    verified = bool(expected["authoritative"] and matches and pagination_complete and not observed_report.get("requested_owner_filter"))
    return {
        "status": "verified-match" if verified else ("mismatch" if missing or unexpected else "partial-unverified"),
        "repository_inventory_verified": verified,
        "account_completeness_verified": False,
        "expected_inventory_authoritative": expected["authoritative"],
        "expected_inventory_reviewed_at": expected["reviewed_at"],
        "expected_repository_count": len(normalized),
        "observed_repository_count": len(observed_names),
        "missing_from_observed": missing,
        "unexpected_in_observed": unexpected,
        "owner_filter_applied": bool(observed_report.get("requested_owner_filter")),
        "pagination_complete": pagination_complete,
        "reconciled_at": datetime.now(timezone.utc).isoformat(),
        "note": ("Exact match to the supplied authoritative inventory; repository inventory is verified, but full account backup/recovery completeness is not."
                 if verified else
                 "Inventory is not verified complete. Review mismatches, expected-inventory authority, pagination evidence, and any owner filter; inaccessible resources remain unknown."),
    }
