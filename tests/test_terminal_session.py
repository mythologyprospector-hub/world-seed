from __future__ import annotations

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
        os.write(master, b"\\x04")
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
