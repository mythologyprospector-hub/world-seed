# Repository and Ecosystem Model

**Status:** Canonical
**Governs:** Separation of reusable ecosystem machinery from operator profiles and individual projects.
**Last verified:** 2026-10-21

## Separate responsibilities

- **world-seed** owns the account/ecosystem operating model and is the intended factory for generating and recovering individual projects: governance, AI leadership, account orientation, repository relationships, shared automation standards, profile-loading procedures, project templates, and recovery. [MISSION.md](MISSION.md) provides the shared discovery method; generated projects may adapt the opening mission sentence to their own purpose while preserving the common operating approach.
- **Operator profile package** holds the relevant operator's working preferences, approved identity/attribution details, environment facts, and account-specific operational notes in an operator-approved access-controlled location.
- **Personal-data package** holds genealogy, birth information, personal history, AI exports, family records, and other personal material under stricter access and disclosure rules.
- **Project Seed (legacy source)** is the existing repository containing reusable individual-project bootstrap rules and lifecycle conventions. It is being audited for absorption into World Seed; it is not yet safe to assume the separate dependency has been eliminated. See [PROJECT_SEED_ABSORPTION.md](PROJECT_SEED_ABSORPTION.md).
- **Generated project repositories** own their mission, canon, architecture, implementation, tests, project data, and roadmap. They receive the appropriate common bootstrap bundle from the World Seed factory but remain sovereign in project-specific decisions.

The ecosystem seed must define the reusable operating machinery without becoming a container for operator-specific or personal data. See [PROFILE_PACKAGES.md](PROFILE_PACKAGES.md) for the canonical profile boundary and loading contract.

## Ecosystem orientation

The target account should have one clear launch point that tells a new builder how to understand the portfolio, where project canon lives, what the account's mission is, what is shared, and what remains project-sovereign.

A world/portfolio repository is not a monolithic application. It maps and coordinates independent projects; cross-project integration occurs through explicit contracts and only when justified.

## Canonical ownership

- Reusable AI operating policy and project-generation machinery: world-seed, once the absorption acceptance gates are met.
- Account mission and portfolio orientation: target account's world/portfolio layer.
- Operator working preferences and machine facts: authorized operator profile package.
- Sensitive personal history and exports: separately protected personal-data package.
- Project mission, architecture, implementation, tests, and project decisions: that project's own repository.
- Credentials and secrets: approved secret manager, never seed files or ordinary profiles.
- Runtime contracts: the actual shared infrastructure repository and installed implementation, not remembered descriptions.

## Discovery and reuse

When a sound world/portfolio layer, operator profile, shared service, or reusable project-bootstrap source already exists, inspect and reuse it. Do not assume the target account resembles the source account. Keep a provenance note when adapting existing rules and document any deliberate divergence.

World Seed should generate projects from its own versioned template without fetching or cloning Project Seed at runtime. During the transition, inspect the existing Project Seed source and preserve it intact until generated-project creation and isolated recovery are demonstrated. See [PROJECT_SEED_ABSORPTION.md](PROJECT_SEED_ABSORPTION.md) for the migration inventory and acceptance gates.

## Boundary rule

Shared governance must not silently override project canon. Project canon must not silently claim authority over the whole account. An operator profile supplies context, not unrestricted authorization. A personal-data package supplies information, not permission to disclose or use it for every purpose. When a real conflict exists, record it, identify the affected boundary, and obtain the appropriate decision rather than hiding it in a generic template.

## Implementation status

The architecture direction is established; implementation is not complete. The current installer does not yet provide the complete project generator, local Project Library, or end-to-end project recovery. Keep these capabilities marked incomplete until acceptance evidence is recorded.
