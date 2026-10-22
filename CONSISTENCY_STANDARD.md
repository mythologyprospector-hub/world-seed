# Ecosystem-Wide Consistency Standard

**Status:** Canonical baseline; mandatory for every bootstrapped repository  
**Governs:** Documentation, code readability, naming, repository layout, engineering conventions, and the automated checks that keep them consistent.  
**Last verified:** 2026-10-22

## Purpose

The ecosystem should feel as though one exceptionally careful editor and engineer established its conventions. A person moving between repositories should not have to relearn the layout, terminology, document style, naming rules, or routine process every time.

Consistency is a reliability feature: it reduces cognitive load, makes defects easier to spot, helps AI builders work safely, and makes handoffs understandable to humans.

## Authority and portability

This standard defines the shared baseline. The target account's mission, language, technology, and project requirements determine the details that must be filled in during bootstrap. Do not blindly impose a language-specific layout on an unrelated project.

When a project needs a legitimate exception:
1. State the reason and scope in its canonical documentation.
2. Keep the exception as narrow as practical.
3. Avoid creating a second convention where an existing one can be extended.
4. Add or adjust validation so the exception is deliberate rather than invisible drift.

An undocumented difference is presumed to be drift until reviewed.

## Editorial and document standards

All maintained documentation must use a coherent house style:

- Use clear, direct language and stable terminology. Define project-specific terms once and use them consistently.
- Use Markdown ATX headings (`#`, `##`, `###`) with a logical hierarchy; do not skip levels for visual effect.
- Give documents descriptive titles. Use consistent metadata fields and ordering where metadata is needed (for example: status, purpose/scope, owner, and last verified).
- Prefer short paragraphs, meaningful lists, and tables only when comparison is genuinely clearer.
- Use sentence case for headings unless a proper name or established technical identifier requires otherwise.
- Use fenced code blocks with an appropriate language label; keep commands copyable and safe to run.
- Use relative links for files within the repository. Verify links when adding or moving documents.
- Keep terminology, capitalization, spelling, date format, status labels, and severity labels consistent across repositories.
- Distinguish observed facts, assumptions, recommendations, decisions, and unresolved questions.
- Include purpose, prerequisites, expected result, failure behavior, and recovery guidance for operational procedures where relevant.
- Avoid duplicate, competing, or misleadingly named “final” documents. Update the canonical document or clearly mark historical records as historical.
- Keep examples, templates, generated reports, and indexes aligned with the canonical rules.

Documentation must be accurate as well as polished. Formatting must never disguise uncertainty or claim work was verified when it was not.

## Human-readable code

Code is written for the next human who must understand, operate, debug, or safely change it.

- Name functions, types, variables, modules, and configuration keys for their meaning, not their brevity.
- Comment intent, invariants, assumptions, non-obvious decisions, edge cases, external contracts, security boundaries, and surprising behavior.
- Explain *why* a decision or workaround exists when that reason is not obvious from the code.
- Document public interfaces, important data shapes, side effects, failure modes, and required configuration.
- Add docstrings or equivalent API documentation to non-trivial public functions and modules according to the language's conventions.
- Use examples for complex interfaces where an example materially improves understanding.
- Keep comments near the behavior they explain and update them when behavior changes.
- Prefer readable control flow and small, purposeful units over cleverness or unnecessary abstraction.
- Use explicit errors and useful diagnostic messages; do not silently swallow failures.
- Do not add comments that merely translate a line of code into English, repeat stale facts, or assert something the code does not guarantee.
- Treat missing comments on genuinely non-obvious or high-risk behavior as a maintainability defect.

The goal is **well-explained code, not maximum comment volume**. A reviewer should be able to understand purpose, assumptions, interfaces, and hazards without reverse-engineering the entire project.

## Naming conventions

Each ecosystem must publish one naming matrix covering, as applicable:

- repository names and descriptions;
- top-level directories and canonical documentation files;
- source modules, packages, classes, functions, variables, constants, and configuration keys;
- test files, fixtures, test names, and test data;
- Git branches, commits, tags, releases, and pull requests;
- CI workflows, jobs, artifacts, environment variables, and automation;
- issues, audit findings, decisions, plans, and operational records.

