# Recovery State Contract

**Status:** Contract, initial versioned JSON Schema, cautious template, and capsule integration are present on `feat/durable-terminal-journal`. The focused local suite and both relevant GitHub Actions workflows passed on commit `ecf795e49704599cd67065999de2d2598283dd69`. Automatic state generation/integration, retrieval service, and remote transfer are not implemented.

## Purpose

Give a future Digital Djinn enough trustworthy context to resume project work without asking the human to reconstruct the whole history. This is a compact, maintained map of the project—not a replacement for source files, canonical documents, terminal evidence, Git history, or human approval.

The recovery package has two distinct kinds of information:

1. **Project state:** deliberately maintained interpretation of what matters, what has been decided, what is unresolved, and what to do next.
2. **Evidence:** records that can be checked independently, such as Git commit IDs, test output, workflow runs, and terminal-journal events.

Never silently turn a claim in project state into verified fact. Link claims to evidence where possible and label unverified claims.

## Design rules

- **Recover, don't pretend to remember.** A new conversation must be able to retrieve the package through an explicit, documented path. A file existing somewhere does not mean the assistant can access it automatically.
- **Canon beats recollection.** Link to authoritative project documents and source files. If a summary conflicts with canon or current repository state, report the conflict and do not silently choose.
- **Evidence beats assertion.** Record exact commit SHA, command, result, and evidence location. Distinguish local test output from GitHub Actions results. Never infer a passing test from a commit message or a missing error.
- **Separate fact from interpretation.** Terminal logs record events; the state document explains their project significance. Neither should rewrite the other.
- **Unknown is a valid value.** Use `unknown`, `not_checked`, or `not_applicable` as appropriate. Do not invent dates, outcomes, decisions, permissions, or destinations.
- **Human authorization remains authoritative.** Prior agreement applies only to the specific decision and action agreed. Silence is not approval. A recovered note cannot authorize destructive changes, merges, permission changes, secret disclosure, or external data transfer.
- **Keep it concise and navigable.** Store the current working brief here; preserve detailed history in linked artifacts and version control.
- **Make staleness visible.** Every generated or maintained snapshot records when it was updated and which repository commit/state it describes. A mismatch with the current checkout must be shown, not hidden.
- **Preserve provenance.** Each important entry should identify its author/source and evidence link or say that no independent evidence is available.
- **Minimize sensitive data.** Never include secrets, tokens, private keys, credential values, or the contents of secret files. Avoid unnecessary personal data, absolute local paths, and raw terminal output in shareable state.

## Required sections for a future project-state record

The initial machine-readable format is JSON, governed by [`schemas/recovery-project-state.schema.json`](schemas/recovery-project-state.schema.json), with a deliberately unverified starter at [`templates/recovery-project-state.template.json`](templates/recovery-project-state.template.json). The template is not a populated project record and must not be treated as project truth. Future versions must preserve these semantic fields or explicitly migrate them.

### 1. Record identity and freshness

- Contract/schema version.
- Project/repository identity and canonical repository URL.
- State record revision or identifier.
- Updated-at timestamp in UTC, plus source/provenance.
- Repository commit SHA the record describes, if known.
- Freshness status: `current`, `possibly_stale`, or `unknown`.
- Any unresolved mismatch between the record and observed repository state.

### 2. Project identity and canon

- One-paragraph purpose and scope.
- Links to authoritative documents, ordered by authority.
- Non-negotiable project rules and safety boundaries.
- Relevant paths or symbols, with links where possible.
- Explicitly named documents that are background/reference only and must not be treated as current canon.

### 3. Verified checkpoint

For each verification claim, record:

- Exact commit SHA tested or inspected.
- Exact command or workflow name.
- Result: `pass`, `fail`, `not_run`, or `unknown`.
- Timestamp, where known.
- Evidence link or reference to captured output.
- Scope and limitations of that verification.

A result applies only to the exact commit and scope recorded. If the current head differs, say so. Keep local test evidence distinct from hosted CI evidence.

### 4. Decisions and constraints

Maintain separate lists for:

