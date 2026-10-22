# Durable Terminal Journal

**Status:** Initial implementation contract; automatic remote synchronization and arbitrary-command shell capture are not yet accepted.

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

The wrapper streams output to the terminal while also recording stdout, stderr, exit status, start/end timestamps, elapsed time, working directory, repository root, branch, and dirty-state summary. A nonzero child exit status is returned to the caller.

This initial interface captures commands deliberately routed through the wrapper. It does **not** silently capture every arbitrary command typed into an existing shell. Automatic shell-wide capture is a separate step because shell hooks and terminal stream capture can expose secrets and can interfere with interactive sessions.

## Local durability and privacy

- Default storage is under `~/.local/state/world-seed-terminal-journal/`, partitioned by project and session date.
- POSIX directories are created with owner-only permissions and journal files with owner read/write permissions.
- Raw stdout/stderr and command text stay local by default.
- Records are append-only JSON Lines. Each completed invocation is flushed to disk before the wrapper exits.
- Never place credentials, access tokens, passwords, private keys, recovery codes, or sensitive personal data in commands or output. Local permissions reduce exposure but do not make captured content harmless.
- The journal does not upload, publish, or change GitHub state.

## Remote synchronization boundary

Remote delivery must use the existing private Intake Dock / Miracle Depot compartment model, not the public World Seed repository. Each project must have its own lane. A private repository is still a repository-wide access boundary, not a lane-level permission boundary.

Automatic sync is not enabled by this initial implementation. Before enabling it, implement and test explicit destination configuration, project/lane validation, bounded batches, integrity receipts, retry behavior, duplicate handling, and a reviewable secret-redaction policy. Heuristic redaction is not a guarantee that a record contains no secrets. Do not sync raw terminal recordings by default.

## Recovery workflow

1. Retrieve the newest session summary and journal records from the private, authorized destination when sync is available.
2. Read the session summary first; inspect individual records for relevant commands, errors, and test outcomes.
3. Distinguish observed command output from interpretation. A captured PASS is evidence that a command printed PASS, not proof of unrelated behavior.
4. Resume from the last verified checkpoint. Do not rerun destructive or consequential commands merely because the conversation ended.
5. Before testing repository changes, remind the operator to run `git pull --ff-only` when appropriate and inspect the current branch/worktree first.

## Acceptance gates

The feature is not complete until tests cover successful and failing commands, exact exit-code preservation, stdout/stderr capture, append/reopen durability, safe file permissions, project separation, interrupted execution behavior, and recovery from a fresh conversation. Remote sync additionally requires synthetic-only end-to-end transfer tests and an explicitly approved exact private target. Do not claim automatic terminal capture or remote sync until those behaviors are demonstrated.
