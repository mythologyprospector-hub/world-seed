#!/usr/bin/env python3
"""Prepare a bounded handoff from one explicitly selected interactive PTY session.

This creates a private local report only. Publication remains a separate,
explicitly confirmed operation through terminal_handoff.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

from terminal_handoff import (
    DEFAULT_JOURNAL_ROOT,
    DEFAULT_OUTBOX,
    MAX_REPORT_BYTES,
    DEFAULT_OUTPUT_LIMIT,
    bounded_text,
    ensure_private_dir,
    redact,
    utc_now,
)

def prepare(args: argparse.Namespace) -> int:
    root = args.journal_root.expanduser() / "interactive"
    matches: list[dict[str, Any]] = []
    source: Path | None = None
    try:
        for path in sorted(root.glob("*.jsonl")):
            with path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(record, dict) and record.get("session_id") == args.session:
                        matches.append(record)
                        source = path
        if not matches or source is None:
            raise ValueError("exact session ID was not found in the interactive journal")
        matches.sort(key=lambda r: int(r.get("sequence", 0)) if str(r.get("sequence", "0")).isdigit() else 0)
        started = next((r for r in matches if r.get("event") == "session_started"), None)
        finished = next((r for r in reversed(matches) if r.get("event") == "session_finished"), None)
        if started is None:
            raise ValueError("selected session has no session_started event")
        raw_output = "".join(str(r.get("text", "")) for r in matches if r.get("event") == "terminal_output")
        safe_output, redactions_applied = redact(raw_output)
        safe_output, truncated = bounded_text(safe_output, args.max_output_bytes)
        cwd = str(started.get("cwd") or "")
        report = {
            "handoff_schema": "world-seed-terminal-output-handoff/v1",
            "created_at": utc_now(),
            "project": "interactive-terminal",
            "session_id": args.session,
            "repository": Path(cwd).name or None,
            "branch": None,
            "working_tree_dirty_at_start": None,
            "command": "interactive shell session (PTY)",
            "started_at": started.get("recorded_at"),
            "finished_at": finished.get("recorded_at") if finished else None,
            "exit_code": finished.get("exit_code") if finished else None,
            "completion": "recorded" if finished else "incomplete_or_unrecorded",
            "stdout": safe_output,
            "stderr": "",
            "truncated": truncated,
            "redactions_applied": redactions_applied,
            "redaction_notice": "Heuristic redaction is not guaranteed to find every secret. Review this file before publishing.",
            "source_journal": source.name,
            "source_journal_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "journal_warnings": 0,
            "session_interrupted": finished.get("interrupted") if finished else None,
            "session_error": finished.get("error") if finished else None,
        }
        encoded = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(encoded) > MAX_REPORT_BYTES:
            raise ValueError(f"prepared report exceeds {MAX_REPORT_BYTES} bytes; lower --max-output-bytes")
        outbox = args.outbox.expanduser()
        ensure_private_dir(outbox)
        safe_id = re.sub(r"[^A-Za-z0-9-]", "", args.session)[:36]
        path = outbox / f"interactive-handoff-{safe_id}.json"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        print(f"[interactive-handoff] prepared: {path}")
        print(f"[interactive-handoff] exit_code: {report['exit_code']}; completion: {report['completion']}; bytes: {len(encoded)}")
        print(f"[interactive-handoff] redactions: {'applied' if redactions_applied else 'none detected'}; truncated: {truncated}")
        print("[interactive-handoff] NOT uploaded; inspect the report before publishing")
        return 0
    except (OSError, ValueError) as exc:
        print(f"[interactive-handoff] ERROR: {exc}", file=sys.stderr)
        return 2

def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare one interactive terminal session for reviewed handoff; never uploads.")
    parser.add_argument("--session", required=True, help="exact session UUID from the local journal")
    parser.add_argument("--journal-root", type=Path, default=DEFAULT_JOURNAL_ROOT)
    parser.add_argument("--outbox", type=Path, default=DEFAULT_OUTBOX)
    parser.add_argument("--max-output-bytes", type=int, default=DEFAULT_OUTPUT_LIMIT)
    args = parser.parse_args()
    if not 1024 <= args.max_output_bytes <= DEFAULT_OUTPUT_LIMIT:
        parser.error(f"--max-output-bytes must be between 1024 and {DEFAULT_OUTPUT_LIMIT}")
    return prepare(args)

if __name__ == "__main__":
    raise SystemExit(main())
