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

## Designated demolition rehearsal subjects

The real-world acceptance subjects are **Praxis and Renaissance**. Their purpose here is to test the factory and recovery system, not to become active rebuild projects. Rehearse each repository independently; do not treat one successful restore as proof for the other. First inspect the actual local checkout and identify its canonical path from the private machine profile. Do not guess paths or capture the entire filesystem.

For each subject, keep these categories separate in the recovery record:

1. Selected project tree: source, tests, useful docs/assets, and explicitly identified non-secret userdata or local project records.
2. Git history and refs: a separately verified bundle/clone and isolated ref check; record whether staged/index state and uncommitted changes existed and how they were preserved.
3. GitHub-only records: issues, PRs, comments/reviews, releases/assets, Actions metadata/artifacts, discussions, repository settings/rulesets/permissions, and any unsupported or inaccessible categories.
4. External/runtime dependencies: actual requirements and data ownership. Organs is not assumed required; record any concrete dependency evidence and keep runtime databases/configuration separate from project source.
5. Private operator/personal records: capture only from the explicitly authorized private roots and keep separate from public seed/project payloads.

The rehearsal passes only when the restored copy is isolated from the source, every selected file/directory matches its manifest, the Git recovery checks pass for the declared scope, relevant project tests run against the restored copy, omissions and unverified categories are reported, and the source is unchanged. A remote GitHub tree inventory is not a substitute for a local working-tree/userdata capture.

## Relationship to factory bootstrap

The local factory installer has a separate read-only destination preflight for operator/personal-data packages and the Intake Dock. When explicitly configured with an owner, repository name, and exact `OWNER/REPOSITORY` confirmation, it can also create-or-verify that private GitHub repository using the already authenticated personal account. This provisions only an empty remote container; it does not upload user files or configure Codex. Destination preflight checks local conflicts before package materialization. None of these factory steps inventories a project, chooses recovery roots, captures userdata, preserves Git history, or proves a restore. Project-tree capture remains a separate explicitly scoped rehearsal, and its omissions must be reviewed.

## Inclusion and exclusion contract

- Ordinary regular files are included recursively beneath each explicitly named top-level file/directory, including nested source, binary assets, dotfiles, and empty directories. Include roots must be direct children of the project root; select each root deliberately.
- .git directories are explicitly excluded and recorded. Git history, refs, remotes, and working-tree/index state are a separate recovery category; use an independently verified Git bundle/clone rather than treating a filesystem tree as Git history.
- The --exclude option excludes an exact relative path and records it in the manifest. Excluding a directory excludes its contents; the containing directory may remain if it is otherwise present. Top-level paths not selected by --include are recorded as not_captured.
- Symlinks and special files are rejected rather than followed. Credential-like paths (including .env names) are rejected; review file contents too, because filenames cannot establish that a file contains no secret.
- Payload and restore destinations must be new and may not overlap the source/payload. POSIX payload files are owner-only; executable files retain only their executable bit. Ownership, timestamps, ACLs, extended attributes, hard-link relationships, and exact permission modes are not preserved.
- The manifest and its hashes detect accidental or unsophisticated alteration, but are not a cryptographic signature or proof that the original inventory was complete.

## Verification

The unit tests cover nested paths, binary data, empty directories, executable status, explicit selection and omissions, exclusions, symlink/credential-like refusal, manifest traversal, tampering, unexpected payload entries, and no-overwrite behavior. The CLI drill uses a temporary synthetic tree and independently compares SHA-256 hashes. CI success is evidence for these tests only; it is not a live-project recovery test.

CI also runs `scripts/run_generated_project_recovery_drill.py`. It uses the actual World Seed project generator to create a disposable project, adds synthetic nested user-authored text and binary userdata, explicitly captures the generated files and `world-seed-manifest.json`, restores into a separate location, independently compares the complete file/hash inventory, confirms the source did not change, and verifies that the restored project still catalogs as `generated-files-match`.

The project-tree helper itself does not preserve Git history or index state; the drill tests a separate Git bundle restore plus a captured working-tree overlay in a synthetic repository. This proves only the fixture path. It does not export GitHub-only records or preserve private operator/personal data, and it is not a substitute for restoring the actual designated demolition-test subject.

## Still required before acceptance

1. Begin from a clean, trusted World Seed checkout at a recorded commit; the factory PR stack is already merged to main.
2. Review each actual target and define essential userdata, preferences, generated files, and recovery metadata. Do not infer this from a repository keep-list.
3. Separately capture and verify Git history and required GitHub-only records/configuration, with access limitations recorded.
4. Restore each reviewed subject into a separate clean location; compare every manifest entry and report all exclusions and omissions.
5. Run relevant project tests and factory checks against each restored copy.
6. Present evidence and limitations to the human. No deletion or reset until the human separately authorizes it.

This tool does not contact GitHub, upload data, inspect file contents for secrets, preserve Git history, export GitHub operating records, or prove a post-wipe rebuild.
