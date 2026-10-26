#!/usr/bin/env python3
"""Run an interactive shell on a PTY while durably journaling its terminal output.

This is an opt-in session launcher, not an automatic system-wide terminal hook.
Remote publication is deliberately not performed by this program.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import select
import signal
import struct
import sys
import termios
import time
import tty
import uuid

DEFAULT_LOG_ROOT = Path.home() / ".local/state/world-seed-terminal-journal"


class SessionTerminated(Exception):
    def __init__(self, signum: int):
        self.signum = signum
        super().__init__(f"received signal {signum}")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix":
        path.chmod(0o700)


def append_record(path: Path, record: dict[str, object]) -> None:
    ensure_private_dir(path.parent)
    data = (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "ab", closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)


def status_code(status: int) -> int:
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    if os.WIFSIGNALED(status):
        return 128 + os.WTERMSIG(status)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Launch an interactive PTY shell and durably journal terminal output locally."
    )
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_ROOT,
                        help="local journal root (default: ~/.local/state/world-seed-terminal-journal)")
    parser.add_argument("--shell", default=os.environ.get("SHELL", "/bin/bash"),
                        help="interactive shell executable (default: $SHELL or /bin/bash)")
    args = parser.parse_args()
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        parser.error("must run from an interactive terminal (TTY)")

    shell = Path(args.shell)
    if not shell.is_absolute() or not os.access(shell, os.X_OK):
        parser.error("--shell must name an executable absolute path")

    session_id = str(uuid.uuid4())
    started_at = utc_now()
    started_mono = time.monotonic()
    root = args.log_dir.expanduser()
    day = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    log_path = root / "interactive" / f"{day}.jsonl"
    base: dict[str, object] = {
        "schema_version": 3,
        "session_id": session_id,
        "event_source": "pty_session",
        "cwd": str(Path.cwd()),
        "shell": str(shell),
    }
    seq = 0
    output_hash = hashlib.sha256()
    output_bytes = 0
    try:
        append_record(log_path, {**base, "event": "session_started",
                                 "sequence": seq, "recorded_at": started_at})
    except OSError as exc:
        print(f"[world-seed-session] cannot persist session start; shell not launched: {exc}",
              file=sys.stderr)
        return 125
    seq += 1

    child_pid = -1
    master_fd = -1
    old_attrs = None
    exit_code = 1
    failure = None
    interrupted = False
    stdin_eof = False
    old_winch = None
    old_signal_handlers: dict[int, object] = {}
    try:
        old_attrs = termios.tcgetattr(sys.stdin.fileno())

        def terminate_session(signum: int, _frame: object) -> None:
            raise SessionTerminated(signum)

        for signum in (signal.SIGTERM, signal.SIGHUP):
            old_signal_handlers[signum] = signal.signal(signum, terminate_session)

        child_pid, master_fd = pty.fork()
        if child_pid == 0:
            os.execv(str(shell), [str(shell), "-i"])
        tty.setraw(sys.stdin.fileno())

        def copy_terminal_size() -> None:
            try:
                size = fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, b"\x00" * 8)
                fcntl.ioctl(master_fd, termios.TIOCSWINSZ, size)
            except OSError:
                pass

        copy_terminal_size()
        old_winch = signal.signal(signal.SIGWINCH, lambda _signum, _frame: copy_terminal_size())
        while True:
            watched = [master_fd]
            if not stdin_eof:
                watched.append(sys.stdin.fileno())
            readable, _, _ = select.select(watched, [], [])
            if sys.stdin.fileno() in readable:
                incoming = os.read(sys.stdin.fileno(), 4096)
                if not incoming:
                    # Treat a closed input stream as one Ctrl-D, then keep
                    # draining output until the shell actually exits.
                    stdin_eof = True
                    os.write(master_fd, b"\x04")
                else:
                    os.write(master_fd, incoming)
            if master_fd in readable:
                try:
                    chunk = os.read(master_fd, 4096)
                except OSError:
                    chunk = b""
                if not chunk:
                    break
                record = {**base, "event": "terminal_output", "sequence": seq,
                          "recorded_at": utc_now(), "text": chunk.decode("utf-8", errors="replace")}
                try:
                    append_record(log_path, record)
                    seq += 1
                except OSError as exc:
                    failure = f"journal write failed: {type(exc).__name__}: {exc}"
                    os.kill(child_pid, signal.SIGTERM)
                    break
                output_hash.update(chunk)
                output_bytes += len(chunk)
                os.write(sys.stdout.fileno(), chunk)
        _, wait_status = os.waitpid(child_pid, 0)
        exit_code = status_code(wait_status)
    except (KeyboardInterrupt, SessionTerminated) as exc:
        interrupted = True
        termination_signal = exc.signum if isinstance(exc, SessionTerminated) else signal.SIGINT
        if child_pid > 0:
            try:
                os.kill(child_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                _, wait_status = os.waitpid(child_pid, 0)
                exit_code = status_code(wait_status)
            except ChildProcessError:
                exit_code = 128 + termination_signal
        else:
            exit_code = 128 + termination_signal
    except OSError as exc:
        failure = f"{type(exc).__name__}: {exc}"
        exit_code = 125
    finally:
        if old_winch is not None:
            signal.signal(signal.SIGWINCH, old_winch)
        for signum, handler in old_signal_handlers.items():
            signal.signal(signum, handler)
        if old_attrs is not None:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_attrs)
        if master_fd >= 0:
            os.close(master_fd)
        ended_at = utc_now()
        final = {**base, "event": "session_finished", "sequence": seq,
                 "recorded_at": ended_at, "started_at": started_at,
                 "duration_seconds": round(time.monotonic() - started_mono, 3),
                 "exit_code": exit_code, "interrupted": interrupted,
                 "output_bytes": output_bytes, "output_sha256": output_hash.hexdigest(),
                 "error": failure}
        try:
            append_record(log_path, final)
        except OSError as exc:
            print(f"\n[world-seed-session] completion record failed: {exc}", file=sys.stderr)
            return 125
    print(f"\n[world-seed-session] local journal: {log_path}", file=sys.stderr)
    if failure:
        print(f"[world-seed-session] ERROR: {failure}", file=sys.stderr)
        return 125
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
