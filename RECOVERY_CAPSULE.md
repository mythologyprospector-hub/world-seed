# Recovery Capsule

**Status:** Local recovery-capsule generator supports terminal-session metadata and an optional schema-validated project-state record on `feat/durable-terminal-journal`. The focused 21-test local suite and both relevant GitHub Actions workflows passed on commit `ecf795e49704599cd67065999de2d2598283dd69`. Not a retrieval service; no network transfer or encryption is implemented.

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

To include a reviewed state record, add `--project-state PATH`. The JSON must validate against `schemas/recovery-project-state.schema.json`, and `project.name` must exactly match the `--project` slug. Install the development dependency first with `uv pip install --python .venv/bin/python -r requirements-dev.txt` when using the documented project virtual environment, or use the equivalent installation for your environment. Without `--project-state`, the capsule explicitly records `not_supplied`; it does not invent a state record.

If the journal was written to a non-default root, supply `--journal-root PATH`. Do not point this at an untrusted directory.

## What it contains

- Selected project slug and capsule schema version.
- Session IDs, timestamps, Git branch and dirty-state metadata when recorded.
- Whether a completion event was recorded, exit code, interruption flag, output-event count, byte counts, and the hashes recorded by the journal.
- Warnings for malformed or unreadable records.
- Optional complete project-state record, included only when explicitly supplied and validated against the versioned schema.
- Explicit limitations and a declaration that raw command/output text was excluded.

It deliberately omits command arguments, absolute working-directory paths, and stdout/stderr text. Hashes and exit codes are copied from journal records; they are **not independently verified** by this generator. A missing completion event is marked incomplete or unrecorded, never successful by inference.

## Safety and limitations

- This is a local report generator, not a bridge, API, token issuer, encryption system, or remote sync client.
- It does not claim that a test passed merely because an exit code is zero; meaningful claims still require matching test output or independently verified CI evidence.
- A capsule cannot reconstruct raw terminal output. A supplied project-state record helps recover canon, decisions, and next action, but schema validation only checks structure and format; it does not prove the record is true, current, authorized, or supported by its cited evidence. The record is included verbatim, so review its contents before sharing the private local capsule.
- Branch names and activity timing can themselves be sensitive. Review a capsule before sharing it.
- Project slug filtering prevents accidental cross-lane aggregation in this tool; it is not a security boundary against a local user with filesystem access.
- No upload, repository provisioning, destination choice, token-based retrieval, or key handling is implemented or authorized by this feature.

## Verification checkpoint

On commit `ecf795e49704599cd67065999de2d2598283dd69`:

- Local command `python -m unittest tests.test_terminal_journal tests.test_recovery_capsule tests.test_recovery_project_state -v`: **21 tests passed** after installing `requirements-dev.txt` into the project virtual environment.
- [Terminal Journal Tests workflow](https://github.com/mythologyprospector-hub/world-seed/actions/runs/39834428937): **passed**.
- [World Seed quality checks workflow](https://github.com/mythologyprospector-hub/world-seed/actions/runs/39834428834): **passed**.

These results apply only to the exact commit and test scope above. They do not establish that retrieval, encryption, or remote transfer works.

## Next milestone

Design and implement a reliable, reviewable way to maintain and refresh the state record from verified project evidence without inventing facts. The first version should remain local and target-agnostic. Only later should we select and authorize a retrieval destination or transport.