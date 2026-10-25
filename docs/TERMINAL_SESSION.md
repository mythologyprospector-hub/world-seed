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


## Enroll a terminal profile

To make this the normal behavior for a chosen World Seed terminal profile, configure that profile's **custom command** to run the launcher from a known checkout:

```text
python3 /absolute/path/to/world-seed/scripts/terminal_session.py
```

Replace the example path with the actual checkout path. The launcher starts the user's configured shell (from `$SHELL`, falling back to Bash) inside the PTY. Create a separate profile such as **World Seed — journaled** first; do not replace the default profile until the enrolled profile has been tested and the user explicitly chooses that behavior.

This is profile-level enrollment, not machine-wide capture:
- Terminals started with the enrolled profile are journaled from shell startup.
- Existing terminal windows and other profiles are unaffected.
- The launcher requires a POSIX PTY and an interactive terminal.
- Keep a plain, unjournaled profile available for recovery if the launcher or journal path fails.
- The profile command points to a particular checkout. If that checkout is moved or removed, update the profile command.

The profile integration itself must be tested on the target terminal emulator before claiming native end-to-end acceptance. In particular, verify startup, interactive input, window resizing, Ctrl-C, Ctrl-D, shell exit status, journal permissions, and what happens if the journal cannot be written.

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