- **Accepted:** explicit decisions, who/what authorized them, and any scope limits.
- **Rejected:** options explicitly declined and the reason, if known.
- **Open:** questions or choices not yet decided.
- **Superseded:** prior decisions replaced by a newer explicit decision, with a link to the replacement.

Do not promote a suggestion, assistant recommendation, tentative plan, or inferred preference to an accepted decision.

### 5. Current work and risks

- Completed work, linked to evidence.
- Work in progress and its exact location/branch.
- Known failures, blockers, and unresolved risks.
- Local modifications or worktrees that must not be disturbed, when known and relevant.
- External dependencies or permissions that are missing.
- Explicit non-goals and deferred work.

### 6. Next safe action

- One precise next action.
- Why it is the next action.
- Preconditions and expected observable result.
- Whether it is safe to do without further authorization.
- Any required human decision before proceeding.

Prefer a small reversible step. If the next action is consequential or authorization is unclear, the next action is to ask the human—not to execute it.

### 7. Retrieval and recovery instructions

- Where the authoritative state record and evidence are stored.
- How a fresh assistant/operator retrieves them.
- How to verify repository identity, branch, and commit before acting.
- What to do when retrieval fails, evidence is stale, or records conflict.
- Which information is deliberately absent and where it may safely be obtained.

## Recovery procedure

A future recovery workflow should do the following in order:

1. Retrieve the state record and report whether retrieval actually succeeded.
2. Verify repository identity and inspect current branch/head before proposing repository changes.
3. Compare observed state with the record's recorded commit and freshness.
4. Read linked canon and relevant current files; do not rely on the summary alone when details matter.
5. Check the exact evidence behind critical claims, especially test/CI status and whether work is merged.
6. Present conflicts, stale claims, missing evidence, and unknowns explicitly.
7. Rebuild a short working brief with: purpose, governing rules, verified checkpoint, accepted decisions, open questions, risks, and one safe next action.
8. Continue only within existing authorization. Ask before new consequential actions.

If the package is unavailable, do not claim to have recovered it. State what is missing and use only independently accessible evidence to rebuild a provisional brief.

## Relationship to the terminal journal and recovery capsule

- The terminal journal is an event ledger for commands explicitly run through its wrapper.
- The metadata-only recovery capsule is an index of selected journal session metadata; it excludes raw command/output text and does not independently validate journal claims.
- This project-state record is the maintained map of canon, decisions, verified checkpoints, risks, and next action.
- A future recovery package may reference all three, but must preserve their distinct roles and provenance.

None of these, by itself, is a retrieval bridge. Encryption, key management, capability-token design, a service that can retrieve/decrypt authorized records, remote destination selection, upload, and transfer authorization are separate future design decisions. This contract does not authorize or implement them.

## Acceptance criteria for a future implementation

The implementation is not complete until it can demonstrate that:

- A fresh session can locate and retrieve the record using documented steps, without relying on hidden conversation context.
- Schema/version is explicit and invalid or unsupported versions are handled visibly.
- Unknown, missing, stale, and conflicting data are surfaced rather than guessed.
- Canon, claims, and evidence are linked and their different authority levels are preserved.
- Verification claims are bound to exact commit IDs and evidence.
- The recovery brief includes accepted decisions, open questions, risks, and one safe next action.
- Secrets and raw output are not included by default.
- No network transfer or remote write occurs without a separately selected destination and explicit authorization.
- Tests cover missing/corrupt/stale records, repository mismatch, conflicting evidence, and authorization boundaries.
- The exact implementation commit passes local tests and relevant hosted checks.

## Current implementation status

As of commit `ecf795e49704599cd67065999de2d2598283dd69`, the terminal journal, metadata-only capsule generator, project-state schema, starter template, and standard-library contract tests exist on the feature branch. The focused local suite passed 21/21 tests, and both the Terminal Journal Tests and World Seed quality checks workflows passed on that exact commit. The template is intentionally not populated with inferred project facts. Automatic state generation/integration, retrieval across fresh conversations, encryption, and the retrieval bridge remain future work.