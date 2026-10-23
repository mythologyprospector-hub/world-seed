# World Seed See: Near-Real-Time Terminal Snapshots

**Status:** Explicit opt-in wrapper. GitHub Actions unit tests cover redaction, privacy refusal, initial-upload failure, bounded output, exit-code preservation, and prompt-like shell context. A harmless live snapshot test has demonstrated local output, intermediate remote snapshots, and final exit-code preservation.

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

Each report includes a prompt-like context snapshot: local time, user and host, current working directory, Git branch, and whether the working tree is clean or dirty. The report refreshes this context along with command output about every 10 seconds and at completion. This reconstructs useful dashboard fields; it does not literally capture Bash's rendered prompt or shell history. At the start of each run, the wrapper also updates the stable private-repository pointer [terminal-live/LATEST.txt](https://github.com/mythologyprospector-hub/miracle-depot/blob/main/terminal-live/LATEST.txt), which identifies the newest report path and URL. The report URL is printed as before. Output is bounded (24 KiB by default; 1 KiB to 1 MiB allowed), and the command's exit code is returned. This makes the newest report discoverable without copying its unique URL, but it is still **near-real-time snapshots, not a live terminal connection**; it does not push a notification into ChatGPT or wake this conversation.

## Privacy and limitations

- Invocation is explicit: only the command placed after `--` is run and shared. Ordinary shell commands are not captured.
- The raw durable journal remains local. This wrapper sends only its bounded snapshot report to the configured private repository.
- Redaction is heuristic and cannot guarantee that secrets are removed. Do not run commands whose output or arguments may contain credentials, private keys, recovery codes, sensitive personal information, or other material you would not want stored in the private repository and its history.
- Because prompt-like context is included, reports contain the local username, hostname, and working-directory path. These are uploaded only for explicitly wrapped commands, but remain visible to everyone and every app authorized for the private destination and persist in commit history. Do not use this wrapper from a directory whose path or machine identity you do not want shared. The command text is included after heuristic redaction.
- Each report refresh is a GitHub commit, so prior versions remain in repository history. Keep runs short and use only harmless output.
- A private repository is visible to all people and apps authorized for it. Private does not mean exclusive to this conversation.
- If a later snapshot upload fails, the local command continues; the printed report may then be stale. The final terminal output reports this limitation.

## Acceptance gate

Do not treat this as accepted until the required GitHub Actions checks pass and an operator runs a harmless synthetic command locally, confirms that output appears in the terminal, confirms the private report updates, verifies the final exit code and URL, and confirms that no sensitive output was used. The report should also show the expected user/host, working directory, branch, and clean/dirty state.
