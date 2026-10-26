#!/usr/bin/env python3
"""Prepare a reviewed terminal-output handoff; publish only on explicit request.

Raw JSONL journals remain local. A prepared report is a bounded derivative of one
session. Publishing is a separate command, restricted to the verified private
Intake Dock repository and requires --confirm-publish.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

DEFAULT_JOURNAL_ROOT = Path.home() / ".local/state/world-seed-terminal-journal"
DEFAULT_OUTBOX = Path.home() / ".local/state/world-seed-terminal-journal/outbox"
# Verified private at implementation time. Keep this allowlist explicit.
APPROVED_REPOSITORY = "mythologyprospector-hub/miracle-depot"
MAX_REPORT_BYTES = 96 * 1024
DEFAULT_OUTPUT_LIMIT = 48 * 1024

REDACTIONS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{8,}"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b)"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"(?i)(\b(?:password|passwd|token|secret|api[_-]?key|client[_-]?secret|access[_-]?key|authorization)\b\s*[=:]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(https?://[^\s/?#]+/[^\s?#]*\?)[^\s#]+"), r"\1[REDACTED_QUERY]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix":
        path.chmod(0o700)


def redact(value: str) -> tuple[str, bool]:
    changed = False
    for pattern, replacement in REDACTIONS:
        value, count = pattern.subn(replacement, value)
        changed = changed or count > 0
    return value, changed


def read_session(journal_root: Path, project: str, session_id: str | None) -> tuple[dict[str, Any], list[dict[str, Any]], Path]:
    project_dir = journal_root.expanduser() / project
    files = sorted(project_dir.glob("*.jsonl"))
    if not files:
        raise ValueError(f"no journal files found for project {project!r} under {project_dir}")
    sessions: dict[str, list[dict[str, Any]]] = {}
    source_by_session: dict[str, Path] = {}
    warnings = 0
    for path in files:
        try:
            with path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        warnings += 1
                        continue
                    if not isinstance(record, dict) or not isinstance(record.get("session_id"), str):
                        warnings += 1
                        continue
                    sid = record["session_id"]
                    sessions.setdefault(sid, []).append(record)
                    source_by_session[sid] = path
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"cannot read journal file {path.name} ({type(exc).__name__})") from exc
    if not sessions:
        raise ValueError("no valid journal sessions found")
    if session_id:
        if session_id not in sessions:
            raise ValueError(f"session ID not found: {session_id}")
        selected = session_id
    else:
        def sort_key(item: tuple[str, list[dict[str, Any]]]) -> str:
            starts = [str(r.get("recorded_at", "")) for r in item[1] if r.get("event") == "command_started"]
            return max(starts, default="")
        selected = max(sessions.items(), key=sort_key)[0]
    records = sorted(sessions[selected], key=lambda r: int(r.get("sequence", 0)) if str(r.get("sequence", "0")).isdigit() else 0)
    starts = [r for r in records if r.get("event") == "command_started"]
    finishes = [r for r in records if r.get("event") == "command_finished"]
    if not starts:
        raise ValueError("selected session has no command_started event")
    return starts[0], records, source_by_session[selected]


def output_for(records: list[dict[str, Any]], stream_name: str) -> str:
    return "".join(str(r.get("text", "")) for r in records if r.get("event") == "output" and r.get("stream") == stream_name)


def bounded_text(value: str, limit: int) -> tuple[str, bool]:
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return value, False
    marker = "\n[OUTPUT TRUNCATED BY HANDOFF LIMIT]\n"
    available = max(0, limit - len(marker.encode()))
    cut = encoded[:available].decode("utf-8", errors="ignore")
    return cut + marker, True


def prepare(args: argparse.Namespace) -> int:
    try:
        started, records, source = read_session(args.journal_root, args.project, args.session)
        finished = next((r for r in reversed(records) if r.get("event") == "command_finished"), None)
        stdout, redacted_out = redact(output_for(records, "stdout"))
        stderr, redacted_err = redact(output_for(records, "stderr"))
        half = args.max_output_bytes // 2
        stdout, trunc_out = bounded_text(stdout, half)
        stderr, trunc_err = bounded_text(stderr, args.max_output_bytes - half)
        command = started.get("command", "[command unavailable]")
        command_text = json.dumps(command, ensure_ascii=False) if not isinstance(command, str) else command
        command_text, redacted_command = redact(command_text)
        report = {
            "handoff_schema": "world-seed-terminal-output-handoff/v1",
            "created_at": utc_now(),
            "project": args.project,
            "session_id": started.get("session_id"),
            "repository": Path(str(started.get("repository_root") or "")).name or None,
            "branch": started.get("git_branch"),
            "working_tree_dirty_at_start": started.get("git_dirty"),
            "command": command_text,
            "started_at": started.get("recorded_at"),
            "finished_at": finished.get("recorded_at") if finished else None,
            "exit_code": finished.get("exit_code") if finished else None,
            "completion": "recorded" if finished else "incomplete_or_unrecorded",
            "stdout": stdout,
            "stderr": stderr,
            "truncated": bool(trunc_out or trunc_err),
            "redactions_applied": bool(redacted_out or redacted_err or redacted_command),
            "redaction_notice": "Heuristic redaction is not guaranteed to find every secret. Review this file before publishing.",
            "source_journal": source.name,
            "source_journal_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "journal_warnings": 0,
        }
        encoded = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(encoded) > MAX_REPORT_BYTES:
            raise ValueError(f"prepared report exceeds {MAX_REPORT_BYTES} bytes; lower --max-output-bytes")
        ensure_private_dir(args.outbox.expanduser())
        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        sid = re.sub(r"[^A-Za-z0-9-]", "", str(report["session_id"]))[:36]
        path = args.outbox.expanduser() / f"terminal-handoff-{timestamp}-{sid}.json"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        print(f"[terminal-handoff] prepared: {path}")
        print(f"[terminal-handoff] bytes: {len(encoded)}; exit_code: {report['exit_code']}; completion: {report['completion']}")
        print(f"[terminal-handoff] redactions: {'applied' if report['redactions_applied'] else 'none detected'}; truncated: {report['truncated']}")
        print("[terminal-handoff] NOT uploaded; inspect the report before publishing")
        return 0
    except (OSError, ValueError) as exc:
        print(f"[terminal-handoff] ERROR: {exc}", file=sys.stderr)
        return 2



def update_latest_index(
    gh: str, repo: str, branch: str, report_url: str, report_path: str,
    report_commit: str, report: dict[str, Any], report_sha256: str,
) -> str:
    """Point the private Intake Dock's latest.json at a published report."""
    index_path = "terminal-handoffs/latest.json"
    endpoint = f"repos/{repo}/contents/{index_path}"
    current = subprocess.run(
        [gh, "api", endpoint, "--jq", ".sha"],
        capture_output=True, text=True, timeout=20, check=False,
    )
    index_sha: str | None = None
    if current.returncode == 0:
        candidate = current.stdout.strip()
        if re.fullmatch(r"[0-9a-f]{40}", candidate):
            index_sha = candidate
        elif candidate not in {"", "null"}:
            raise ValueError("could not parse existing latest handoff index SHA")
    elif "404" not in current.stderr and "Not Found" not in current.stderr:
        raise ValueError("could not read latest handoff index; published report remains available")

    index = {
        "schema": "world-seed-terminal-handoff-index/v1",
        "updated_at": utc_now(),
        "latest": {
            "repository": repo, "path": report_path, "url": report_url,
            "commit_sha": report_commit, "report_sha256": report_sha256,
            "session_id": report.get("session_id"), "project": report.get("project"),
            "branch": report.get("branch"), "created_at": report.get("created_at"),
            "exit_code": report.get("exit_code"), "completion": report.get("completion"),
        },
    }
    encoded = base64.b64encode((json.dumps(index, indent=2) + "\n").encode("utf-8")).decode("ascii")
    args = [gh, "api", endpoint, "--method", "PUT",
            "-f", "message=Update latest reviewed terminal handoff",
            "-f", f"content={encoded}", "-f", f"branch={branch}"]
    if index_sha:
        args.extend(["-f", f"sha={index_sha}"])
    result = subprocess.run(args, capture_output=True, text=True, timeout=60, check=False)
    if result.returncode:
        raise ValueError("report was uploaded, but updating latest.json failed; inspect the Intake Dock before retrying")
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("report was uploaded, but latest.json update response was invalid") from exc
    if not response.get("content", {}).get("html_url") or not response.get("commit", {}).get("sha"):
        raise ValueError("report was uploaded, but GitHub did not confirm the latest.json update")
    return response["content"]["html_url"]


