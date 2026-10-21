# Profile Package Boundary

**Status:** Canonical architecture rule; initial migration in progress.
**Governs:** How world-seed separates portable operating machinery from operator-specific and personal information.
**Last verified:** 2026-10-20

## Purpose

World-seed must be reusable across owners, GitHub accounts, missions, and machines without carrying the source operator's personal information into every installation. The seed defines how an AI steward discovers, loads, protects, and applies profile information; it is not the storage location for a person's full profile or personal records.

## Three distinct layers

### 1. Portable world-seed

Keep here:
- universal governance, authority boundaries, humane-purpose rules, and stewardship expectations;
- bootstrap, audit, recovery, automation, and verification procedures;
- profile schemas/templates and instructions for discovering the target operator's approved profile;
- explicit privacy and access-control requirements.

Do not embed a real operator's machine inventory, personal history, family records, credentials, or private repository map in the distributable seed. Example data must be clearly fictional or intentionally public and must not be mistaken for the target operator's live state.

### 2. Operator profile package

Store in a separate, access-controlled location chosen by the operator. It may include:
- preferred name and working/communication preferences;
- approved public attribution details where needed;
- machine nicknames, hostnames, clone roots, installed services, and environment-specific procedures;
- approved account/repository orientation pointers and permission boundaries;
- credential-manager locations or retrieval procedures only when safe to disclose in that private environment—never credential values;
- profile provenance, verification dates, expiry/recheck rules, and explicit disclosure limits.

Load only the relevant profile material for the current task. Treat mutable machine facts as leads to verify, not as proof of current state. Never copy the private package into a public seed or project merely for convenience.

### 3. Personal-data package

Keep genealogy, birth information, personal history, exports from AI services, family records, and other sensitive or deeply personal material separate from the operator profile. Give this package stricter access controls and its own purpose, provenance, retention, and disclosure rules.

A project may request a specific piece of personal context only when it is relevant and authorized. Do not give every project a complete personal archive by default. Never include personal-data package contents in public artifacts, audit reports, prompts to unrelated services, or repositories without explicit authorization and a clear need.

## Loading contract

At bootstrap, the steward must:

1. Discover whether an operator profile package exists and whether the current identity is authorized to read it.
2. If accessible, read its index/manifest and only the profile sections relevant to the task.
3. Verify mutable environment facts against the live machine and account wherever possible.
4. Keep public attribution separate from private contact details, personal records, and credentials.
5. Record profile source, version/ref, access status, and any unverified fields in the private handoff or report—not in a public repository.
6. If the package is absent or inaccessible, proceed with universal rules and safe discovery; mark operator-specific assumptions unknown rather than inventing them.

The seed must remain useful when no profile package is available.

## Package format and portability

Prefer plain Markdown plus a small manifest for human readability and easy recovery. The manifest should identify package version, intended operator/account, included sections, sensitivity classification, last review date, and disclosure restrictions. Do not place secrets in the manifest.

Keep the package portable across storage providers. Its canonical home and access controls are an operator decision; world-seed must not assume that a particular private repository, cloud drive, or local path exists.

## Migration and acceptance

A legacy operator-specific profile is being removed from the proposed distributable tree in a reviewable privacy-cleanup change. Do not call the boundary complete merely because this architecture document exists. Before the foundation is accepted for distribution:

- establish an authorized, private destination for the operator package;
- preserve and verify the needed profile information there;
- replace bundled operator-specific content in the distributable seed with a generic template or loading instructions;
- remove source-operator-specific assumptions from universal procedures and tests;
- inspect the final public tree and generated artifacts for personal or private operational data;
- confirm that a fresh builder can bootstrap with the private package absent, and with it present when authorized.

Removing content from the current tree does not erase prior Git history or copies already made. If historical exposure needs remediation, assess that separately and do not claim that a file deletion retroactively makes previously public data private.

## Approval and safety boundaries

Creating a new repository or changing access controls requires explicit owner approval. For this migration, the private destination exists and the migration draft's presence and provenance have been checked. Its mutable machine facts were not live-verified, and the profile remains subject to owner review; keep the public-tree cleanup and private package reviewable until both boundaries are confirmed. Never make a private package public to simplify bootstrap, and never place credentials or secrets in either package.


## Post-wipe regeneration and private repository provisioning

Use the rooted-Android ROM Manager analogy as a practical mental model: the factory is the installable system; not every partition or runtime artifact must be backed up. After a wipe, the installer can rediscover the machine, reinstall portable machinery, regenerate disposable infrastructure, and reload authorized settings. However, anything unique that cannot be recreated must be independently preserved and verified before the wipe.

The intended bootstrap should:

1. Discover live machine facts and collect only the system information needed for the operator's environment.
2. Load the approved operator preferences/profile package if available; do not treat stale machine facts as authoritative.
3. Use the owner's authorized GitHub CLI/API identity to create or verify the required private repositories/containers for the operator profile and personal-data package.
4. Restore the corresponding approved package contents from the independent recovery set. Creating an empty repository is not data recovery.
5. Create or verify a dedicated **private Intake Dock** repository for user-supplied exports, documents, source bundles, and other material that Codex is meant to work with.
6. Verify private visibility, owner/target identity, access boundaries, upload results, and idempotent reruns. Fail safely if authorization, visibility, or target identity cannot be verified.

The Intake Dock is a private staging area, separate from the portable public seed, operator profile, personal-data archive, and generated project outputs. Codex should be directed to use it as an explicit input/work area, not treated as authorized to roam across every repository just because GitHub is connected. Never put credentials or secret values into these packages or the Dock.

This is intended architecture, **not a claim of current capability**. The existing local installer still needs implementation and an isolated post-wipe acceptance test for private repository creation, package restoration/upload, and Intake Dock provisioning. See [RECOVERY.md](RECOVERY.md) for the state classification and complete recovery sequence.


## Separate Intake Dock

The Intake Dock is not a third profile/personal-data package. It is a separate staging/work-handoff boundary for source material and derived work. See [INTAKE_DOCK.md](INTAKE_DOCK.md). The current `scripts/materialize_intake_dock.py` creates a private local directory structure only; it does not create a GitHub repository, upload files, or grant Codex access to unrelated repositories. Preserve original inputs and keep derived outputs separate. User-supplied contents remain untrusted and may contain sensitive information; keep them out of the public seed. The full remote capability and synthetic handoff acceptance remain open under issue #17.
