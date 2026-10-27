from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import pty
import select
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import terminal_session


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "terminal_session.py"


def test_unexpected_reporter_exception_disables_reporting_once(capsys) -> None:
    class BrokenReporter:
        enabled = True
        failure_warned = False

        def observe(self, _chunk: bytes) -> None:
            raise RuntimeError("synthetic reporter failure")

    reporter = BrokenReporter()
    terminal_session._report_safely(reporter, "observe", b"local output")
    terminal_session._report_safely(reporter, "refresh", "running")

    assert reporter.enabled is False
    warning = capsys.readouterr().err
    assert warning.count("Live reporting disabled after an error") == 1
    assert "RuntimeError" in warning
    assert "synthetic reporter failure" not in warning


def test_reporter_initialization_warning_does_not_echo_sensitive_exception(capsys) -> None:
    sensitive = "synthetic-token-value"
    with patch.object(terminal_session.live_report, "gh", side_effect=RuntimeError(sensitive)):
        reporter = terminal_session.LiveReporter()

    warning = capsys.readouterr().err
    assert reporter.enabled is False
    assert "Live-report initialization failed (RuntimeError)" in warning
    assert sensitive not in warning


def test_latest_pointer_warning_does_not_echo_sensitive_exception(capsys) -> None:
    repo_info = {"isPrivate": True, "defaultBranchRef": {"name": "main"}}
    with patch.object(terminal_session.live_report, "gh", return_value=type(
            "Result", (), {"stdout": json.dumps(repo_info)})()), \
         patch.object(terminal_session.live_report, "upload", return_value="blob-sha"), \
         patch.object(terminal_session.live_report, "publish_latest",
                      side_effect=RuntimeError("synthetic-report-secret")), \
         patch.object(terminal_session.live_report, "collect_shell_context", return_value={}), \
         patch.object(terminal_session.live_report, "format_shell_context", return_value=""):
        reporter = terminal_session.LiveReporter()

    warning = capsys.readouterr().err
    assert reporter.enabled is True
    assert "Latest-report pointer refresh failed (RuntimeError)" in warning
    assert "synthetic-report-secret" not in warning


def test_final_report_is_attempted_when_completion_record_fails(tmp_path: Path) -> None:
    class FakeReporter:
        enabled = True
        failure_warned = False
        calls = []

        def refresh(self, state: str, exit_code: int, *, force: bool) -> None:
            self.calls.append((state, exit_code, force))

    reporter = FakeReporter()
    final = {"event": "session_finished", "exit_code": 7}
    with patch.object(terminal_session, "append_record", side_effect=OSError("disk full")):
        failed = terminal_session._write_final_state(
            tmp_path / "journal.jsonl", final, reporter, 7
        )

    assert failed is True
    assert reporter.calls == [("finished", 7, True)]


def test_live_reporting_is_opt_in_and_no_live_report_remains_compatible() -> None:
    with patch.object(terminal_session, "LiveReporter") as reporter_class:
        default_args = terminal_session._parse_args([])
        assert default_args.live_report is False
        assert terminal_session._make_reporter(default_args.live_report) is None
        reporter_class.assert_not_called()

        opt_in_args = terminal_session._parse_args(["--live-report"])
        assert opt_in_args.live_report is True
        reporter = terminal_session._make_reporter(opt_in_args.live_report)
        assert reporter is reporter_class.return_value
        reporter_class.assert_called_once_with()

        legacy_args = terminal_session._parse_args(["--no-live-report"])
        assert legacy_args.live_report is False
        assert terminal_session._make_reporter(legacy_args.live_report) is None


def test_live_report_options_reject_conflicting_flags() -> None:
    with pytest.raises(SystemExit) as raised:
        terminal_session._parse_args(["--live-report", "--no-live-report"])
    assert raised.value.code == 2


def test_interactive_pty_session_journals_output_and_exit_status(tmp_path: Path) -> None:
    master, slave = pty.openpty()
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["SHELL"] = "/bin/bash"
    process = subprocess.Popen(
        [sys.executable, str(SCRIPT), "--log-dir", str(tmp_path / "journal")],
        stdin=slave, stdout=slave, stderr=slave, env=env, close_fds=True,
    )
    os.close(slave)
    captured = bytearray()
    try:
        os.write(master, b"printf 'PTY_SESSION_SENTINEL\\n'; exit 7\n")
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    chunk = b""
                if chunk:
                    captured.extend(chunk)
            if process.poll() is not None:
                # Drain any bytes already queued by the terminal.
                ready, _, _ = select.select([master], [], [], 0.1)
                if ready:
                    try:
                        captured.extend(os.read(master, 4096))
                    except OSError:
                        pass
                break
        assert process.poll() is not None, "PTY session did not exit before timeout"
        assert process.returncode == 7
        assert b"PTY_SESSION_SENTINEL" in captured
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)

    journal_files = list((tmp_path / "journal" / "interactive").glob("*.jsonl"))
    assert len(journal_files) == 1
    records = [json.loads(line) for line in journal_files[0].read_text().splitlines()]
    assert records[0]["event"] == "session_started"
    output = "".join(record.get("text", "") for record in records if record["event"] == "terminal_output")
    assert "PTY_SESSION_SENTINEL" in output
    finished = records[-1]
    assert finished["event"] == "session_finished"
    assert finished["exit_code"] == 7
    assert finished["output_bytes"] > 0
    if os.name == "posix":
        assert journal_files[0].stat().st_mode & 0o777 == 0o600
        assert journal_files[0].parent.stat().st_mode & 0o777 == 0o700


