# Bash Prompt and Local Operator Workflow

**Status:** Portable guidance; local shell configuration is operator-owned.
**Governs:** How a builder discovers and works with an operator's interactive shell environment.

## Purpose

The shell prompt is a local situational-awareness aid for the human and AI builder. Depending on the environment, it may expose the current machine, directory, Git branch, uncommitted changes, and the last command's exit status. It is not a security boundary, approval mechanism, test result, or substitute for checking repository state.

## Dashboard signals

A prompt configuration may include:

- A timestamp and user/host/directory display.
- A terminal-mode label, such as **NORMAL** or **JOURNAL**.
- The current Git branch or an abbreviated commit when detached HEAD.
- A marker when Git reports changes and ahead/behind counts when available.
- A marker for a preceding command that exited unsuccessfully.
- A command-history hook or timestamp formatting.
- Machine-specific environment setup, aliases, or helper commands.

These are possible signals, not claims that every operator has them. Verify the actual configuration when authorized local-machine access is available.

The current Bucky operator dashboard uses these signals together: timestamp, user/host, working directory, terminal mode, Git branch, and a compact working-tree/ahead-behind indicator where Git can provide it. In that local configuration, **green means accepted/working** and **red means a failing command or failure state**. These color meanings are operator-specific conventions, not portable guarantees. Always confirm a consequential state with the command's exit status and Git or service evidence; color alone is not proof.

### NORMAL and JOURNAL labels

An operator may use a small prompt label to distinguish an ordinary shell from one launched by an interactive terminal-journaling wrapper. In an operator configuration that uses this convention, the label is driven by the `WORLD_SEED_TERMINAL_MODE` environment variable:

- `WORLD_SEED_TERMINAL_MODE=journal` displays **JOURNAL**.
- When the variable is unset or has another value, the prompt displays **NORMAL**.

The label is a launcher-origin indicator, not an independent detector of the terminal application's profile. Child shells inherit environment variables, so a shell started inside a journaled session may continue to display JOURNAL. Color is presentation only; a text fallback should remain understandable when terminal colors are unavailable.

The current `scripts/terminal_session.py` launcher sets this marker in the child shell it starts. This is an implementation fact for the current launcher, not a guarantee that every older or independently configured launcher does so. The marker itself does not capture, store, or transmit anything. The journaling launcher is responsible for recording the session. Its raw journal is local by default; any remote handoff or publication is a separate, explicit workflow. See [TERMINAL_JOURNAL.md](TERMINAL_JOURNAL.md).

### Three distinct terminal mechanisms

Do not conflate these tools:

1. **Bash prompt/dashboard** — displays local context. It does not capture terminal output, publish reports, fetch Git state, or connect to ChatGPT.
2. **Interactive PTY journal** — when deliberately launched, records the interactive session's terminal output to the local durable journal. The raw journal remains local by default. A reviewed handoff is a separate operation. See [TERMINAL_JOURNAL.md](TERMINAL_JOURNAL.md) and [scripts/terminal_session.py](scripts/terminal_session.py).
3. **World Seed See** — an explicitly invoked command wrapper that shares bounded, heuristically redacted snapshots to the private Intake Dock about every 10 seconds. It is not the interactive PTY journal and is not a live chat connection. See [WORLD_SEED_SEE.md](WORLD_SEED_SEE.md).

The dashboard's Git indicators are local observations. They do not fetch from a remote or prove that a branch is current. World Seed See's remote report publication is not caused by the prompt.

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

World Seed may provide an optional, documented prompt enhancement or diagnostics helper, but must not overwrite a shell startup file, replace an operator's prompt, or silently change aliases, environment variables, history settings, or shell startup behavior. Preserve existing configuration and propose changes as a reviewable diff. Shell configuration may contain private paths or operational details; do not copy it wholesale into the distributable seed.

A prompt can improve visibility. Governance remains in the constitution, GitHub policy, review workflow, tests, and verified evidence.
