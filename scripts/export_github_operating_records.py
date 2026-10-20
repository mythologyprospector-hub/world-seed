#!/usr/bin/env python3
"""Export selected GitHub operating records to private local recovery storage.

This is a read-only metadata/content export. It never downloads release assets or
Actions artifact binaries, and it explicitly records inaccessible endpoints.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from private_report import write_private_json

API_ROOT = "https://api.github.com"
PAGE_SIZE = 100
MAX_PAGES = 10000


def _token() -> str | None:
    """Read an existing token from the environment or GitHub CLI without printing it."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token.strip() or None
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], check=False, capture_output=True,
            text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def _get(path: str, token: str):
    """Read one GitHub API resource; never perform writes."""
    request = Request(API_ROOT + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "world-seed-read-only-recovery-exporter",
    })
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def _collection(path: str, token: str, key: str | None = None) -> list[dict]:
    """Collect all pages, failing closed on malformed or incomplete pagination."""
    collected: list[dict] = []
    for page in range(1, MAX_PAGES + 1):
        separator = "&" if "?" in path else "?"
        payload = _get(f"{path}{separator}{urlencode({'per_page': PAGE_SIZE, 'page': page})}", token)
        if key is not None:
            if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
                raise ValueError(f"unexpected collection shape for {path}")
            items = payload[key]
        else:
            items = payload
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ValueError(f"unexpected page shape for {path}")
        collected.extend(items)
        if len(items) < PAGE_SIZE:
            return collected
    raise ValueError(f"pagination safety limit reached for {path}")


def _capture(label: str, operation) -> dict:
    """Capture a collection or report a bounded failure without claiming absence."""
    try:
        records = operation()
        return {"status": "captured", "count": len(records), "records": records, "reason": None}
    except HTTPError as exc:
        return {
            "status": "not-found-or-not-visible" if exc.code == 404 else "blocked",
            "count": None, "records": None,
            "reason": "not-found-or-not-visible" if exc.code == 404 else f"http-{exc.code}",
        }
    except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "blocked", "count": None, "records": None, "reason": type(exc).__name__}


