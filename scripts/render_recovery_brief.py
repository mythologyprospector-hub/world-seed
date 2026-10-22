#!/usr/bin/env python3
"""Render a reviewed recovery-state JSON record as a compact Markdown brief.

The brief is an orientation aid, not independent evidence or authorization.
This command reads local files only and writes the brief to stdout.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from audit_recovery_state import load_state, safe_slug


def safe_repository_url(value: str) -> str:
    """Drop userinfo, query, and fragment before rendering a repository URL."""
    try:
        parsed = urlsplit(value)
        if parsed.scheme and parsed.netloc:
            host = parsed.hostname or ""
            if parsed.port:
                host = f"{host}:{parsed.port}"
            return urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    except ValueError:
        pass
    return "[repository URL omitted: not safely parseable]"


def bullet_list(values: list[Any], empty: str = "_None recorded._") -> list[str]:
    if not values:
        return [empty]
    result: list[str] = []
    for value in values:
        if isinstance(value, dict):
            result.append("- " + str(value.get("statement", value.get("item", json.dumps(value, ensure_ascii=False))))
                         )
            provenance = value.get("provenance")
            scope = value.get("scope")
            evidence = value.get("evidence")
            if provenance:
                result.append("  - Provenance: " + str(provenance))
            if scope:
                result.append("  - Scope: " + str(scope))
            if evidence:
                result.append("  - Evidence: " + "; ".join(map(str, evidence)))
            location = value.get("location")
            status = value.get("status")
            if location:
                result.append("  - Location: " + str(location))
            if status:
                result.append("  - Status: " + str(status))
        else:
            result.append("- " + str(value))
    return result


def render(state: dict[str, Any]) -> str:
    project = state["project"]
    record = state["record"]
    canon = state["canon"]
    verification = state["verification"]
    decisions = state["decisions"]
    work = state["current_work"]
    next_action = state["next_action"]
    retrieval = state["retrieval"]

    lines = [
        "# Recovery Brief — " + project["name"],
        "",
        "> **Orientation aid, not proof.** This brief renders a maintained state record. It does not independently verify its claims, current remote state, tests, hosted CI, permissions, or authorization.",
        "",
        "## Status and identity",
        "",
        "- Purpose (recorded): " + project["purpose"],
        "- Repository: " + safe_repository_url(project["repository_url"]),
        "- State record ID: " + record["record_id"],
        "- Updated at: " + str(record["updated_at"] or "UNKNOWN"),
        "- Updated by: " + record["updated_by"],
        "- Commit this record describes: " + str(record["describes_commit"] or "UNKNOWN"),
        "- Recorded freshness: **" + record["freshness"] + "**",
        "- Provenance: " + ("; ".join(record["provenance"]) if record["provenance"] else "NONE RECORDED"),
    ]
    if record["freshness"] != "current":
        lines += ["", "> **Freshness warning:** the record is marked " + record["freshness"] + ". Re-check repository identity, current HEAD, canon, and evidence before relying on current-work or next-action claims."]
    if record.get("mismatches"):
        lines += ["", "Recorded mismatches:", *bullet_list(record["mismatches"])]

    lines += [
        "",
        "## Canon and authority",
        "",
        canon["summary"] or "UNKNOWN — no canon summary recorded.",
        "",
        "### Authoritative documents",
        *bullet_list([
            {"statement": f'{doc["title"]} — {doc["location"]} (authority: {doc["authority"]})'}
            for doc in canon["authoritative_documents"]
        ]),
        "",
        "### Non-negotiable rules",
        *bullet_list(canon["non_negotiable_rules"], "_No rules recorded; retrieve and read canon before acting._"),
        "",
        "### Reference-only material",
        *bullet_list(canon["reference_only"]),
        "",
        "## Verification claims (not re-verified by this renderer)",
    ]
    if verification:
        for item in verification:
            lines += [
                "",
                "- **" + item["claim"] + "**",
                "  - Result recorded: " + item["result"],
                "  - Commit: " + str(item["commit"] or "UNKNOWN"),
                "  - Method: " + item["method"],
                "  - Checked at: " + str(item["checked_at"] or "UNKNOWN"),
                "  - Evidence: " + ("; ".join(item["evidence"]) if item["evidence"] else "NONE RECORDED"),
                "  - Scope limitations: " + ("; ".join(item["scope_limitations"]) if item["scope_limitations"] else "NONE RECORDED"),
            ]
            if item["result"] != "pass":
                lines.append("  - Caution: this record does not claim a passing result.")
            if item["commit"] != record["describes_commit"]:
                lines.append("  - Caution: this verification commit differs from the state record's described commit.")
    else:
        lines.append("")
        lines.append("_No verification claims recorded._")

    for heading, key in [
        ("Accepted decisions", "accepted"),
        ("Rejected decisions", "rejected"),
        ("Open decisions and questions", "open"),
        ("Superseded decisions", "superseded"),
    ]:
        lines += ["", "## " + heading, *bullet_list(decisions[key])]

    lines += [
        "",
        "## Current work",
        "",
        "### Completed (recorded)",
        *bullet_list(work["completed"]),
        "",
        "### In progress (recorded)",
        *bullet_list(work["in_progress"]),
        "",
        "### Risks and blockers",
        *bullet_list(work["risks_and_blockers"]),
        "",
        "### Protect / do not disturb",
        *bullet_list(work["protect_do_not_disturb"]),
        "",
        "### Deferred",
        *bullet_list(work["deferred"]),
        "",
        "## One proposed next action",
        "",
        "**Action:** " + next_action["action"],
        "",
        "**Rationale:** " + (next_action["rationale"] or "Not recorded."),
        "",
        "**Preconditions:**",
        *bullet_list(next_action["preconditions"]),
        "",
        "**Expected result:** " + (next_action["expected_result"] or "Not recorded."),
        "",
        "**Recorded authorization status:** " + next_action["authorization"],
        "",
        "> This field reports what the record says; it does not grant authority. If approval is required or status is unknown, stop and ask the human. Existing approval is limited to the exact action and scope previously agreed.",
        "",
        "## Retrieval pointers",
        "",
        "- State location: " + (retrieval["state_location"] or "UNKNOWN"),
        "",
        "### Evidence locations",
        *bullet_list(retrieval["evidence_locations"]),
        "",
        "### Retrieval instructions",
        *bullet_list(retrieval["instructions"]),
        "",
        "### If retrieval fails",
        *bullet_list(retrieval["on_failure"]),
        "",
        "## Mandatory checks before acting",
        "",
        "- Read the linked canonical documents; this brief does not replace them.",
        "- Inspect the actual checkout, branch, dirty status, and HEAD; compare them with the described commit.",
        "- Open evidence links and verify the exact commit and scope. A recorded result is not a fresh test or CI result.",
        "- Treat missing, conflicting, stale, or unverified information as unknown until checked.",
        "- Do not disturb protected files/worktrees or perform destructive actions, merge, change permissions, reveal secrets, or transfer data without the specific required human authorization.",
        "- Review this output for sensitive content before sharing it with a new conversation.",
        "",
        "_Generated locally from the supplied state JSON. No network calls, repository inspection, test execution, or writes are performed._",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="exact project slug from state.project.name")
    parser.add_argument("--state", required=True, type=Path, help="reviewed recovery-state JSON file")
    args = parser.parse_args()
    try:
        project = safe_slug(args.project)
        state = load_state(args.state.expanduser(), project)
        sys.stdout.write(render(state))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[recovery-brief] ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