Choose conventions appropriate to the language and platform (for example, Python's established naming conventions) and document them in one canonical place. Prefer descriptive, predictable names; avoid unexplained abbreviations, inconsistent singular/plural forms, ambiguous generic names, and ad-hoc suffixes such as `new`, `final2`, or `fixed-final`.

Use established ecosystem vocabulary consistently. Names should reveal role and scope where possible. Do not rename public interfaces, repositories, or important paths casually: assess references, integrations, compatibility, and migration requirements first.

## Repository shape and process

Repositories should share a recognizable structure wherever their purpose permits. Bootstrap must define the canonical locations for:

- entry-point instructions and project constitution;
- README and user/operator documentation;
- architecture, decisions, plans, and current status;
- source code and public interfaces;
- tests, fixtures, and test utilities;
- configuration, dependency declarations, and reproducible setup;
- CI/workflows and quality checks;
- security, contribution, license, and support material where applicable;
- audit findings, verification evidence, and handoff/recovery records.

Not every repository needs every directory or file. Avoid empty scaffolding and ceremonial files. A deviation must follow the exception policy above.

Processes should also be recognizable across the ecosystem: discovery before change, evidence-backed plans, scoped implementation, automated validation, independent review where appropriate, recorded outcomes, and explicit handoff. The exact commands may differ by technology, but each repository must document a clear, canonical path to set up, check, test, run, and recover it.

## Public repository launch readiness

Every public GitHub repository should have a social preview image before it is treated as launch-ready.

- Prepare a PNG, JPG, or GIF under 1 MB, preferably 1280 × 640 pixels (640 × 320 is the minimum recommended size in the source guidance).
- Keep the source image in the repository so it can be recreated or uploaded again.
- GitHub applies the image through repository Settings → Social preview → Edit → Upload an image; committing the file does not apply it.
- Treat preparation and upload as separate states. Do not claim the preview is applied until the owner confirms the GitHub setting was completed.
- Verify current GitHub requirements when preparing the image, because platform guidance can change.

Private repositories may retain a source image, but the source guidance notes that GitHub only shares a social preview from a public repository.

## Engineering quality baseline

Each repository must identify the applicable tools and commands for:

- formatting and style/lint checks;
- static analysis and type checking where useful;
- unit and integration tests, including critical cross-repository contracts;
- dependency and lockfile consistency;
- documentation/link checks where practical;
- secret, permission, and security checks appropriate to the risk;
- reproducible setup and clean-environment validation.

Prefer shared reusable configuration and workflows over copying near-identical implementations. Pin or constrain tools where reproducibility requires it. Explain justified omissions and tool-specific differences. Do not claim a check exists or passes unless it is configured and evidence confirms the result.

## Enforcement and drift control

The rolling audit defined in [AUDIT_SYSTEM.md](AUDIT_SYSTEM.md) must check consistency at all three scopes: repository, cross-repository, and account. It should inspect both canonical guidance and observable files/configuration, and flag conflicts between them.

At minimum, bootstrap and rolling audits must check:

1. Required canonical documents and expected structure.
2. Heading hierarchy, metadata conventions, broken internal links, and obvious duplicate/conflicting guidance where tooling supports detection.
3. Naming-rule violations and unexplained naming exceptions.
4. Presence and usability of documented setup, formatting, lint, test, and recovery commands.
5. Relevant formatter/linter/type/test configuration and whether the prescribed commands actually run.
6. Comment/docstring quality for non-obvious interfaces and risky behavior, using human review where reliable automation is unavailable.
7. Drift in shared templates, instructions, workflows, schemas, and service contracts.
8. Exceptions, owners, rationale, expiry/review conditions, and unresolved findings.

Use automated checks for mechanically decidable rules and human/AI review for semantic quality. Do not pretend a regex can reliably judge whether a comment is useful. Record tool limitations and partial coverage explicitly.

New repositories inherit the standard at creation. Existing repositories receive a baseline assessment and a prioritized migration plan; do not make sweeping or breaking changes solely for cosmetic uniformity. Fix high-risk inconsistencies first, preserve behavior, verify changes, and use reviewable pull requests. No automatic cross-repository rewrite or merge is authorized by this standard.

## Acceptance condition

A repository is not “consistent” merely because its README looks tidy. The claim requires a documented convention, checks appropriate to that repository, recorded results, explicit exceptions, and an audit that considers its relationship to the rest of the ecosystem.
