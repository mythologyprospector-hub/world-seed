# Repository and Ecosystem Model

**Status:** Canonical
**Governs:** Separation of reusable ecosystem machinery from individual projects.
**Last verified:** 2026-10-19

## Two levels of seed

- **world-seed** bootstraps the account/ecosystem operating model: governance, AI leadership, account orientation, repository relationships, shared automation standards, machine profile, and recovery.
- **project seed** bootstraps an individual repository's reusable working relationship and document conventions. It does not decide the project's mission or architecture.

The ecosystem seed may invoke or point to a project seed, but the two must not compete for ownership of the same responsibilities.

## Ecosystem orientation

The target account should have one clear launch point that tells a new builder how to understand the portfolio, where project canon lives, what the account's mission is, what is shared, and what remains project-sovereign.

A world/portfolio repository is not a monolithic application. It maps and coordinates independent projects; cross-project integration occurs through explicit contracts and only when justified.

## Canonical ownership

- Account constitution and reusable AI operating policy: ecosystem governance source.
- Account mission and portfolio orientation: target account's world/portfolio layer.
- Project mission, architecture, implementation, tests, and project decisions: that project's own repository.
- Machine facts and environment-specific configuration: machine profile or secure configuration outside source control.
- Credentials and secrets: approved secret manager, never seed files.
- Runtime contracts: the actual shared infrastructure repository and installed implementation, not remembered descriptions.

## Existing systems

When a sound world/portfolio layer or project seed already exists, inspect and reuse it. Do not assume the target account resembles the source account. Keep a provenance note when adapting existing rules and document any deliberate divergence.

For Jimmy's current environment, the existing sources include:
- [World](https://github.com/mythologyprospector-hub/world) for account-level orientation and stewardship;
- [Project Seed](https://github.com/mythologyprospector-hub/project_seed) for the project-level constitution and documentation standards;
- [Organs](https://github.com/mythologyprospector-hub/organs) for shared runtime infrastructure contracts and implementation.

These are reference sources for this operator's ecosystem, not mandatory repository names for other accounts. Inspect their current contents before relying on them.

## Boundary rule

Shared governance must not silently override project canon. Project canon must not silently claim authority over the whole account. When a real conflict exists, record it, identify the affected boundary, and obtain the appropriate decision rather than hiding it in a generic template.
