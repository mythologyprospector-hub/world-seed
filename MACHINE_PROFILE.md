# Machine Profile and Discovery

**Status:** Canonical procedure; actual machine facts belong in an authorized operator profile package.
**Governs:** How the builder discovers local environment facts without confusing one operator's machine with a universal requirement.
**Last verified:** 2026-10-20

## General rule

Discover the actual environment before relying on paths, installed tools, services, ports, operating system, or machine names. Machine facts are useful starting points, not proof of current state. Never infer a missing path or runtime detail.

The reusable seed must not carry a real operator's hostname, clone paths, installed service locations, credential-vault details, or private repository map. See [PROFILE_PACKAGES.md](PROFILE_PACKAGES.md) for the boundary and loading contract.

## Local discovery procedure

For local operations:

1. Inspect the current directory and Git state.
2. Inspect the actual machine and installed tool versions.
3. Identify clone roots and active worktrees.
4. Inspect shared services and their published contracts.
5. Read only the relevant authorized operator-profile sections, if available.
6. Record only stable, useful facts in the approved private location.
7. Keep secrets and sensitive configuration outside source control.

Do not assume that a machine is online, a tool is installed, a checkout is clean, a branch is safe to change, or a shared service is healthy merely because a profile says it should exist.

For interactive-shell discovery and the role/limits of the local prompt, follow [BASH_PROMPT.md](BASH_PROMPT.md). Record useful local context signals, but do not overwrite shell configuration or assume a prompt is an enforcement mechanism. Ask before changing operator-owned startup files.

## Local collector

Use `scripts/collect_machine_profile.py` for a first-pass, local-only machine readiness report. It is deliberately an allowlist, not a general system dump.

Run from a world-seed checkout:

```bash
python3 scripts/collect_machine_profile.py
```

This prints a small JSON report to the terminal. To save a new report locally:

```bash
python3 scripts/collect_machine_profile.py --output ./machine-report.json
```

Repository names and local paths are omitted unless explicitly requested:

```bash
python3 scripts/collect_machine_profile.py --include-repositories
```

The optional repository scan checks immediate child Git checkouts under `~/projects` (or a supplied `--projects-root`). It records names, paths, current branch, and whether tracked changes exist. It does not collect remote URLs, file names, diffs, commit contents, or untracked-file names.

The collector does not upload data, read credential files, inspect environment-variable values, run authentication commands, or overwrite an existing report. Its output is not automatically safe for public publication: review it before sharing, and place operator-specific output only in an authorized private destination. This first version reports platform and selected tool availability/version; it does not configure the machine, change shell files, test network access, or prove service health.

## Operator profile unavailable

If no authorized profile package is present or accessible, continue with universal rules and safe discovery. Treat operator-specific paths, preferences, tools, and service details as unknown until verified. Do not ask the human to reconstruct routine details that can be safely discovered from the actual environment.

## Other operators and machines

Use [profiles/ACCOUNT_PROFILE.template.md](profiles/ACCOUNT_PROFILE.template.md) to create a profile in an operator-approved, access-controlled location. Do not fill the template with real personal or machine details inside the distributable seed. Keep universal discovery procedures here; keep mutable machine details in the authorized private profile. Never copy one operator's hostname, paths, service locations, or preferences into another operator's profile.
