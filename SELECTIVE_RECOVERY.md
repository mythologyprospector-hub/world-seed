# Selective Project Recovery — v1 proposal

**Status:** Experimental recovery increment; not yet accepted as a complete recovery system.
**Purpose:** Prove that an explicitly chosen set of regular files can be privately captured, verified, and restored into a new isolated destination.
**Scope:** Direct-child files only. This does not back up a whole project, Git history, working tree, ignored files, repository configuration, issues, pull requests, releases, or other GitHub records.

## Capture

Choose each file deliberately. The output must be a new directory outside the source:

```bash
uv run --no-project scripts/selective_recovery.py capture \
  --source "$HOME/projects/your-disposable-project" \
  --output "$HOME/private-recovery/payloads/your-disposable-project-001" \
  --include README.md \
  --include MISSION.md
```

Replace the example paths and include only files you have reviewed. Repeat `--include` for each required direct-child filename. The command does not recurse and does not infer that omitted files are unimportant. It refuses hidden files, manifest files, likely credential-bearing names, symlinks, missing files, duplicate names, and existing output directories.

Payload files and the inventory are written with owner-only permissions on POSIX systems. The inventory records each selected file's size and SHA-256 digest. Keep payloads private: user-authored text may itself be sensitive.

## Restore and verify

Restore only into a destination that does not already exist:

```bash
uv run --no-project scripts/selective_recovery.py restore \
  --payload "$HOME/private-recovery/payloads/your-disposable-project-001" \
  --destination "$HOME/private-recovery/restore-tests/your-disposable-project-001"
```

The tool checks the payload inventory, rejects unexpected or missing payload entries, verifies hashes before copying, stages the restore in a new sibling directory, verifies restored bytes, then publishes the result at the new destination. It never overwrites an existing destination. Review the output before using it.

## Disposable end-to-end drill

The factory's CLI drill creates synthetic text and binary files in a temporary directory, invokes the actual capture and restore commands, independently compares restored bytes and SHA-256 hashes, confirms unselected data stays out, and verifies the source fixture is unchanged. It never reads a real project or contacts the network.

Run it from a trusted checkout:

```bash
uv run --no-project scripts/run_selective_recovery_drill.py
```

A successful run prints `SELECTIVE_RECOVERY_CLI_DRILL=PASSED`. CI runs the same drill. This is a useful local CLI acceptance step, but still only validates a synthetic fixture; it is not whole-project or account recovery.

## Safety and acceptance limits

- No network access, upload, credential-file access, GitHub mutation, or Organs changes.
- No recursive walk of project files; only named direct-child regular files are captured.
- A payload is not a snapshot of the whole project. The project manifest is deliberately excluded and is not recreated by restore.
- File names that look credential-related are refused as a basic guardrail, not as a guarantee that file contents contain no secrets. Review every selected file before capture.
- A source revision copied from the project manifest is informational metadata, not proof that the source tree was clean or that a commit contains the captured content.
- A passing fixture test is not proof that the installer works on Bucky or that account-wide recovery works.

Acceptance still requires review, CI, execution against a disposable fixture, capture, restore into a separate empty location, and independent comparison of restored bytes. Further gates must address whole-tree and binary assets, Git history and working-tree state, GitHub-only operating records, machine-specific private data, and a clean-environment factory drill. Until those gates pass, do not call live projects recovery-ready or begin the larger reset.
