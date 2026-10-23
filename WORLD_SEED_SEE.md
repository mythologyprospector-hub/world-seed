# World Seed See: Near-Real-Time Terminal Snapshots

**Status:** Explicit opt-in wrapper. GitHub Actions unit tests cover redaction, privacy refusal, initial-upload failure, bounded output, and exit-code preservation. A harmless live test against the configured private destination is still required before relying on it.

## Run

From the World Seed checkout:

```bash
python3 scripts/world_seed_see.py -- python -m unittest discover -s tests -v
```

Or inspect a small, harmless command:

```bash
python3 scripts/world_seed_see.py -- git status --short --branch
```

The wrapper streams combined stdout/stderr to the local terminal and creates a report in the private `mythologyprospector-hub/miracle-depot` repository. It verifies that the repository is private and reads its actual default branch before starting the command. If either check or the initial upload fails, the command does not start.

The report is refreshed about every 10 seconds and at command completion. Output is bounded (24 KiB by default; 1 KiB to 1 MiB allowed), the command's exit code is returned, and the report URL is printed for the assistant to reread when asked. This is **near-real-time snapshots, not a live terminal connection**; it does not push a notification into ChatGPT.

## Privacy and limitations

- Invocation is explicit: only the command placed after `--` is run and shared. Ordinary shell commands are not captured.
- The raw durable journal remains local. This wrapper sends only its bounded snapshot report to the configured private repository.
- Redaction is heuristic and cannot guarantee that secrets are removed. Do not run commands whose output or arguments may contain credentials, private keys, recovery codes, sensitive personal information, or other material you would not want stored in the private repository and its history.
- The report omits the local working-directory path. The command text is included after heuristic redaction.
- Each report refresh is a GitHub commit, so prior versions remain in repository history. Keep runs short and use only harmless output.
- A private repository is visible to all people and apps authorized for it. Private does not mean exclusive to this conversation.
- If a later snapshot upload fails, the local command continues; the printed report may then be stale. The final terminal output reports this limitation.

## Acceptance gate

Do not treat this as accepted until the required GitHub Actions checks pass and an operator runs a harmless synthetic command locally, confirms that output appears in the terminal, confirms the private report updates, verifies the final exit code and URL, and confirms that no sensitive output was used.
