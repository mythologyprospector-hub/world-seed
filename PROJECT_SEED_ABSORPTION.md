# Project Seed Absorption Map

**Status:** In progress — source-level audit and final acceptance remain open
**Governs:** The migration of reusable individual-project bootstrap capabilities into World Seed; the existing Project Seed repository remains preserved until acceptance gates pass.
**Last verified:** 2026-10-21

## Decision

World Seed is intended to be the factory for the ecosystem, including the ability to generate and recover individual projects. A separately maintained Project Seed repository must not remain a runtime/build-time dependency once World Seed can independently generate and verify the complete project bootstrap bundle.

Absorption means transferring responsibility for reusable capabilities, not blindly copying every source file or erasing history. Keep `mythologyprospector-hub/project_seed` intact during this migration. Its current default-branch tree is the reference inventory, and its commit history remains provenance.

## Source inventory and disposition

Source inspected: `mythologyprospector-hub/project_seed`, default branch `main`, tree commit `e5f9cc7d5b7962b8fcbb16ab9b3d1e9ee2d2dbe2`.

| Source path | Initial disposition | Target / action |
|---|---|---|
| `AGENTS.md` | Absorb by reconciliation | Derive the generated-project agent contract from World Seed's canonical constitution and builder mandate. Preserve project-local mission sovereignty and useful factory-manager readiness requirements; do not blindly copy 54 KB of overlapping policy. |
| `DOCS.md` | Absorb by reconciliation | Reconcile into `CONSISTENCY_STANDARD.md`. Keep one canonical documentation standard; retain useful requirements such as status language, naming, no duplicate final files, and social-preview readiness where appropriate. |
| `HUMAN.md` | Absorb by reconciliation | Use World Seed's `HUMAN.md` and `CONSTITUTION.md` as the portable source. Operator-specific preferences, identity, and machine details remain in private profile packages. |
| `MACHINE.md` | Replace with generated context | Do not ship Bucky-specific paths as universal defaults. Generate or link machine facts from an explicit, private machine profile; use portable placeholders where a project needs local context. |
| `ORGANS.md` | Absorb by reconciliation | Preserve the external-runtime boundary and contract-first guidance. Validate all capability claims against the current Organs repository/installation before treating them as current. |
| `README.md` | Supersede as separate-seed entry point | World Seed's project-template documentation should explain generation, customization, provenance, and validation. Preserve attribution and relevant source provenance. |
| `LICENSE` | Review before incorporating source | Preserve license notices and provenance. Do not assume the source repository's license automatically changes the licensing status of all material or third-party content. |
| `.github/workflows/project-seed-sync.yml` | Inspect, then replace or exclude | Understand the existing sync workflow and its permissions/triggers. Prefer World Seed's tested generation/release mechanism; never copy an automation workflow without reviewing its write authority and target-selection behavior. |
| `SEED_SYNC.md` | Absorb the useful lifecycle contract | Document the canonical template source, versioning, generated-file ownership, update behavior, and safe conflict handling in World Seed's factory documentation. |
| `WORKTREE_LIFECYCLE.md` | Absorb the useful lifecycle contract | Incorporate relevant project lifecycle/recovery rules into the generated-project and Project Library contracts. Keep one authoritative description of each lifecycle rule. |

“Initial disposition” is an audit starting point, not proof that a capability has been implemented. Each row must be revisited against the complete source content and its actual workflow behavior before it is marked absorbed or superseded.

## Target architecture

- **World Seed owns the factory:** reusable governance, project-template source, project generator, version/provenance manifest, validators, local Project Library, selective backup, and isolated restore verification.
- **Generated projects own their mission:** project-specific mission, architecture, data, implementation, tests, and decisions remain in each generated repository.
- **Private profiles stay separate:** operator preferences, identity, machine-specific facts, personal records, and credentials are not copied into a portable public project template. Secrets are provisioned through an approved secret mechanism, never generated into source files by default.
- **Organs stays external:** World Seed may document and use verified contracts; it does not absorb Organs' implementation or modify the installed runtime incidentally.
- **Project Seed stays intact during migration:** it is an audit source and fallback until World Seed-only generation and recovery are demonstrated.

## Acceptance gates

