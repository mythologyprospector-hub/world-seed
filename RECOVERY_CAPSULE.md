# Recovery Capsule

**Status:** Initial local metadata-only generator implemented on `feat/durable-terminal-journal`. Not a retrieval service; no network transfer or encryption is implemented.

## Purpose

Create a small project-scoped inventory of terminal-journal sessions that can help a fresh assistant understand what evidence exists without automatically copying raw command text or stdout/stderr into a shareable artifact.

## Generate a capsule

From the World Seed checkout, use the exact project lane name recorded by the journal. Example:

```bash
python3 scripts/build_recovery_capsule.py \
  --project world-seed \
  --output "$HOME/.local/state/world-seed-recovery/world-seed-capsule.json"
```

The output must be a new file; existing files are never overwritten. The file is created with owner read/write permissions on POSIX. The tool reads only the selected project's immediate journal directory and does not make network requests.

If the journal was written to a non-default root, supply `--journal-root PATH`. Do not point this at an untrusted directory.

## What it contains

- Selected project slug and capsule schema version.
- Session IDs, timestamps, Git branch and dirty-state metadata when recorded.
- Whether a completion event was recorded, exit code, interruption flag, output-event count, byte counts, and the hashes recorded by the journal.
- Warnings for malformed or unreadable records.
- Explicit limitations and a declaration that raw command/output text was excluded.

It deliberately omits command arguments, absolute working-directory paths, and stdout/stderr text. Hashes and exit codes are copied from journal records; they are **not independently verified** by this generator. A missing completion event is marked incomplete or unrecorded, never successful by inference.

## Safety and limitations

- This is a local report generator, not a bridge, API, token issuer, encryption system, or remote sync client.
- It does not claim that a test passed merely because an exit code is zero; meaningful claims still require matching test output or independently verified CI evidence.
- A metadata-only capsule cannot reconstruct the actual output or, by itself, tell an assistant the project's canon, current decisions, or next step. A future complete recovery package must combine it with an intentionally maintained project-state summary and links to independently verifiable evidence.
- Branch names and activity timing can themselves be sensitive. Review a capsule before sharing it.
- Project slug filtering prevents accidental cross-lane aggregation in this tool; it is not a security boundary against a local user with filesystem access.
- No upload, repository provisioning, destination choice, token-based retrieval, or key handling is implemented or authorized by this feature.

## Initial verification gates

Tests cover omission of command/output text and absolute working paths, project-lane separation, invalid project names, incomplete sessions, malformed records, private output-file mode, and refusal to overwrite an existing output. The generator is not considered accepted until the operator's local suite and the relevant GitHub Actions checks pass on the exact commit.

## Next milestone

After the metadata-only report is verified, design the human-authored project-state portion of the recovery package: canonical project identity, current verified commit/checks, decisions and constraints, unresolved questions, and one safe next action. Only later should we select and authorize a retrieval destination or transport.
