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

## Backup coverage is not one thing

A Git clone, Git bundle, or source ZIP preserves repository content to varying degrees; it does **not** preserve the full GitHub operating record. Every backup set must carry a coverage manifest that distinguishes at least these categories:

| Category | Required evidence |
|---|---|
| Git source and history | Repository/ref list, bundle integrity check, and isolated restore test |
| Issues and pull requests | Export status and record counts, including closed records |
| Issue comments and pull-request reviews/comments | Export status and record counts; identify unsupported or inaccessible endpoints |
| Releases and attached assets | Release metadata plus separate asset-preservation status |
| GitHub Actions | Workflow-run metadata, artifact metadata, and separate status for downloading binary artifact contents |
| Repository/organization configuration | Exported settings, rulesets, branch protections, environments, webhooks, and permission coverage where authorized |
| Secrets and credentials | Never copied into a general backup; document approved recreation/rotation steps instead |
| Discussions and other GitHub-only records | Explicitly included, excluded, or unverified—never silently assumed covered |

An endpoint returning successfully proves only that the current identity could retrieve that endpoint at that time. It does not prove every record was paginated, every binary artifact was downloaded, or every setting was visible. Store detailed manifests and exports in access-controlled storage outside the public seed. Do not publish private repository names, private discussions, or security-sensitive configuration.

The current `prepare_local_handoff_backup.sh` script covers repository checkouts, Git bundles, and source ZIP snapshots only. Until a separately verified operating-record export and configuration-coverage procedure exists, the account backup remains **incomplete for full GitHub reconstruction**. Do not delete, archive, or restructure source repositories on the strength of a source-only backup.

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
