"""Compare observed repositories with an explicitly authoritative private inventory."""
from __future__ import annotations
from datetime import datetime, timezone


def reconcile_expected_inventory(observed_report: dict, expected: dict) -> dict:
    """Reconcile exact names without treating token visibility alone as completeness."""
    if not isinstance(expected, dict) or expected.get("schema_version") != 1:
        raise ValueError("expected inventory must be an object with schema_version=1")
    names = expected.get("repositories")
    if not isinstance(names, list) or not names or any(not isinstance(n, str) or not n.strip() or "/" not in n for n in names):
        raise ValueError("expected inventory repositories must be a non-empty list of owner/name strings")
    normalized = [n.strip().casefold() for n in names]
    if len(set(normalized)) != len(normalized):
        raise ValueError("expected inventory contains duplicate repository names")
    if not isinstance(expected.get("authoritative"), bool):
        raise ValueError("expected inventory must explicitly declare authoritative true or false")
    if not expected.get("reviewed_at"):
        raise ValueError("expected inventory must include reviewed_at")
    observed = observed_report.get("repositories", [])
    observed_names = []
    for item in observed:
        name = item.get("full_name") or item.get("repository") or (item.get("inventory") or {}).get("full_name")
        if name:
            observed_names.append(name.strip())
    observed_set = {n.casefold() for n in observed_names}
    expected_set = set(normalized)
    missing = sorted((name.strip() for name in names if name.strip().casefold() not in observed_set), key=str.casefold)
    unexpected = sorted((n for n in observed_names if n.casefold() not in expected_set), key=str.casefold)
    matches = not missing and not unexpected and len(observed_names) == len(observed_set)
    verified = bool(expected["authoritative"] and matches and not observed_report.get("requested_owner_filter"))
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
        "reconciled_at": datetime.now(timezone.utc).isoformat(),
        "note": ("Exact match to the supplied authoritative inventory; repository inventory is verified, but full account backup/recovery completeness is not."
                 if verified else
                 "Inventory is not verified complete. Review mismatches, expected-inventory authority, and any owner filter; inaccessible resources remain unknown."),
    }
