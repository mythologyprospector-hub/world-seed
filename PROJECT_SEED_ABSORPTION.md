# Project Seed Absorption Map

**Status:** In progress — source-level audit and final acceptance remain open
**Governs:** The migration of reusable individual-project bootstrap capabilities into World Seed; the existing Project Seed repository remains preserved until acceptance gates pass.
**Last verified:** 2026-10-23

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
- **Organs is evaluated as optional factory-managed runtime plumbing:** do not absorb the entire repository blindly or make Organs mandatory for World Seed/generated projects. Follow [RUNTIME_PLUMBING.md](RUNTIME_PLUMBING.md) for the capability-by-capability disposition. No live Organs runtime has been modified.
- **Project Seed stays intact during migration:** it is an audit source and fallback until World Seed-only generation and recovery are demonstrated.

## Acceptance gates

1. Reconcile every path in the source inventory against its complete content, workflow behavior, license, and provenance.
2. Establish a single canonical source for each reusable policy and lifecycle rule.
3. Implement a versioned World Seed project template and generator that work without fetching or cloning Project Seed at runtime.
4. Generate a disposable fixture with an explicit mission and manifest containing source revision, generated-file inventory, and validation results.
5. Test portable defaults, mission customization, repeatability/idempotence, conflict handling, broken-link detection, and private-data exclusion.
6. **Prove project quality first:** a fresh builder uses World Seed alone to create a coherent, useful, implemented project with mission-appropriate architecture, meaningful tests, reproducible setup, and evidence-backed documentation. A generated scaffold or green factory test suite alone does not satisfy this gate.
7. After gate 6 passes, prove selective backup and isolated reconstruction of that worthy fixture; compare the restored result against its manifest and run relevant checks. Recovery must protect demonstrated value, not displace the project-quality milestone.
8. Only after the preceding evidence exists, recommend whether to archive Project Seed. Do not delete it or rewrite its history as part of this work.
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
| Documentation style and drift controls | `CONSISTENCY_STANDARD.md`, generated `templates/project/DOCS.md`, and current repository documentation | **Partial absorption in PR #46.** The public social-preview launch requirement is being added to the canonical standard and generated template; clause-by-clause reconciliation of the remaining `DOCS.md` rules and status language is still open. |
| Worktree discovery, active register, preservation, safe retirement | `WORKTREE_LIFECYCLE.md`, adapted from the source contract to avoid hardcoding Bucky's paths and linked from the builder arrival protocol | **Merged into World Seed main by PR #28; the main quality check passed.** The contract is now available in the factory, while its use during real recovery remains to be demonstrated. |
| Project Seed sync workflow and target list | Source `.github/workflows/project-seed-sync.yml` and `SEED_SYNC.md` | **Not to be copied.** It uses a broad cross-repository token and target-specific root-file mappings. Before Project Seed retirement, record whether any required target still depends on it, disable/retire the automation safely, and verify no required project relies on future upstream sync. Never reproduce its token or write authority in the public seed. |
| License, provenance, and history | Source `LICENSE` and Git history | **History remains valuable provenance.** Do not rewrite or delete it as part of absorption. Confirm attribution/license handling for any material actually copied. |
| Unique lessons and latest operating rules | Source commit history through `e5f9cc7`, including October 19 Rule #2 / Project-First Rule update | **Review required.** The recent history shows that reading only an old snapshot would miss important rules; the comparison must use the recorded source commit and check for later changes immediately before final acceptance. |

This is a scoped audit, not a claim that every paragraph in the large source constitution has already been proven equivalent. The remaining work is a semantic coverage review of each source document, a check of automation dependencies, and final acceptance against the gates below.

### Downstream sync PRs found during demolition inventory

