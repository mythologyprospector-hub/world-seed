#!/usr/bin/env python3
"""Read-only inspection of default-branch protection and rulesets.

This collector never changes GitHub settings. Reports can contain private repository
names and governance details; keep them outside public repositories.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from private_report import write_private_json

API_ROOT = "https://api.github.com"
PAGE_SIZE = 100
MAX_PAGES = 100


def api_get(path: str, token: str):
    """GET GitHub API JSON without logging credentials or response bodies."""
    request = Request(
        API_ROOT + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "world-seed-read-only-auditor",
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def _read_control(path: str, token: str, *, absent_status: str = "unknown") -> dict:
    """Represent endpoint access truthfully; never turn an access error into absence."""
    try:
        payload = api_get(path, token)
    except HTTPError as exc:
        if exc.code == 404 and absent_status != "unknown":
            return {"status": absent_status, "evidence": "GitHub returned HTTP 404 for the settings endpoint."}
        if exc.code in {401, 403, 404}:
            return {
                "status": "unverified",
                "http_status": exc.code,
                "evidence": "Settings could not be verified with the current identity/endpoint.",
            }
        return {"status": "error", "http_status": exc.code, "evidence": "GitHub settings request failed."}
    except (URLError, TimeoutError, OSError, ValueError):
        return {"status": "error", "evidence": "Settings request failed; no absence claim is possible."}
    return {"status": "observed", "data": payload}


def inspect_branch_safeguards(full_name: str, default_branch: str | None, token: str) -> dict:
    """Inspect visible branch protection and rulesets for one repository."""
    result = {
        "repository": full_name,
        "default_branch": default_branch,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "classic_branch_protection": {"status": "unverified", "evidence": "Default branch is unknown."},
        "repository_rulesets": {"status": "unverified", "evidence": "Repository settings were not inspected."},
        "organization_rulesets": {"status": "unverified", "evidence": "Owner type and organization policy were not verified."},
        "interpretation": "No conclusion about effective protection until all applicable controls are inspected.",
    }
    if not default_branch:
        return result

    branch_path = f"/repos/{full_name}/branches/{default_branch}/protection"
    classic = _read_control(branch_path, token, absent_status="not-reported")
    if classic["status"] == "observed":
        payload = classic.pop("data")
        classic["configured"] = True
        classic["required_status_checks"] = payload.get("required_status_checks")
        classic["required_pull_request_reviews"] = payload.get("required_pull_request_reviews")
        classic["restrictions_present"] = bool(payload.get("restrictions"))
        classic["enforce_admins"] = payload.get("enforce_admins")
        classic["allow_force_pushes"] = payload.get("allow_force_pushes")
        classic["allow_deletions"] = payload.get("allow_deletions")
        classic["required_conversation_resolution"] = payload.get("required_conversation_resolution")
    elif classic["status"] == "not-reported":
        classic["evidence"] = "GitHub returned 404 for classic protection; verify this interpretation against rulesets and UI/API permissions."
    result["classic_branch_protection"] = classic

    rulesets = []
    blocked = []
    for page in range(1, MAX_PAGES + 1):
        try:
            batch = api_get(f"/repos/{full_name}/rulesets?per_page={PAGE_SIZE}&page={page}", token)
        except HTTPError as exc:
            blocked.append({"status": "unverified", "http_status": exc.code, "evidence": "Repository rulesets could not be read."})
            break
        except (URLError, TimeoutError, OSError, ValueError):
            blocked.append({"status": "error", "evidence": "Repository rulesets request failed."})
            break
        if not isinstance(batch, list):
            blocked.append({"status": "error", "evidence": "Unexpected rulesets response shape."})
            break
        rulesets.extend({
            "id": item.get("id"),
            "name": item.get("name"),
            "target": item.get("target"),
            "enforcement": item.get("enforcement"),
            "conditions": item.get("conditions"),
            "bypass_actors": item.get("bypass_actors"),
        } for item in batch if isinstance(item, dict))
        if len(batch) < PAGE_SIZE:
            break
    else:
        blocked.append({"status": "error", "evidence": f"Ruleset pagination exceeded safety limit ({MAX_PAGES} pages)."})
    if blocked:
        result["repository_rulesets"] = {"status": "unverified", "rulesets_observed": rulesets, "errors": blocked}
    else:
        result["repository_rulesets"] = {"status": "observed", "count": len(rulesets), "rulesets": rulesets}

    # The owner type is queried rather than inferred from a repository name.
    owner = full_name.split("/", 1)[0]
    owner_meta = _read_control(f"/users/{owner}", token)
    if owner_meta["status"] == "observed":
        owner_data = owner_meta.pop("data")
        if owner_data.get("type") == "Organization":
            org_result = _read_control(f"/orgs/{owner}/rulesets?per_page={PAGE_SIZE}&page=1", token)
            if org_result["status"] == "observed":
                payload = org_result.pop("data")
                if isinstance(payload, list):
                    result["organization_rulesets"] = {
                        "status": "observed",
                        "count": len(payload),
                        "rulesets": [{
                            "id": item.get("id"),
                            "name": item.get("name"),
                            "target": item.get("target"),
                            "enforcement": item.get("enforcement"),
                            "conditions": item.get("conditions"),
                            "bypass_actors": item.get("bypass_actors"),
                        } for item in payload if isinstance(item, dict)],
                    }
                else:
                    result["organization_rulesets"] = {"status": "error", "evidence": "Unexpected organization rulesets response shape."}
            else:
                result["organization_rulesets"] = org_result
        else:
            result["organization_rulesets"] = {"status": "not-applicable", "evidence": "Repository owner is not an organization."}
    else:
        result["organization_rulesets"] = {"status": "unverified", "evidence": "Could not establish owner type, so organization rulesets were not inferred absent."}

    statuses = [
        result["classic_branch_protection"]["status"],
        result["repository_rulesets"]["status"],
        result["organization_rulesets"]["status"],
    ]
    if any(status in {"unverified", "error"} for status in statuses):
        result["interpretation"] = "Coverage is partial: at least one applicable control could not be verified."
    elif result["classic_branch_protection"]["status"] == "not-reported" and result["repository_rulesets"].get("count") == 0:
        result["interpretation"] = "No classic protection or repository rulesets were reported by the inspected endpoints; verify any applicable organization rulesets and review the GitHub settings UI before claiming the branch is unprotected."
    else:
        result["interpretation"] = "Settings endpoints were readable; review the returned rules and bypass actors to determine effective protection."
    return result


def main(argv: list[str] | None = None) -> int:
    """Write one repository's read-only safeguard report to private local storage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="Repository in OWNER/NAME form")
    parser.add_argument("--output", required=True, type=Path, help="Private local report path outside this repository")
    args = parser.parse_args(argv)
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("BLOCKED: set GH_TOKEN or GITHUB_TOKEN in the environment; do not pass tokens as arguments.", file=sys.stderr)
        return 2
    if args.repository.count("/") != 1 or not all(args.repository.split("/", 1)):
        print("BLOCKED: --repository must be OWNER/NAME.", file=sys.stderr)
        return 2
    output = args.output.expanduser().resolve()
    seed_root = Path(__file__).resolve().parents[1]
    if output == seed_root or seed_root in output.parents:
        print("BLOCKED: report output must remain outside the public world-seed repository.", file=sys.stderr)
        return 2
    try:
        metadata = api_get(f"/repos/{args.repository}", token)
        report = inspect_branch_safeguards(args.repository, metadata.get("default_branch"), token)
        output.parent.mkdir(parents=True, exist_ok=True)
        write_private_json(output, report)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        print(f"BLOCKED: safeguard inspection failed ({type(exc).__name__}); no absence claim is possible.", file=sys.stderr)
        return 2
    statuses = [
        report["classic_branch_protection"]["status"],
        report["repository_rulesets"]["status"],
        report["organization_rulesets"]["status"],
    ]
    print(f"Safeguard report written to the chosen local path. Endpoint statuses: {', '.join(statuses)}.")
    print("Read the report's interpretation and evidence; unverified settings are not proof that safeguards are absent.")
    return 0 if not any(status in {"unverified", "error"} for status in statuses) else 1


if __name__ == "__main__":
    raise SystemExit(main())
