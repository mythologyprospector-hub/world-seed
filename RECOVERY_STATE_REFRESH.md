# Recovery State Refresh Design

**Status:** Design checkpoint for the next local-only milestone. This document does not authorize remote retrieval, encryption, or data transfer.

## Problem

The versioned project-state record has the right broad sections, but it is currently a hand-maintained template. A future assistant must not mistake stale notes for current repository truth, silently rewrite human decisions, or claim a test passed because a log or summary merely says so.

## First implementation: read-only audit and refresh proposal

Implement a local command that reads one explicitly selected state JSON file and inspects one explicitly selected local Git checkout. It produces a separate **audit/proposal report**; it does not edit or replace the state file.

The first version should:

1. Validate the supplied state against the versioned JSON Schema.
2. Verify the requested project slug against `state.project.name`.
3. Inspect the selected checkout's Git root, configured origin URL, HEAD commit, branch/detached state, and tracked/untracked dirty status.
4. Compare observed repository identity and HEAD with the state record's repository URL and `record.describes_commit`.
5. Report mismatches and freshness conservatively. A dirty checkout, unknown recorded commit, repository mismatch, or commit mismatch must not be labelled current.
6. Preserve all human-maintained content unchanged and list suggested metadata changes separately.
7. Emit a new report file only; refuse to overwrite an existing path. Use owner-only file permissions on POSIX.
8. Run locally without network access. Do not call GitHub, upload data, or access credentials.
9. Use explicit statuses such as `pass`, `mismatch`, and `unknown`; never turn unavailable evidence into success.
10. Validate any generated JSON report with tests and keep the report distinct from independent test/CI evidence.

## Non-goals for the first version

- No automatic edits to the project-state source record.
- No inferred decisions, project purpose, canon, risks, or next action.
- No running project tests automatically.
- No treating local Git metadata as proof that a commit passed tests or CI.
- No remote GitHub queries or Actions-status claims.
- No encryption, key storage, token issuance, retrieval API, or remote transfer.
- No changes to the terminal journal's raw event records.
- No shell startup changes or automatic shell-wide capture.

## Report contract

The report should contain:

- Report schema/version and UTC creation timestamp.
- State-file path represented only as a user-local diagnostic if needed; avoid absolute paths in portable/shareable fields.
- Project slug and recorded repository URL/commit/freshness.
- Observed Git root identity, origin URL, HEAD, branch or detached state, and dirty status.
- Explicit comparisons for project identity, origin, commit, and freshness.
- Suggested state metadata changes, each with a reason and source evidence.
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

## Authorization boundary

The operator has authorized continued development of the local recovery workflow. That does not authorize a merge, destructive changes, secret disclosure, remote provisioning, or transfer of records. Keep this milestone local and reversible.
