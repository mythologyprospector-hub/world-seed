# world-seed

**Portable genesis for AI-led project ecosystems, with a real operator profile.**

world-seed preserves the reusable operating system for starting and governing a whole GitHub account: the constitution, AI leadership mandate, human approval boundaries, repository architecture, onboarding, automation standards, machine profile, and recovery procedure.

It is deliberately **mission-portable and operator-aware**:
- The core works with any GitHub account, mission, repository set, and capable AI builder.
- The included Jimmy profile records the known local environment and working preferences without pretending those facts apply to other operators.
- Account-specific mission, inventory, credentials, and current state are discovered at bootstrap; they are not guessed from this seed.

## Start here

1. Give the AI builder the repository URL and the instructions in [ONBOARDING_PROMPT.md](ONBOARDING_PROMPT.md).
2. The builder reads [AGENTS.md](AGENTS.md), [CONSTITUTION.md](CONSTITUTION.md), [HUMAN.md](HUMAN.md), and [BOOTSTRAP.md](BOOTSTRAP.md).
3. It inspects the target account and environment before changing anything.
4. It prepares an evidence-backed plan and proceeds within the authority already granted, stopping only at real approval gates.
5. It leaves durable records and verifies what it actually did.

## Contents

- [AGENTS.md](AGENTS.md) — entry-point instructions for any AI builder.
- [CONSTITUTION.md](CONSTITUTION.md) — governance, leadership, Rule #1, Rule #2, authority, and safeguards.
- [HUMAN.md](HUMAN.md) — the intended working relationship and communication style.
- [BOOTSTRAP.md](BOOTSTRAP.md) — account-level discovery and genesis sequence.
- [REPOSITORY_MODEL.md](REPOSITORY_MODEL.md) — ecosystem vs project responsibilities and the role of lower-level seeds.
- [AUTOMATION.md](AUTOMATION.md) — workflow and automation requirements.
- [AUDIT_SYSTEM.md](AUDIT_SYSTEM.md) — mandatory rolling repository, cross-repository, and account-wide audits.
- [CONSISTENCY_STANDARD.md](CONSISTENCY_STANDARD.md) — shared editorial, code-commenting, naming, repository-layout, process, and quality standards.
- [MACHINE_PROFILE.md](MACHINE_PROFILE.md) — how to discover an environment and the known Jimmy profile.
- [BASH_PROMPT.md](BASH_PROMPT.md) — the local prompt's role, limits, and safe integration into the operator workflow.
- [RECOVERY.md](RECOVERY.md) — independent backup and reconstruction requirements.
- [ONBOARDING_PROMPT.md](ONBOARDING_PROMPT.md) — reusable prompt for a fresh chat or builder.
- [profiles/ACCOUNT_PROFILE.template.md](profiles/ACCOUNT_PROFILE.template.md) — template for a different operator/account.

## Mission boundaries and license

The seed's canonical constitution prohibits dystopian, Orwellian, apocalyptic, inhumane, exploitative, greedy, deceptive, underhanded, devious, nefarious, or otherwise unethical purposes and methods. It requires respect for human dignity, autonomy, privacy, licenses, EULAs, and applicable boundaries; it rejects pay-to-enter access and requires the MIT License for applicable project-owned material. See [CONSTITUTION.md](CONSTITUTION.md).

This repository is distributed under the [MIT License](LICENSE). A repository's MIT license does not relicense third-party material or override third-party licenses, terms, privacy rights, trademarks, or other obligations. Check compatibility and required notices rather than assuming everything in a repository can be relicensed.

## Important boundaries

This repository is a bootstrap source, not proof that a target account has been configured or recovered. Reading it is not execution. A file existing is not evidence that a workflow runs. Every bootstrap must report completed, verified, blocked, and unverified items separately.

Never store credentials, tokens, private keys, recovery codes, or other secrets here. Keep the seed independently backed up from the account it is meant to recover.

## Evolution

When a reusable rule changes, update its canonical document here and record the rationale. Do not silently let temporary chat context become policy. Keep operator-specific details in the profile, not in the universal constitution.


### Local backup coverage inventory

After creating a handoff backup, generate a private coverage report outside the backup directory:

