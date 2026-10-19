# Machine Profile and Discovery

**Status:** Canonical procedure; profile facts are operator-specific.
**Governs:** How the builder discovers local environment facts without confusing one operator's machine with a universal requirement.
**Last verified:** 2026-10-19

## General rule

Discover the actual environment before relying on paths, installed tools, services, ports, operating system, or machine names. Profile facts are useful starting points, not proof of current state. Never infer a missing path or runtime detail.

For local operations:
1. inspect the current directory and Git state;
2. inspect the actual machine and installed tool versions;
3. identify clone roots and active worktrees;
4. inspect shared services and their published contracts;
5. record only stable, useful facts;
6. keep secrets and sensitive configuration outside source control.

## Jimmy profile (known facts)

The following facts were documented in World and Project Seed as of 2026-10-19. Verify them before relying on them in a new environment.

- Primary development machine nickname: **Bucky**.
- Hostname: `mythos1`.
- Standard local project clone root: `~/projects`.
- Normal clone path: `~/projects/<repo-name>`.
- Organs installation/runtime location: `/srv/organs`.
- The Organs installation is existing shared infrastructure. Do not reinstall, modify, or reconfigure it as an incidental part of project work. Inspect its current repository/contracts and installed state; changes to shared infrastructure require explicit authorization.
- Jimmy prefers complete copy/paste command blocks and does not want routine Git or code machinery delegated back to him.

Routine main-branch update, only when appropriate to the current task:

```bash
cd ~/projects/<repo-name>
git switch main
git pull --ff-only origin main
```

Do not assume that the machine is online, a tool is installed, a checkout is clean, a branch is safe to change, or Organs is healthy merely because the profile says it should exist.

## Other operators and machines

For a different operator or machine, create a separate profile using [profiles/ACCOUNT_PROFILE.template.md](profiles/ACCOUNT_PROFILE.template.md). Keep universal discovery procedures here; keep mutable machine details in the profile. Never copy Jimmy's hostname, paths, service locations, or preferences into another operator's profile.
