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

The current `prepare_local_handoff_backup.sh` script covers repository checkouts, Git bundles, and source ZIP snapshots only. After capture, run `scripts/verify_source_artifacts.py` against the backup directory and write its report outside that directory and outside the public seed checkout:

```bash
python3 scripts/verify_source_artifacts.py \\
  --backup-dir "$HOME/archive/your-backup-directory" \\
  --output "$HOME/private-recovery/source-verification.json"
```

This verifier attempts an isolated mirror clone of each unambiguous Git bundle, compares the bundle's refs with the checkout's refs, checks ZIP CRC integrity, compares ZIP file names and contents against an archive of the checkout's `HEAD` tree, and checks that each checkout is a Git work tree. A `source-artifacts-verified` result is still only a source-artifact integrity signal: it does not establish that every expected GitHub ref was originally captured, that checkout `HEAD` is the intended revision, that GitHub-only records/settings are preserved, or that full account restoration succeeds. Run it only on a trusted local backup directory; it invokes Git against local artifacts and does not contact GitHub. Run `scripts/export_github_operating_records.py` once per repository to preserve paginated issue/PR records, conversation comments, PR reviews and inline comments, releases and asset metadata, workflow-run metadata, and Actions artifact metadata. It writes dated private JSON snapshots and a private manifest. Binary artifact contents, release asset contents, discussions, and other unsupported records remain explicitly incomplete. The separate `scripts/export_governance_settings.py` collector preserves readable repository metadata, classic default-branch protection, repository rulesets, and applicable organization rulesets. It writes to a caller-chosen local directory outside the seed checkout and attempts restrictive directory/file permissions. Use it with `GH_TOKEN` or `GITHUB_TOKEN` supplied through the environment, never as a command-line argument:

```bash
python3 scripts/export_governance_settings.py \
  --repository OWNER/REPOSITORY \
  --output-dir "$HOME/private-recovery/records/governance"
```

Treat the resulting JSON as sensitive account-operating data. Store it in private, access-controlled storage independent of the GitHub account being protected; do not commit it to this or any public repository. Review each control's status. HTTP 403/401 and other access failures remain unverified/error; HTTP 404 is recorded as not-reported, not proof that no effective protection exists. A partial export is not a backup-completeness pass.

This exporter is **capture-only**: it does not restore settings, cover every GitHub operating record, or certify effective enforcement. Restore must be a separate, deliberate, reviewable operation. Before declaring governance recoverable, recreate settings in an isolated test repository/account, reread the effective settings, compare them against the export, and document unsupported fields, missing permissions, and any differences. Never automatically apply an export to a live repository during routine audit or recovery discovery.



For each repository in the backup inventory, run the metadata exporter with a private output directory outside the public seed checkout:

`python3 scripts/export_github_operating_records.py --repository OWNER/REPOSITORY --output-dir "$HOME/private-recovery/records"`

It uses `GH_TOKEN` or `GITHUB_TOKEN` from the environment, or an existing GitHub CLI login. Never pass or print a token. Review every endpoint status in the report and manifest; successful metadata collection is not a complete backup. Until exports are reviewed for every expected repository, governance restoration has been tested, coverage is integrated, and an isolated recovery drill has passed, the account backup remains **incomplete for full GitHub reconstruction**.

Do not delete, archive, or restructure source repositories on the strength of a source-only backup.

## Never include

Do not commit passwords, access tokens, private keys, recovery codes, session cookies, or secrets. Do not include sensitive private-repository contents in public profiles or manifests. Store credentials only in approved secure systems and document the safe procedure for reacquiring access.

## Governance settings restoration protocol

**Current implementation status:** export-only. There is not yet an automated settings-restoration command. Do not infer otherwise from the presence of an export.

For every recovery, treat the governance export as evidence to review—not as an instruction to blindly apply settings:

1. **Validate the source.** Confirm the export's repository identity, timestamp, schema version, and per-control status. Reject malformed, partial, or unverified exports as a complete source of truth. Confirm the inventory and default branch independently.
2. **Choose an isolated target.** Restore into a dedicated test repository in a test organization/account where feasible. Never test destructive or potentially locking settings against the live account.
3. **Build a reviewable change plan.** Compare classic protection fields, every ruleset's conditions/rules/enforcement/bypass actors, and applicable organization rulesets. Record fields that cannot be recreated, unsupported settings, identity-specific actor IDs, and permission gaps. Do not silently omit or weaken a control.
4. **Require explicit human approval before writes.** The proposed settings and their intended target must be reviewed before applying any settings. No routine audit, inventory, or export command may perform restoration implicitly.
5. **Apply deliberately.** Use GitHub's supported settings UI or API to recreate the reviewed policy on the isolated target. Keep the operation separate from the read-only exporter. Do not copy credentials or secrets from an export.
6. **Read back and compare.** Retrieve the target's effective settings again. Compare required checks by their exact names, pull-request/review requirements, conversation resolution, admin enforcement, force-push/deletion controls, ruleset conditions, enforcement modes, and bypass actors. A successful write response alone is insufficient.
7. **Test enforcement safely.** Verify expected allowed and blocked actions using a disposable test branch/repository and non-destructive test changes. Never attempt a live bypass or destructive test just to prove a rule works.
8. **Record evidence and residual gaps.** Preserve source and target identities, timestamps, comparison results, safe test outcomes, and unresolved differences in private recovery storage. Keep the recovery status unverified until the drill passes.

