# Project Generation

**Status:** Implemented baseline; full factory acceptance remains incomplete.  
**Governs:** Creation of a new project from the portable World Seed template; recovery requirements remain in `RECOVERY.md`.  
**Last verified:** 2026-10-22

## Purpose

World Seed generates a disposable project bundle from its own versioned templates without cloning or contacting the separate Project Seed repository. The generated project owns its mission and project-specific decisions. Generation creates a starting point, not a finished product.

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
- `AGENTS.md` — project-builder instructions, including the first-build quality protocol, accountable delegation/context economy, durable handoffs, and licensing/attribution checks.
- `CONSTITUTION.md` and `HUMAN.md` — project operating rules and human/AI working boundaries.
- `LICENSE` — the MIT license template with copyright placeholders that must be completed accurately before publication.
- `DOCS.md` — documentation conventions.
- `MACHINE.md` — a portable placeholder for facts to be discovered locally; no Bucky-specific values are embedded.
- `ORGANS.md` — conditional integration guidance that requires checking actual contracts.
- `README.md` — project entry point.
- `world-seed-manifest.json` — template version, source revision, mission, generated-file inventory, SHA-256 hashes for each generated file, generation timestamp, and pre-write validation results covering required files, mission substitution, unresolved template markers, and local Markdown links.

The project template version is recorded in `templates/project/PROJECT_TEMPLATE_VERSION` and the generated manifest. Changes to the generated builder contract must bump that version and update the generation tests. Template version `1.3.0` also carries forward Project Seed's reusable implementation-agent handoff/context-economy rules and its MIT-by-default guidance for new software projects, while keeping owner identity out of the portable template. The generated `LICENSE` deliberately retains `<YEAR>` and `<COPYRIGHT HOLDER>` placeholders because the portable generator does not yet load an authorized operator profile. Complete those fields accurately before publication; do not guess ownership.

The manifest records the initial generated bundle, not future changes to it. It excludes itself from its own generated-file list. Hashes detect later changes to listed files; they do not authenticate the manifest or capture user-added data. The [Local Project Library](PROJECT_LIBRARY.md) can compare listed generated files with these hashes. A match is only a local integrity signal, not a backup or restore guarantee.

## First-build quality loop

After generation, the builder must continue beyond the scaffold:

1. Read the mission and governing documents; inspect the real problem and relevant existing work.
2. Define observable acceptance criteria and record material assumptions.
3. Choose an architecture and technology suited to the mission rather than assuming a universal stack.
4. Build the smallest complete, useful end-to-end slice.
5. Add meaningful behavior tests and appropriate quality checks.
6. Document reproducible setup, run, and test commands, and verify them in a clean environment when practical.
7. Review the implementation, canon, docs, tests, dependencies, and automation together; fix contradictions and unfinished placeholders.
8. Report evidence, remaining gaps, and the next justified action. Do not equate green CI or a generated directory with project quality.

## Verification and limits

Automated tests cover bundle completeness, mission substitution, manifest provenance and file hashes, the recorded pre-write validation checks, rejection of broken local Markdown links, invalid names, refusal to overwrite, refusal to generate inside the factory source checkout, exclusion of operator machine details and credentials, and the presence of the generated first-build quality protocol.

CI also runs `scripts/run_generated_project_recovery_drill.py`, which generates a disposable project, adds synthetic user-authored text and binary data, captures and restores the tree including its manifest, verifies the source remains unchanged, and confirms the restored project catalogs as `generated-files-match`.

The synthetic drill proves the specific generator and fixture behavior it exercises. It does not demonstrate that a fresh builder can produce a coherent, useful, implemented project from a real mission. That remains a primary factory acceptance gate. Nor does it prove recovery of live repository history/working-tree state, restore private operator/personal data, or export GitHub-only records. Do not claim the factory or a generated project is fully accepted until the relevant gates have direct evidence.
