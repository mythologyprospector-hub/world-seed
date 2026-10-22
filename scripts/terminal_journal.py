#!/usr/bin/env python3
"""Capture one command as a durable local JSONL terminal-journal record."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
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


def pump(stream: BinaryIO, destination: BinaryIO, collected: bytearray, lock: threading.Lock) -> None:
    while True:
        chunk = stream.read(4096)
        if not chunk:
            break
        collected.extend(chunk)
        with lock:
            destination.write(chunk)
            destination.flush()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a command, stream its output, and append a private local journal record."
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
    start_time = utc_now()
    day = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    log_path = root / project / f"{day}.jsonl"
    started = time.monotonic()
    stdout_data = bytearray()
    stderr_data = bytearray()
    output_lock = threading.Lock()
    child: subprocess.Popen[bytes] | None = None
    interrupted = False
    spawn_error: str | None = None
    exit_code = 127

    try:
        child = subprocess.Popen(child_argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert child.stdout is not None and child.stderr is not None
        threads = [
            threading.Thread(target=pump, args=(child.stdout, sys.stdout.buffer, stdout_data, output_lock), daemon=True),
            threading.Thread(target=pump, args=(child.stderr, sys.stderr.buffer, stderr_data, output_lock), daemon=True),
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
        record: dict[str, object] = {
            "schema_version": 1,
            "started_at": start_time,
            "ended_at": ended_time,
            "duration_seconds": round(time.monotonic() - started, 3),
            "project": project,
            "cwd": str(cwd),
            **git,
            "command": command_record,
            "exit_code": exit_code,
            "interrupted": interrupted,
            "spawn_error": spawn_error,
            "stdout": stdout_data.decode("utf-8", errors="replace"),
            "stderr": stderr_data.decode("utf-8", errors="replace"),
        }
        try:
            append_record(log_path, record)
            print(f"\n[terminal-journal] saved: {log_path}", file=sys.stderr)
        except OSError as exc:
            print(
                f"\n[terminal-journal] ERROR: could not persist this command record: {exc}",
                file=sys.stderr,
            )
            return 125

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