As of 2026-10-21, Praxis PR [#6](https://github.com/mythologyprospector-hub/praxis/pull/6) and Renaissance PR [#13](https://github.com/mythologyprospector-hub/renaissance/pull/13) remain open automated Project Seed sync PRs. Their changed files are the downstream `.project_seed` reference snapshot and its sync README; they do not change the subjects' domain source or tests. The audited snapshot files match the current Project Seed main source for the corresponding seed documents. Do not merge these PRs merely to make them disappear. Preserve their PR metadata/diffs as part of GitHub-only recovery coverage before retiring either subject. This does not clear other branches, history, or GitHub-only records for deletion.

## Current state

World Seed now has its own generator, templates, local Project Library, profile-package scaffolding, selective recovery, and isolated synthetic recovery drills. The protected-branch check on integrated `main` passed on 2026-10-21 (193 tests, both recovery drills, and 112 required-file/Markdown-link checks). After PRs #29 and #30 were merged, the exact latest main commit `0c5d33b8b355f088fee1b25b1db57b2b86057ac4` also passed its Actions check. This proves those specific tested paths only.

Project Seed is **not yet cleared for retirement**. No repository deletion is authorized by this map. The next acceptance work is to finish the semantic comparison, verify the generated-project contract and source provenance, and document any accepted omissions. The factory's actual demolition rehearsals for Praxis and Renaissance, GitHub-only record preservation, and independent operator/personal-data restoration remain separate gates.

## Reconciliation pass — 2026-10-23

The source inventory was re-read from the current Project Seed default-branch tree. Its tree SHA remains `e5f9cc7d5b7962b8fcbb16ab9b3d1e9ee2d2dbe2`; the most recent source commit is still `e5f9cc7d5b7962b8fcbb16ab9b3d1e9ee2d2dbe2` (2026-10-19, Project-First Rule). The tree contains exactly these ten tracked files:

- `.github/workflows/project-seed-sync.yml`
- `AGENTS.md`
- `DOCS.md`
- `HUMAN.md`
- `LICENSE`
- `MACHINE.md`
- `ORGANS.md`
- `README.md`
- `SEED_SYNC.md`
- `WORKTREE_LIFECYCLE.md`

The list contains ten paths, including the workflow; no additional source files were present in the recursive tree. The 54 KB `AGENTS.md` was reviewed by its complete section structure and its distinctive operating-policy sections, alongside the complete supporting documents and sync workflow. This pass records targeted dispositions; it is **not** a claim that every sentence has passed a final legal or line-by-line equivalence review.

### Reusable operating rules and disposition

| Project Seed rule or capability | World Seed destination / evidence | Disposition |
|---|---|---|
| Genie Principle and unbounded-mission discovery | `MISSION.md`, root `AGENTS.md`, generated project `AGENTS.md` | Represented. Builder must discover the right form of solution instead of demanding a technical specification. |
| Human gate, delegated initiative, Dots Principle, chain of command | `HUMAN.md`, `CONSTITUTION.md`, root `AGENTS.md` | Represented in portable terms. Owner retains consequential authority; the builder owns routine direction and coordination. |
| Fun Rule and Project-First Rule | `CONSTITUTION.md`, `HUMAN.md` | Represented as Rule #1 and Rule #2. |
| Miracle Tokens: director/implementation labor/durable memory/evidence loop and context economy | Root leadership/evidence rules existed; generated builder contract was thinner on bounded delegation and compact handoffs. | Added to generated `templates/project/AGENTS.md` in template version 1.3.0, with regression assertions. The portable template describes the method without requiring a particular tool or promising unlimited usage. |
| Durable truth, inspect-before-change, truth discipline, retry discipline, standard work loop | Root `AGENTS.md`, `PROJECT_GENERATION.md`, generated first-build protocol and existing tests | Substantially represented. Exact operational details remain subject to the final clause-level pass; retry rules must never bypass safety or permissions. |
| Default MIT licensing and attribution safeguards | Generated `LICENSE` template, profile boundary, generated builder contract | Added generic MIT-by-default guidance for new software projects, subject to ownership and third-party obligations. Copyright identity stays profile-authorized; generated placeholders must be completed before publication. No source-specific personal identity is hard-coded into the portable template. |
| Documentation style, status language, naming, drift control, social preview | `CONSISTENCY_STANDARD.md`, generated `templates/project/DOCS.md` | Represented across the canonical and generated standards. Public preview preparation and owner-side upload are separate states. |
| Operator machine context | `MACHINE_PROFILE.md`, `PROFILE_PACKAGES.md`, generated `MACHINE.md` placeholder | Boundary represented; source `MACHINE.md` must not be copied because it contains Bucky-specific paths and runtime locations. |
| Organs external-runtime and contract-first boundary | Root and generated `ORGANS.md` | Represented. Organs remains optional per project; the live Organs repository/installation is authoritative for current technical details. |
| Worktree discovery, tracking, preservation, retirement | World Seed `WORKTREE_LIFECYCLE.md` | Previously merged and adapted to avoid treating machine-specific paths as universal. Real recovery use remains unproven. |
| Seed synchronization and cross-repository write workflow | Source `SEED_SYNC.md` and `.github/workflows/project-seed-sync.yml` | Exclude from the portable factory. The source workflow uses `PROJECT_SEED_SYNC_TOKEN`, six target mappings, reference snapshots, and PR creation. Never reproduce its token or cross-repository write authority. Before retirement, confirm no required downstream project depends on future Project Seed sync and preserve relevant PR/branch/history records. |
| Source license and history | Source `LICENSE` and Git history | Preserve source repository/history as provenance until acceptance. Reusing text does not justify deleting source history or silently changing another project's license. |

### Automation and downstream status

The most recent Project Seed sync workflow run observed during this pass was successful on 2026-10-19. That establishes only that run's result; it does not establish that every target remains configured or that future synchronization is unnecessary.

The previously recorded Praxis PR #6 and Renaissance PR #13 could not be retrieved by their direct pull-request API URLs during this pass (both returned 404). Their current state is therefore **unverified**, not presumed closed or open. Before Project Seed retirement, rediscover the relevant downstream sync PRs and branches through the authorized GitHub connection and record their actual state and disposition.

### Remaining gates

1. Complete the clause-level comparison of Project Seed's operating constitution and supporting documents; record any omissions as accepted, adapted, or deliberately excluded.
2. Verify sync dependencies, downstream PR/branch state, and the retirement plan for `PROJECT_SEED_SYNC_TOKEN` without exposing or copying the secret.
3. Run the World Seed generator test suite and relevant CI for template version 1.3.0; do not infer green status from this proposed change.
4. Pass the fresh-project quality gate with a real mission and useful implemented result.
5. Only after the quality gate, perform the separate isolated recovery proof and then recommend archive/retirement. Deletion remains unauthorized by this map.
