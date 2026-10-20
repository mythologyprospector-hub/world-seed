# Repository and Ecosystem Model

**Status:** Canonical
**Governs:** Separation of reusable ecosystem machinery from operator profiles and individual projects.
**Last verified:** 2026-10-20

## Separate responsibilities

- **world-seed** bootstraps the account/ecosystem operating model: governance, AI leadership, account orientation, repository relationships, shared automation standards, profile-loading procedures, and recovery.
- **Operator profile package** holds the relevant operator's working preferences, approved identity/attribution details, environment facts, and account-specific operational notes in an operator-approved access-controlled location.
- **Personal-data package** holds genealogy, birth information, personal history, AI exports, family records, and other personal material under stricter access and disclosure rules.
- **Project seed** bootstraps an individual repository's reusable working relationship and document conventions. It does not decide the project's mission or architecture.
- **Project repositories** own their mission, canon, architecture, implementation, tests, project data, and roadmap.

The ecosystem seed may describe and invoke these layers, but must not become a container for all of them. See [PROFILE_PACKAGES.md](PROFILE_PACKAGES.md) for the canonical profile boundary and loading contract.

## Ecosystem orientation

The target account should have one clear launch point that tells a new builder how to understand the portfolio, where project canon lives, what the account's mission is, what is shared, and what remains project-sovereign.

A world/portfolio repository is not a monolithic application. It maps and coordinates independent projects; cross-project integration occurs through explicit contracts and only when justified.

## Canonical ownership

- Reusable AI operating policy: world-seed governance.
- Account mission and portfolio orientation: target account's world/portfolio layer.
- Operator working preferences and machine facts: authorized operator profile package.
- Sensitive personal history and exports: separately protected personal-data package, disclosed only when relevant and authorized.
- Project mission, architecture, implementation, tests, and project decisions: that project's own repository.
- Credentials and secrets: approved secret manager, never seed files or ordinary profiles.
- Runtime contracts: the actual shared infrastructure repository and installed implementation, not remembered descriptions.

## Discovery and reuse

When a sound world/portfolio layer, operator profile, shared service, or project seed already exists, inspect and reuse it. Do not assume the target account resembles the source account. Keep a provenance note when adapting existing rules and document any deliberate divergence.

Discover the actual target account's ecosystem-orientation repository, project seed, and shared infrastructure from authorized profile information and live account records. Do not hard-code the source account's repository names into this portable model.

## Boundary rule

Shared governance must not silently override project canon. Project canon must not silently claim authority over the whole account. An operator profile supplies context, not unrestricted authorization. A personal-data package supplies information, not permission to disclose or use it for every purpose. When a real conflict exists, record it, identify the affected boundary, and obtain the appropriate decision rather than hiding it in a generic template.
