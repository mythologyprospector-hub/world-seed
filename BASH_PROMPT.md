# Bash Prompt and Local Operator Workflow

**Status:** Portable guidance; local shell configuration is operator-owned.
**Governs:** How a builder discovers and works with an operator's interactive shell environment.

## Purpose

The shell prompt is a local situational-awareness aid for the human and AI builder. Depending on the environment, it may expose the current machine, directory, Git branch, uncommitted changes, and the last command's exit status. It is not a security boundary, approval mechanism, test result, or substitute for checking repository state.

## Possible prompt signals

A prompt configuration may include:

- A timestamp and user/host/directory display.
- The current Git branch or an abbreviated commit when detached HEAD.
- A marker when Git reports changes.
- A marker for a preceding command that exited unsuccessfully.
- A command-history hook or timestamp formatting.
- A helper that reports the current branch, short Git status, and latest commit.
- Machine-specific environment setup, aliases, or helper commands.

These are examples of possible signals, not claims about the target operator's environment. Verify the actual configuration when authorized local-machine access is available. Do not copy one operator's prompt configuration or machine-specific details into the distributable seed.

## Required builder behavior

At bootstrap, inspect the actual interactive shell and relevant local configuration when local-machine access is available. Do not assume Bash, a particular prompt, a clone path, or a shell startup file. Ask before changing operator-owned shell configuration.

When the prompt indicates a repository and branch:

1. Confirm the working directory and repository root before issuing commands.
2. Read `git status --short --branch` before switching branches, pulling, resetting, cleaning, or editing.
3. Treat a dirty marker as a warning to inspect, not as a complete explanation of changes.
4. After a command fails, capture and diagnose its actual error; do not assume a red marker identifies the cause.
5. Verify consequential results explicitly with Git status, commit IDs, tests, or the relevant service/API—not by appearance of the prompt.
6. Keep commands short, paste-safe, and separable from explanatory prose. If a terminal closes or behaves unexpectedly, recover with a small diagnostic step rather than repeatedly pasting a large block.

A prompt helper is useful for a quick check, but it does not establish whether the branch is current with its remote, whether required checks passed, whether a backup is recoverable, or whether GitHub protections are configured.

## Portability and maintenance

World Seed may provide an optional, documented prompt enhancement or diagnostics helper, but must not overwrite a shell startup file, replace an operator's prompt, or silently change aliases, environment variables, history settings, or shell startup behavior. Preserve existing configuration and propose changes as a reviewable diff. Shell configuration may contain private paths or operational details; do not copy it wholesale into a public repository.

A prompt can improve visibility. Governance remains in the constitution, GitHub policy, review workflow, tests, and verified evidence.

## Branch-aware Git signal contract

When an operator chooses the enhanced Bash prompt pattern, use the following meanings consistently. This is a portable behavioral contract, not a requirement to install or replace a shell prompt.

- **Branch label:** show the current symbolic branch. If `HEAD` is detached, show an abbreviated commit ID instead. Outside a Git worktree, omit the Git segment.
- **Dirty marker (`*`):** show when local Git status reports tracked changes or ordinary untracked files. The marker is only a quick warning; inspect full status to learn what changed.
- **Ahead marker (`↑N`):** `N` commits exist on local `HEAD` but not on its configured upstream, based on locally available Git refs.
- **Behind marker (`↓N`):** `N` commits exist on the configured upstream but not on local `HEAD`, based on locally available Git refs.
- **Both markers:** show both counts when the branches have diverged. Omit zero-valued counts. Omit divergence markers when no upstream is configured or the comparison cannot be computed.
- **Failure marker:** show the previous command's nonzero exit status. Capture `$?` before running helper commands; otherwise the prompt may report the helper's status instead of the user's command.
- **Context:** a timestamp and user/host/directory display may remain alongside the Git segment. Terminal-title handling, color fallback, and history behavior must remain compatible with the operator's existing setup.

The arrows are **local-ref comparisons, not live GitHub status**. They must never trigger `fetch`, `pull`, `push`, or any other network operation from prompt rendering. Counts can be stale until the operator deliberately updates refs. A missing arrow is not proof that a remote branch is current or that a push would succeed.

## Companion repository report

A `pstatus`-style helper may provide a deliberate, one-shot local report containing:

- repository root and current branch (or detached-HEAD state);
- configured upstream, if any;
- locally known ahead/behind counts, when computable;
- short working-tree status, including the branch/upstream summary;
- unstaged and staged diff summaries; and
- the latest local commit.

The report should be read-only and must not fetch or mutate Git state. It complements, but does not replace, detailed commands such as `git status --short --branch`, `git diff`, and `git log`. If a repository has no upstream, say so rather than implying synchronization was checked.

## Implementation and acceptance checks

Before treating an enhanced prompt as ready, verify the actual sourced configuration and test these states in a disposable repository or other safe fixture:

1. outside a Git repository;
2. clean branch with no upstream;
3. clean branch with an upstream and equal refs;
4. local-only commits, upstream-only commits, and divergence;
5. tracked modifications, staged changes, and ordinary untracked files;
6. detached `HEAD`;
7. a successful command followed by a failing command, and vice versa;
8. a terminal without usable color support; and
9. an existing `PROMPT_COMMAND` hook, including any hook that also edits `PS1`.

Check `bash -n ~/.bashrc` for syntax, then open a fresh interactive shell and inspect the visible behavior. Syntax validation alone does not prove prompt correctness. Measure prompt latency in a large repository before optimizing; prefer correctness and a no-network guarantee over cleverness.

Do not claim these acceptance checks passed unless their results were actually observed. When the operator has already installed and sourced a prompt change, document the intended signal and remaining verification honestly; do not overwrite the operator-owned file just to make it match this document.
