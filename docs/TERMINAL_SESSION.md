# World Seed interactive terminal sessions

## What this provides

`scripts/terminal_session.py` starts an interactive shell on a pseudo-terminal (PTY) and writes a local JSON Lines journal while terminal output is being displayed. It is an opt-in session launcher, not a hook that silently captures every terminal on the computer.

From the World Seed checkout, start an enrolled session with:

```bash
python3 scripts/terminal_session.py
```

When you exit that shell, the launcher prints the local journal path. The journal lives under:

```text
~/.local/state/world-seed-terminal-journal/interactive/
```

Use `--log-dir PATH` to select a different local journal root, or `--shell /absolute/path/to/shell` to choose an interactive shell. The journal directory is created with owner-only permissions (0700) and journal files with owner-only permissions (0600) on POSIX systems.

## Privacy and publication

- The journal is local-only. This launcher does not upload transcripts to GitHub or Miracle Depot.
- Terminal output may contain credentials, personal information, or other secrets. Treat the journal as sensitive even though its permissions are restricted.
- Do not publish the raw journal. Review and redact a bounded excerpt, then use the existing explicit terminal-handoff publication flow if a report is needed.
- File permissions are not encryption. They do not protect against another process running as the same user, root, backups, or a compromised machine.

## Current limits

- Capture begins only after starting this launcher. It does not automatically enroll an existing terminal window or all terminal sessions.
- It captures the PTY output stream; it does not guarantee semantic command boundaries for every interactive application.
- This is a shell session, not a replacement for terminal emulator features. Test terminal-specific workflows before relying on it for long-running work.
- End-to-end native integration is not complete until an ordinary enrolled World Seed terminal session, intermediate evidence, handoff/readback, and failure recovery are verified together.

## Safe smoke test

Use a disposable terminal and synthetic text only:

```bash
python3 scripts/terminal_session.py
```

At the new prompt, type:

```bash
printf 'WORLD_SEED_SESSION_SMOKE_TEST\n'
exit
```

Check that the displayed journal path exists and that the JSONL file contains the synthetic marker. Do not use real credentials or sensitive output for acceptance tests.
