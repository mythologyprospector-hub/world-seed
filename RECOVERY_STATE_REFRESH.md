# Recovery State Refresh Design

**Status:** Initial read-only audit implementation and focused CI tests are present on `feat/durable-terminal-journal`. This document does not authorize remote retrieval, encryption, or data transfer.

## Problem

The versioned project-state record has the right broad sections, but it is currently a hand-maintained template. A future assistant must not mistake stale notes for current repository truth, silently rewrite human decisions, or claim a test passed because a log or summary merely says so.

## Implemented first milestone: read-only audit

The local audit command reads one explicitly selected state JSON file and inspects one explicitly selected local Git checkout. It produces a separate **audit report**; it does not edit or replace the state file. It may propose a freshness value based on local Git comparisons, but it must not propose changing `record.describes_commit` merely to match the observed HEAD: that field says which commit the human-reviewed state actually describes, not whichever commit happens to be checked out.

The initial implementation:

1. Validate the supplied state against the versioned JSON Schema.
2. Verify the requested project slug against `state.project.name`.
3. Inspect the selected checkout's Git root, configured origin URL, HEAD commit, branch/detached state, and tracked/untracked dirty status.
4. Compare observed repository identity and HEAD with the state record's repository URL and `record.describes_commit`.
5. Report mismatches and freshness conservatively. A dirty checkout, unknown recorded commit, repository mismatch, or commit mismatch must not be labelled current.
6. Preserve all human-maintained content unchanged. Only propose the derived freshness value; report observed HEAD separately as evidence, not as a suggested replacement for `record.describes_commit`.
7. Emit a new report file only; refuse to overwrite an existing path. Use owner-only file permissions on POSIX.
8. Run locally without network access. Do not call GitHub, upload data, or access credentials.
9. Use explicit statuses such as `pass`, `mismatch`, and `unknown`; never turn unavailable evidence into success.
10. Validate any generated JSON report with tests and keep the report distinct from independent test/CI evidence.

## Non-goals for this version

- No automatic edits to the project-state source record.
- No inferred decisions, project purpose, canon, risks, or next action.
- No running project tests automatically.
- No treating local Git metadata as proof that a commit passed tests or CI.
- No remote GitHub queries or Actions-status claims.
- No encryption, key storage, token issuance, retrieval API, or remote transfer.
- No changes to the terminal journal's raw event records.
- No shell startup changes or automatic shell-wide capture.

## Run the audit

From the World Seed checkout, after installing the pinned development dependency into the project virtual environment, run:

```bash
.venv/bin/python scripts/audit_recovery_state.py \
  --project world-seed \
  --state /path/to/reviewed-world-seed-state.json \
  --repo /path/to/world-seed-checkout \
  --output \"$HOME/.local/state/world-seed-recovery/world-seed-audit.json\"
```

Replace both input paths with the actual reviewed state file and checkout. The output path must not already exist. The tool is read-only with respect to the state input and writes a private report. It does not create a state record from the template for you.

## Report contract

The report should contain:

- Report schema/version and UTC creation timestamp.
- State-file path represented only as a user-local diagnostic if needed; avoid absolute paths in portable/shareable fields.
- Project slug and recorded repository URL/commit/freshness.
- Observed Git root identity, origin URL, HEAD, branch or detached state, and dirty status.
- Explicit comparisons for project identity, origin, commit, and freshness.
- A freshness proposal derived from local Git comparisons. The observed HEAD is recorded separately; it is not automatically proposed as the state record's described commit.
- Limitations: local Git inspection does not verify tests, hosted CI, authorization, or truth of human-authored claims.

Do not include environment variables, command arguments from journal records, terminal output, secret-file contents, tokens, or private key material.

## Acceptance tests

- Valid, matching clean checkout is reported consistently without rewriting the state file.
- Dirty checkout is not called current.
- Commit mismatch and origin mismatch are surfaced independently.
- Invalid JSON, invalid schema, wrong project, missing Git checkout, and missing origin fail closed or are explicitly unknown.
- Detached HEAD is represented accurately.
- Report output is private and an existing output is never overwritten.
- State input bytes remain unchanged on every path, including failures.
- Report never claims local Git inspection proves test or CI success.
- No network requests are made.
- The local suite and hosted workflows pass on the exact implementation commit.

## Current verification checkpoint

On commit `7ff2801f8d941c7123bb5c5010c65ece9361d932`, the operator's focused local suite passed 27/27 tests. The [World Seed quality checks run](https://github.com/mythologyprospector-hub/world-seed/actions/runs/39836684488) reports completed/success, with all listed steps successful. The [Terminal Journal Tests run](https://github.com/mythologyprospector-hub/world-seed/actions/runs/39836684620) also reports completed/success and its test step succeeded; however, the jobs endpoint still returned `in_progress` for the job despite all listed steps being completed successfully. Preserve that endpoint inconsistency rather than treating the job-level status as independently confirmed.

## Authorization boundary

The operator has authorized continued development of the local recovery workflow. That does not authorize a merge, destructive changes, secret disclosure, remote provisioning, or transfer of records. Keep this milestone local and reversible.
