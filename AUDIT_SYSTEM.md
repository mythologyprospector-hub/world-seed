# Rolling Audit and Continuous Integrity System

**Status:** Mandatory constitutional operating machinery
**Governs:** Repository health, cross-repository coherence, account-wide integrity, and continuous drift detection.
**Last verified:** 2026-10-19

## Why this exists

A shared template, common service, or successful initial setup does not prove that the resulting ecosystem is coherent. Repositories can diverge, defects can remain hidden between components, workflows can decay, and assumptions can become false. A one-time audit discovers a snapshot; a rolling audit system continually checks whether the whole remains fit for purpose.

**Auditing is a day-one capability, not a cleanup phase reserved for a mature ecosystem.** No repository, template, automation, or shared service is exempt merely because the AI created it or it passed an earlier audit.

## Non-negotiable operating rule

Every bootstrapped ecosystem must establish an account-wide rolling audit loop at genesis. Before broad project construction, define its scope, evidence model, cadence, ownership, findings ledger, remediation path, and recovery procedure. If the account lacks the permissions or automation needed for full coverage, record the gap as a blocking readiness risk and implement the best safe partial coverage possible.

The steward is responsible for the audit program: plan it, operate it, review the evidence, assign remediation, recheck fixes, and report remaining risks. The human should not have to design or manually coordinate this machinery.

## Three mandatory audit scopes

### 1. Repository integrity

Inspect each repository's:
- mission, canonical documentation, ownership, and status;
- default branch, branch protection where visible, uncommitted/local state when accessible, open issues and pull requests;
- required files, links, templates, licenses, security policy, and handoff records as appropriate;
- GitHub Actions workflows, triggers, permissions, secrets references, external dependencies, and failure behavior;
- tests, validation commands, recent runs, failures, releases, and dependency/update signals;
- consistency between claims in documentation and observable implementation/evidence.

### 2. Cross-repository coherence

Inspect the seams between repositories, not only each repository in isolation:
- duplicated or contradictory constitutions, instructions, schemas, templates, and workflows;
- shared services and actual runtime contracts versus client assumptions;
- producer/consumer compatibility, API and event/message contracts, provenance, identity, evidence status, and version expectations where applicable;
- reusable workflow and project-seed versions, inheritance, drift, and local deviations;
- dependencies, ownership boundaries, circular responsibilities, hidden manual steps, and missing integration tests;
- account-wide requirements that no individual repository can prove on its own.

A shared template or shared service is a dependency to verify, not proof of conformity. Track the version or commit each consumer uses where practical. Validate the actual installed service and its interfaces; do not infer runtime health from repository documentation.

### 3. Account and ecosystem integrity

Inspect:
- the complete accessible repository inventory, visibility, purpose, ownership, and lifecycle state;
- whether every repository has a clear mission, responsible steward, canonical documents, and place in the portfolio map;
- whether account-level rules are applied consistently and exceptions are documented;
- account-wide workflows, organization/repository permissions, token scope, branch protections, security settings, and automation coverage where access permits;
- orphaned repositories, duplicate roles, undocumented dependencies, dead workflows, open high-risk findings, and repositories missing from audit coverage;
- ecosystem readiness, recovery capability, independent backups, and whether a fresh builder can reconstruct the operating model.

Clearly distinguish “all repositories accessible to this identity” from “the entire account.” Permissions, pagination, API limits, private resources, and disconnected machines can create blind spots. Never label a partial inventory complete.

## Rolling cycle

Run the following cycle from the first bootstrap onward:

1. **Discover:** enumerate repositories, workflows, shared services, and their current refs/versions.
2. **Collect evidence:** inspect configuration and canonical files; retrieve test and workflow results; run safe, bounded checks where authorized.
3. **Compare:** evaluate findings against the constitution, project canon, cross-repository contracts, and prior audit baseline.
4. **Classify:** record severity, confidence, affected assets, impact, evidence, and whether the finding is confirmed, suspected, or blocked by missing access.
5. **Prioritize:** choose work by risk and mission impact, not by convenience or which repository is easiest.
6. **Remediate:** open focused issues/PRs or make authorized reversible fixes. Preserve existing work and respect approval gates.
7. **Verify:** rerun the specific check and relevant regression/integration checks; link evidence to the finding.
8. **Reassess:** update the ecosystem risk picture, coverage gaps, next audit window, and durable handoff. New defects can reopen old assumptions.