```bash
python scripts/audit_backup_coverage.py \
  --backup-dir "$HOME/archive/PATH-TO-BACKUP" \
  --output "$HOME/archive/backup-coverage.json"
```

This report inventories visible evidence for source/history and optional GitHub operating-record exports. It deliberately leaves settings/permissions, binary artifacts, release assets, and isolated recovery unverified unless a future evidence collector covers them. A coverage report is not a restore test, and its overall status remains `incomplete-unverified` until the separate gaps are closed.

## Local quality gate

Run the dependency-free baseline checks and unit tests from the repository root:

```bash
python scripts/validate_seed.py
python -m unittest discover -s tests -v
```

GitHub Actions runs these checks on pull requests and pushes, supports manual execution, and schedules a weekly repository-local check. This is the first executable quality gate—not the complete account-wide audit. It checks required seed documents and obvious broken relative Markdown links. It does not prove semantic consistency, private-repository coverage, security posture, runtime health, or recovery readiness.


## GitHub governance safeguards

During bootstrap, inspect branch protection and rulesets for each default branch, including repository and organization-level policies where the available identity permits. Record endpoint access failures as unverified coverage, not as proof that protection is absent. Prepare a tailored, evidence-backed protection plan for uncovered repositories. Because changing security settings is consequential, apply it only after explicit human approval, then re-read the settings and verify the effective policy. See [AUTOMATION.md](AUTOMATION.md) and [BOOTSTRAP.md](BOOTSTRAP.md).


## Read-only account inventory

### Repository layout inspection

For one repository, the optional metadata-only inspector records root entry names and signals such as README, builder instructions, tests, and workflow files:

```bash
python scripts/inspect_repository_layout.py --repo OWNER/REPOSITORY --output /secure/private/path/repository-layout.json
```

Set `GH_TOKEN` or `GITHUB_TOKEN` in the environment. The report may reveal private repository names and structure, so keep it outside public repositories in access-controlled storage. This is a review aid, not a pass/fail policy: expected files vary by project purpose, and the inspector does not read file contents or verify branch protections, secrets, actual workflow runs, or cross-repository contracts.


For an operator with a GitHub token already configured in the environment, `scripts/audit_account_inventory.py` can collect a repository inventory without changing GitHub. It requires an explicit local report path:

```bash
python scripts/audit_account_inventory.py --owner YOUR_ACCOUNT_OR_ORG --output /secure/private/path/account-inventory.json
```

Set `GH_TOKEN` or `GITHUB_TOKEN` in the environment before running; never put the token in the command, report, or repository. The report can contain private repository names. Keep it in access-controlled storage and never commit it to this public repository. Its coverage is intentionally labelled `partial-unverified`: token-visible inventory is not proof that every account repository was discovered, and this collector does not inspect repository contents or cross-repository contracts.


### Combined account baseline

The combined read-only baseline runs repository discovery, root-layout inspection, bounded inspection of selected governance-document headings, and read-only default-branch safeguard inspection in one report. It records classic branch-protection state and repository/organization rulesets where the authenticated identity permits. Inaccessible controls remain unverified rather than being treated as absent. It records document hashes and headings but does not retain document bodies:

```bash
python scripts/run_account_audit.py --owner YOUR_ACCOUNT_OR_ORG --output /secure/private/path/repositories/account-baseline.json
```

Set `GH_TOKEN` or `GITHUB_TOKEN` in the environment. The output must remain outside this public repository and in access-controlled storage. Repositories that cannot be inspected are recorded as blocked rather than silently omitted. A zero blocked count still does **not** prove complete account coverage, repository-content quality, security posture, or cross-repository compatibility; the report deliberately remains `partial-unverified`.

To check declared cross-repository contract artifacts, maintain a **private local JSON inventory** outside this public repository and pass it to the combined runner with `--expected-contracts /secure/private/path/contracts.json`. The inventory uses `schema_version: 1`, an explicit `authoritative` boolean, `reviewed_at`, and a non-empty `contracts` list. Each contract names a unique `contract_id`, `producer` and `consumer` as `owner/name`, and a repository-relative `path` for the producer's canonical artifact. The auditor records artifact status and blob hash only; it does not retain contract bodies. A missing or inaccessible artifact remains unverified. Even a verified result proves only that declared producer artifacts exist and both endpoints were observed—not that consumers use them correctly or that APIs, events, versions, or runtime behavior are compatible. Keep private repository names out of the public inventory and public reports.

