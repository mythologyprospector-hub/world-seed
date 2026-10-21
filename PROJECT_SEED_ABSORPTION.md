# Project Seed Absorption Map

**Status:** Proposed
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

## Current state

This map is a proposed migration contract. It does not claim that the generator, Project Library, or full recovery path already exists. The current local installer is only the first bootstrap layer; Bucky acceptance and isolated end-to-end recovery remain required.
