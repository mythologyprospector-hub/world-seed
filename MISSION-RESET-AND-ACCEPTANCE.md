# Mission: Build the Machine Before Building Projects

**Status:** Authoritative mission statement
**Date:** 2026-10-21

## Actual goal

Build and prove a portable World-Seed operating system with working recovery that preserves the operator's user data and preferences. Only after it passes acceptance tests should it create projects intended to last.

Projects are downstream products. The operating system that reliably creates, governs, tests, and recovers projects is the current product.

## Operating principles

- Build the machine, not its first product.
- Recovery is built in, not bolted on during an emergency.
- Keep operator profile and personal data independent of individual projects and chat history.
- Use disposable projects to test creation, backup, restoration, and verification.
- A saved snapshot is evidence of a checkpoint, not proof the system is complete.
- An audit, plan, or green test suite is not a win unless it closes a defined acceptance gap.
- On chat changes, read the durable handoff and verify only the state relevant to the next action; do not repeat broad audits without cause.
- The human owner approves destructive actions and consequential architecture choices. The assistant drives and reports evidence honestly.

## Essential assets

1. world-seed — portable operating instructions, governance, bootstrap machinery, and the project-creation path.
2. personal-data — durable user-controlled personal records.
3. operator-profile — preferences, working conventions, approval rules, and collaboration protocol.
4. miracle-depot or successor — controlled staging and project handoff.
5. Recovery capability — part of the operating system unless separation materially improves portability, permissions, or testing.

The old World and recovery worktrees are disposable test material. Salvage useful discoveries, code, tests, and backups, but do not treat the old architecture as binding. Bucky contains substantial old World backups for archiving.

**Designated real demolition-test subjects: `praxis` and `renaissance`.** They are not downstream products to rehabilitate. Use them to prove that World Seed can inventory, preserve, restore, and verify essential material before their old repositories are retired. Preserve lasting code, tests, discoveries, documentation, useful Git history, and required metadata only to the extent the recovery manifest and acceptance evidence justify. Do not rebuild Episteme or either subject as a side mission. Do not delete or reset either subject until isolated recovery and relevant checks pass and the human gives explicit final authorization.

**Organs is a separate infrastructure disposition.** Evaluate its reusable runtime plumbing as a possible factory-managed, optional local capability under [RUNTIME_PLUMBING.md](RUNTIME_PLUMBING.md). Its old integration assumptions do not make it a required dependency of World Seed or the demolition subjects.

## Acceptance gates

The system is not complete until all are demonstrated:

1. **Fresh start:** bootstrap from documented source in a clean environment.
2. **Profile continuity:** restore chosen user data and preferences independently of any project.
3. **Project generation:** create a disposable project without requiring chat archaeology.
4. **Governance:** coherent canon and aligned core documents; approval boundaries honored.
5. **Verification:** run declared tests and structural checks; record actual results.
6. **Recovery:** create backup, restore into an isolated clean location, compare against a manifest, and pass relevant tests.
7. **Handoff continuity:** a new chat can continue from a compact repository record without repeating the investigation.
8. **Honest completion:** disclose limitations; never declare green without evidence.

## GitHub reset policy

Do not keep repairing the old project's architecture merely to preserve it. Use the old work as a test subject and Bucky archives for historical recovery.

Before removing repositories from GitHub, make an explicit keep/archive/delete inventory. Prefer archiving for the first pass. Do not delete repositories, branches, or history based on an inferred keep list; confirm exact names and backup status before irreversible deletion.

## Working rule

Every action should close a concrete gap toward the tested operating system. Prefer the next small productive step over another broad audit. Verify what the next step requires, not everything repeatedly.

**Rule #1:** If we aren't having fun, we're doing it wrong. Make the factory humane, joyful, curious, and evidence-driven.
