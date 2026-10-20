"""Inspect explicitly declared cross-repository contract artifacts without retaining bodies."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


API_ROOT = "https://api.github.com"


def validate_expected_contracts(expected: dict) -> list[dict]:
    """Validate a private contract inventory; never infer relationships from names."""
    if not isinstance(expected, dict) or expected.get("schema_version") != 1:
        raise ValueError("expected contracts must be an object with schema_version=1")
    if not isinstance(expected.get("authoritative"), bool):
        raise ValueError("expected contracts must explicitly declare authoritative true or false")
    if not isinstance(expected.get("reviewed_at"), str) or not expected["reviewed_at"].strip():
        raise ValueError("expected contracts must include reviewed_at")
    contracts = expected.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        raise ValueError("expected contracts must contain a non-empty contracts list")
    seen = set()
    for item in contracts:
        if not isinstance(item, dict):
            raise ValueError("each contract must be an object")
        for field in ("contract_id", "producer", "consumer", "path"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"each contract requires a non-empty {field}")
        path = item["path"].strip()
        if path.startswith("/") or any(part in {".", ".."} for part in path.split("/")):
            raise ValueError("contract paths must be safe repository-relative paths")
        if "/" not in item["producer"] or "/" not in item["consumer"]:
            raise ValueError("producer and consumer must be owner/name repository strings")
        key = item["contract_id"].strip().casefold()
        if key in seen:
            raise ValueError("expected contracts contains duplicate contract_id values")
        seen.add(key)
    return contracts


def _api_get(path: str, token: str):
    request = Request(API_ROOT + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "world-seed-read-only-auditor",
    })
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def inspect_expected_contracts(observed_report: dict, expected: dict, token: str) -> dict:
    """Check declared endpoints and artifact existence; this does not prove compatibility."""
    contracts = validate_expected_contracts(expected)
    observed = {}
    for item in observed_report.get("repositories", []):
        name = item.get("full_name") or item.get("repository") or (item.get("inventory") or {}).get("full_name")
        if name:
            observed[name.casefold()] = item

    results = []
    for contract in contracts:
        producer = contract["producer"].strip()
        consumer = contract["consumer"].strip()
        base = {
            "contract_id": contract["contract_id"].strip(),
            "producer": producer,
            "consumer": consumer,
            "path": contract["path"].strip(),
            "artifact_status": "unverified",
            "producer_observed": producer.casefold() in observed,
            "consumer_observed": consumer.casefold() in observed,
            "blob_sha": None,
            "reason": None,
        }
        if not base["producer_observed"] or not base["consumer_observed"]:
            base["reason"] = "producer-or-consumer-not-observed"
            results.append(base)
            continue
        try:
            encoded_repo = quote(producer, safe="/")
            metadata = _api_get(f"/repos/{encoded_repo}", token)
            branch = metadata.get("default_branch")
            if not branch:
                base["reason"] = "default-branch-unavailable"
                results.append(base)
                continue
            encoded_path = quote(base["path"], safe="/")
            encoded_ref = quote(branch, safe="")
            artifact = _api_get(f"/repos/{encoded_repo}/contents/{encoded_path}?ref={encoded_ref}", token)
            if artifact.get("type") == "file" and isinstance(artifact.get("sha"), str):
                base["artifact_status"] = "present"
                base["blob_sha"] = artifact["sha"]
            else:
                base["artifact_status"] = "unverified"
                base["reason"] = "path-is-not-a-file"
        except HTTPError as exc:
            base["artifact_status"] = "not-found-or-not-visible" if exc.code == 404 else "blocked"
            base["reason"] = "not-found-or-not-visible" if exc.code == 404 else f"http-{exc.code}"
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            base["artifact_status"] = "blocked"
            base["reason"] = type(exc).__name__
        results.append(base)

    inventory_names = set(observed)
    expected_names = {
        item[field].strip().casefold()
        for item in contracts for field in ("producer", "consumer")
    }
    missing_repositories = sorted(expected_names - inventory_names)
    all_present = all(item["artifact_status"] == "present" for item in results)
    verified = bool(
        expected["authoritative"]
        and not observed_report.get("requested_owner_filter")
        and not missing_repositories
        and all_present
    )
    return {
        "schema_version": 1,
        "status": "verified-artifacts" if verified else "partial-unverified",
        "cross_repository_contract_inventory_verified": verified,
        "expected_contracts_authoritative": expected["authoritative"],
        "expected_contracts_reviewed_at": expected["reviewed_at"],
        "contract_count": len(results),
        "missing_repositories": missing_repositories,
        "owner_filter_applied": bool(observed_report.get("requested_owner_filter")),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "contracts": results,
        "note": (
            "Every declared producer artifact was found and producer/consumer repositories were observed. "
            "This verifies artifact presence only; it does not validate consumer usage, API/event semantics, "
            "versions, runtime health, or compatibility."
            if verified else
            "Cross-repository contract coverage remains unverified. Missing, inaccessible, or unobserved items "
            "must be reviewed; absence from this report is not proof that a contract does not exist."
        ),
    }
