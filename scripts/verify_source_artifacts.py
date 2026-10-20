#!/usr/bin/env python3
"""Verify Git bundle readability and ZIP integrity without modifying backup artifacts.

This is a local integrity check, not proof that all GitHub metadata is preserved
or that the complete account can be restored.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from private_report import write_private_json


def _run(command: list[str], timeout: int = 60) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=False, timeout=timeout
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, type(exc).__name__
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode == 0, output[-4000:]


def verify_source_artifacts(root: Path) -> dict:
    root = root.expanduser().resolve()
    manifest = root / "manifest.tsv"
    rows: list[dict] = []
    errors: list[str] = []
    if not manifest.is_file():
        return {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": "blocked",
            "repository_results": [],
            "errors": ["manifest.tsv is missing"],
            "note": "No source-artifact verification was possible.",
        }

    lines = manifest.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].split("\t")[:4] != ["owner", "visibility", "archived", "result"]:
        return {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": "blocked",
            "repository_results": [],
            "errors": ["manifest.tsv has an unrecognized header"],
            "note": "No source-artifact verification was possible.",
        }

    parsed = []
    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) < 4 or fields[0].count("/") != 1 or any(not part for part in fields[0].split("/")):
            errors.append(f"manifest line {line_number} is malformed")
            continue
        parsed.append({
            "repository": fields[0],
            "visibility": fields[1],
            "archived": fields[2],
            "manifest_result": fields[3],
        })

    names = [item["repository"] for item in parsed]
    basenames = {name: name.rsplit("/", 1)[1] for name in names}
    counts: dict[str, int] = {}
    for basename in basenames.values():
        counts[basename] = counts.get(basename, 0) + 1

    for item in parsed:
        repository = item["repository"]
        basename = basenames[repository]
        result = {
            **item,
            "status": "unverified",
            "bundle": {"status": "not-checked"},
            "source_zip": {"status": "not-checked"},
            "checkout": {"status": "not-checked"},
        }
        if counts[basename] > 1:
            result["status"] = "ambiguous"
            result["bundle"] = {"status": "ambiguous", "reason": "duplicate repository basename"}
            result["source_zip"] = {"status": "ambiguous", "reason": "duplicate repository basename"}
            result["checkout"] = {"status": "ambiguous", "reason": "duplicate repository basename"}
            rows.append(result)
            continue
        if item["manifest_result"] != "OK":
            result["status"] = "manifest-failed"
            result["bundle"] = {"status": "not-checked", "reason": "manifest result is not OK"}
            result["source_zip"] = {"status": "not-checked", "reason": "manifest result is not OK"}
            result["checkout"] = {"status": "not-checked", "reason": "manifest result is not OK"}
            rows.append(result)
            continue

        bundle = root / "bundles" / f"{basename}.bundle"
        if not bundle.is_file() or bundle.is_symlink():
            result["bundle"] = {"status": "missing-or-unsafe"}
        else:
            with tempfile.TemporaryDirectory(prefix="world-seed-bundle-verify-") as temp:
                clone = Path(temp) / "mirror.git"
                ok, output = _run(["git", "clone", "--mirror", "--", str(bundle), str(clone)])
                result["bundle"] = {
                    "status": "verified" if ok else "invalid",
                    "detail": output,
                }
                if ok:
                    heads_ok, heads = _run(["git", "--git-dir", str(clone), "show-ref"])
                    result["bundle"]["has_refs"] = heads_ok
                    result["bundle"]["refs_detail"] = heads
                    if not heads_ok:
                        result["bundle"]["status"] = "invalid"

        source_zip = root / "zips" / f"{basename}.zip"
        if not source_zip.is_file() or source_zip.is_symlink():
            result["source_zip"] = {"status": "missing-or-unsafe"}
        else:
            try:
                with zipfile.ZipFile(source_zip) as archive:
                    bad_member = archive.testzip()
                    names_in_zip = archive.namelist()
                    zip_ok = bad_member is None and bool(names_in_zip)
                    result["source_zip"] = {
                        "status": "verified" if zip_ok else "invalid",
                        "member_count": len(names_in_zip),
                        "bad_member": bad_member,
                    }
            except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
                result["source_zip"] = {"status": "invalid", "reason": type(exc).__name__}

        checkout = root / "checkouts" / basename
        if not checkout.is_dir() or checkout.is_symlink():
            result["checkout"] = {"status": "missing-or-unsafe"}
        else:
            ok, output = _run(["git", "-C", str(checkout), "rev-parse", "--is-inside-work-tree"])
            result["checkout"] = {
                "status": "verified" if ok and output.splitlines()[0:1] == ["true"] else "invalid",
                "detail": output,
            }

        checks = [result["bundle"]["status"], result["source_zip"]["status"], result["checkout"]["status"]]
        result["status"] = "verified" if all(status == "verified" for status in checks) else "partial"
        rows.append(result)

    all_verified = bool(rows) and not errors and all(row["status"] == "verified" for row in rows)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": "source-artifacts-verified" if all_verified else ("partial" if rows else "blocked"),
        "repository_count": len(rows),
        "verified_repository_count": sum(row["status"] == "verified" for row in rows),
        "repository_results": rows,
        "errors": errors,
        "note": (
            "This verifies bundle readability by isolated mirror clone, ZIP CRC integrity, and checkout Git identity. "
            "It does not prove every expected ref is present, compare ZIP contents to Git trees, verify GitHub-only records, "
            "or prove a complete account restoration."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    requested_output = args.output.expanduser()
    if requested_output.is_symlink():
        parser.error("verification report output must not be a symlink")
    output = requested_output.resolve()
    root = args.backup_dir.expanduser().resolve()
    seed_root = Path(__file__).resolve().parents[1]
    if output == seed_root or seed_root in output.parents:
        parser.error("verification report must be written outside the public world-seed checkout")
    if output == root or root in output.parents:
        parser.error("verification report must be written outside the backup directory being inspected")
    report = verify_source_artifacts(root)
    write_private_json(output, report)
    print(f"Source artifact verification: {report['overall_status']}")
    print(f"Repositories verified: {report.get('verified_repository_count', 0)}/{report.get('repository_count', 0)}")
    return 0 if report["overall_status"] == "source-artifacts-verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