1. Reconcile every path in the source inventory against its complete content, workflow behavior, license, and provenance.
2. Establish a single canonical source for each reusable policy and lifecycle rule.
3. Implement a versioned World Seed project template and generator that work without fetching or cloning Project Seed at runtime.
4. Generate a disposable fixture with an explicit mission and manifest containing source revision, generated-file inventory, and validation results.
5. Test portable defaults, mission customization, repeatability/idempotence, conflict handling, broken-link detection, and private-data exclusion.
6. Prove the fixture's selective backup and isolated reconstruction; compare the restored result against its manifest and expected behavior.
7. Demonstrate a fresh builder can generate and validate a project from World Seed alone.
8. Only after the above evidence exists, recommend whether to archive Project Seed. Do not delete it or rewrite its history as part of this work.

## Source-level audit update — 2026-10-21

The following repository state has now been inspected directly:

- Project Seed default-branch tree and latest source commit: `e5f9cc7d5b7962b8fcbb16ab9b3d1e9ee2d2dbe2`.
- World Seed default-branch generator, templates, installer, profile-package materializer, recovery tooling, canon, and project lifecycle documentation.
- Project Seed's full file inventory, the headings/structure of its 54 KB `AGENTS.md`, its human/machine contracts, Organs contract, documentation standard, seed-sync policy/workflow, and worktree lifecycle rules.

### Evidence-backed disposition

| Source capability | World Seed evidence | Current finding |
|---|---|---|
| Generate a project without cloning Project Seed | `scripts/create_project.py`, `templates/project/`, `PROJECT_GENERATION.md`, and passing generated-project recovery drill | **Implemented and synthetically tested.** Does not by itself prove every policy in Project Seed has been reconciled. |
| Human/assistant/implementation-agent division of labor; Genie Principle; Miracle Tokens; Fun Rule; Project-First Rule; Dots Principle | `AGENTS.md`, `HUMAN.md`, `CONSTITUTION.md`, `ONBOARDING_PROMPT.md` | **Substantially represented in the factory canon.** Final semantic diff is still required; do not infer exact equivalence from matching headings or terms. |
| Portable vs operator-specific machine context | `MACHINE_PROFILE.md`, `PROFILE_PACKAGES.md`, operator-profile templates | **Boundary represented.** Project Seed's `MACHINE.md` contains Bucky-specific paths and must not be copied verbatim into the public seed. |
| Organs is shared external infrastructure, used only when fit | `ORGANS.md`, generated `templates/project/ORGANS.md` | **Contract represented.** Organs implementation is not to be absorbed into World Seed; its necessity remains project-dependent. |
| Documentation style and drift controls | `CONSISTENCY_STANDARD.md` and current repository documentation | **Candidate equivalent exists.** Finish clause-by-clause reconciliation of `DOCS.md`, including social-preview requirements and status language. |
| Worktree discovery, active register, preservation, safe retirement | Newly added `WORKTREE_LIFECYCLE.md`, adapted from the source contract to avoid hardcoding Bucky's paths | **Transferred to World Seed in this branch; pending CI/review and canonical-link integration.** |
| Project Seed sync workflow and target list | Source `.github/workflows/project-seed-sync.yml` and `SEED_SYNC.md` | **Not to be copied.** It uses a broad cross-repository token and target-specific root-file mappings. Before Project Seed retirement, record whether any required target still depends on it, disable/retire the automation safely, and verify no required project relies on future upstream sync. Never reproduce its token or write authority in the public seed. |
| License, provenance, and history | Source `LICENSE` and Git history | **History remains valuable provenance.** Do not rewrite or delete it as part of absorption. Confirm attribution/license handling for any material actually copied. |
| Unique lessons and latest operating rules | Source commit history through `e5f9cc7`, including October 19 Rule #2 / Project-First Rule update | **Review required.** The recent history shows that reading only an old snapshot would miss important rules; the comparison must use the recorded source commit and check for later changes immediately before final acceptance. |

This is a scoped audit, not a claim that every paragraph in the large source constitution has already been proven equivalent. The remaining work is a semantic coverage review of each source document, a check of automation dependencies, and final acceptance against the gates below.

## Current state

World Seed now has its own generator, templates, local Project Library, profile-package scaffolding, selective recovery, and isolated synthetic recovery drills. The protected-branch check on integrated `main` passed on 2026-10-21 (193 tests, both recovery drills, and 112 required-file/Markdown-link checks). This proves those specific tested paths only.

Project Seed is **not yet cleared for retirement**. No repository deletion is authorized by this map. The next acceptance work is to finish the semantic comparison, verify the generated-project contract and source provenance, check the seed-sync workflow's remaining dependencies, and document any accepted omissions. Real Bucky recovery and private-data restoration remain separate gates.
