#!/usr/bin/env python3
"""Run one command and publish redacted, bounded snapshots to the private Intake Dock.

This is an explicit opt-in wrapper, not shell-wide recording. GitHub updates are
commits, so snapshots must never contain secrets or sensitive personal data.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import getpass
import json
import os
from pathlib import Path
import re
import selectors
import socket
import subprocess
import sys
import time
import uuid

REPO = "mythologyprospector-hub/miracle-depot"
MAX_BYTES = 24 * 1024
SNAPSHOT_SECONDS = 10

# A small, entirely local curiosity. Keep this out of normal help and execution.
EASTER_EGG = r'''
                         .-=========-.
                      .-'  .-"""-.    '-.
                    .'    /  .-.         '.
                   /     |  (   )  |        \
                  ;       \  '-'  /          ;
                  |     .--'-----'--.        |
                  |    /  .--------. \       |
                  ;   |  /  .----.  \ |      ;
                   \  | |  ( moo ) | | |    /
                    '.|  \  '----'  / |   .'
                      '-. '--------' .-'
                         '---.  .---'
                             \/

             THE WORLD-SEED FIELD CURIOSITY SOCIETY
                       specimen no. 0001

       Observed: one (1) unusually well-dressed bovine.
       Method:   patient observation; absolutely no milking.
       Result:   the universe remains delightfully unexplained.

                    Keep looking. Keep wondering.
