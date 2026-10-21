# Manifest-backed project-tree recovery — experimental

**Status:** Experimental implementation; not yet accepted as the complete recovery system.

## What this increment does

The script at scripts/project_tree_recovery.py recursively captures only explicitly selected top-level files and directories into a new payload and restores it to a new isolated destination. This is deliberate: a capture cannot silently mean “copy everything.” The manifest records top-level entries that were not selected as well as explicit exclusions. The payload manifest records relative paths, file sizes, SHA-256 hashes, executable-bit status, directory paths (including empty directories), and explicit exclusions. Restore validates the manifest, checks that the payload contains exactly the declared paths, verifies payload hashes, stages the restore, independently verifies restored bytes, and refuses to overwrite an existing destination.

Run from a trusted checkout:

    python scripts/project_tree_recovery.py capture \
      --source "$HOME/projects/REVIEWED-PROJECT" \
      --output "$HOME/private-recovery/payloads/REVIEWED-PROJECT-tree-001" \
      --include README.md \
      --include src \
      --include tests
    python scripts/project_tree_recovery.py restore \
      --payload "$HOME/private-recovery/payloads/REVIEWED-PROJECT-tree-001" \
      --destination "$HOME/private-recovery/restore-tests/REVIEWED-PROJECT-tree-001"

Replace example paths only after reviewing the target and storage permissions. Do not run this against a real subject until the target and preservation scope have been explicitly identified. Review the full inventory and exclusions before relying on a payload.

## Inclusion and exclusion contract

- Ordinary regular files are included recursively beneath each explicitly named top-level file/directory, including nested source, binary assets, dotfiles, and empty directories. Include roots must be direct children of the project root; select each root deliberately.
- .git directories are explicitly excluded and recorded. Git history, refs, remotes, and working-tree/index state are a separate recovery category; use an independently verified Git bundle/clone rather than treating a filesystem tree as Git history.
- The --exclude option excludes an exact relative path and records it in the manifest. Excluding a directory excludes its contents; the containing directory may remain if it is otherwise present. Top-level paths not selected by --include are recorded as not_captured.
- Symlinks and special files are rejected rather than followed. Credential-like paths (including .env names) are rejected; review file contents too, because filenames cannot establish that a file contains no secret.
- Payload and restore destinations must be new and may not overlap the source/payload. POSIX payload files are owner-only; executable files retain only their executable bit. Ownership, timestamps, ACLs, extended attributes, hard-link relationships, and exact permission modes are not preserved.
- The manifest and its hashes detect accidental or unsophisticated alteration, but are not a cryptographic signature or proof that the original inventory was complete.

## Verification

The unit tests cover nested paths, binary data, empty directories, executable status, explicit selection and omissions, exclusions, symlink/credential-like refusal, manifest traversal, tampering, unexpected payload entries, and no-overwrite behavior. The CLI drill uses a temporary synthetic tree and independently compares SHA-256 hashes. CI success is evidence for these tests only; it is not a live-project recovery test.

## Still required before acceptance

1. Reconcile the stacked factory branches against current main without blind merges.
2. Review the actual target project and define what counts as essential userdata, preferences, generated files, and recovery metadata. Do not infer this from a repository keep-list.
3. Separately capture and verify Git history and required GitHub-only records/configuration, with access limitations recorded.
4. Restore the actual reviewed subject into a separate clean location; compare every manifest entry and report all exclusions and omissions.
5. Run project-specific tests and factory checks against the restored copy.
6. Present evidence and limitations to the human. No deletion or reset until the human separately authorizes it.

This tool does not contact GitHub, upload data, inspect file contents for secrets, preserve Git history, export GitHub operating records, or prove a post-wipe rebuild.
