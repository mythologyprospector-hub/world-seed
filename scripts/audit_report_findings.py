#!/usr/bin/env python3
"""Turn observed account-audit gaps into private ledger findings.

Missing findings in a later report are never treated as resolved.
"""
from __future__ import annotations
import re
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_findings_ledger import get_record, upsert_record


def _now():
    return datetime.now(timezone.utc).isoformat()


def _asset_id(value):
    return re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-") or "UNKNOWN"


def _candidate(finding_id, title, scope, severity, assets, impact, description, next_action, observed_at):
    return {
        "finding_id": finding_id, "title": title, "scope": scope, "severity": severity,
        "confidence": "confirmed", "status": "observed",
        "affected_assets": sorted(set(assets)), "impact": impact,
        "evidence": [{"description": description, "uri": None, "observed_at": observed_at, "commit": None}],
        "owner": "AI steward", "first_observed": observed_at, "last_reviewed": observed_at,
        "remediation": {"next_action": next_action, "issue_url": None, "pull_request_url": None,
                        "accepted_risk_rationale": None, "review_by": None},
        "verification": {"verified": False, "evidence": [], "verified_at": None, "verified_by": None},
        "related_findings": [],
    }


def derive_findings(report):
    """Derive stable findings from explicit report conditions, not inferred absence."""
    observed_at = report.get("generated_at") or _now()
    coverage = report.get("coverage") or {}
    findings = []
    gaps = [
        ("account_completeness_verified", "AUDIT-COVERAGE-ACCOUNT-COMPLETENESS",
         "Account repository coverage is not verified", "account", "high", ["account inventory"],
         "Repositories or resources may be missing from the audit.",
         str(coverage.get("note") or "The report does not verify account inventory completeness."),
         "Compare visible repositories with an authoritative expected inventory and document inaccessible scopes."),
        ("cross_repository_contracts_checked", "AUDIT-COVERAGE-CROSS-REPOSITORY-CONTRACTS",
         "Cross-repository contracts have not been checked", "cross-repository", "medium", ["repository ecosystem"],
         "Dependencies and shared-protocol drift between repositories may go undetected.",
         "The report explicitly marks cross_repository_contracts_checked as false.",
         "Define a reviewable contract inventory and implement read-only checks."),
        ("security_posture_verified", "AUDIT-COVERAGE-SECURITY-POSTURE",
         "Account security posture is not verified", "account", "high", ["account security controls"],
         "The audit cannot establish that relevant security controls were visible and correctly configured.",
         "The report explicitly marks security_posture_verified as false.",
         "Collect control evidence with least-privilege access; retain inaccessible results as unverified."),
    ]
    for key, fid, title, scope, severity, assets, impact, evidence, action in gaps:
        if coverage.get(key) is not True:
            findings.append(_candidate(fid, title, scope, severity, assets, impact, evidence, action, observed_at))

    for repo in report.get("repositories", []):
        name = repo.get("repository") or (repo.get("inventory") or {}).get("full_name")
        if not name:
            continue
        controls = repo.get("branch_safeguards") or {}
        uncertain = sorted(k for k in ("classic_branch_protection", "repository_rulesets", "organization_rulesets")
                           if (controls.get(k) or {}).get("status") in {"unverified", "error"})
        if uncertain:
            findings.append(_candidate(
                "AUDIT-BRANCH-SAFEGUARDS-" + _asset_id(name),
                "Branch safeguards are not fully verified for " + name, "repository", "high", [name],
                "Required branch controls may be absent or may simply be inaccessible to this audit token.",
                "Controls with unverified/error status: " + ", ".join(uncertain) + ". No absence is inferred.",
                "Resolve the access gap or obtain authorized evidence; do not change settings automatically.",
                observed_at))

    blocked = report.get("blocked_inspections") or []
    if blocked:
        assets = sorted({item.get("repository") for item in blocked if item.get("repository")})
        findings.append(_candidate(
            "AUDIT-COVERAGE-INSPECTIONS-BLOCKED", "One or more repository inspections were blocked",
            "account", "high", assets or ["repository inspections"],
            "Blocked inspection stages leave repository state unknown.",
            "The private source report records " + str(len(blocked)) + " blocked inspection event(s).",
            "Review each blocked stage and rerun with authorized access; do not infer uninspected controls are absent.",
            observed_at))
    return findings


def ingest_report(connection, report):
    """Upsert current observations; preserve lifecycle and never resolve absent findings."""
    observed = derive_findings(report)
    reopened = preserved = 0
    for candidate in observed:
        prior = get_record(connection, candidate["finding_id"])
        if prior:
            candidate["first_observed"] = prior["first_observed"]
            candidate["status"] = prior["status"]
            candidate["verification"] = prior["verification"]
            candidate["remediation"] = prior["remediation"]
            evidence = list(prior.get("evidence", []))
            for item in candidate["evidence"]:
                if item not in evidence:
                    evidence.append(item)
            candidate["evidence"] = evidence[-20:]
            if prior["status"] == "verified-resolved":
                candidate["status"] = "reopened"
                candidate["verification"] = {"verified": False, "evidence": [],
                                              "verified_at": None, "verified_by": None}
                reopened += 1
            else:
                preserved += 1
        upsert_record(connection, candidate)
    return {"observations_upserted": len(observed),
            "existing_lifecycle_states_preserved": preserved,
            "verified_resolutions_reopened_by_new_evidence": reopened,
            "absent_findings_auto_resolved": 0}