def publish(args: argparse.Namespace) -> int:
    report_path = args.report.expanduser().resolve()
    outbox = args.outbox.expanduser().resolve()
    try:
        report_path.relative_to(outbox)
    except ValueError:
        print("[terminal-handoff] ERROR: report must be inside the configured local outbox", file=sys.stderr)
        return 2
    if not args.confirm_publish:
        print("[terminal-handoff] ERROR: review the report, then add --confirm-publish to authorize upload", file=sys.stderr)
        return 2
    if args.repo != APPROVED_REPOSITORY:
        print(f"[terminal-handoff] ERROR: destination is not the approved repository ({APPROVED_REPOSITORY})", file=sys.stderr)
        return 2
    try:
        if report_path.stat().st_size > MAX_REPORT_BYTES:
            raise ValueError(f"report exceeds {MAX_REPORT_BYTES} byte limit")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if not isinstance(report, dict) or report.get("handoff_schema") != "world-seed-terminal-output-handoff/v1":
            raise ValueError("file is not a recognized terminal handoff report")
        gh = shutil.which("gh")
        if not gh:
            raise ValueError("GitHub CLI (gh) is required; no upload attempted")
        meta = subprocess.run(
            [gh, "repo", "view", args.repo, "--json", "isPrivate,defaultBranchRef", "--jq", "[.isPrivate, .defaultBranchRef.name] | @tsv"],
            capture_output=True, text=True, timeout=20, check=False,
        )
        if meta.returncode:
            raise ValueError("could not verify destination through gh; check authentication and repository access")
        parts = meta.stdout.strip().split("\t")
        if len(parts) != 2 or parts[0] != "true" or not parts[1]:
            raise ValueError("destination did not verify as private; refusing upload")
        branch = parts[1]
        payload = report_path.read_bytes()
        remote_path = f"terminal-handoffs/{dt.datetime.now(dt.timezone.utc):%Y/%m/%d}/{report_path.name}"
        message = f"Add reviewed terminal handoff {report.get('session_id', 'unknown')}"
        encoded = base64.b64encode(payload).decode("ascii")
        result = subprocess.run(
            [gh, "api", f"repos/{args.repo}/contents/{remote_path}", "--method", "PUT",
             "-f", f"message={message}", "-f", f"content={encoded}", "-f", f"branch={branch}"],
            capture_output=True, text=True, timeout=60, check=False,
        )
        if result.returncode:
            raise ValueError("GitHub upload failed; report remains local and no success is claimed")
        response = json.loads(result.stdout)
        url = response.get("content", {}).get("html_url")
        commit = response.get("commit", {}).get("sha")
        if not url or not commit:
            raise ValueError("GitHub response lacked a file URL or commit SHA; inspect repository before retrying")
        report_sha256 = hashlib.sha256(payload).hexdigest()
        receipt = report_path.with_suffix(".receipt.json")
        receipt_data = {"uploaded_at": utc_now(), "repository": args.repo, "url": url, "commit_sha": commit, "report_sha256": report_sha256}
        fd = os.open(receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(receipt_data, stream, indent=2)
            stream.write("\\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            index_url = update_latest_index(
                gh, args.repo, branch, url, remote_path, commit, report, report_sha256,
            )
        except ValueError:
            print(f"[terminal-handoff] uploaded: {url}")
            print(f"[terminal-handoff] commit: {commit}")
            print(f"[terminal-handoff] receipt: {receipt}")
            raise
        print(f"[terminal-handoff] uploaded: {url}")
        print(f"[terminal-handoff] commit: {commit}")
        print(f"[terminal-handoff] latest index: {index_url}")
        print(f"[terminal-handoff] receipt: {receipt}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"[terminal-handoff] ERROR: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a bounded terminal handoff; publish only after review.")
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare", help="prepare one session locally; does not upload")
    prep.add_argument("--project", default=Path.cwd().name, help="journal project lane")
    prep.add_argument("--session", help="exact session UUID; defaults to latest session")
    prep.add_argument("--journal-root", type=Path, default=DEFAULT_JOURNAL_ROOT)
    prep.add_argument("--outbox", type=Path, default=DEFAULT_OUTBOX)
    prep.add_argument("--max-output-bytes", type=int, default=DEFAULT_OUTPUT_LIMIT)
    prep.set_defaults(func=prepare)
    pub = sub.add_parser("publish", help="upload a reviewed report to the approved private repository")
    pub.add_argument("--report", type=Path, required=True)
    pub.add_argument("--outbox", type=Path, default=DEFAULT_OUTBOX)
    pub.add_argument("--repo", default=APPROVED_REPOSITORY)
    pub.add_argument("--confirm-publish", action="store_true", help="explicitly authorize this report upload")
    pub.set_defaults(func=publish)
    args = parser.parse_args()
    if args.action == "prepare" and not 1024 <= args.max_output_bytes <= DEFAULT_OUTPUT_LIMIT:
        parser.error(f"--max-output-bytes must be between 1024 and {DEFAULT_OUTPUT_LIMIT}")
    if args.action == "prepare":
        try:
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", args.project) or args.project in {".", ".."}:
                parser.error("--project must be a 1-80 character repository-style slug")
        except TypeError:
            parser.error("invalid project name")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
