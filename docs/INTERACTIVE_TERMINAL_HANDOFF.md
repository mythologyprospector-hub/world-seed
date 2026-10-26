# Interactive terminal journal handoff

The interactive PTY launcher writes a local journal under
`~/.local/state/world-seed-terminal-journal/interactive/`. The raw journal is
sensitive and is never uploaded by the launcher.

## Prepare a local report

After the enrolled terminal session has finished, run from the World Seed
checkout:

```bash
python3 scripts/terminal_handoff.py prepare --project world-seed
```

The handoff tool now reads the interactive PTY lane as well as command-wrapper
journals. To select an exact session, add `--session SESSION_UUID`. The report
is written to the private local outbox with owner-only permissions. Preparation
does not upload anything.

The report includes a bounded terminal-output excerpt, redaction status,
session identity, and the recorded exit status. PTY output can include shell
input echoed by the terminal and may contain secrets. Heuristic redaction is
not a guarantee: open and inspect the prepared JSON report before publishing.
If it contains unrelated, sensitive, or excessive output, do not publish it.

## Explicit publication

Only after reviewing the exact report and deciding it is safe to share, use
the printed report path:

```bash
python3 scripts/terminal_handoff.py publish --report /absolute/path/to/reviewed-report.json --confirm-publish
```

Publication remains a separate explicit action. The tool verifies the approved
destination is private and reads the uploaded bytes back before writing a
success receipt. A read-back failure or mismatch is not success; inspect the
remote repository before retrying.

## Limits

- This bridges a completed local PTY journal into the existing reviewed handoff
  workflow; it does not stream intermediate output to the assistant.
- It does not grant this chat direct access to local files.
- Raw journals remain local. Never upload the journal itself.
- Do not use real secrets or personal information in acceptance tests.
