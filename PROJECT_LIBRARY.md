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

Next increment: see [Selective Project Recovery](SELECTIVE_RECOVERY.md) for a bounded proposal that captures explicitly named direct-child files and restores them into a new destination after hash verification. It does not yet provide a complete project snapshot or prove account-wide recovery. Review, CI, fixture execution, and a clean-environment factory drill remain required. Expand coverage later for live Git repositories, working-tree changes, binary assets, and GitHub-only records. Unknown or unsupported state must remain visible rather than silently omitted.
