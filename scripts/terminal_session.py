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

import world_seed_see as live_report

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



class LiveReporter:
    """Best-effort bounded report publisher; never owns the local journal."""

    def __init__(self, limit: int = live_report.MAX_BYTES):
        self.limit = limit
        self.retained = bytearray()
        self.truncated = False
        self.enabled = False
        self.sha = None
        self.last_upload = time.monotonic()
        self.path = ""
        self.url = ""
        self.branch = ""
        self.header = ""
        self.failure_warned = False
        try:
            check = live_report.gh([
                "repo", "view", live_report.REPO,
                "--json", "isPrivate,defaultBranchRef", "--jq", ".",
            ])
            import json
            info = json.loads(check.stdout)
            if info.get("isPrivate") is not True:
                raise RuntimeError(f"{live_report.REPO} is not verified private")
            ref = info.get("defaultBranchRef")
            branch = ref.get("name") if isinstance(ref, dict) else None
            if not isinstance(branch, str) or not branch:
                raise RuntimeError("could not verify the repository default branch")

            now = dt.datetime.now(dt.timezone.utc)
            self.path = (
                "terminal-live/world-seed-session-"
                + now.strftime("%Y%m%dT%H%M%SZ") + "-"
                + uuid.uuid4().hex[:8] + ".txt"
            )
            self.branch = branch
            self.url = f"https://github.com/{live_report.REPO}/blob/{branch}/{self.path}"
            self.header = (
                "World Seed — interactive terminal snapshot\n"
                f"Started (UTC): {now.isoformat(timespec='seconds')}\n"
                "Source: bounded PTY output excerpt; raw local journal is not uploaded.\n"
                "NOTE: redaction is heuristic and cannot guarantee removal of secrets.\n"
            )
            initial = (
                self.header
                + live_report.format_shell_context(
                    "shell context at session start",
                    live_report.collect_shell_context(),
                )
                + "----- output -----\n[Waiting for terminal output]\n"
            )
            initial = self._bounded_report(initial)
            self.sha = live_report.upload(self.path, initial, None, self.branch)
            self.enabled = True
            try:
                live_report.publish_latest(self.path, self.url, self.branch)
            except Exception as exc:
                diagnostic = live_report.safe_diagnostic(exc, "Latest-report pointer refresh")
                print(f"\n[world-seed-session] {diagnostic}; pointer not refreshed.",
                      file=sys.stderr, flush=True)
            print(f"\n[world-seed-session] Private live report: {self.url}",
                  file=sys.stderr, flush=True)
            print("[world-seed-session] Bounded output is shared about every 10 seconds; "
                  "redaction is not guaranteed.", file=sys.stderr, flush=True)
        except Exception as exc:
            diagnostic = live_report.safe_diagnostic(exc, "Live-report initialization")
            print(f"\n[world-seed-session] {diagnostic}; local journal continues.",
                  file=sys.stderr, flush=True)

    def _bounded_report(self, report: str) -> str:
        report = live_report.redact(report)
        encoded = report.encode("utf-8", errors="replace")
        if len(encoded) <= self.limit:
            return report
        marker = b"\n[REPORT TRUNCATED TO BYTE LIMIT]\n"
        if self.limit <= len(marker):
            return marker[:max(0, self.limit)].decode("ascii")
        keep = self.limit - len(marker)
        prefix = encoded[:keep].decode("utf-8", errors="ignore")
        return prefix + marker.decode("ascii")

    def observe(self, chunk: bytes) -> None:
        remaining = self.limit - len(self.retained)
        if remaining > 0:
            self.retained.extend(chunk[:remaining])
        if len(chunk) > max(remaining, 0):
            self.truncated = True

    def refresh(self, state: str, exit_code: int | None = None, force: bool = False) -> None:
        if not self.enabled:
            return
        now_mono = time.monotonic()
        if not force and now_mono - self.last_upload < live_report.SNAPSHOT_SECONDS:
            return
        output = self.retained.decode("utf-8", errors="replace")
        if self.truncated:
            output += "\n[OUTPUT TRUNCATED: local journal retains the full output]\n"
        report = (
            self.header
            + live_report.format_shell_context(
                "current shell/repository context",
                live_report.collect_shell_context(),
            )
            + "----- bounded output excerpt -----\n"
            + output
            + "\n----- session status -----\n"
            + f"Snapshot (UTC): {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}\n"
            + f"Session state: {state}\n"
            + f"Exit code: {exit_code if exit_code is not None else 'not yet available'}\n"
        )
        report = self._bounded_report(report)
        self.last_upload = now_mono
        try:
            self.sha = live_report.upload(self.path, report, self.sha, self.branch)
            if force:
                live_report.publish_latest(self.path, self.url, self.branch)
                print(f"\n[world-seed-session] Final report: {self.url}",
                      file=sys.stderr, flush=True)
        except Exception as exc:
            self.enabled = False
            _warn_report_failure(self, exc)