def _append_manifest(path: Path, row: str) -> None:
    """Append one private TSV row, refusing symlinks and restricting permissions."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as stream:
            fd = -1
            if path.stat().st_size == 0:
                stream.write("repository\tfile\tresult\tendpoint_status\n")
            stream.write(row + "\n")
    finally:
        if fd >= 0:
            os.close(fd)


def export_repository(repository: str, token: str) -> dict:
    """Export supported records for one explicitly named repository."""
    if repository.count("/") != 1 or any(not part for part in repository.split("/")):
        raise ValueError("repository must be OWNER/REPOSITORY")
    owner, name = repository.split("/")
    encoded = f"{quote(owner, safe='')}/{quote(name, safe='')}"
    base = f"/repos/{encoded}"
    endpoints = {
        "issues_including_pull_request_issue_records": lambda: _collection(
            base + "/issues?state=all", token
        ),
        "issue_and_pull_request_conversation_comments": lambda: _collection(
            base + "/issues/comments", token
        ),
        "pull_requests": lambda: _collection(base + "/pulls?state=all", token),
        "releases_and_asset_metadata": lambda: _collection(base + "/releases", token),
    }
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository_requested": repository,
        "scope": "single repository; current identity's API-visible records only",
        "endpoints": {},
        "pull_request_reviews_and_inline_comments": {
            "status": "not-attempted", "count": None, "records": [], "reason": None
        },
        "workflow_runs_and_artifact_metadata": {
            "status": "not-attempted", "count": None, "records": None, "reason": None
        },
        "binary_content": {
            "actions_artifacts": "not-downloaded",
            "release_assets": "not-downloaded",
            "discussions": "not-attempted",
            "note": "Metadata capture does not preserve binary contents or prove full operating-record coverage."
        },
        "coverage_status": "unverified",
    }

    report["endpoints"]["repository_metadata"] = _capture(
        "repository_metadata", lambda: [_get(base, token)]
    )
    for label, operation in endpoints.items():
        report["endpoints"][label] = _capture(label, operation)

    pulls = report["endpoints"]["pull_requests"]
    if pulls["status"] == "captured":
        details = []
        failures = 0
        for pull in pulls["records"]:
            number = pull.get("number")
            if not isinstance(number, int):
                failures += 1
                details.append({"number": None, "status": "blocked", "reason": "pull-number-unavailable"})
                continue
            reviews = _capture(
                f"pull-{number}-reviews",
                lambda number=number: _collection(f"{base}/pulls/{number}/reviews", token),
            )
            comments = _capture(
                f"pull-{number}-inline-comments",
                lambda number=number: _collection(f"{base}/pulls/{number}/comments", token),
            )
            if reviews["status"] != "captured" or comments["status"] != "captured":
                failures += 1
            details.append({"number": number, "reviews": reviews, "inline_comments": comments})
        report["pull_request_reviews_and_inline_comments"] = {
            "status": "captured" if failures == 0 else "partial",
            "count": len(details), "records": details,
            "reason": None if failures == 0 else f"{failures} pull request review/comment collection(s) incomplete",
        }
    else:
        report["pull_request_reviews_and_inline_comments"] = {
            "status": "blocked", "count": None, "records": None,
            "reason": "pull-request-list-not-available"
        }

    runs = _capture(
        "workflow_runs",
        lambda: _collection(base + "/actions/runs", token, key="workflow_runs"),
    )
    if runs["status"] == "captured":
        run_details = []
        failures = 0
        for run in runs["records"]:
            run_id = run.get("id")
            if not isinstance(run_id, int):
                failures += 1
                run_details.append({"id": None, "status": "blocked", "reason": "run-id-unavailable"})
                continue
            artifacts = _capture(
                f"run-{run_id}-artifacts",
                lambda run_id=run_id: _collection(f"{base}/actions/runs/{run_id}/artifacts", token, key="artifacts"),
            )
            if artifacts["status"] != "captured":
                failures += 1
            run_details.append({"run": run, "artifacts": artifacts})
        report["workflow_runs_and_artifact_metadata"] = {
            "status": "captured" if failures == 0 else "partial",
            "count": len(run_details), "records": run_details,
            "reason": None if failures == 0 else f"{failures} workflow run artifact collection(s) incomplete",
        }
    else:
        report["workflow_runs_and_artifact_metadata"] = runs

    statuses = [item["status"] for item in report["endpoints"].values()]
    statuses += [
        report["pull_request_reviews_and_inline_comments"]["status"],
        report["workflow_runs_and_artifact_metadata"]["status"],
    ]
    if all(status == "captured" for status in statuses):
        report["coverage_status"] = "partial"
        report["coverage_note"] = (
            "All implemented endpoints were captured, but discussions and binary artifact/release contents "
            "were not captured. This is not a complete GitHub operating-record backup."
        )
    elif any(status == "captured" for status in statuses):
        report["coverage_status"] = "partial"
        report["coverage_note"] = "One or more endpoints were blocked or incomplete; review every status and reason."
    else:
        report["coverage_status"] = "unverified"
        report["coverage_note"] = "No endpoint collection succeeded; no coverage is established."
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="One repository as OWNER/REPOSITORY")
    parser.add_argument("--output-dir", required=True, type=Path, help="Private recovery directory outside the seed checkout")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    requested_output_dir = args.output_dir.expanduser()
    if requested_output_dir.is_symlink():
        parser.error("output directory must not be a symlink")
    output_dir = requested_output_dir.resolve()
    if output_dir == root or root in output_dir.parents:
        parser.error("output directory must be outside the public world-seed checkout")
    token = _token()
    if not token:
        print("BLOCKED: set GH_TOKEN/GITHUB_TOKEN or authenticate GitHub CLI with gh auth login.", file=sys.stderr)
        return 2
    try:
        output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if hasattr(output_dir, "chmod"):
            output_dir.chmod(0o700)
        report = export_repository(args.repository, token)
        safe_name = args.repository.replace("/", "__")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = output_dir / f"operating-records-{safe_name}-{stamp}.json"
        write_private_json(output, report)
        endpoint_statuses = [item["status"] for item in report["endpoints"].values()]
        endpoint_statuses += [
            report["pull_request_reviews_and_inline_comments"]["status"],
            report["workflow_runs_and_artifact_metadata"]["status"],
        ]
        result = "OK" if all(status == "captured" for status in endpoint_statuses) else "PARTIAL"
        manifest = output_dir / "manifest.tsv"
        _append_manifest(manifest, f"{args.repository}\t{output.name}\t{result}\t{report['coverage_status']}")
    except (OSError, ValueError) as exc:
        print(f"BLOCKED: operating-record export failed ({type(exc).__name__}); no complete export is implied.", file=sys.stderr)
        return 2
    print(f"Operating-record metadata export: {report['coverage_status']}")
    print(f"Private report: {output}")
    print("Binary artifacts, release assets, and discussions are not fully captured; review the manifest and report.")
    return 0 if result == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
