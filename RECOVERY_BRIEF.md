# Recovery Brief Renderer

**Status:** A local Markdown renderer and focused tests are present on `feat/durable-terminal-journal`. The renderer is an orientation aid, not independent evidence, a freshness audit, or an authorization mechanism.

## Purpose

Turn an existing, human-reviewed recovery-state JSON record into a compact briefing that can be inspected and supplied to a fresh conversation. The brief brings together project identity, canon pointers, recorded verification claims, accepted/rejected/open/superseded decisions, current work and risks, protected areas, one next action, and retrieval instructions.

## Run locally

From a World Seed checkout with its development dependencies installed:

```bash
.venv/bin/python scripts/render_recovery_brief.py \
  --project world-seed \
  --state /path/to/reviewed-world-seed-state.json
```

The brief is written to standard output. Redirect it to a local file only after choosing an appropriate private destination and filename. The renderer does not create or overwrite files.

## Trust and safety rules

- The source JSON must validate against the versioned recovery-state schema and its `project.name` must exactly match `--project`.
- The renderer performs no network access, Git inspection, test execution, CI lookup, state refresh, or file writes.
- Recorded verification claims are labelled as recorded claims, not freshly verified results. A verification commit that differs from `record.describes_commit` is called out.
- If recorded freshness is not `current`, the brief shows a prominent warning. Even `current` is only the state record's label; this renderer does not establish that it is accurate.
- Repository URL user information, query strings, and fragments are removed from the rendered URL. This is not a general-purpose secret scanner.
- All other state text is rendered as supplied. Do not place credentials, tokens, private keys, raw terminal output, or other secrets in the state record. Review the finished brief before sharing it.
- The recorded next-action authorization is descriptive only. It does not create permission. Approval remains specific to the exact action and scope previously agreed.
- Missing or conflicting facts must remain unknown; the renderer must not fill gaps with guesses.

## Not implemented

This is not the retrieval bridge. It does not automatically find the state record in a fresh conversation, independently open evidence, query GitHub, establish current checkout freshness, encrypt records, manage keys, select a remote destination, or transfer any data. Those capabilities require separate design and explicit authorization.

## Acceptance checks

The focused tests cover stale warnings, key sections, verification commit mismatch, URL credential/query redaction, and rejection of a wrong project slug. Run the full focused suite documented in `RECOVERY_STATE_CONTRACT.md`; report the exact local result and hosted workflow status separately.
