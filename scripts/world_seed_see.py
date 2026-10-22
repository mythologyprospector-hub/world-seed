#!/usr/bin/env python3
"""Run one command and publish redacted, bounded snapshots to the private Intake Dock.

This is an explicit opt-in wrapper, not shell-wide recording. GitHub updates are
commits, so snapshots must never contain secrets or sensitive personal data.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import time
import uuid

REPO = "mythologyprospector-hub/miracle-depot"
MAX_BYTES = 24 * 1024
SNAPSHOT_SECONDS = 10
PATTERNS = [
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{8,}"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"(?i)(\b(?:password|passwd|token|secret|api[_-]?key|client[_-]?secret|access[_-]?key|authorization)\b\s*[=:]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(https?://[^\s/?#]+/[^\s?#]*\?)[^\s#]+"), r"\1[REDACTED_QUERY]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
]


def redact(text: str) -> str:
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def gh(args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], input=input_text, text=True, capture_output=True, check=True)


def upload(path: str, body: str, sha: str | None) -> str:
    payload = base64.b64encode(body.encode("utf-8", errors="replace")).decode("ascii")
    args = [
        "api", "--method", "PUT", f"repos/{REPO}/contents/{path}",
        "-f", "message=Refresh live terminal snapshot",
        "-f", f"content={payload}", "-f", "branch=main",
    ]
    if sha:
        args.extend(["-f", f"sha={sha}"])
    result = gh(args)
    import json
    return str(json.loads(result.stdout)["content"]["sha"])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a command, show its output, and share redacted snapshots about every 10 seconds."
    )
    parser.add_argument("--limit-bytes", type=int, default=MAX_BYTES,
                        help="maximum retained output bytes (default: 24576)")
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="command to run; place -- before it")
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("provide a command after --, e.g. -- python -m unittest")
    if not 1024 <= args.limit_bytes <= 1024 * 1024:
        parser.error("--limit-bytes must be between 1024 and 1048576")

    try:
        check = gh(["repo", "view", REPO, "--json", "isPrivate", "--jq", ".isPrivate"])
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"[world-seed-see] Cannot verify GitHub CLI access to {REPO}: {exc}", file=sys.stderr)
        return 125
    if check.stdout.strip().lower() != "true":
        print(f"[world-seed-see] Refusing to upload: {REPO} was not verified private.", file=sys.stderr)
        return 125

    now = dt.datetime.now(dt.timezone.utc)
    path = f"terminal-live/world-seed-see-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}.txt"
    url = f"https://github.com/{REPO}/blob/main/{path}"
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    print(f"[world-seed-see] Live report: {url}", flush=True)
    print("[world-seed-see] Explicitly wrapped output is shared to the private repo about every 10 seconds.", flush=True)
    print("[world-seed-see] Redaction is heuristic; never run commands whose output contains secrets.", flush=True)

    retained = bytearray()
    truncated = False
    sha: str | None = None
    last_upload = 0.0
    upload_failed = False
    header = (
        "World Seed See — live terminal snapshot\n"
        f"Started (UTC): {started}\n"
        f"Working directory: {Path.cwd()}\n"
        f"Command: {redact(' '.join(command))}\n"
        "NOTE: output is heuristically redacted, not guaranteed secret-free.\n"
        "----- output -----\n"
    )
    selector = selectors.DefaultSelector()
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
    except OSError as exc:
        print(f"[world-seed-see] Could not start command: {exc}", file=sys.stderr)
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
                report = header + redact(decoded) + (
                    f"\n----- status -----\n"
                    f"Snapshot (UTC): {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}\n"
                    f"Process state: {'finished' if finished else 'running'}\n"
                    f"Exit code: {proc.returncode if finished else 'not yet available'}\n"
                )
                try:
                    sha = upload(path, report, sha)
                    last_upload = now_mono
                    if not finished:
                        print(f"\n[world-seed-see] Snapshot refreshed: {url}", flush=True)
                except (OSError, subprocess.CalledProcessError, ValueError, KeyError) as exc:
                    upload_failed = True
                    print(f"\n[world-seed-see] Snapshot upload failed; command continues: {exc}", file=sys.stderr, flush=True)
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
