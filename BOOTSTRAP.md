# Account Bootstrap and Genesis

**Status:** Canonical procedure
**Governs:** The repeatable process for establishing the operating machinery in a new or existing GitHub account.
**Last verified:** 2026-10-19

## Objective

Establish an AI-led operating ecosystem for the target account and its mission, using actual discovery rather than assumptions. The bootstrap must work for different missions, account owners, AI builders, and repository sets.

## Phase 0 — Establish authority and target

1. Identify the target GitHub account/organization and the human owner.
2. Confirm which connected identity and tools can actually access it.
3. Read the owner's stated mission, constraints, and risk boundaries. If absent, ask the smallest necessary mission-level question; do not invent a mission.
4. Distinguish read-only discovery from writes. Confirm authorization for consequential actions before executing them.
5. Never request or place credentials in chat, repository files, issues, or logs. Use approved credential managers and platform permission flows.
6. Before declaring an integration blocked for lack of credentials, consult the operator's private machine/profile notes for an existing credential vault. Verify only whether an appropriate credential is available and scoped; do not reveal, copy, or log its value. Never assume one provider's credential grants access to another provider or to the required repositories.

## Phase 1 — Discover reality

Inventory:
- repositories and visibility;
- default branches, current heads, open pull requests/issues, workflows, and automation;
- canonical governance and project documents;
- reusable templates, seeds, shared services, and cross-repository contracts;
- account/team permission boundaries available to the current tools;
- local machines, clone locations, installed runtimes, and required tools where accessible;
- independent backups and recovery dependencies.

Label every finding as observed, inferred, or unknown. Do not imply a complete inventory when permissions or API coverage prevent it. Avoid exposing private repository names or details in public files.

## Phase 2 — Assess the operating machinery

Before downstream implementation, compare existing rules and automation for contradictions, gaps, unsafe assumptions, duplicated sources of truth, unverified claims, and missing recovery paths.

Test whether a fresh builder can distinguish:
- inventory from portfolio assessment;
- evidence from inference;
- recommendation from authorization;
- intended work from implemented work;
- tested from verified;
- project-level authority from account-level coordination.

Repair or propose repairs to the operating machinery before directing broad downstream work. Keep discovery moving while readiness issues are investigated.

## Phase 3 — Establish the ecosystem layer

Select or establish one canonical ecosystem-orientation repository. It should contain:
- the launch/arrival protocol;
- the AI stewardship mandate;
- a project map or documented discovery procedure;
- account mission and governance references;
- cross-project integration and ownership boundaries;
- the current readiness/gap assessment and handoff;
- links to the lower-level project bootstrap.

Do not assume the source seed's repository names or structure are appropriate for the target account. Choose the smallest coherent structure that supports the mission.

## Phase 4 — Establish project-level bootstrap

Use the target account's existing project seed/template if sound. If none exists, derive one from this seed without copying ecosystem-specific account details into it.

A project seed should preserve reusable interaction, documentation, testing, security, licensing, provenance, and machine-discovery standards, while leaving each project's purpose, architecture, and roadmap to its own canon.

Never silently overwrite a repository's established canon with a template. Use a reviewable proposal and resolve conflicts explicitly.

## Phase 5 — Automation and safety

Inventory every workflow and its triggers, permissions, secrets, target repositories, write effects, and failure behavior. Prefer least privilege, explicit allowlists, pinned or controlled dependencies where appropriate, validation before writes, clear logs, and human gates for consequential actions.

Do not assume a workflow is safe because it is YAML or because it passes syntax validation. Do not run live evaluations or trigger side effects without the required authorization.

## Phase 5A — Verify and establish GitHub branch safeguards

For each repository, discover the default branch and inspect classic branch protection plus repository rulesets. Inspect organization-level rulesets when the current identity and integration can access them. Confirm pagination and record inaccessible settings as unverified, never as absent. Determine whether pull-request requirements, approvals, required checks, force-push/deletion restrictions, and bypasses actually support the human approval gate.

Prepare a concrete protection plan based on real workflows and the operator's role. Do not require nonexistent status checks or assume the owner can satisfy a second-reviewer rule alone. Because applying branch policies changes security/permissions, present the exact plan and obtain explicit approval before writing settings. After approval, apply it, re-read the effective policy, test the expected behavior where safe, and record what remains unverified. A clean build or a green CI run does not prove branch protection.

Also inspect the actual interactive shell and prompt when local machine access is available. Read [BASH_PROMPT.md](BASH_PROMPT.md) and record useful local context signals, but do not overwrite shell configuration or assume a prompt is an enforcement mechanism. Ask before changing operator-owned startup files.

## Phase 6 — Establish rolling audit machinery

Before calling the ecosystem bootstrapped, implement the requirements in [AUDIT_SYSTEM.md](AUDIT_SYSTEM.md): define repository, cross-repository, and account-wide coverage; establish the initial baseline and findings ledger; configure appropriate pull-request checks and scheduled/manual audit execution; document the cross-repository permission model; and make coverage gaps visible. Test the audit machinery against a known fixture or safe test environment. If full account-wide access or scheduling cannot yet be configured, explicitly label the ecosystem not audit-ready, record the blocker, and continue with safe partial coverage.

## Phase 7 — Verify and hand off

Produce a compact report with:
- what was inspected and at what ref/commit;
- what was created or changed;
- exact commits/branches/PRs;
- checks actually run and their results;
- permissions or environment areas not verified;
- remaining blockers and risks;
- the next best action.

Keep these categories separate: complete, implemented but unverified, blocked, and not attempted. Leave a durable handoff in the canonical ecosystem repository.

## Repeatability

The process should be idempotent where practical. On rerun, inspect the current state and reconcile rather than blindly duplicating files or overwriting local changes. A bootstrap must be safe to interrupt and resume.

## Acceptance test

A bootstrap is not complete merely because seed files were copied. Demonstrate that a fresh builder can identify the mission, locate the canonical rules, describe the authority boundaries, find the project bootstrap, assess the real account state, and produce a truthful readiness report without relying on prior chat history.


## Safe inventory utility

The repository includes `scripts/audit_account_inventory.py` for an initial read-only inventory of repositories visible to an authenticated GitHub identity. Use an environment-provided `GH_TOKEN` or `GITHUB_TOKEN` with the narrowest appropriate read access, and write the report to access-controlled storage outside the public repository. Never paste credentials into commands, files, prompts, or logs.

Treat its output as a starting inventory, not a complete audit. Compare it with an authoritative expected repository list, verify access to private and organization-owned repositories, and record missing coverage as a blocker. This utility alone does not satisfy the account-wide audit acceptance gate.