'''
PATTERNS = [
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{8,}"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"(?i)(\b(?:password|passwd|token|secret|api[_-]?key|client[_-]?secret|access[_-]?key|authorization)\b\s*[=:]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(https?://[^\s/?#]+/[^\s?#]*\?)[^\s#]+"), r"\1[REDACTED_QUERY]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"(?i)(--?(?:password|passwd|token|secret|api[_-]?key|client[_-]?secret|access[_-]?key)(?:=|\s+))([^\s,;]+)"), r"\1[REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "[REDACTED_API_TOKEN]"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "[REDACTED_SLACK_TOKEN]"),
    (re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b"), "[REDACTED_NPM_TOKEN]"),
]


def redact(text: str) -> str:
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def gh(args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], input=input_text, text=True, capture_output=True, check=True)


def safe_diagnostic(exc: BaseException, operation: str) -> str:
    """Describe a failure without echoing command arguments, stderr, or payloads."""
    if isinstance(exc, subprocess.CalledProcessError):
        return f"{operation} failed (exit status {exc.returncode})"
    if isinstance(exc, subprocess.TimeoutExpired):
        return f"{operation} timed out"
    return f"{operation} failed ({type(exc).__name__})"


def upload(path: str, body: str, sha: str | None, branch: str) -> str:
    payload = base64.b64encode(body.encode("utf-8", errors="replace")).decode("ascii")
    request_body = {
        "message": "Refresh live terminal snapshot",
        "content": payload,
        "branch": branch,
    }
    if sha:
        request_body["sha"] = sha
    args = ["api", "--method", "PUT", f"repos/{REPO}/contents/{path}", "--input", "-"]
    for attempt in range(3):
        try:
            result = gh(args, input_text=json.dumps(request_body))
            return str(json.loads(result.stdout)["content"]["sha"])
        except subprocess.CalledProcessError as exc:
            diagnostic = f"{exc.stderr or ''} {exc.stdout or ''}".lower()
            is_write_conflict = any(
                marker in diagnostic
                for marker in ("http 409", "409 conflict", "update is not a fast forward")
            )
            if not is_write_conflict or attempt == 2:
                raise
            time.sleep(0.25 * (attempt + 1))
            # A concurrent writer may have changed this exact file. Refresh
            # its blob SHA before retrying; reusing the stale SHA would simply
            # repeat the same Contents API conflict.
            latest = gh(["api", f"repos/{REPO}/contents/{path}", "--jq", ".sha"])
            latest_sha = latest.stdout.strip()
            if latest_sha:
                request_body["sha"] = latest_sha
            else:
                request_body.pop("sha", None)
    raise RuntimeError("Unreachable upload retry state")


def publish_latest(report_path: str, report_url: str, branch: str, pointer_path: str = "terminal-live/LATEST.txt") -> None:
    """Point a stable private-repo path at the current run's report."""
    try:
        existing = gh(["api", f"repos/{REPO}/contents/{pointer_path}", "--jq", ".sha"])
        pointer_sha = existing.stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        # A missing pointer is expected on the first run. If lookup failed for
        # another reason, the write below will fail and the caller will warn.
        pointer_sha = None
    body = (
        "Latest World Seed See report\n"
        f"Updated (UTC): {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}\n"
        f"Report path: {report_path}\n"
        f"Report URL: {report_url}\n"
        "This pointer identifies the newest run; fetch the report itself for current output.\n"
    )
    upload(pointer_path, body, pointer_sha, branch)


def collect_shell_context() -> dict[str, str]:
    """Capture prompt-like context without recording shell history or arbitrary environment."""
    cwd = str(Path.cwd())
    branch = "(unavailable)"
    git_state = "not a Git worktree"
    try:
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd, text=True, capture_output=True, check=True,
        )
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd, text=True, capture_output=True, check=True,
        )
        branch = branch_result.stdout.strip() or "(detached HEAD)"
        status_result = subprocess.run(
            ["git", "status", "--short"],
            cwd=cwd, text=True, capture_output=True, check=True,
        )
        git_state = "dirty" if status_result.stdout.strip() else "clean"
    except (OSError, subprocess.CalledProcessError):
        pass
    return {
        "timestamp_local": dt.datetime.now().astimezone().strftime("%H:%M:%S"),
        "user": getpass.getuser(),
        "host": socket.gethostname(),
        "cwd": cwd,
        "git_branch": branch,
        "git_state": git_state,
    }


def format_shell_context(label: str, context: dict[str, str]) -> str:
    return redact(
        f"----- {label} -----\n"
        f"Prompt-like timestamp (local): {context['timestamp_local']}\n"
        f"User/host: {context['user']}@{context['host']}\n"
        f"Working directory: {context['cwd']}\n"
        f"Git branch: {context['git_branch']}\n"
        f"Git working tree: {context['git_state']}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a command, show its output, and share redacted snapshots about every 10 seconds."
    )
    parser.add_argument("--limit-bytes", type=int, default=MAX_BYTES,
                        help="maximum retained output bytes (default: 24576)")
    parser.add_argument("--moo", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="command to run; place -- before it")
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if args.moo:
        if command or args.limit_bytes != MAX_BYTES:
            parser.error("--moo cannot be combined with command or snapshot options")
        print(EASTER_EGG)
        return 0
    if not command:
        parser.error("provide a command after --, e.g. -- python -m unittest")
    if not 1024 <= args.limit_bytes <= 1024 * 1024:
        parser.error("--limit-bytes must be between 1024 and 1048576")

    try:
        check = gh(["repo", "view", REPO, "--json", "isPrivate,defaultBranchRef", "--jq", "."])
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"[world-seed-see] {safe_diagnostic(exc, 'GitHub CLI access check')} for {REPO}.", file=sys.stderr)
        return 125
    try:
        repo_info = json.loads(check.stdout)
    except (TypeError, json.JSONDecodeError):
        print(f"[world-seed-see] Refusing to upload: could not parse repository privacy/default-branch metadata for {REPO}.", file=sys.stderr)
        return 125
    if repo_info.get("isPrivate") is not True:
        print(f"[world-seed-see] Refusing to upload: {REPO} was not verified private.", file=sys.stderr)
        return 125
    default_ref = repo_info.get("defaultBranchRef")
    branch = default_ref.get("name") if isinstance(default_ref, dict) else None
    if not isinstance(branch, str) or not branch:
        print(f"[world-seed-see] Refusing to upload: could not verify the default branch for {REPO}.", file=sys.stderr)
        return 125

    now = dt.datetime.now(dt.timezone.utc)
    path = f"terminal-live/world-seed-see-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}.txt"
    url = f"https://github.com/{REPO}/blob/{branch}/{path}"
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    start_context = collect_shell_context()
    retained = bytearray()
    truncated = False
    sha: str | None = None
    last_upload = 0.0
    upload_failed = False
    header = (
        "World Seed See — live terminal snapshot\n"
        f"Started (UTC): {started}\n"
        f"Command: {redact(' '.join(command))}\n"
        "NOTE: output is heuristically redacted, not guaranteed secret-free.\n"
    )
    initial_report = (
        header
        + format_shell_context("shell context at wrapper start", start_context)
        + "----- output -----\n"
        + "[Waiting for command output]\n"
    )
    try:
        sha = upload(path, initial_report, None, branch)
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError) as exc:
        print(f"[world-seed-see] {safe_diagnostic(exc, 'Private live-report creation')}; command not started.", file=sys.stderr)
        return 125
    last_upload = time.monotonic()
    try:
        publish_latest(path, url, branch, pointer_path="terminal-live/LATEST-SEE.txt")
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError) as exc:
        print(f"[world-seed-see] {safe_diagnostic(exc, 'Latest-report pointer refresh')}; use the printed report URL.", file=sys.stderr, flush=True)
    print(f"[world-seed-see] Live report: {url}", flush=True)
    print("[world-seed-see] Explicitly wrapped output is shared to the private repo about every 10 seconds.", flush=True)
    print("[world-seed-see] Redaction is heuristic; never run commands whose output contains secrets.", flush=True)

    selector = selectors.DefaultSelector()
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
    except OSError as exc:
        print(f"[world-seed-see] {safe_diagnostic(exc, 'Command launch')}.", file=sys.stderr)
        return 127
    assert proc.stdout is not None
    selector.register(proc.stdout, selectors.EVENT_READ)
    try:
        while True:
            events = selector.select(timeout=1.0)
            for key, _ in events:
                chunk = os.read(key.fd, 8192)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
                remaining = args.limit_bytes - len(retained)
                if remaining > 0:
                    retained.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    truncated = True
            now_mono = time.monotonic()
            finished = proc.poll() is not None and not selector.get_map()
            if (now_mono - last_upload >= SNAPSHOT_SECONDS) or finished:
                decoded = retained.decode("utf-8", errors="replace")
                if truncated:
                    decoded += "\n[OUTPUT TRUNCATED LOCALLY]\n"
                current_context = collect_shell_context()
                report = (
                    header
                    + format_shell_context("shell context at wrapper start", start_context)
                    + format_shell_context("current shell/repository context", current_context)
                    + "----- output -----\n"
                    + redact(decoded)
                    + f"\n----- status -----\n"
                    + f"Snapshot (UTC): {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}\n"
                    + f"Process state: {'finished' if finished else 'running'}\n"
                    + f"Exit code: {proc.returncode if finished else 'not yet available'}\n"
                )
                try:
                    sha = upload(path, report, sha, branch)
                    last_upload = now_mono
                    if not finished:
                        print(f"\n[world-seed-see] Snapshot refreshed: {url}", flush=True)
                except (OSError, subprocess.CalledProcessError, ValueError, KeyError) as exc:
                    upload_failed = True
                    print(f"\n[world-seed-see] {safe_diagnostic(exc, 'Snapshot upload')}; command continues.", file=sys.stderr, flush=True)
                    # Avoid spamming the GitHub API on persistent failure.
                    last_upload = now_mono
            if finished:
                break
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
        return 130
    finally:
        selector.close()
        proc.stdout.close()
    if upload_failed:
        print("[world-seed-see] Some live snapshots failed. The final URL may be stale.", file=sys.stderr)
    print(f"\n[world-seed-see] Final report: {url}", flush=True)
    return int(proc.returncode or 0)


if __name__ == "__main__":
    raise SystemExit(main())
