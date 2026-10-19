# world-seed

**Portable genesis for AI-led project ecosystems, with a real operator profile.**

world-seed preserves the reusable operating system for starting and governing a whole GitHub account: the constitution, AI leadership mandate, human approval boundaries, repository architecture, onboarding, automation standards, machine profile, and recovery procedure.

It is deliberately **mission-portable and operator-aware**:
- The core works with any GitHub account, mission, repository set, and capable AI builder.
- The included Jimmy profile records the known local environment and working preferences without pretending those facts apply to other operators.
- Account-specific mission, inventory, credentials, and current state are discovered at bootstrap; they are not guessed from this seed.

## Start here

1. Give the AI builder the repository URL and the instructions in [ONBOARDING_PROMPT.md](ONBOARDING_PROMPT.md).
2. The builder reads [AGENTS.md](AGENTS.md), [CONSTITUTION.md](CONSTITUTION.md), [HUMAN.md](HUMAN.md), and [BOOTSTRAP.md](BOOTSTRAP.md).
3. It inspects the target account and environment before changing anything.
4. It prepares an evidence-backed plan and proceeds within the authority already granted, stopping only at real approval gates.
5. It leaves durable records and verifies what it actually did.

## Contents

- [AGENTS.md](AGENTS.md) — entry-point instructions for any AI builder.
- [CONSTITUTION.md](CONSTITUTION.md) — governance, leadership, Rule #1, Rule #2, authority, and safeguards.
- [HUMAN.md](HUMAN.md) — the intended working relationship and communication style.
- [BOOTSTRAP.md](BOOTSTRAP.md) — account-level discovery and genesis sequence.
- [REPOSITORY_MODEL.md](REPOSITORY_MODEL.md) — ecosystem vs project responsibilities and the role of lower-level seeds.
- [AUTOMATION.md](AUTOMATION.md) — workflow and automation requirements.
- [AUDIT_SYSTEM.md](AUDIT_SYSTEM.md) — mandatory rolling repository, cross-repository, and account-wide audits.
- [CONSISTENCY_STANDARD.md](CONSISTENCY_STANDARD.md) — shared editorial, code-commenting, naming, repository-layout, process, and quality standards.
- [MACHINE_PROFILE.md](MACHINE_PROFILE.md) — how to discover an environment and the known Jimmy profile.
- [RECOVERY.md](RECOVERY.md) — independent backup and reconstruction requirements.
- [ONBOARDING_PROMPT.md](ONBOARDING_PROMPT.md) — reusable prompt for a fresh chat or builder.
- [profiles/ACCOUNT_PROFILE.template.md](profiles/ACCOUNT_PROFILE.template.md) — template for a different operator/account.

## Important boundaries

This repository is a bootstrap source, not proof that a target account has been configured or recovered. Reading it is not execution. A file existing is not evidence that a workflow runs. Every bootstrap must report completed, verified, blocked, and unverified items separately.

Never store credentials, tokens, private keys, recovery codes, or other secrets here. Keep the seed independently backed up from the account it is meant to recover.

## Evolution

When a reusable rule changes, update its canonical document here and record the rationale. Do not silently let temporary chat context become policy. Keep operator-specific details in the profile, not in the universal constitution.


## Local quality gate

Run the dependency-free baseline checks and unit tests from the repository root:

```bash
python scripts/validate_seed.py
python -m unittest discover -s tests -v
```

GitHub Actions runs these checks on pull requests and pushes, supports manual execution, and schedules a weekly repository-local check. This is the first executable quality gate—not the complete account-wide audit. It checks required seed documents and obvious broken relative Markdown links. It does not prove semantic consistency, private-repository coverage, security posture, runtime health, or recovery readiness.
