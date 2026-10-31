# World Seed See: Near-Real-Time Terminal Snapshots

**Status:** Explicit opt-in wrapper. GitHub Actions unit tests cover redaction, privacy refusal, initial-upload failure, bounded output, exit-code preservation, prompt-like shell context, and concurrent-write recovery. On 2026-10-31, the full local suite passed (269 tests and 54 subtests), and both required GitHub Actions workflows passed for the pointer/concurrency repair. This is verified near-real-time snapshot reporting, not a live terminal connection.

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

Each report includes a prompt-like context snapshot: local time, user and host, current working directory, Git branch, and whether the working tree is clean or dirty. The report refreshes this context along with command output about every 10 seconds and at completion. This reconstructs useful dashboard fields; it does not literally capture Bash's rendered prompt or shell history. At the start of each run, the wrapper also updates the stable private-repository pointer [terminal-live/LATEST-SEE.txt](https://github.com/mythologyprospector-hub/miracle-depot/blob/main/terminal-live/LATEST-SEE.txt), which identifies the newest World Seed See report path and URL. This is intentionally separate from `terminal-live/LATEST.txt`, which remains available to the general terminal-report stream. The report URL is printed as before. Output is bounded (24 KiB by default; 1 KiB to 1 MiB allowed), and the command's exit code is returned. If a GitHub Contents API write reports HTTP 409, the uploader waits briefly, fetches the current remote blob SHA for that path, and retries with the refreshed SHA (up to three total write attempts). Non-conflict errors are not retried. This reduces same-file concurrent-write failures; it cannot guarantee publication during persistent API, authentication, network, or repository failures. The command's local execution continues if a later snapshot upload fails, and the final terminal output warns that the report may be stale. The report is still **near-real-time snapshots, not a live terminal connection**; it does not push a notification into ChatGPT or wake this conversation.

## Privacy and limitations

- Invocation is explicit: only the command placed after `--` is run and shared. Ordinary shell commands are not captured.
- The raw durable journal remains local. This wrapper sends only its bounded snapshot report to the configured private repository.
- Redaction is heuristic and cannot guarantee that secrets are removed. Do not run commands whose output or arguments may contain credentials, private keys, recovery codes, sensitive personal information, or other material you would not want stored in the private repository and its history.
- Because prompt-like context is included, reports contain the local username, hostname, and working-directory path. These are uploaded only for explicitly wrapped commands, but remain visible to everyone and every app authorized for the private destination and persist in commit history. Do not use this wrapper from a directory whose path or machine identity you do not want shared. The command text is included after heuristic redaction.
- Each report refresh is a GitHub commit, so prior versions remain in repository history. Keep runs short and use only harmless output.
- A private repository is visible to all people and apps authorized for it. Private does not mean exclusive to this conversation.
- If a later snapshot upload fails, the local command continues; the printed report may then be stale. The final terminal output reports this limitation.

## Acceptance gate

## Acceptance evidence (2026-10-23)

- Both required GitHub Actions workflows passed on the 2026-10-31 pointer/concurrency repair commit.
- A fresh harmless synthetic command ran locally and printed `World Seed See prompt-context smoke test passed`.
- The private `terminal-live/LATEST-SEE.txt` pointer is the dedicated World Seed See discovery pointer; `LATEST.txt` is kept separate for the general terminal-report stream.
- No sensitive command output was used.

The 2026-10-23 live smoke test remains historical evidence for the original snapshot path. The 2026-10-31 CI result verifies the later retry/pointer code, but a fresh live publication test after that change remains a separate acceptance check. Any later code changes must be verified again against their resulting commit.
