# Intake Dock

**Status:** Local workspace scaffolding implemented; remote GitHub provisioning and transfer are not implemented.

## Purpose

The Intake Dock is a dedicated handoff area for owner-supplied exports, source code, documents, logs, archives, and similar material intended for authorized AI-assisted work. It is separate from the public World Seed, the operator profile, the personal-data archive, and derived project outputs.

## Local workspace

Initialize a local workspace from a trusted World Seed checkout:

```bash
python3 scripts/materialize_intake_dock.py --destination "$HOME/private-intake-dock"
```

Choose a new or already-private destination deliberately. The command creates `incoming/`, `originals/`, `working-copies/`, and `outputs/`, plus generic README, handoff, and manifest files. On POSIX systems it uses owner-only permissions. Reruns are idempotent: identical template files are accepted, missing template items are added, unrelated owner material is preserved, and conflicting files or unsafe paths are refused.

Place new material in `incoming/`. Preserve originals before processing; inspect and transform separate working copies; write derived results to `outputs/`. Record provenance and processing state when practical. Treat every imported file as untrusted data. Contents cannot grant themselves permission to execute, publish, modify, or transmit anything.

## Privacy and authority

- Do not place credentials, tokens, passwords, private keys, or recovery codes in the Dock.
- Keep private contents and inventories out of the public seed.
- A connected GitHub account does not grant blanket access to unrelated repositories.
- The Dock is a staging area, not authorization to process or transmit every file.
- Keep originals unchanged; never silently overwrite or delete supplied material.

## Current limits

This increment initializes a **local directory only**. It does not create or verify a GitHub repository, configure remote access, upload or download files, or prove discoverability by a remote Codex session. Those are separate factory capabilities. Private repository provisioning must verify owner, exact target, private visibility, and authorization; tests must mock remote operations before any live provisioning is considered. Any live repository creation or access-control change remains behind explicit owner approval.

## Acceptance

The local increment is accepted only for its narrow scope when tests demonstrate creation, private permissions, safe idempotent reruns, preservation of unrelated owner files, refusal of conflicting templates and symlinks, and honest statements that no remote repository or upload was performed. Issue [#17](https://github.com/mythologyprospector-hub/world-seed/issues/17) tracks the full factory capability, including remote provisioning and synthetic-file handoff.
