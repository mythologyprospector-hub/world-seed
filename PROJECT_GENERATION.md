# Project Generation

**Status:** Implemented baseline; full factory acceptance remains incomplete.
**Governs:** Creation of a new project from the portable World Seed template; recovery requirements remain in `RECOVERY.md`.
**Last verified:** 2026-10-21

## Purpose

World Seed can generate a new, disposable project bundle from its own versioned templates without cloning or contacting the separate Project Seed repository. The generated project owns its mission and project-specific decisions.

## Generate a project

Run from a trusted World Seed checkout:

```bash
python scripts/create_project.py \
  --name example-project \
  --mission "Make useful knowledge easier to discover." \
  --destination "$HOME/projects/example-project"
```

The name must be a lowercase slug. The destination must not already exist and must be outside the World Seed source checkout. The generator refuses to overwrite an existing path. It creates the directory locally and does not create a GitHub repository, configure a remote, upload data, provision credentials, or alter Organs.

## Generated bundle

The generator creates:

- `MISSION.md` — the shared discovery method with the supplied mission sentence.
- `AGENTS.md`, `CONSTITUTION.md`, and `HUMAN.md` — project operating rules and human/AI working boundaries.
- `LICENSE` — the MIT license template with copyright placeholders that must be completed from the authorized owner profile before publication.
- `DOCS.md` — documentation conventions.
- `MACHINE.md` — a portable placeholder for facts to be discovered locally; no Bucky-specific values are embedded.
- `ORGANS.md` — conditional integration guidance that requires checking actual contracts.
- `README.md` — project entry point.
- `world-seed-manifest.json` — template version, source revision, mission, generated-file inventory, SHA-256 hashes for each generated file, and generation timestamp.

The generated `LICENSE` deliberately retains `<YEAR>` and `<COPYRIGHT HOLDER>` placeholders because this portable generator does not yet load an authorized operator profile. Complete those fields accurately before publication; do not guess ownership. The manifest records the initial generated bundle, not future changes to it. It excludes itself from its own generated-file list. Hashes detect later changes to listed files; they do not authenticate the manifest or capture user-added data.

The [Local Project Library](PROJECT_LIBRARY.md) can compare listed generated files with these hashes. A match is only a local integrity signal, not a backup or restore guarantee.

## Verification and limits

Automated tests cover bundle completeness, mission substitution, manifest provenance and file hashes, invalid names, refusal to overwrite, refusal to generate inside the factory source checkout, and exclusion of operator machine details and credentials.

This generator is not yet a complete factory. It does not initialize Git, create a remote repository, discover and apply account-specific profiles, collect unique project data, back up live Git state, or prove isolated project recovery. Do not treat a generated folder as backed up or recoverable until those separate acceptance gates pass.
