# Durable Terminal Journal

**Status:** Incremental local capture is implemented on this feature branch. Automatic shell-wide capture and remote synchronization are not enabled.

## Purpose

Conversation context is temporary. Terminal evidence must survive a lost chat, a closed terminal, or a reboot. The journal records command executions as durable, machine-readable evidence that a fresh assistant session can retrieve or the operator can hand off without copying a terminal wall.

## Initial capture interface

Run assistant-provided commands through `scripts/terminal_journal.py`:

```bash
python3 scripts/terminal_journal.py -- python -m unittest discover -s tests -v
```

For shell syntax (pipes, redirects, or multiple commands), use:

```bash
python3 scripts/terminal_journal.py --shell 'python3 scripts/validate_seed.py && python3 -m unittest discover -s tests -v'
```

The wrapper streams output to the terminal and writes a `command_started` event before launching the child. Each stdout/stderr chunk is then appended as an `output` event and flushed with `fsync` before those bytes are displayed. The output readers use non-blocking-when-available buffered reads so small chunks can be delivered without waiting for a full buffer. A final `command_finished` event records exit status, elapsed time, byte counts, output hashes, interruption state, and journal-write errors. Events share a session ID and sequence numbers. On keyboard interruption, the wrapper terminates the child and drains reader threads before writing the completion event. A host or wrapper crash can still leave a recoverable partial session rather than losing all output until command completion.

The journal uses event-oriented JSON Lines. To reconstruct output, concatenate each session's `output` event `text` fields separately by `stream` (`stdout` or `stderr`) in sequence order. A missing `command_finished` event means the session did not record normal completion; do not infer an exit status.

This initial interface captures commands deliberately routed through the wrapper. It does **not** silently capture every arbitrary command typed into an existing shell. Automatic shell-wide capture is a separate step because shell hooks and terminal stream capture can expose secrets and can interfere with interactive sessions.

## Local durability and privacy

- Default storage is under `~/.local/state/world-seed-terminal-journal/`, partitioned by project and UTC date.
- POSIX directories are created with owner-only permissions and journal files with owner read/write permissions.
- Raw stdout/stderr and command text stay local by default.
- Each event is appended and fsynced separately. This favors recoverability over throughput and may slow commands that produce very high volumes of output.
- Never place credentials, access tokens, passwords, private keys, recovery codes, or sensitive personal data in commands or output. Local permissions reduce exposure but do not make captured content harmless.
- The journal does not upload, publish, or change GitHub state.

## Remote synchronization boundary

Remote delivery must use a separately approved private destination with explicit project/lane isolation. The Intake Dock remains an unproven scaffold, and Miracle Depot is not assumed to be the final destination. Do not treat a private repository as lane-level isolation: repository privacy is a repository-wide access boundary.

Automatic sync is not enabled. Before enabling it, implement and test explicit destination configuration, project/lane validation, bounded batches, integrity receipts, retry behavior, duplicate handling, and a reviewable secret-redaction policy. Heuristic redaction is not a guarantee that a record contains no secrets. Do not sync raw terminal recordings by default.

## Recovery workflow

1. Retrieve the newest session summary and journal records from the private, authorized destination when sync is available.
2. Read the session summary first; inspect individual records for relevant commands, errors, and test outcomes.
3. Distinguish observed command output from interpretation. A captured PASS is evidence that a command printed PASS, not proof of unrelated behavior.
4. Treat a session without a completion event as interrupted or incomplete, not as a successful run.
5. Resume from the last verified checkpoint. Do not rerun destructive or consequential commands merely because the conversation ended.
6. Before testing repository changes, remind the operator to run `git pull --ff-only` when appropriate and inspect the current branch/worktree first.

## Acceptance gates

The feature is not complete until tests cover successful and failing commands, exact exit-code preservation, stdout/stderr capture, incremental output durability, append/reopen behavior, safe file permissions, project separation, interrupted execution behavior, journal-write failures, and recovery from a fresh conversation. Remote sync additionally requires synthetic-only end-to-end transfer tests and an explicitly approved exact private target. Do not claim automatic terminal capture or remote sync until those behaviors are demonstrated.
