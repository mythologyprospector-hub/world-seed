# Runtime Plumbing and Organs Disposition

**Status:** Architecture direction; implementation and migration not yet accepted  
**Governs:** Where shared runtime services belong in the World Seed factory, local installer, and generated projects  
**Last audited:** 2026-10-21

## Decision direction

World Seed is the portable factory and recovery system. The factory installer is the local machine setup and lifecycle entry point. Shared runtime services should be treated as **factory-managed, optional local capabilities**, not as an independent ecosystem foundation that every project must install or depend on.

Organs is the existing implementation and contract source for several potentially reusable capabilities. Its age and existing code make it important recovery material, but neither its repository identity nor its current architecture is sacred. The factory should absorb the useful capabilities and lessons after an evidence-based audit, then retain, simplify, replace, or retire each component according to demonstrated need.

This is a direction for the migration, not a claim that Organs has already been absorbed. The current installer does not install, configure, start, or recover Organs services.

## Responsibility boundaries

| Layer | Responsibility | Must not become |
|---|---|---|
| World Seed | Portable rules, templates, factory workflows, recovery manifests and verification | A mandatory running server for every generated project |
| Factory installer / local manager | Discover prerequisites, install versioned local components, manage configuration and lifecycle safely, report exact state, support recovery | A monolithic application that embeds every service |
| Shared runtime capabilities | Optional local services with explicit contracts, bounded permissions, owned state, tests and replaceable implementations | Hidden authority or a universal domain database |
| Generated project | Own its mission, domain model, project data and declared dependencies | A consumer of shared services merely because they exist |
| Operator profile and personal-data package | Private operator preferences and irreplaceable personal records | Public seed content or generic project templates |

The factory can manage a service without making that service mandatory. Projects should declare a runtime capability as required only when a verified workflow actually needs it. Standalone operation should remain possible where the project supports it.

## Organs capability inventory

The current Organs repository has 138 tracked source/documentation files in its default-branch tree at `76fe42259f43414afc6a825556180d70c24b8f73`. It includes independently tested Python/FastAPI services, shared request/error/correlation conventions, a registry client, a persistent BUS, memory, telemetry, bounded execution, risk classification, approval coordination, introspection and operator interfaces. The code and test suites are migration inputs, not proof that every capability should survive.

| Capability / asset | Initial disposition | Required evidence before adoption |
|---|---|---|
| Shared API conventions: health/info, error envelope, correlation IDs | Candidate shared library/contract | Minimal contract and compatibility tests; avoid imposing HTTP service wrappers on in-process code |
| Registry / service discovery | Optional local service if multiple independently running services need it | Demonstrate actual discovery need; specify boot order, stale services, failure behavior and local-only exposure |
| Communications BUS | Candidate optional shared service | Verify durable delivery, dispatch semantics, cursor ownership, idempotency and recovery from its real database |
| Runtime memory | Keep distinct from operator personal data and domain truth | Define owner, retention, export/restore, migration, deletion and privacy boundaries |
| Telemetry | Optional operational service or library | Define event schema, storage owner, retention and failure isolation; never equate telemetry with scientific evidence |
| Critic / Executive approval mechanisms | Reuse only where a concrete action workflow requires them | Threat model and tests for real human approval, caller identity, bypasses and fail-closed behavior |
| Sandbox / Orchestrator | Optional, high-risk capabilities; not part of the minimum installer baseline | Explicit execution threat model, fixed allowlists, containment tests and separate enablement |
| Introspection / Reflection / I/O Interface / TUI | Optional operator tools or future modules | Demonstrate a current user need and ensure no hidden authority or unbounded autonomy |
| Tests, architecture, security notes, decision history | Preserve as migration evidence | Map each relevant test/contract to the adopted, replaced or retired component |
| Runtime databases under `/srv/organs` | Separate recovery inventory; not source code | Inventory exact files, owners, permissions, schema/version, contents and restore requirements before any move or deletion |
| Systemd units, environment files and installer behavior | Re-evaluate, do not copy blindly | Least privilege, private configuration, no secret disclosure, safe reruns, explicit target, clean install/uninstall and rollback tests |

## Security and installation findings

The current Organs documentation states that services bind to loopback and that the current threat model trusts processes running as the same machine user; it also acknowledges no cryptographic authentication on the HTTP surfaces. Those are material limitations, not details to inherit silently.

The current Organs `install.sh` overlays files into `/srv/organs`, changes ownership recursively, installs Python dependencies using `--break-system-packages`, and runs tests against the installed tree. It says runtime data is preserved. That legacy installer is **not** an acceptable drop-in implementation for the World Seed factory installer.

The World Seed installer currently installs a versioned World Seed release and private local scaffolding, and explicitly does not install or reconfigure Organs. Preserve that safe separation while the service-manager design is developed. Do not change live `/srv/organs`, running services, systemd units, runtime databases, credentials or network exposure as part of a documentation/audit step.

## Migration sequence

1. **Preserve evidence.** Keep the Organs repository and useful history intact while recovery inventory captures source, tests, contracts, licenses, configuration templates and runtime-data locations separately.
2. **Map requirements.** Tie each capability to a concrete factory or project workflow. A service with no demonstrated consumer remains optional or is retired; age alone is not a reason to keep it.
3. **Define the local component model.** The installer should manage versioned components through explicit manifests and lifecycle commands. Keep the installer as orchestrator, not the implementation of all services. Installation should be opt-in by capability, idempotent, least-privilege, auditable and safe to roll back.
4. **Extract and test.** Reuse existing implementation only where its contracts and security posture pass review. Prefer small libraries or services behind stable contracts. Add clean-environment, failure-mode, data-migration, and recovery tests before enabling a component by default.
5. **Prove recovery.** Capture the selected source and any explicitly authorized runtime data; restore into an isolated location; verify manifests/hashes, service health, data semantics and relevant tests. Synthetic drills alone do not clear live runtime state.
6. **Retire deliberately.** Once the factory owns the adopted capability and recovery is proven, update the repository inventory and only then decide the fate of the old Organs repository and local installation.

## Acceptance criteria

Runtime-plumbing absorption is not complete until:

- World Seed can be installed and recovered without Organs being present.
- The installer reports installed, enabled, running, healthy, disabled and missing states distinctly; it never equates installation with health.
- Every managed service has an explicit manifest, version, configuration boundary, state location, health check, test command, upgrade path and rollback/recovery procedure.
- A generated project declares whether each runtime capability is optional or required and documents degraded behavior if an optional service is unavailable.
- No secrets or personal records enter public templates, logs, manifests or telemetry by default.
- The selected capabilities pass automated tests and an isolated clean-install/recovery drill.
- Unadopted Organs components, old repositories and runtime data remain untouched until their preservation and retirement gates are independently satisfied.

## Current status

**Verified:** World Seed's existing installer intentionally avoids Organs installation; Organs source and contracts are available for audit; the current installer and synthetic recovery suite have independent test coverage.

**Not yet verified:** any factory-managed runtime-service implementation, migration of Organs services, restore of real Organs databases, clean-machine runtime installation, or the suitability of each Organs component for the rebuilt ecosystem.

**Next step:** finish the World Seed recovery acceptance gates and the real project-tree rehearsal; then implement the smallest tested local service-management layer, beginning with inventory and declarative manifests rather than enabling every Organs service at once.
