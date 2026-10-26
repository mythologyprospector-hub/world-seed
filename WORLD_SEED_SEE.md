# World Seed See: Near-Real-Time Terminal Snapshots

**Status:** Explicit opt-in wrapper. GitHub Actions unit tests cover redaction, privacy refusal, initial-upload failure, bounded output, exit-code preservation, and prompt-like shell context. Verification passed on 2026-10-23: both required GitHub Actions workflows passed, and a fresh harmless live smoke test confirmed local output, the uploaded report, all expected prompt-like context fields, and exit code 0. A further launcher-stability smoke test passed on 2026-10-24. This is verified near-real-time snapshot reporting, not a live terminal connection.

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

## Stable installed launcher

The intended installed launcher is `$HOME/.local/bin/world-seed-see`, resolving through the user's `PATH`. Its stable source should be the tracked script `$HOME/projects/world-seed/scripts/world_seed_see.py` from the clean `main` checkout—not a temporary or dirty feature worktree. The launcher must forward arguments with `"$@"`:

```bash
#!/usr/bin/env bash
set -eu
exec python3 "$HOME/projects/world-seed/scripts/world_seed_see.py" "$@"
```

A previous local inspection and harmless smoke test are recorded below. To gather current evidence without asking the operator to paste output into chat, run this **read-only diagnostic** from a World Seed checkout through the installed wrapper:

```bash
world-seed-see -- bash scripts/inspect_world_seed_see_launcher.sh
```

The report includes the resolved launcher path, a bounded launcher source excerpt, current World Seed worktree paths/branches, and checkout status. The wrapper uploads this output and the local machine/path context to the configured private repository. Do not run it if you do not want those paths stored there. The diagnostic does not change files and does not decide acceptance automatically; the builder must compare the launcher target and any referenced script with the actual worktree list.

Do not wrap a shell script containing single quotes inside a single-quoted `bash -lc '...'` argument; nested quoting can cause the wrapper to receive an empty command. Run multi-step setup scripts directly, and use the wrapper for harmless final smoke tests.

## Privacy and limitations

- Invocation is explicit: only the command placed after `--` is run and shared. Ordinary shell commands are not captured.
- The raw durable journal remains local. This wrapper sends only its bounded snapshot report to the configured private repository.
- Redaction is heuristic and cannot guarantee that secrets are removed. Do not run commands whose output or arguments may contain credentials, private keys, recovery codes, sensitive personal information, or other material you would not want stored in the private repository and its history.
- Because prompt-like context is included, reports contain the local username, hostname, and working-directory path. These are uploaded only for explicitly wrapped commands, but remain visible to everyone and every app authorized for the private destination and persist in commit history. Do not use this wrapper from a directory whose path or machine identity you do not want shared. The command text is included after heuristic redaction.
- Each report refresh is a GitHub commit, so prior versions remain in repository history. Keep runs short and use only harmless output.
- A private repository is visible to all people and apps authorized for it. Private does not mean exclusive to this conversation.
- If a later snapshot upload fails, the local command continues; the printed report may then be stale. The final terminal output reports this limitation.

## Acceptance evidence (2026-10-24)

- The installed launcher was reported to resolve from `PATH` as `$HOME/.local/bin/world-seed-see`; direct inspection reportedly showed the launcher forwarding arguments with `"$@"`.
- A harmless smoke test from the home directory printed `Launcher arguments work` and returned exit code 0. [Private terminal report](https://github.com/mythologyprospector-hub/miracle-depot/blob/main/terminal-live/world-seed-see-20261024T175300Z-3f6d558a.txt)
- The setup sequence was run directly (not nested inside the reporting wrapper), then its final wrapped smoke test printed `Stable launcher smoke test passed`, returned exit code 0, and recorded the World Seed checkout on branch `main` with a clean working tree. [Private terminal report](https://github.com/mythologyprospector-hub/miracle-depot/blob/main/terminal-live/world-seed-see-20261024T175455Z-e25f4634.txt)
- The latest-report pointer advanced to each fresh report. No sensitive command output was used in these tests.

These checks support launcher argument forwarding, a stable source path, local output, fresh private reports, and exit-status reporting for the harmless commands above. The current diagnostic provides a way to recheck the actual installed launcher against the current worktree inventory. Keep the full terminal-stack acceptance gate open until current launcher evidence and the remaining journal/handoff layers are reviewed.
