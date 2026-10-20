# Bash Prompt and Local Operator Workflow

**Status:** Portable guidance; local shell configuration is operator-owned.
**Governs:** How a builder discovers and works with an operator's interactive Bash environment.
**Last verified:** 2026-10-19

## Purpose

The shell prompt is a local situational-awareness aid for the human and AI builder. It can expose the current machine, directory, Git branch, uncommitted changes, and the last command's exit status. It is not a security boundary, approval mechanism, test result, or substitute for checking repository state.

## Jimmy's current prompt signals

The provided `~/.bashrc` configuration includes:

- Timestamp and `user@host:directory`, helping distinguish machines and working locations.
- Git branch (or abbreviated commit when detached HEAD) in parentheses.
- An asterisk when `git status --porcelain` reports tracked or untracked changes.
- A red `✗N` marker when the preceding command exits nonzero.
- `history -a` in `PROMPT_COMMAND`, appending interactive command history after each command.
- `HISTTIMEFORMAT` timestamps in command history.
- `pstatus`, which reports the current branch, short Git status, and latest commit.
- Existing machine-specific environment setup and aliases, including NVM, Android SDK, CUDA, `~/.scripts`, and `teresa-oracle`.

Treat these as observed in the supplied configuration, not proof that every setting is active in every terminal. The configuration is local to the operator and is not currently a tracked, portable World Seed file.

## Required builder behavior

At bootstrap, inspect the actual interactive shell and relevant local configuration when local-machine access is available. Do not assume Bash, a particular prompt, a clone path, or a shell startup file. Ask before changing operator-owned shell configuration.

When the prompt indicates a repository and branch:

1. Confirm the working directory and repository root before issuing commands.
2. Read `git status --short --branch` before switching branches, pulling, resetting, cleaning, or editing.
3. Treat the dirty marker as a warning to inspect, not as a complete explanation of changes.
4. After a command fails, capture and diagnose its actual error; do not assume a red marker identifies the cause.
5. Verify consequential results explicitly with Git status, commit IDs, tests, or the relevant service/API—not by appearance of the prompt.
6. Keep commands short, paste-safe, and separable from explanatory prose. If a terminal closes or behaves unexpectedly, recover with a small diagnostic step rather than repeatedly pasting a large block.

The `pstatus` helper is useful for a quick check, but it only reports local branch/status/last commit. It does not establish whether the branch is current with its remote, whether required checks passed, whether a backup is recoverable, or whether GitHub protections are configured.

## Portability and maintenance

World Seed may provide an optional, documented prompt enhancement or diagnostics helper, but must not overwrite `~/.bashrc`, replace an operator's prompt, or silently change aliases, environment variables, history settings, or shell startup behavior. Preserve existing configuration and propose changes as a reviewable diff. Shell configuration may contain private paths or operational details; do not copy it wholesale into a public repository.

A prompt can improve visibility. Governance remains in the constitution, GitHub policy, review workflow, tests, and verified evidence.