The safeguard collector can also be run directly for a single repository:

```bash
python scripts/audit_branch_safeguards.py --repository OWNER/REPOSITORY --output /secure/private/path/branch-safeguards.json
```

It is read-only. A report is evidence about endpoints visible to the current token, not a claim that all effective GitHub policy was observed. Apply security-setting changes only after explicit human approval and verify the effective settings afterward.

### Findings ledger

The SQLite ledger stores schema-validated findings privately and supports lookup/filtering by stable finding ID, lifecycle status, and severity. It is not initialized against the live account by CI; choose a private local path and preserve backups securely.

```bash
python scripts/audit_findings_ledger.py --db /secure/private/path/findings.sqlite3 init
python scripts/audit_findings_ledger.py --db /secure/private/path/findings.sqlite3 upsert --record /secure/private/path/AUDIT-EXAMPLE.json
python scripts/audit_findings_ledger.py --db /secure/private/path/findings.sqlite3 list --status observed
python scripts/audit_findings_ledger.py --db /secure/private/path/findings.sqlite3 show AUDIT-EXAMPLE
```

The database is created with owner-only permissions and paths inside this public repository are refused. Export, when needed, uses the same private-file writer. A ledger only becomes useful once real, evidence-backed findings are entered and the backup/review procedure is established.

### Compare two baselines

After saving two reports from the same baseline utility, compare them without changing either source report:

```bash
python scripts/compare_audit_baselines.py --previous /secure/private/path/previous.json --current /secure/private/path/current.json --output /secure/private/path/comparison.json
```

The comparison reports added/removed repositories and changes in selected metadata, layout signals, document headings, and document hashes. Its output is written with owner-only file permissions. It compares only the records supplied; it cannot explain a disappearance or prove the inventory complete. It is a structural delta, not the durable findings ledger or a semantic review.


## Audit finding contract

The portable finding record is defined in [schemas/audit-finding.schema.json](schemas/audit-finding.schema.json), with a starter record at [templates/audit-finding.template.json](templates/audit-finding.template.json). Findings must preserve evidence, ownership, severity, lifecycle state, remediation, and verification. A finding may be marked `verified-resolved` only when verification evidence is recorded.

The dependency-free `scripts/validate_audit_findings.py` enforces core required-field and lifecycle invariants. `scripts/validate_audit_schema.py` applies the full Draft 2020-12 JSON Schema, including format checks, using the development dependency in `requirements-dev.txt`; CI checks the canonical template against both validators. The durable, queryable findings ledger remains pending. `scripts/compare_audit_baselines.py` can compare two saved baseline reports and report repository additions, removals, and structural changes without retaining document bodies; its output is written with owner-only file permissions and remains explicitly partial/unverified. Keep real audit records in access-controlled storage when they expose private repositories or security-sensitive details.


## Prepare a local handoff backup

Before a fresh builder assesses retirement or restructuring, preserve the GitHub repositories locally. On Jimmy's Bucky machine, this script uses the existing GitHub CLI login; it does not require switching accounts or creating a new one.

From a terminal:

```bash
cd ~/projects/world-seed
git status --short --branch
```

If this branch has the latest proposed seed work checked out, run:

```bash
bash scripts/prepare_local_handoff_backup.sh
```

The script lists repositories visible under `mythologyprospector-hub`, then saves a checkout, a Git bundle, and a ZIP snapshot for each repository under a new timestamped directory in `~/archive`. It uses owner-only local permissions, refuses to overwrite an existing destination, records successes/failures in a local manifest, and does not change any GitHub repository. Review the output and manifest; investigate every failure before relying on the backup.

This is a first preservation pass, not a complete GitHub account export. It does not preserve issues, pull-request discussions, Actions artifacts, releases, repository settings, or every account-level permission. Keep all original GitHub repositories intact until the handoff audit confirms what else must be preserved. Do not run repository deletion or archival as part of this step.
