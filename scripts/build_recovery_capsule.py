#!/usr/bin/env python3
"""Build a metadata-only recovery capsule from a local terminal journal.

Raw commands and stdout/stderr are deliberately excluded. This tool performs no
network access and never uploads records.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


def safe_project_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value) or value in {".", ".."}:
        raise ValueError("project must be a 1-80 character repository-style slug")
    return value


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def load_records(paths: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    records: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    for path in sorted(paths):
        try:
            with path.open("r", encoding="utf-8") as stream:
                for line_number, line in enumerate(stream, 1):
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        warnings.append({"file": path.name, "reason": f"invalid JSON at line {line_number}"})
                        continue
                    if not isinstance(record, dict) or not isinstance(record.get("session_id"), str):
                        warnings.append({"file": path.name, "reason": f"invalid record at line {line_number}"})
                        continue
                    records.append(record)
        except OSError as exc:
            warnings.append({"file": path.name, "reason": f"unreadable journal ({type(exc).__name__})"})
    return records, warnings


def build_capsule(project: str, journal_root: Path) -> dict[str, Any]:
    project = safe_project_name(project)
    project_dir = journal_root / project
    if not project_dir.is_dir():
        raise FileNotFoundError(f"no journal directory for project {project!r}")
    paths = list(project_dir.glob("*.jsonl"))
    records, warnings = load_records(paths)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record.get("project") != project:
            warnings.append({"file": "journal", "reason": "record project did not match requested project"})
            continue
        grouped.setdefault(str(record["session_id"]), []).append(record)

    sessions: list[dict[str, Any]] = []
    for session_id, events in grouped.items():
        starts = [r for r in events if r.get("event") == "command_started"]
        finishes = [r for r in events if r.get("event") == "command_finished"]
        outputs = [r for r in events if r.get("event") == "output"]
        start = starts[0] if starts else {}
        finish = finishes[-1] if finishes else {}
        sessions.append({
            "session_id": session_id,
            "started_at": start.get("recorded_at"),
            "finished_at": finish.get("recorded_at") if finish else None,
            "completion": "recorded" if finish else "incomplete_or_unrecorded",
            "exit_code": finish.get("exit_code") if finish else None,
            "interrupted": finish.get("interrupted") if finish else None,
            "git_branch": start.get("git_branch"),
            "git_dirty": start.get("git_dirty"),
            "output_event_count": len(outputs),
            "stdout_bytes_recorded": finish.get("stdout_bytes") if finish else None,
            "stderr_bytes_recorded": finish.get("stderr_bytes") if finish else None,
            "stdout_sha256_recorded": finish.get("stdout_sha256") if finish else None,
            "stderr_sha256_recorded": finish.get("stderr_sha256") if finish else None,
            "journal_write_error_reported": bool(finish.get("journal_errors")) if finish else None,
        })
    sessions.sort(key=lambda item: (item["started_at"] or "", item["session_id"]))
    return {
        "schema_version": 1,
        "capsule_type": "world-seed-terminal-journal-metadata",
        "generated_at": utc_now(),
        "project": project,
        "source": {
            "journal_files_found": len(paths),
            "records_loaded": len(records),
            "raw_command_text_included": False,
            "stdout_stderr_text_included": False,
            "network_transfer_performed": False,
        },
        "sessions": sessions,
        "warnings": warnings,
        "limitations": [
            "This capsule contains metadata only; it cannot reconstruct terminal output.",
            "Recorded exit codes and hashes are reported as journal claims, not independently verified.",
            "A missing completion event is incomplete or unrecorded; no exit status is inferred.",
            "Review this file before sharing; branch names and activity timing may still be sensitive.",
        ],
    }


def write_private_new_file(path: Path, payload: str) -> None:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix":
        path.parent.chmod(0o700)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    fd = os.open(path, flags, 0o600)
    try:
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a metadata-only, local recovery capsule from a terminal journal."
    )
    parser.add_argument("--project", required=True, help="exact project lane name")
    parser.add_argument(
        "--journal-root",
        type=Path,
        default=Path.home() / ".local/state/world-seed-terminal-journal",
        help="journal root (default: ~/.local/state/world-seed-terminal-journal)",
    )
    parser.add_argument("--output", required=True, type=Path, help="new output file; existing files are never overwritten")
    args = parser.parse_args()
    try:
        capsule = build_capsule(args.project, args.journal_root.expanduser())
        write_private_new_file(args.output, json.dumps(capsule, ensure_ascii=False, indent=2) + "\n")
    except (ValueError, FileNotFoundError, OSError) as exc:
        print(f"[recovery-capsule] ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"[recovery-capsule] created metadata-only capsule: {args.output}")
    print(f"[recovery-capsule] sessions: {len(capsule['sessions'])}; warnings: {len(capsule['warnings'])}")
    print("[recovery-capsule] no raw command/output text included; no network transfer performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
