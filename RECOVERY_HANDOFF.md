# Recovery Session Handoff

**Checkpoint date:** 2026-10-21  
**Purpose:** Resume the World Seed recovery-and-retirement work without requiring the operator to reconstruct prior chat or terminal scrollback.

> Start here when continuing this mission. Read this file, check the linked recovery issue, verify live GitHub state, then resume from the next safe step. This is a checkpoint, not proof that any repository is ready for deletion.

## Mission

Use World Seed's factory and recovery machinery to learn what each legacy project uniquely contains, preserve essentials, restore each subject into an isolated clean location, verify the restored material, and only then ask the human for explicit authorization before retiring or deleting any repository.

The target is **selective, useful recovery**, not a full-device image or indiscriminate archive. Preserve valuable source, tests, project data, personal records, relevant preferences, metadata, Git history, and GitHub-only records as applicable. Keep public seed machinery generic; keep operator profile and personal data separate and private.

## Safety and operating rules

- No repository deletion, destructive cleanup, reset, or removal of worktrees without explicit authorization.
- A successful Git bundle is not proof that the worktree, ignored files, GitHub discussions, reviews, releases, settings, or other remote records are preserved.
- Do not copy private/personal material into this public repository. Do not print or paste private document contents into chat or public logs.
- Do not assume connector access grants permission to unrelated repositories.
- Separate **verified**, **reported**, **intended**, and **unknown** states. Never claim a test, restore, Action, or upload passed unless evidence confirms it.
- The operator is the human gate and final approver. Ask before consequential new decisions.
- The operator uses `.` to mean proceed with the specific action already under discussion; silence is not approval.
- Rule #1: if you're not having fun, you're doing it wrong.

## Verified preservation checkpoint

The operator created and verified two sets of Git bundles for seven local retirement candidates:

1. **Original local bundles** preserve refs/history present in the original local checkouts at bundle time.
2. **Fresh GitHub mirror bundles** were built from new mirror clones of each configured origin, then verified with `git bundle verify`. The terminal output confirmed successful mirror clone, bundle creation, and verification for all seven repositories.

The fresh mirrors address missing or stale remote-tracking refs in the original checkouts. Example counts observed: the live `world` mirror bundle had 58 refs and the live `episteme` mirror bundle had 120 refs. Exact local bundle files and branch-audit reports are on the operator's machine under:

`~/retirement-preservation-2026-10-21/`

Subdirectories include `git-bundles/`, `github-bundles/`, `remote-mirrors/`, `branch-audit/`, and `out-of-git/`.

**Important limitations:** Git bundles preserve Git objects reachable from included refs; they do not by themselves preserve working-tree changes, ignored/untracked files, reflogs, GitHub-only discussions/reviews/issues/settings/releases, or guarantee that external LFS/submodule content is present. Verify each relevant category separately.

Two known out-of-Git files were copied into the local `out-of-git/` directory with mode `600`; each source and copy had matching SHA-256 output. One is an Episteme dependency lockfile; the other is a private incoming personal-profile document. Their contents and identifying personal details intentionally do not appear here. Originals were left untouched.

## Local checkout / worktree findings

A read-only worktree inventory found one checkout each for the six other local candidate repositories, and three Episteme worktrees:

- Episteme main checkout at `~/projects/episteme`, commit `414709b`.
- Episteme PR #43 test worktree at `~/projects/.worktrees/episteme/episteme-pr43-test`, detached HEAD `bd58c07`.
- Episteme PR #59 test worktree at `~/projects/.worktrees/episteme/episteme-pr59-test`, detached HEAD `4dbc710`.

