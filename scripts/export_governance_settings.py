#!/usr/bin/env python3
"""Export readable GitHub branch-protection and ruleset payloads to private storage.

This is an export-only collector. It never changes GitHub settings and never exports
credentials or secrets. A successful export is evidence of visibility, not proof that
all effective governance has been captured or can be restored.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
PAGE_SIZE = 100
MAX_PAGES = 100


def api_get(path: str, token: str):
    request = Request(
        API_ROOT + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "world-seed-governance-recovery-exporter",
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def read_endpoint(path: str, token: str) -> dict:
    try:
        return {"status": "captured", "data": api_get(path, token), "endpoint": path}
    except HTTPError as exc:
        if exc.code == 404:
            return {
                "status": "not-reported",
                "http_status": 404,
                "endpoint": path,
                "evidence": "GitHub returned 404; this is not proof of effective absence.",
            }
        if exc.code in {401, 403}:
            return {
                "status": "unverified",
                "http_status": exc.code,
                "endpoint": path,
                "evidence": "The current identity could not read this endpoint.",
            }
        return {
            "status": "error",
            "http_status": exc.code,
            "endpoint": path,
            "evidence": "GitHub rejected the request; no absence claim is possible.",
        }
    except (URLError, TimeoutError, OSError, ValueError):
        return {
            "status": "error",
            "endpoint": path,
            "evidence": "The request failed; no absence claim is possible.",
        }


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "record"


def capture_rulesets(owner_path: str, list_path: str, token: str) -> dict:
    items = []
    page = 1
    while page <= MAX_PAGES:
        path = f"{list_path}?per_page={PAGE_SIZE}&page={page}"
        result = read_endpoint(path, token)
        if result["status"] != "captured":
            return {
                "status": result["status"],
                "endpoint": list_path,
                "rulesets": items,
                "error": {key: value for key, value in result.items() if key != "data"},
            }
        batch = result["data"]
        if not isinstance(batch, list):
            return {
                "status": "error",
                "endpoint": list_path,
                "rulesets": items,
                "evidence": "Unexpected ruleset-list response shape.",
            }
        items.extend(item for item in batch if isinstance(item, dict))
        if len(batch) < PAGE_SIZE:
            break
        page += 1
    else:
        return {
            "status": "error",
            "endpoint": list_path,
            "rulesets": items,
            "evidence": f"Pagination exceeded safety limit ({MAX_PAGES} pages).",
        }

    detailed = []
    detail_failures = []
    for item in items:
        ruleset_id = item.get("id")
        if ruleset_id is None:
            detail_failures.append({"id": None, "status": "error", "evidence": "Listed ruleset had no ID."})
            continue
        detail_path = f"{owner_path}/{ruleset_id}"
        detail = read_endpoint(detail_path, token)
        detailed.append({
            "id": ruleset_id,
            "list_record": item,
            "detail": detail,
        })
        if detail["status"] != "captured":
            detail_failures.append({"id": ruleset_id, "status": detail["status"]})
    return {
        "status": "captured" if not detail_failures else "partial",
        "endpoint": list_path,
        "listed_count": len(items),
        "captured_detail_count": sum(item["detail"]["status"] == "captured" for item in detailed),
        "rulesets": detailed,
        "detail_failures": detail_failures,
    }


def export_governance(repository: str, token: str) -> dict:
    metadata_result = read_endpoint(f"/repos/{repository}", token)
    if metadata_result["status"] != "captured":
        return {
            "schema_version": 1,
            "repository": repository,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": "unverified",
            "repository_metadata": metadata_result,
            "controls": {},
            "note": "Repository metadata was not readable; applicable governance could not be discovered.",
        }

    metadata = metadata_result["data"]
    default_branch = metadata.get("default_branch")
    controls = {
        "repository_metadata": metadata_result,
        "classic_default_branch_protection": (
            read_endpoint(f"/repos/{repository}/branches/{default_branch}/protection", token)
            if default_branch else {
                "status": "unverified",
                "evidence": "Default branch is unknown; classic protection was not queried.",
            }
        ),
        "repository_rulesets": capture_rulesets(
            f"/repos/{repository}/rulesets",
            f"/repos/{repository}/rulesets",
            token,
        ),
    }

    owner = repository.split("/", 1)[0]
    owner_result = read_endpoint(f"/users/{owner}", token)
    controls["owner_metadata"] = owner_result
    if owner_result["status"] == "captured" and owner_result["data"].get("type") == "Organization":
        controls["organization_rulesets"] = capture_rulesets(
            f"/orgs/{owner}/rulesets",
            f"/orgs/{owner}/rulesets",
            token,
        )
    elif owner_result["status"] == "captured":
        controls["organization_rulesets"] = {
            "status": "not-applicable",
            "evidence": "Repository owner is not an organization.",
        }
    else:
        controls["organization_rulesets"] = {
            "status": "unverified",
            "evidence": "Owner type could not be established; organization rulesets were not inferred absent.",
        }

    statuses = [value.get("status", "unverified") for value in controls.values()]
    overall = "captured" if all(status in {"captured", "not-applicable"} for status in statuses) else "partial"
    return {
        "schema_version": 1,
        "repository": repository,
        "default_branch": default_branch,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall,
        "controls": controls,
        "interpretation": (
            "This export preserves readable API payloads. It does not establish effective enforcement, "
            "capture every GitHub governance surface, or prove restoration. Review every status and run "
            "an isolated recovery drill before claiming governance recovery is verified."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="Repository in OWNER/NAME form")
    parser.add_argument("--output-dir", required=True, type=Path, help="Private directory outside the seed checkout")
    args = parser.parse_args(argv)
    if args.repository.count("/") != 1 or not all(args.repository.split("/", 1)):
        parser.error("--repository must be OWNER/NAME")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("BLOCKED: set GH_TOKEN or GITHUB_TOKEN in the environment; never pass tokens as arguments.", file=sys.stderr)
        return 2

    output_dir = args.output_dir.expanduser().resolve()
    seed_root = Path(__file__).resolve().parents[1]
    if output_dir == seed_root or seed_root in output_dir.parents:
        print("BLOCKED: export directory must be outside the world-seed repository.", file=sys.stderr)
        return 2
    try:
        output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            output_dir.chmod(0o700)
        except OSError:
            pass
        report = export_governance(args.repository, token)
        output = output_dir / f"governance-{safe_name(args.repository)}.json"
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        try:
            output.chmod(0o600)
        except OSError:
            pass
    except (OSError, RuntimeError) as exc:
        print(f"BLOCKED: export failed ({type(exc).__name__}); inspect local storage permissions.", file=sys.stderr)
        return 2
    print(f"Governance export written to private local storage: {output}")
    print(f"Export status: {report['overall_status']}. Review every control status; this is not a restore certification.")
    return 0 if report["overall_status"] == "captured" else 1


if __name__ == "__main__":
    raise SystemExit(main())
