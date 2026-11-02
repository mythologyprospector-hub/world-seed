from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from prepare_interactive_handoff import (
    extract_command_history,
    git_context,
    readable_terminal_text,
)


def test_readable_terminal_text_removes_ansi_and_normalizes_newlines() -> None:
    raw = "\x1b[32mgreen\x1b[0m\r\nnext\rline\x1b]0;terminal title\x07"
    assert readable_terminal_text(raw) == "green\nnext\nline"


def test_readable_terminal_text_drops_highlighted_paste_preview() -> None:
    raw = (
        "\x1b[7mprintf 'CHECK\\n'\x1b[27m\r\n\r"
        "\x1b[7mpwd\x1b[27m\r\n\r"
        "printf 'CHECK\\n'\r\nCHECK\r\n"
    )
    text = readable_terminal_text(raw)
    assert text.count("printf 'CHECK") == 1
    assert text.rstrip().endswith("CHECK")


def test_readable_terminal_text_removes_nonprinting_controls() -> None:
    assert readable_terminal_text("hello\x00world\x7f!") == "helloworld!"


def test_git_context_does_not_mislabel_non_repository_directory(tmp_path: Path) -> None:
    assert git_context(str(tmp_path)) == (None, None, None)


def test_git_context_reports_repository_for_repository_root() -> None:
    root = Path(__file__).resolve().parents[1]
    repository, branch, dirty = git_context(str(root))
    assert repository == root.name
    assert branch is None or isinstance(branch, str)
    assert dirty is None or isinstance(dirty, bool)


def test_extract_command_history_keeps_only_the_latest_ten_completed_commands() -> None:
    import base64

    chunks = []
    for number in range(12):
        command = f"printf 'COMMAND_{number}'"
        encoded = base64.b64encode(command.encode()).decode()
        chunks.append(
            f"prompt$ {command}\r\nOUTPUT_{number}\r\n"
            f"\x1b]777;world-seed-command;{number % 3};1793600000.{number:06d};{encoded}\x07"
        )
    transcript, recent, available, redacted = extract_command_history("".join(chunks))

    assert available is True
    assert redacted is False
    assert len(recent) == 10
    assert recent[0]["command"] == "printf 'COMMAND_2'"
    assert recent[-1]["command"] == "printf 'COMMAND_11'"
    assert recent[-1]["exit_code"] == 2
    assert "COMMAND_0" not in transcript
    assert "OUTPUT_2" in transcript
    assert "OUTPUT_11" in transcript


def test_extract_command_history_redacts_command_and_output() -> None:
    import base64

    command = "printf 'API_KEY=super-secret-value'"
    encoded = base64.b64encode(command.encode()).decode()
    raw = (
        "prompt$ printf output\r\nAPI_KEY=super-secret-value\r\n"
        f"\x1b]777;world-seed-command;0;1793600000.123456;{encoded}\x07"
    )
    transcript, recent, available, redacted = extract_command_history(raw)

    assert available is True
    assert redacted is True
    assert "super-secret-value" not in transcript
    assert "super-secret-value" not in recent[0]["command"]
    assert "[REDACTED]" in transcript


def test_extract_command_history_reports_unavailable_without_markers() -> None:
    transcript, recent, available, redacted = extract_command_history("ordinary terminal output")

    assert transcript == ""
    assert recent == []
    assert available is False
    assert redacted is False
