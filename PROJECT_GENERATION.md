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
- `DOCS.md` — documentation conventions.
- `MACHINE.md` — a portable placeholder for facts to be discovered locally; no Bucky-specific values are embedded.
- `ORGANS.md` — conditional integration guidance that requires checking actual contracts.
- `README.md` — project entry point.
- `world-seed-manifest.json` — template version, source revision, mission, generated-file inventory, and generation timestamp.

The manifest records the initial generated bundle, not future changes to it. It excludes itself from its own generated-file list. A later Project Library capability must independently capture the manifest and selected user data, preserve revisions, and verify reconstruction.

## Verification and limits

Automated tests cover bundle completeness, mission substitution, manifest provenance, invalid names, refusal to overwrite, refusal to generate inside the factory source checkout, and exclusion of operator machine details and credentials.

This generator is not yet a complete factory. It does not initialize Git, create a remote repository, discover and apply account-specific profiles, collect unique project data, build the local Project Library, or prove isolated project recovery. Do not treat a generated folder as backed up or recoverable until those separate acceptance gates pass.