Restoration is proven only for the tested scope. A successful isolated drill does not establish that unrelated settings, permissions, environments, webhooks, secrets, or GitHub-only records are recoverable.

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

The automated `scripts/run_local_recovery_drill.py` is the first small acceptance test. It creates a temporary synthetic Git repository, creates and verifies a bundle, clones the bundle into a fresh directory, deliberately damages a tracked file, restores the known checkpoint, and verifies a clean working tree. It uses no network and does not touch real project files. Run it with:

```bash
python3 scripts/run_local_recovery_drill.py
```

It can optionally write a private JSON report to a new path whose parent directory already exists:

```bash
python3 scripts/run_local_recovery_drill.py --output "$HOME/private-recovery/local-drill.json"
```

The report explicitly limits its claim to this synthetic local Git exercise. A passing result is **not** proof of real-project recovery, complete backup coverage, independent account recovery, or GitHub metadata/settings restoration. Those require separate acceptance tests.

At a chosen cadence, perform a safe recovery drill in an isolated test account or environment. Verify that the seed can be retrieved without the original GitHub account and that a fresh builder can follow the instructions. Do not test destructive recovery against the live account.

Record the drill date, seed version, scope, results, and remaining gaps. A written recovery plan without a demonstrated drill is planned recovery, not proven recovery.


## Selective recovery payload: preserve state, regenerate machinery

The primary recovery set is **not a copy of every repository or of the whole world**. It is a small, explicit payload of irreplaceable user/project state plus the metadata and recipes needed to reconstruct the operating system and regenerate disposable projects.

Classify each item before backup:

- **Preserve as userdata:** operator preferences and approved personal records; project-specific decisions, specifications, datasets, authored material, provenance, and other details that cannot be recovered from an authoritative source. Keep personal-data and operator-profile packages separate from public seed material.
- **Record as recovery metadata:** repository identities and roles, canonical source locations and revisions, project-generation parameters, dependency/service contracts, ownership and permission requirements, configuration schemas, restore order, and verification procedures. Metadata must say where the source of truth lives and whether it was actually checked.
- **Regenerate after bootstrap:** the factory itself, World Seed from its trusted source, APIs/BUS components, dependencies, generated project repositories, and other machinery—provided the factory can fetch their authoritative source, provision them safely, and verify the result.
- **Discard or rebuild as cache:** temporary files, generated indexes, downloaded build artifacts, and other replaceable outputs.
- **Re-provision separately:** credentials and secrets. Store neither in general backups nor public manifests. Record the approved method to reacquire them without exposing their values.

A project repository is disposable by default. Do not preserve its entire Git history merely because it exists. Preserve its unique user/project details and a recipe that can recreate it. If an audit establishes that some repository contains unique material not captured elsewhere, classify that material as userdata before any reset; never infer that deletion is safe from the word “disposable.” A repository marked as a required source of truth must be independently reachable or separately preserved before relying on regeneration.

The seed itself is bootstrap machinery, not userdata and not part of each project-data backup. Because it is needed to recover from loss of the target GitHub account, keep a small independent copy of the seed/bootstrap entry point outside that account. This is a separate bootstrap safeguard, not a reason to bundle the whole seed, all private repositories, or all project source into every recovery payload.

Every recovery manifest must identify the preservation class, source of truth, capture time/revision, sensitivity, verification method, and restore action for each included item. The default project backup should contain the selective payload and manifest, not full repository clones/bundles/ZIPs. Full source snapshots are opt-in exceptions when the project has a documented reason. The factory must refuse destructive reset while required unique state is unclassified, missing, or unverified.

## Local factory bootstrap status

The first local installer is documented in [FACTORY_INSTALLER.md](FACTORY_INSTALLER.md) and implemented in `scripts/install_local_factory.sh`. It installs a versioned local bootstrap and saves a private machine profile. It is deliberately not yet the full factory: project-specific userdata collection, private profile restoration, API/BUS wiring, secure delivery, repository regeneration, and a clean-environment end-to-end recovery acceptance drill remain open gates.