Audit and remediation are separate states. A finding is not closed because a fix was proposed, a PR was opened, or a test passed unrelated to the defect.

## Cadence and triggers

Use multiple triggers because no single schedule catches every class of failure:

- **On change:** validate affected repository documents, workflows, tests, and declared contracts on pull requests and relevant pushes.
- **Scheduled:** run recurring repository and account inventory/audit passes even when no one has recently changed code.
- **After a consequential event:** audit after seed/template changes, shared-service changes, permission changes, broad automation changes, migrations, releases, or recovery.
- **Rolling deep review:** rotate through the full repository portfolio and cross-repository seams so the entire accessible ecosystem receives substantive coverage over a declared window.
- **On incident or evidence of drift:** run a targeted investigation immediately and determine whether the finding implies a wider systemic defect.

Set the exact cadence from risk, account size, API limits, and available resources. Record the chosen schedule and justify any uncovered interval. “Scheduled workflow exists” is not evidence that a scheduled run succeeded.

## Findings ledger and audit record

Every meaningful audit pass must leave a durable, queryable record in the canonical ecosystem repository or designated audit store. At minimum record:

- audit ID, timestamp, auditor/builder identity, scope, and completeness;
- account/repository inventory source and relevant branch/commit refs;
- checks run, tools/versions where relevant, and evidence links;
- repositories, workflows, contracts, and services actually inspected;
- findings with unique IDs, severity, confidence, impact, owner/steward, status, and remediation link;
- access gaps, excluded resources, API limits, untested paths, and assumptions;
- comparison with the previous baseline, including new, resolved, recurring, and reopened findings;
- next actions, due/next review window, and verification evidence.

Do not dump secrets or sensitive private-repository content into public audit records. Public reports must not reveal private project names, contents, endpoints, or security weaknesses. Use access-controlled storage for sensitive evidence and publish only appropriately redacted summaries.

Recommended finding states: `observed`, `triaged`, `accepted-risk`, `planned`, `in-progress`, `fixed-unverified`, `verified-resolved`, `blocked`, and `reopened`. Accepted risk requires a recorded rationale, owner, and review point; it is not the same as resolved.

## Severity and response

Use the target project's existing severity vocabulary where one exists. Otherwise define a consistent account-level scale before the first audit. At minimum distinguish:
- **Critical:** active compromise, destructive automation, serious data exposure, or systemic failure threatening the mission or recoverability.
- **High:** material security, correctness, integrity, or cross-repository failure with substantial impact.
- **Medium:** meaningful defect, drift, missing contract, or recurring operational risk.
- **Low:** limited-impact inconsistency, maintenance debt, or documentation gap.

Severity must be evidence-based. Prioritize critical/high risks promptly; do not hide them inside a long list of cosmetic issues. If an immediate fix would cross an approval gate, contain what is safely authorized and escalate with a clear recommendation.

## Automation architecture

Use GitHub Actions and other automation as evidence collectors and guardrails, not as a substitute for judgment.

At genesis, establish:
- a local pull-request validation workflow appropriate to the seed's actual files;
- an account-audit workflow or reusable template with manual dispatch and a declared schedule;
- an explicit inventory of target repositories and the credential/permission model required to inspect them;
- a durable findings destination and run-to-finding links;
- least-privilege permissions, bounded scope, rate-limit handling, pagination, timeouts, and clear partial-failure reporting;
- a path for human review of consequential changes and for the AI steward to own follow-through.

A workflow's default token usually cannot inspect arbitrary private repositories across an account. Cross-repository auditing may require an explicitly configured GitHub App or narrowly scoped token with access to each target repository. Do not assume such access exists, embed credentials, or silently broaden permissions. Until configured, report cross-repository coverage as blocked/partial and still perform the accessible checks.

Prefer read-only inventory and evidence collection by default. Audit automation must not automatically merge PRs, delete/move repositories, change permissions, rotate credentials, or perform destructive remediation. Open a finding or reviewable PR instead.

## Independence and anti-self-certification

