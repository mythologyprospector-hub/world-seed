#!/usr/bin/env python3
"""Report which recovery-backup categories have evidence in a local handoff directory.

This is an evidence inventory, not a recovery certification. It never reads credential
files or sends backup contents anywhere.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def audit_backup_coverage(root: Path) -> dict:
    root = root.expanduser().resolve()
    manifest = root / "manifest.tsv"
    manifest_exists = manifest.is_file()
    lines = manifest.read_text(encoding="utf-8").splitlines() if manifest_exists else []
    rows = [line.split("\t") for line in lines[1:] if line.strip()]
    repo_rows = [row for row in rows if len(row) >= 4]
    source_ok = sum(row[3] == "OK" for row in repo_rows)
    source_failed = sum(row[3] != "OK" for row in repo_rows)
    bundles = list((root / "bundles").glob("*.bundle")) if (root / "bundles").is_dir() else []
    zips = list((root / "zips").glob("*.zip")) if (root / "zips").is_dir() else []
    checkouts = list((root / "checkouts").iterdir()) if (root / "checkouts").is_dir() else []
    records_root = root / "records"
    records_manifest = records_root / "manifest.tsv"
    record_lines = records_manifest.read_text(encoding="utf-8").splitlines() if records_manifest.is_file() else []
    record_rows = [line.split("\t") for line in record_lines[1:] if line.strip()]
    record_ok = sum(len(row) >= 3 and row[2] == "OK" for row in record_rows)
    record_failed = sum(len(row) >= 3 and row[2] != "OK" for row in record_rows)

    categories = {
        "repository_inventory": {
            "status": "present" if manifest_exists else "missing",
            "evidence": "manifest.tsv",
            "repository_rows": len(repo_rows),
        },
        "git_source_and_history": {
            "status": "partial" if source_ok and (source_failed or not bundles or not zips) else ("present" if source_ok else "missing"),
            "evidence": "checkouts/, bundles/, zips/, manifest.tsv",
            "repository_rows_ok": source_ok,
            "repository_rows_failed": source_failed,
            "bundle_count": len(bundles),
            "source_zip_count": len(zips),
            "checkout_count": len(checkouts),
        },
        "issues_pull_requests_comments_reviews_releases_actions_metadata": {
            "status": "partial" if record_ok else "unverified",
            "evidence": "records/manifest.tsv" if records_manifest.is_file() else None,
            "endpoint_exports_ok": record_ok,
            "endpoint_exports_failed": record_failed,
        },
        "actions_binary_artifact_contents": {"status": "unverified", "evidence": None},
        "release_asset_contents": {"status": "unverified", "evidence": None},
        "repository_and_organization_settings_permissions": {"status": "unverified", "evidence": None},
        "discussions_webhooks_environments_and_other_operating_records": {"status": "unverified", "evidence": None},
        "secrets_and_credentials": {
            "status": "excluded-by-design",
            "evidence": "Recreate or rotate through approved secure procedures; never store in this backup",
        },
        "isolated_recovery_drill": {"status": "not-tested", "evidence": None},
    }
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "backup_root": str(root),
        "overall_status": "incomplete-unverified",
        "categories": categories,
        "note": (
            "Presence of files or successful API responses is not proof of integrity, completeness, "
            "or successful restoration. Verify record counts, hashes, access coverage, and an isolated "
            "recovery drill before declaring the backup ready."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    root = args.backup_dir.expanduser().resolve()
    if output == root or root in output.parents:
        parser.error("coverage report must be written outside the backup directory being inspected")
    report = audit_backup_coverage(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    try:
        output.chmod(0o600)
    except OSError:
        pass
    print(f"Backup coverage: {report['overall_status']}")
    print(f"Report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