def test_interactive_pty_session_exits_cleanly_on_ctrl_d(tmp_path: Path) -> None:
    master, slave = pty.openpty()
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["SHELL"] = "/bin/bash"
    process = subprocess.Popen(
        [sys.executable, str(SCRIPT), "--no-live-report", "--log-dir", str(tmp_path / "journal")],
        stdin=slave, stdout=slave, stderr=slave, env=env, close_fds=True,
    )
    os.close(slave)
    captured = bytearray()
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and b"bash-" not in captured and b"$ " not in captured:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    captured.extend(os.read(master, 4096))
                except OSError:
                    break
            if process.poll() is not None:
                break
        assert process.poll() is None, "interactive shell exited before it was ready"
        os.write(master, b"\x04")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and process.poll() is None:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    captured.extend(os.read(master, 4096))
                except OSError:
                    break
        assert process.poll() is not None, "Ctrl-D did not close the interactive shell"
        assert process.returncode == 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)

    journal_files = list((tmp_path / "journal" / "interactive").glob("*.jsonl"))
    assert len(journal_files) == 1
    records = [json.loads(line) for line in journal_files[0].read_text().splitlines()]
    assert records[0]["event"] == "session_started"
    assert records[-1]["event"] == "session_finished"
    assert records[-1]["exit_code"] == 0

def test_interactive_pty_session_refuses_to_launch_without_writable_journal(tmp_path: Path) -> None:
    blocked_log_root = tmp_path / "not-a-directory"
    blocked_log_root.write_text("block journal creation")
    master, slave = pty.openpty()
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["SHELL"] = "/bin/bash"
    process = subprocess.Popen(
        [sys.executable, str(SCRIPT), "--no-live-report", "--log-dir", str(blocked_log_root)],
        stdin=slave, stdout=slave, stderr=slave, env=env, close_fds=True,
    )
    os.close(slave)
    captured = bytearray()
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and process.poll() is None:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    captured.extend(os.read(master, 4096))
                except OSError:
                    break
        assert process.poll() is not None, "launcher did not fail promptly when journaling was unavailable"
        assert process.returncode == 125
        assert b"cannot persist session start" in captured
        assert b"PTY_SESSION_SENTINEL" not in captured
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)



def test_interactive_pty_session_cleans_up_on_sigterm(tmp_path: Path) -> None:
    master, slave = pty.openpty()
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["SHELL"] = "/bin/bash"
    process = subprocess.Popen(
        [sys.executable, str(SCRIPT), "--no-live-report", "--log-dir", str(tmp_path / "journal")],
        stdin=slave, stdout=slave, stderr=slave, env=env, close_fds=True,
    )
    os.close(slave)
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    chunk = b""
                if b"bash-" in chunk or b"$ " in chunk:
                    break
            if process.poll() is not None:
                break
        assert process.poll() is None, "interactive shell exited before signal test"
        process.terminate()
        process.wait(timeout=5)
        assert process.returncode == 143
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)

    journal_files = list((tmp_path / "journal" / "interactive").glob("*.jsonl"))
    assert len(journal_files) == 1
    records = [json.loads(line) for line in journal_files[0].read_text().splitlines()]
    assert records[0]["event"] == "session_started"
    assert records[-1]["event"] == "session_finished"
    assert records[-1]["interrupted"] is True
    assert records[-1]["exit_code"] == 143



def test_terminate_child_process_escalates_when_sigterm_is_ignored() -> None:
    spec = importlib.util.spec_from_file_location("terminal_session", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    ready_read, ready_write = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(ready_read)
        os.setsid()
        import signal
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        os.write(ready_write, b"1")
        os.close(ready_write)
        while True:
            time.sleep(1)

    os.close(ready_write)
    try:
        assert os.read(ready_read, 1) == b"1"
        started = time.monotonic()
        module.terminate_child_process(child_pid)
        elapsed = time.monotonic() - started
        assert elapsed >= 0.45
        assert elapsed < 2.0
        try:
            os.waitpid(child_pid, os.WNOHANG)
        except ChildProcessError:
            pass
        else:
            raise AssertionError("terminated child was not reaped")
    finally:
        os.close(ready_read)
        try:
            os.killpg(child_pid, 9)
        except ProcessLookupError:
            pass
        try:
            os.waitpid(child_pid, 0)
        except ChildProcessError:
            pass