- The system must report failures in its own workflows and missing audit runs.
- Keep a visible list of repositories that have never been audited or are overdue.
- Verify the audit process with fixtures or a test account where practical.
- Periodically review whether the checks themselves miss known classes of defects.
- Do not allow the same unverified assertion to serve as both implementation and proof.
- A green check means only that its declared checks passed on the declared scope and ref.

## Bootstrap acceptance gate

The ecosystem is not considered operationally bootstrapped until:
1. repository and account audit scope is defined;
2. an initial inventory and baseline pass has been recorded;
3. coverage and permission gaps are explicit;
4. a recurring schedule or documented external cadence is configured;
5. findings have a durable home and a remediation/verification lifecycle;
6. cross-repository seams and shared-service dependencies are represented;
7. at least one safe test demonstrates that the audit machinery detects a known fixture or reports its own inability to run;
8. a fresh AI steward can find the latest audit, identify overdue coverage, and continue the loop without prior chat context.

If any condition is unmet, label the ecosystem **not yet audit-ready** and make closing the gap a top-level work item.

## Guiding test

The question is not “Did every repository start from the same template?” It is: **“What evidence shows that the ecosystem still works as a coherent whole today, where are the blind spots, and what happens when it does not?”**


## Mandatory consistency and maintainability audit

Every rolling audit must apply [CONSISTENCY_STANDARD.md](CONSISTENCY_STANDARD.md) at repository, cross-repository, and account scope. Evaluate documentation presentation and accuracy, code comments/docstrings, naming, repository layout, process naming, quality-tool configuration, and alignment between declared conventions and actual practice. Distinguish mechanical checks from semantic review; report unverified areas honestly. Track justified exceptions and prioritize risks and operational friction over cosmetic churn. A newly created repository inherits the standard from day one.


## Implementation status and honest readiness

The initial executable baseline now consists of a repository-local structural validator, unit tests, and a read-only GitHub Actions workflow with pull-request, push, manual, and weekly scheduled triggers. This gives world-seed an initial self-check; it does not yet implement the full audit loop specified above.

Still required before claiming account-wide audit readiness:

- authenticated, paginated discovery of the target account's accessible repositories, with explicit distinction between complete and partial coverage;
- a safe permission model for private repositories and sensitive evidence;
- repository, cross-repository, and account-level checks beyond this seed's required-file/link baseline;
- a durable findings ledger with lifecycle and remediation verification;
- scheduled/manual audit runs that preserve evidence without exposing private project details in public logs or artifacts;
- fixture tests, confirmed workflow-run evidence, and a fresh-builder/bootstrap recovery drill.

Until those conditions are demonstrated, report readiness as **NOT VERIFIED** and coverage as **repository-local only** for this implementation. Missing credentials, inaccessible repositories, failed or overdue runs, and unavailable evidence must remain visible blockers rather than being interpreted as a clean audit.


## Read-only inventory collector

`scripts/audit_account_inventory.py` is an initial authenticated inventory utility. It uses GitHub API GET requests, paginates the repositories visible to the authenticated identity, optionally filters by repository owner, and writes a JSON report to a path explicitly selected by the operator. It does not modify GitHub.

The report contains repository names and may contain private metadata. Store it only in an approved, access-controlled location outside the public seed repository. The utility deliberately reports `partial-unverified` coverage and does not claim to prove account completeness. It is not the full audit engine: it does not inspect repository contents, workflows, branch protections, cross-repository seams, or remediation state.


## Canonical finding record

Use [schemas/audit-finding.schema.json](schemas/audit-finding.schema.json) as the portable record contract and [templates/audit-finding.template.json](templates/audit-finding.template.json) as the starter record. Every finding needs a stable ID, scope, severity, confidence, lifecycle state, affected assets, impact, evidence, owner, timestamps, remediation, and verification state.

The schema encodes important lifecycle invariants: `verified-resolved` requires positive verification and evidence; `accepted-risk` requires a rationale and review date. The dependency-free `scripts/validate_audit_findings.py` checks core required fields and lifecycle invariants, and the CI workflow validates the template. It does not implement every JSON Schema keyword, and a durable queryable findings store remains unimplemented. Store sensitive findings only in appropriately access-controlled locations.
