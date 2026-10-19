# Independent Recovery and Reconstruction

**Status:** Canonical
**Governs:** Preserving and rebuilding the operating ecosystem if an account, repository, machine, or conversation is lost.
**Last verified:** 2026-10-19

## Recovery principle

The seed must not depend solely on the GitHub account it is intended to recover. Maintain an independent copy of world-seed and essential recovery documentation outside that account, in a location controlled by the owner.

A GitHub repository alone is not an independent backup of itself.

## Keep recoverable

- world-seed at a known version/ref;
- the target account's mission and governance profile;
- an inventory of repositories and their roles;
- bootstrap commands and prerequisites;
- machine profiles and non-secret configuration;
- external dependencies, service contracts, and recovery order;
- verification instructions and known limitations.

Keep project data and project-specific backups according to each project's needs. This seed does not replace those backups.

## Never include

Do not commit passwords, access tokens, private keys, recovery codes, session cookies, or secrets. Do not include sensitive private-repository contents in public profiles or manifests. Store credentials only in approved secure systems and document the safe procedure for reacquiring access.

## Rebuild sequence

1. Recover the independent seed copy.
2. Restore access to the owner-controlled GitHub identity using the platform's official recovery process.
3. Verify ownership and establish credentials securely.
4. Inventory the target account; do not recreate repositories until the inventory is reconciled against any surviving copies.
5. Restore the ecosystem/world orientation layer and its governance.
6. Restore or initialize project-seed machinery.
7. Recreate repository configuration, workflows, and permissions deliberately from documented state.
8. Restore projects from their own authoritative backups and provenance records.
9. Re-establish shared infrastructure only after inspecting the replacement machine and current contracts.
10. Run verification and report missing data, unverified behavior, and residual risk.

## Recovery drill

At a chosen cadence, perform a safe recovery drill in an isolated test account or environment. Verify that the seed can be retrieved without the original GitHub account and that a fresh builder can follow the instructions. Do not test destructive recovery against the live account.

Record the drill date, seed version, scope, results, and remaining gaps. A written recovery plan without a demonstrated drill is planned recovery, not proven recovery.
