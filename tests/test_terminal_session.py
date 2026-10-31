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


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "terminal_session.py"


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
        [sys.executable, str(SCRIPT), "--log-dir", str(tmp_path / "journal")],
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
        [sys.executable, str(SCRIPT), "--log-dir", str(blocked_log_root)],
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
        [sys.executable, str(SCRIPT), "--log-dir", str(tmp_path / "journal")],
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
