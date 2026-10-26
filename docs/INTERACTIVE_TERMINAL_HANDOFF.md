# Interactive terminal handoff

This helper prepares a **local, reviewable report** from one exact session in
`~/.local/state/world-seed-terminal-journal/interactive/`. It does not upload
anything. Select the session UUID from the local journal and run:

```sh
python3 scripts/prepare_interactive_handoff.py --session SESSION_UUID
```

Inspect the resulting JSON in the private local outbox before any publication.
Heuristic redaction can miss sensitive data; review the entire report. Never
publish raw journals. Upload remains a separate, explicit action through
`scripts/terminal_handoff.py publish --report PATH --confirm-publish`, and only
after the report has been reviewed and publication authorized. Verify the exact
uploaded report from the private Miracle Depot repository; a successful local
preparation alone is not proof of remote publication or read-back.

The report includes a digest of the source journal for provenance. It is not
proof that the journal itself is trustworthy, and the digest does not replace
review of the report contents.

## Session outcome fields

`completion` describes whether a session-finished record was captured; it does
not mean the command succeeded. `command_outcome` separately reports
`succeeded`, `failed`, `interrupted`, or `unknown`. Interruption takes
precedence over the exit code, and missing or contradictory evidence is
reported as `unknown`. These fields describe recorded evidence, not proof that
the command's intended work was correct.
