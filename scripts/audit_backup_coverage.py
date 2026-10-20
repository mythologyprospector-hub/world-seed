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

from private_report import write_private_json


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
    checkouts = [
        path for path in (root / "checkouts").iterdir()
        if path.is_dir()
    ] if (root / "checkouts").is_dir() else []

    # The backup collector names artifacts by repository basename. If two owners
    # have repositories with the same basename, filenames alone cannot prove
    # which repository an artifact belongs to; report that ambiguity conservatively.
    expected_repositories = sorted({row[0] for row in repo_rows if row and "/" in row[0]})
    repository_basenames = {
        repository: repository.rsplit("/", 1)[1]
        for repository in expected_repositories
    }
    basename_counts: dict[str, int] = {}
    for basename in repository_basenames.values():
        basename_counts[basename] = basename_counts.get(basename, 0) + 1
    ambiguous_basenames = sorted(
        basename for basename, count in basename_counts.items() if count > 1
    )
    bundle_stems = {path.name[:-len(".bundle")] for path in bundles}
    zip_stems = {path.name[:-len(".zip")] for path in zips}
    checkout_names = {path.name for path in checkouts}
    missing_bundles = sorted(
        repository for repository, basename in repository_basenames.items()
        if basename not in bundle_stems
    )
    missing_zips = sorted(
        repository for repository, basename in repository_basenames.items()
        if basename not in zip_stems
    )
    missing_checkouts = sorted(
        repository for repository, basename in repository_basenames.items()
        if basename not in checkout_names
    )
    ambiguous_repositories = sorted(
        repository for repository, basename in repository_basenames.items()
        if basename in ambiguous_basenames
    )
    source_artifacts_complete = (
        bool(expected_repositories)
        and source_failed == 0
        and not missing_bundles
        and not missing_zips
        and not missing_checkouts
        and not ambiguous_repositories
    )
    if not repo_rows:
        source_status = "missing"
    elif source_artifacts_complete:
        source_status = "present"
    else:
        source_status = "partial"
    records_root = root / "records"
    records_manifest = records_root / "manifest.tsv"
    record_lines = records_manifest.read_text(encoding="utf-8").splitlines() if records_manifest.is_file() else []
    record_rows = [line.split("\t") for line in record_lines[1:] if line.strip()]
    record_ok = sum(len(row) >= 3 and row[2] == "OK" for row in record_rows)
    record_failed = sum(len(row) >= 3 and row[2] != "OK" for row in record_rows)
    governance_dir = records_root / "governance"
    governance_files = sorted(governance_dir.glob("governance-*.json")) if governance_dir.is_dir() else []
    governance_statuses = []
    governance_invalid = []
    governance_repositories = []
    for governance_file in governance_files:
        try:
            payload = json.loads(governance_file.read_text(encoding="utf-8"))
            status = payload.get("overall_status")
            repository_name = payload.get("repository")
            if isinstance(repository_name, str) and repository_name:
                governance_repositories.append(repository_name)
            if status not in {"captured", "partial", "unverified"}:
                governance_invalid.append(governance_file.name)
            else:
                governance_statuses.append(status)
        except (OSError, ValueError, AttributeError):
            governance_invalid.append(governance_file.name)
    expected_repositories = {row[0] for row in repo_rows if row and "/" in row[0]}
    exported_repositories = set(governance_repositories)
    missing_governance_repositories = sorted(expected_repositories - exported_repositories)
    unexpected_governance_repositories = sorted(exported_repositories - expected_repositories)
    if not governance_files:
        governance_status = "unverified"
    elif (
        governance_invalid
        or any(status != "captured" for status in governance_statuses)
        or not expected_repositories
        or missing_governance_repositories
        or unexpected_governance_repositories
    ):
        governance_status = "partial"
    else:
        governance_status = "present"

    categories = {
        "repository_inventory": {
            "status": "present" if manifest_exists else "missing",
            "evidence": "manifest.tsv",
            "repository_rows": len(repo_rows),
        },
        "git_source_and_history": {
            "status": source_status,
            "evidence": "checkouts/, bundles/, zips/, manifest.tsv",
            "repository_rows_ok": source_ok,
            "repository_rows_failed": source_failed,
            "expected_repository_count": len(expected_repositories),
            "missing_bundle_repositories": missing_bundles,
            "missing_source_zip_repositories": missing_zips,
            "missing_checkout_repositories": missing_checkouts,
            "ambiguous_repository_basenames": ambiguous_basenames,
            "repositories_with_ambiguous_artifact_identity": ambiguous_repositories,
            "bundle_count": len(bundles),
            "source_zip_count": len(zips),
            "checkout_count": len(checkouts),
            "note": "Artifact names are matched to manifest repository basenames; duplicate basenames are ambiguous. Bundle/ZIP integrity and restoration are not tested here.",
        },
        "issues_pull_requests_comments_reviews_releases_actions_metadata": {
            "status": "partial" if (record_ok or record_failed) else "unverified",
            "evidence": "records/manifest.tsv" if records_manifest.is_file() else None,
            "endpoint_exports_ok": record_ok,
            "endpoint_exports_failed": record_failed,
        },
        "actions_binary_artifact_contents": {"status": "unverified", "evidence": None},
        "release_asset_contents": {"status": "unverified", "evidence": None},
        "branch_protection_and_ruleset_exports": {
            "status": governance_status,
            "evidence": "records/governance/governance-*.json" if governance_files else None,
            "export_count": len(governance_files),
            "invalid_or_unrecognized_exports": governance_invalid,
            "export_statuses": governance_statuses,
            "expected_repository_count": len(expected_repositories),
            "missing_repositories": missing_governance_repositories,
            "unexpected_repositories": unexpected_governance_repositories,
            "note": "A present status requires one captured export per repository in manifest.tsv; exports are not proof of restoration or effective enforcement.",
        },
        "repository_and_organization_settings_permissions": {
            "status": "partial" if governance_status == "present" else "unverified",
            "evidence": "Governance exports cover classic default-branch protection and repository/organization rulesets only; other settings, permissions, environments, and webhooks remain uncovered.",
        },
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
    requested_output = args.output.expanduser()
    if requested_output.is_symlink():
        parser.error("coverage report output must not be a symlink")
    output = requested_output.resolve()
    root = args.backup_dir.expanduser().resolve()
    seed_root = Path(__file__).resolve().parents[1]
    if output == seed_root or seed_root in output.parents:
        parser.error("coverage report must be written outside the public world-seed checkout")
    if output == root or root in output.parents:
        parser.error("coverage report must be written outside the backup directory being inspected")
    report = audit_backup_coverage(root)
    write_private_json(output, report)
    print(f"Backup coverage: {report['overall_status']}")
    print(f"Report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