## Post-wipe regeneration model (ROM Manager analogy)

**Design intent:** Treat recovery like a rooted-Android ROM workflow, not like a demand to preserve every partition. A wipe removes the disposable operating environment; the factory installer then flashes/installs the portable machinery, discovers the live system, loads authorized preferences, regenerates derived structures, and reboots into a usable environment. Some state must survive independently; other state is expected to be recreated after the wipe.

The analogy is a design guide, not evidence that the current installer already implements every step. The end-to-end acceptance drill must prove each claimed step.

### Classify state before deciding what to back up

| State class | Recovery treatment | Examples |
|---|---|---|
| Portable factory / seed | Preserve independently and verify integrity before the wipe | World Seed source and history, bootstrap instructions, schemas, installer, tests |
| Irreplaceable owner data | Capture independently, verify, and test restoration before the wipe | Personal records, user-created documents/exports, unique project data, essential operating records |
| Operator profile and preferences | Preserve the approved source package; regenerate the private repository container after bootstrap if needed, then restore the package | Communication preferences, approved attribution, machine/account orientation, non-secret configuration |
| Machine-derived facts | Rediscover after installation and compare with any prior profile as a clue, not truth | OS/hardware inventory, installed tools, paths, available services, current repository access |
| Regenerable private infrastructure | Recreate after the wipe through the factory installer and authorized GitHub CLI/API access | Private operator-profile repository, private personal-data repository/container, private Intake Dock |
| Credentials and secrets | Never place in generic backups, profile manifests, public seed, or Dock payloads unless an explicitly approved secure secret system is designed for them | Tokens, passwords, private keys; document safe re-authentication/rotation instead |
| Disposable build/runtime state | Rebuild from source and configuration; preserve only if it contains unique, classified user data | Virtual environments, caches, generated artifacts, temporary worktrees |

Do not confuse **recreating a repository** with **recovering its contents**. The factory may create a fresh private repository after a wipe, but any irreplaceable contents must first be preserved independently and then selectively restored. If a package is absent, inaccessible, or cannot be restored, bootstrap may continue only within the documented safe scope and must report the gap honestly.

### Expected post-wipe bootstrap sequence

1. Start from the independently preserved, integrity-checked seed and authorized bootstrap instructions.
2. Install the portable factory machinery on the clean machine.
3. Discover the live machine and available tools; record current facts rather than assuming an old machine profile is still accurate.
4. Load the authorized operator profile and preferences, if available, and keep personal-data access separate and purpose-limited.
5. Through the factory installer, use the owner's authorized GitHub CLI/API identity to create or verify the required **private** repositories/containers. Intended targets include the operator profile, personal-data package, and private Intake Dock. Check visibility and ownership explicitly; never silently create public repositories.
6. Upload only the corresponding approved profile/package contents to their correct private destinations. Do not upload credentials, secrets, or unrelated personal records.
7. Restore irreplaceable data from the independently preserved recovery set, with integrity checks and a manifest of what was restored, omitted, or failed.
8. Rebuild derived machine state and disposable project state from the seed and approved configuration.
9. Verify permissions, repository contents, bootstrap health, and the acceptance checks; record evidence and residual gaps.

Repository creation and access-control changes require owner authorization. The design must not assume that GitHub CLI authentication implies blanket permission to modify every repository. Use an explicit allowlist/declared target set, least privilege, idempotent operations, and clear failure reporting.

### Private Intake Dock

The factory should create or verify a dedicated private GitHub repository used as a **loading dock** for user-supplied exports, documents, source bundles, and other material intended for Codex to work with. It is a staging boundary, not the public seed, not the operator profile, and not the personal-data archive.

- Confirm the repository is private before uploading anything.
- Keep uploaded material clearly separated from generated outputs and implementation changes.
- Record provenance, intended purpose, sensitivity, and retention/cleanup expectations where practical.
- Give Codex access only to this declared work area and other specifically authorized project repositories; a connected account is not blanket authorization.
- Do not use the Dock as the only copy of irreplaceable data. Anything required for recovery needs an independent preservation path.
- Do not automatically forward Dock contents to unrelated projects, public repositories, prompts, or services.

### Current implementation status

This section defines the intended architecture and acceptance target; it does not certify that the current installer already creates repositories, uploads profile/data packages, creates the Intake Dock, or completes an end-to-end post-wipe restore. Track those as implementation gates and prove them in an isolated recovery drill before claiming recovery readiness.
