from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from prepare_interactive_handoff import git_context, readable_terminal_text


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
