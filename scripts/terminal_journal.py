#!/usr/bin/env python3
"""Run a command while durably journaling output chunks as they arrive."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import uuid
from typing import BinaryIO


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def git_context(cwd: Path) -> dict[str, str | bool | None]:
    root_result = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2,
        check=False,
    )
    if root_result.returncode:
        return {"repository_root": None, "git_branch": None, "git_dirty": None}
    root = root_result.stdout.strip()
    branch_result = subprocess.run(
        ["git", "-C", root, "branch", "--show-current"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2,
        check=False,
    )
    status_result = subprocess.run(
        ["git", "-C", root, "status", "--porcelain"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2,
        check=False,
    )
    return {
        "repository_root": root,
        "git_branch": branch_result.stdout.strip() if branch_result.returncode == 0 else None,
        "git_dirty": bool(status_result.stdout) if status_result.returncode == 0 else None,
    }


def safe_project_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value):
        raise ValueError("project name must be a 1-80 character repository-style slug")
    if value in {".", ".."}:
        raise ValueError("project name must not be a path component")
    return value


def ensure_private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix":
        path.chmod(0o700)


def append_record(path: Path, record: dict[str, object]) -> None:
    ensure_private_directory(path.parent)
    payload = (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    fd = os.open(path, flags, 0o600)
    try:
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "ab", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)


def pump(
    source: BinaryIO,
    destination: BinaryIO,
    stream_name: str,
    collected: bytearray,
    lock: threading.Lock,
    log_path: Path,
    base_record: dict[str, object],
    sequence: dict[str, int],
    journal_errors: list[str],
) -> None:
    while True:
        chunk = source.read(4096)
        if not chunk:
            return
        collected.extend(chunk)
        with lock:
            event = {
                **base_record,
                "event": "output",
                "sequence": sequence["value"],
                "recorded_at": utc_now(),
                "stream": stream_name,
                "text": chunk.decode("utf-8", errors="replace"),
            }
            try:
                # Persist before displaying the bytes: visible output should already be recoverable.
                append_record(log_path, event)
                sequence["value"] += 1
            except OSError as exc:
                journal_errors.append(f"{type(exc).__name__}: {exc}")
            destination.write(chunk)
            destination.flush()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a command, stream its output, and durably journal output chunks locally."
    )
    parser.add_argument("--project", help="project lane name (defaults to Git root or current directory name)")
    parser.add_argument(
        "--log-dir", type=Path,
        help="journal root for testing or deliberate relocation (default: ~/.local/state/world-seed-terminal-journal)",
    )
    parser.add_argument("--shell", metavar="COMMAND", help="run COMMAND through /bin/bash -lc")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="command after -- (not interpreted by a shell)")
    args = parser.parse_args()

    if args.shell is not None and args.command:
        parser.error("use either --shell COMMAND or a command after --, not both")
    if args.shell is None:
        command = args.command
        if command and command[0] == "--":
            command = command[1:]
        if not command:
            parser.error("provide a command after -- or use --shell COMMAND")
        command_record: object = command
        child_argv = command
    else:
        if not args.shell.strip():
            parser.error("--shell COMMAND must not be empty")
        command_record = {"shell": "/bin/bash -lc", "command": args.shell}
        child_argv = ["/bin/bash", "-lc", args.shell]

    cwd = Path.cwd().resolve()
    git = git_context(cwd)
    default_project = Path(git["repository_root"]).name if git["repository_root"] else cwd.name
    try:
        project = safe_project_name(args.project or default_project)
    except ValueError as exc:
        parser.error(str(exc))

    root = (args.log_dir or (Path.home() / ".local/state/world-seed-terminal-journal")).expanduser()
    day = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    log_path = root / project / f"{day}.jsonl"
    session_id = str(uuid.uuid4())
    start_time = utc_now()
    started = time.monotonic()
    stdout_data = bytearray()
    stderr_data = bytearray()
    output_lock = threading.Lock()
    sequence = {"value": 0}
    journal_errors: list[str] = []
    child: subprocess.Popen[bytes] | None = None
    interrupted = False
    spawn_error: str | None = None
    exit_code = 127
    base_record: dict[str, object] = {
        "schema_version": 2,
        "session_id": session_id,
        "project": project,
        "cwd": str(cwd),
        **git,
        "command": command_record,
    }

    try:
        append_record(log_path, {
            **base_record,
            "event": "command_started",
            "sequence": sequence["value"],
            "recorded_at": start_time,
        })
        sequence["value"] += 1
    except OSError as exc:
        print(f"[terminal-journal] ERROR: cannot persist command start; command not run: {exc}", file=sys.stderr)
        return 125

    try:
        child = subprocess.Popen(child_argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert child.stdout is not None and child.stderr is not None
        threads = [
            threading.Thread(
                target=pump,
                args=(child.stdout, sys.stdout.buffer, "stdout", stdout_data, output_lock,
                      log_path, base_record, sequence, journal_errors),
                daemon=True,
            ),
            threading.Thread(
                target=pump,
                args=(child.stderr, sys.stderr.buffer, "stderr", stderr_data, output_lock,
                      log_path, base_record, sequence, journal_errors),
                daemon=True,
            ),
        ]
        for thread in threads:
            thread.start()
        exit_code = child.wait()
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        interrupted = True
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        exit_code = 130
    except OSError as exc:
        spawn_error = f"{type(exc).__name__}: {exc}"
        exit_code = 127
    finally:
        ended_time = utc_now()
        finished: dict[str, object] = {
            **base_record,
            "event": "command_finished",
            "sequence": sequence["value"],
            "recorded_at": ended_time,
            "started_at": start_time,
            "duration_seconds": round(time.monotonic() - started, 3),
            "exit_code": exit_code,
            "interrupted": interrupted,
            "spawn_error": spawn_error,
            "stdout_bytes": len(stdout_data),
            "stderr_bytes": len(stderr_data),
            "stdout_sha256": hashlib.sha256(stdout_data).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr_data).hexdigest(),
            "journal_errors": journal_errors,
        }
        try:
            append_record(log_path, finished)
            print(f"\n[terminal-journal] saved: {log_path}", file=sys.stderr)
        except OSError as exc:
            print(f"\n[terminal-journal] ERROR: could not persist completion record: {exc}", file=sys.stderr)
            return 125

    if journal_errors:
        print(
            "\n[terminal-journal] ERROR: one or more output chunks could not be persisted; "
            "see journal_errors in the completion record if it was saved.",
            file=sys.stderr,
        )
        return 125
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