A read-only `git status --short --untracked-files=all` check showed `?? uv.lock` in the Episteme main checkout and no tracked/untracked output in either test worktree. The lockfile was separately copied and hash-verified. A subsequent ignored-path summary found these top-level counts: main checkout — `.pytest_cache` 5, `scripts` 2, `src` 70, `tests` 91, `.venv` 647; each detached test worktree — `src` 25. These were counts of ignored paths grouped by top-level path, not a content review. A follow-up `git check-ignore -v --no-index` report resolved all 815 ignored entries to ordinary project rules: `.venv/` (647), `__pycache__/` (157), `*.egg-info/` (6), and `.pytest_cache/` (5). The apparent `src`, `tests`, and `scripts` top-level groups were paths nested under these ignored directories, not evidence of 187 ignored source files. The full path/rule report is stored privately at `~/retirement-preservation-2026-10-21/local-state/episteme-ignored-rules.txt`. No ignored caches have been copied or removed. The two detached worktrees still need their own ignored-path and local-state review. Do not remove or reset the detached test worktrees.

The local branch audit showed multiple GitHub branches absent from original local remote-tracking caches and several differing branch tips. Fresh GitHub mirrors/bundles have since been created and verified; do not treat that as completion of the wider GitHub-record inventory.

The attempt to run a large shell block for all local status inventories was interrupted because the paste broke across lines. Do not repeat a large multi-line paste blindly. Use short, manageable commands or a script file, and preserve the user's prompt if a command is accidentally left incomplete (Ctrl+C cancels the unfinished shell input).

## Not yet done

- [ ] Inspect local-only and ignored files for all seven subjects, including the two Episteme detached worktrees; preserve selected essentials without copying caches indiscriminately.
- [ ] Confirm the contents and integrity of the local preservation directory and record a private inventory without publishing private paths or personal details.
- [ ] Check relevant Git LFS objects, submodules, tags, and any refs not covered by the bundle verification as applicable.
- [ ] Inventory GitHub-only records for each candidate: issues, PRs and review threads, discussions, releases/tags, Actions artifacts/logs, wikis, project boards, repo settings, collaborators, secrets/variables names where appropriate, and other project metadata. Record what is actually available; do not expose secret values.
- [ ] Restore each subject into an isolated clean destination using World Seed recovery tooling, compare hashes/metadata, and run relevant checks.
- [ ] Report a per-subject recovery verdict and unresolved gaps.
- [ ] Ask the human for explicit authorization before any deletion or destructive retirement step.

## Current next safe step

Continue with a **small, read-only inventory of local-only/ignored files**, starting with Episteme's two detached test worktrees and then the other candidate checkouts. Capture paths/status privately; do not display private document contents. Keep the existing bundles and worktrees untouched.

Then continue the GitHub-only record inventory. The overall recovery issue is [World Seed issue #12](https://github.com/mythologyprospector-hub/world-seed/issues/12); use it as the central progress thread and link this handoff from there.

## Related factory context

World Seed's recovery/factory stack was previously merged through PR #27, and the reported protected-branch Action run showed 193 unit tests passing, both synthetic recovery drills passing, and 112 required-file/Markdown-link checks. This verifies synthetic checks, **not recovery of the real retirement candidates**.

Project Seed absorption audit PR #28 has since been verified merged at `64a5b290e52d396682eb9611067ba9f9aa0adf5e`. Its merged audit still does not clear Project Seed for retirement: full semantic review, sync-dependency review, and the separate real recovery gates remain open. The handoff PR #32 was merged at `bf2f8efffce8cdc4c842a14d7d5e12bbeb1ef3cd`; its PR-head quality workflow completed successfully before merge, while a separate workflow run for the merge commit had not yet appeared at the last check.

## Resume protocol for the next assistant

1. Read this file and issue #12 before asking the operator to repeat context.
2. Verify current GitHub main/PR/Actions state directly; this checkpoint can become stale.
3. Ask the operator for one short command/output at a time when terminal work is required.
4. Prefer read-only inspection first. Keep personal files and private-repository details out of public notes.
5. Update this handoff and issue #12 as meaningful milestones are verified.
6. Never describe a repository as retirement-ready until isolated restore and verification are complete and all significant preservation gaps are disclosed.