def _warn_report_failure(reporter: object, exc: Exception) -> None:
    """Emit one concise warning when best-effort reporting has to stop."""
    if getattr(reporter, "failure_warned", False):
        return
    reporter.failure_warned = True
    diagnostic = live_report.safe_diagnostic(exc, "Live reporting")
    print(f"\n[world-seed-session] Live reporting disabled after an error: {diagnostic}",
          file=sys.stderr, flush=True)


def _report_safely(reporter: LiveReporter | None, method: str, *args: object,
                   **kwargs: object) -> None:
    """Keep reporter faults outside the PTY lifecycle and local journal path."""
    if reporter is None or not reporter.enabled:
        return
    try:
        getattr(reporter, method)(*args, **kwargs)
    except Exception as exc:
        reporter.enabled = False
        _warn_report_failure(reporter, exc)


def _write_final_state(log_path: Path, final: dict[str, object],
                       reporter: LiveReporter | None, exit_code: int) -> bool:
    """Attempt both durable local completion and best-effort final reporting."""
    journal_failed = False
    try:
        append_record(log_path, final)
    except OSError as exc:
        journal_failed = True
        print(f"\n[world-seed-session] completion record failed: {exc}", file=sys.stderr)
    _report_safely(reporter, "refresh", "finished", exit_code, force=True)
    return journal_failed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch an interactive PTY shell and durably journal terminal output locally."
    )
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_ROOT,
                        help="local journal root (default: ~/.local/state/world-seed-terminal-journal)")
    report_options = parser.add_mutually_exclusive_group()
    report_options.add_argument("--live-report", dest="live_report", action="store_true",
                                help="opt in to bounded private GitHub live reporting")
    report_options.add_argument("--no-live-report", dest="live_report", action="store_false",
                                help="disable live reporting; local journaling remains enabled")
    parser.set_defaults(live_report=False)
    parser.add_argument("--shell", default=os.environ.get("SHELL", "/bin/bash"),
                        help="interactive shell executable (default: $SHELL or /bin/bash)")
    return parser


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return _build_parser().parse_args(argv)


def _make_reporter(enabled: bool) -> LiveReporter | None:
    """Construct the GitHub reporter only after explicit user opt-in."""
    return LiveReporter() if enabled else None



def terminate_child_process(child_pid: int, grace_seconds: float = 0.5) -> None:
    """Terminate a PTY process group, escalating if any member remains."""
    try:
        os.killpg(child_pid, signal.SIGTERM)
    except ProcessLookupError:
        pass

    deadline = time.monotonic() + grace_seconds
    child_reaped = False
    while time.monotonic() < deadline:
        if not child_reaped:
            try:
                waited_pid, _ = os.waitpid(child_pid, os.WNOHANG)
                child_reaped = waited_pid == child_pid
            except ChildProcessError:
                child_reaped = True
        try:
            os.killpg(child_pid, 0)
        except ProcessLookupError:
            if child_reaped:
                return
        except PermissionError:
            pass
        time.sleep(0.02)

    try:
        os.killpg(child_pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    if not child_reaped:
        try:
            os.waitpid(child_pid, 0)
        except ChildProcessError:
            pass



def main() -> int:
    parser = _build_parser()
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

    reporter = _make_reporter(args.live_report)

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
        tty.setraw(sys.stdin.fileno(), when=termios.TCSANOW)

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
            readable, _, _ = select.select(watched, [], [], 1.0)
            _report_safely(reporter, "refresh", "running")
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
                    terminate_child_process(child_pid)
                    child_pid = -1
                    exit_code = 125
                    break
                output_hash.update(chunk)
                output_bytes += len(chunk)
                os.write(sys.stdout.fileno(), chunk)
                _report_safely(reporter, "observe", chunk)
                _report_safely(reporter, "refresh", "running")
        if child_pid > 0:
            _, wait_status = os.waitpid(child_pid, 0)
            exit_code = status_code(wait_status)
    except (KeyboardInterrupt, SessionTerminated) as exc:
        interrupted = True
        termination_signal = exc.signum if isinstance(exc, SessionTerminated) else signal.SIGINT
        if child_pid > 0:
            terminate_child_process(child_pid)
            child_pid = -1

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
        if _write_final_state(log_path, final, reporter, exit_code):
            return 125
    print(f"\n[world-seed-session] local journal: {log_path}", file=sys.stderr)
    if failure:
        print(f"[world-seed-session] ERROR: {failure}", file=sys.stderr)
        return 125
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
