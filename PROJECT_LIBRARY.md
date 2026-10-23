# Local Project Library

**Status:** Catalog-only first increment; backup and restoration are not implemented.
**Purpose:** Maintain a private local inventory of projects while distinguishing observable state from verified integrity.
**Security:** The catalog can contain local paths, project names, and mission text. Store it outside public repositories with owner-only permissions.

## Build a catalog

Run against one or more parent directories whose immediate child directories are projects:

```bash
python scripts/project_library.py \
  --root "$HOME/projects" \
  --output "$HOME/private-recovery/project-library.json"
```

Repeat `--root` to inspect another parent directory. The scan is one level deep; it does not follow symlinked project directories and does not recursively walk arbitrary project files. Keep the output outside every scanned root. The output is written atomically with owner-only permissions.

## Manifest compatibility

The catalog accepts World Seed project manifest schemas 1 and 2. Schema 2 records the generator's pre-write validation results; the catalog treats those results as recorded metadata, not independently authenticated proof.

## Catalog states

- `unmanaged-directory` — a directory was found without a World Seed manifest. The catalog does not inspect its files.
- `cataloged-legacy-unverified` — a supported manifest exists, but it has no generated-file hashes.
- `generated-files-match` — every manifest-listed generated file exists as a regular, non-symlink file and matches its recorded SHA-256 hash.
- `generated-files-drift` — one or more manifest-listed generated files differ from the recorded hashes.
- `missing-generated-files` — at least one manifest-listed generated file is missing or unreadable.
- `unsafe-project-files` — a manifest-listed generated file is a symbolic link.
- `invalid-manifest` — the manifest schema, generated-file list, or hash inventory is invalid.

A hash match verifies only the manifest-listed generated files against the local manifest. It does not establish that the manifest is authentic, that user-added or ignored files are preserved, that Git history or remote records are backed up, or that a project can be reconstructed. The manifest itself is not included in its own hash inventory.

## Privacy and non-interference

The catalog is read-only with respect to scanned projects. It does not initialize Git, create remote repositories, upload anything, inspect credentials, collect arbitrary file names from unmanaged projects, or alter Organs. Keep reports private: even names, paths, and mission statements may be sensitive.

The output can be regenerated and replaces the previous catalog atomically. Review its path before running; do not place it in a public repository.

## Acceptance boundary

This increment is an inventory and integrity signal, **not a backup or restore system**. It does not yet capture changed generated files, user-added files, untracked/ignored data, Git history, or GitHub-only operating records. It does not perform reconstruction. No project is labelled recovery-ready or recovery-verified by this tool.

The seed now contains two experimental recovery paths: [Selective Project Recovery](SELECTIVE_RECOVERY.md) for explicitly named direct-child files and [Manifest-backed Project-tree Recovery](PROJECT_TREE_RECOVERY.md) for explicitly selected top-level roots with recursive capture and isolated restore. CI runs both synthetic CLI drills plus a generated-project round trip that checks manifest preservation and confirms the restored project still catalogs as `generated-files-match`. These checks validate fixture behavior, not complete project or account recovery. Remaining gaps include Git history and working-tree state, GitHub-only records, operator/personal-data continuity, and recovery of the actual designated test subject. Unknown or unsupported state must remain visible rather than silently omitted.
