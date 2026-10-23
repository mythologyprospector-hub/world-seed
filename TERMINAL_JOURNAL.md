# Durable Terminal Journal

**Status:** Initial local-only implementation; this does not yet provide remote handoff or near-real-time sharing.

## Purpose

Run a command while its output remains visible in the terminal and is durably recorded locally. This avoids losing all useful command evidence when a conversation or terminal session ends.

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

The journal is JSON Lines under `~/.local/state/world-seed-terminal-journal/`, separated by project and date. On POSIX systems, directories use owner-only permissions and files use owner read/write permissions. Each event is appended and flushed with `fsync` to favor durability.

## Privacy boundary

- Raw command text and output stay local by default. This feature does not upload or publish anything.
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

Publishing is restricted to the explicitly allowlisted `mythologyprospector-hub/miracle-depot` repository and verifies that the repository is private at publish time. A private repository is still visible to all authorized collaborators. The raw JSONL journal is never uploaded by this handoff path. Preparation does not upload anything, and publishing requires the explicit confirmation flag.

## Acceptance

The local journal is accepted only when tests verify stdout/stderr capture, successful and failing commands, exact exit-code preservation, incremental persistence, append/reopen behavior, project separation, file permissions, interruption handling, and journal-write failure behavior. This local journal alone does not let an assistant remotely inspect the terminal. Remote handoff and near-real-time snapshots are separate, explicitly bounded steps.
