# Durable Terminal Journal

**Status:** Local durable capture is available through both command-scoped journaling and an opt-in interactive PTY session. A reviewed private handoff is a separate, explicit operation; neither journal mode automatically publishes raw terminal data.

## Purpose

Preserve terminal evidence while keeping the raw record local by default. Use command-scoped capture for one command or command sequence. Use the interactive PTY launcher when the goal is to record a whole interactive shell session.

## Interactive journaled terminal session

The opt-in `scripts/terminal_session.py` launcher starts an interactive shell under a pseudo-terminal (PTY) and durably records the terminal output as it arrives. It requires an interactive TTY; it is not a system-wide terminal hook and does not silently journal ordinary terminal windows.

The local JSON Lines journal is stored under:

```text
~/.local/state/world-seed-terminal-journal/interactive/
```

The session records start and finish events, terminal output, timestamps, session identity, working-directory context, output byte count and hash, and the shell's exit status. The launcher restores terminal settings when the session ends. Raw journal data remains local; this launcher does not upload it.

If a local prompt/launcher integration sets `WORLD_SEED_TERMINAL_MODE=journal` in the child shell environment, the prompt can display a JOURNAL label. An ordinary shell with no marker displays NORMAL. This label is only a visual indication of how the shell was launched. It is not proof that recording is healthy, and it does not itself perform recording or remote publication. See [BASH_PROMPT.md](BASH_PROMPT.md).

## Run a command

From a World Seed checkout:

```bash
python3 scripts/terminal_journal.py -- python -m unittest discover -s tests -v
```

For shell syntax such as pipes, redirects, or a sequence of commands:

```bash
python3 scripts/terminal_journal.py --shell 'python3 scripts/validate_seed.py && python -m unittest discover -s tests -v'
```

Only commands explicitly passed to this wrapper are captured. It does not silently record every command typed into an existing shell.

## What is recorded

- Command-start and command-finish events, with timestamps and a unique session ID.
- Output chunks for stdout and stderr, appended as they arrive.
- Exit status, elapsed time, byte counts, and output hashes.
- Available working-directory and Git context.

The command-scoped journal is JSON Lines under `~/.local/state/world-seed-terminal-journal/`, separated by project and date. The interactive PTY journal uses the `interactive/` subdirectory. On POSIX systems, directories use owner-only permissions and files use owner read/write permissions. Each event is appended and flushed with `fsync` to favor durability.

## Privacy boundary

- Raw command text and output stay local by default. Neither journaling mode uploads or publishes raw journal data.
- Output can contain credentials, tokens, private keys, recovery codes, or personal information. Do not capture sensitive commands or output.
- Owner-only local permissions reduce exposure but do not make captured content harmless.
- High-volume output may be slower because each event is durably written.

## Explicit reviewed private handoff

The local journal remains the source of raw terminal evidence. To share one selected session, prepare a bounded derivative report:

```bash
python3 scripts/terminal_handoff.py prepare --project world-seed
```

The command prints the private outbox path. Inspect that exact JSON report before publishing it. Review the command, stdout/stderr, paths, and redaction results; heuristic redaction is not guaranteed to remove every secret.

Publish only after review and deliberate confirmation:

```bash
python3 scripts/terminal_handoff.py publish --report /path/to/reviewed-report.json --confirm-publish
```

Publishing is restricted to the explicitly allowlisted `mythologyprospector-hub/miracle-depot` repository and verifies that the repository is private at publish time. After uploading a report, the publisher independently reads the exact report path back from the verified default branch and compares the returned bytes with the reviewed local report. A success receipt is written only when that read-back matches. If read-back fails or differs, the command reports that the upload may already exist and writes no success receipt; inspect the remote repository before retrying. A private repository is still visible to all authorized collaborators. The raw JSONL journal is never uploaded by this handoff path. Preparation does not upload anything, and publishing requires the explicit confirmation flag. After verification, the publisher updates `terminal-handoffs/latest.json` with report metadata, its URL, commit, and digest—never terminal output. This stable pointer lets an authorized reader discover the newest handoff without needing its unique URL. If report upload succeeds but index update fails, the command reports that partial outcome so the report is not mistaken for missing.

## Relationship to World Seed See

[WORLD_SEED_SEE.md](WORLD_SEED_SEE.md) documents a different mechanism: an explicitly invoked command wrapper that publishes bounded, heuristically redacted terminal snapshots to the private Intake Dock during a command. It is not the interactive PTY journal, does not publish the raw local journal, and is not a live chat connection. Do not treat the presence of a JOURNAL prompt label as evidence that World Seed See is running.

## Acceptance

The command-scoped local journal is accepted only when tests verify stdout/stderr capture, successful and failing commands, exact exit-code preservation, incremental persistence, append/reopen behavior, project separation, file permissions, interruption handling, and journal-write failure behavior. The interactive PTY launcher has its own lifecycle and terminal-restoration behavior and must be verified independently. Neither local journal mode alone lets an assistant remotely inspect the terminal. A reviewed handoff provides a bounded, explicit remote path; it is not live streaming. The latest index is discovery metadata, not a substitute for reviewing the report itself.
