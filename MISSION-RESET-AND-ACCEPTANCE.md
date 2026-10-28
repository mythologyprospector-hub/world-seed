# Mission: Build a Wise Djinn That Helps Fulfill Worthwhile Wishes

**Status:** Authoritative mission statement  
**Date:** 2026-10-28

## Actual goal

World Seed is the Djinn's bottle: a human-serving system for helping people discover worthwhile wishes and turn them into reality. It should preserve the intent behind imperfect wishes, investigate what would genuinely help, surface better opportunities and consequential unknowns, and pursue authorized work with evidence and judgment. It must respect human agency rather than decide what people should want.

Software factories, research tools, reproducible experiments, scientific collaboration, businesses, inventions, and infrastructure are possible means—not the mission itself. The right means depend on the wish, the evidence, and the likely human benefit.

Episteme, Praxis, and the other experimental projects are lessons and historical evidence, not products that must be rescued or copied. Recover their underlying ambitions when useful; do not preserve or rebuild them for their own sake.

**The immediate acceptance milestone remains a genuinely useful project produced by World Seed.** This is a bounded test that the system can turn a worthwhile goal into a working result—not the ultimate purpose of the Djinn. A passing unit suite, a complete checklist, or an impressive recovery mechanism cannot substitute for that evidence.

## Active execution lock — 2026-10-23

**This section is the controlling scope and finish-line decision for the current World Seed rebuild.** It resolves any broader or older sequencing language elsewhere in the portable seed. This is a feature freeze, not a claim that every existing component is finished.

### The work allowed before the first successful factory trial

1. **Close demonstrated foundation blockers** that prevent a clean generation, usable generated onboarding, safe project boundaries, meaningful verification, or the trial itself. Do not add polish or capabilities merely because they might be useful someday.
2. **Finish the bounded terminal-visibility path already underway.** Keep it to the opt-in local terminal journal, an explicit reviewed handoff to the configured private Intake Dock / Miracle Depot, and the explicit near-real-time snapshot wrapper needed to inspect command output. Preserve local-only raw journaling, deliberate invocation, private-destination verification, bounded heuristic redaction, honest limits, and harmless synthetic tests. Do not upload sensitive output.
3. **Run the factory acceptance trial.** Generate a fresh disposable project from World Seed alone, have a fresh builder follow its generated instructions and build a genuinely useful end-to-end slice, run meaningful tests, and record evidence and factory-caused defects. Fix only defects that prevent this acceptance bar, then repeat the trial.
4. **Run one bounded Door Two discovery trial using existing capabilities.** Start from the mission and no user-supplied project idea. Use available research and reasoning tools to identify and investigate a consequential cross-domain opportunity; verify prior work and counterevidence; compare benefit, feasibility, cost, uncertainty, and risk; and produce a decision-ready brief with the smallest informative next test. Do not build a persistent service, add adapters, introduce dependencies, or use Bucky as a reason to constrain the whole search. This is a manual, inspectable behavior trial—not a claim that autonomous or continuous discovery is implemented. Record the evidence and what the trial reveals about the missing operating mechanism.

### Explicitly deferred until after project-quality proof

- Recovery expansion, broad recovery acceptance, account-wide recovery, and restoration engineering.
- Omni-context, general memory/continuity infrastructure beyond the bounded terminal journal and handoff required above.
- Broad account/repository audits that do not resolve a concrete trial blocker.
- New subsystems, adapter collections, always-on services, optional features, architecture redesigns, unrelated cleanup, and revival or preservation of experimental projects. The bounded Door Two behavior trial above is an explicit exception and must use existing capabilities.
- Any GitHub reset or destructive repository action before the quality gate and a separate exact inventory/authorization gate.

Existing work is not automatically in scope just because a pull request or issue exists. Review the terminal stack in dependency order and verify each layer; do not merge untested drafts blindly. Other open work is deferred unless evidence shows that it blocks one of the allowed work items above.

### The finish line

World Seed is **done enough for the first trial** when (a) its documented generator can create a clean project with coherent canon, usable onboarding, correct provenance, and no operator-private leakage; (b) the terminal path has passed a harmless end-to-end local test with the intended privacy and exit-status behavior; and (c) a fresh builder has produced a useful, implemented project with meaningful tests and reproducible setup. Record the exact evidence and remaining limitations. Do not extend the finish line to include recovery or omni-context.

A defect exposed by the trial may justify a narrow factory fix. A new idea, a theoretical future risk without a demonstrated blocker, or a desire to make the factory more comprehensive does not reopen feature scope.

## Priority order

1. **Finish the foundation and plumbing.** Close concrete gaps in the builder, generated-project template, onboarding, governance, documentation, tests, and verification. Absorb useful Project Seed capabilities into World Seed so generation does not depend on a separate seed repository.
2. **Prove project quality.** Use World Seed alone to generate a fresh, disposable project from a clear mission. Have a fresh builder follow the generated onboarding and develop the project far enough to evaluate coherence, completeness, usability, testability, and whether the architecture serves its mission. Record real evidence and defects; improve World Seed when the factory causes them.
3. **Prepare the GitHub reset.** Identify the exact repositories and account state to clear, distinguishing World Seed and explicitly retained essentials from disposable experiments. Do not let old project preservation dictate the factory architecture.
4. **Reset only at the agreed gate.** Once World Seed has produced a project that meets the quality bar, prepare the clean slate for the next real project. Repository deletion or other irreversible account changes require an exact inventory and explicit final human authorization.
5. **Make recovery protect value.** Recovery is a welcome and important factory capability, not the lead objective. Once the builder can produce a worthy project, back that project up and prove restoration into an isolated location against a manifest. Expand recovery based on the real assets and risks of worthwhile projects, rather than treating every experimental repository as a preservation target.

## Operating principles

- Build a strong project factory; judge it by the projects it produces.
- Foundation first; project-quality evidence next; recovery protects the resulting value.
- Keep portable factory rules separate from operator-specific identity, preferences, machine facts, personal records, and credentials.
- Use fresh, disposable projects as acceptance fixtures. Do not confuse an artificial recovery fixture with proof of project quality.
- An audit, plan, green test suite, generated folder, or saved snapshot is evidence only for the specific claim it verifies.
- Keep the factory mission portable and project architecture mission-specific.
- Keep durable canon and handoffs current so a new chat or builder can continue without chat archaeology.
- The human owner supplies purpose and approves consequential choices; the assistant drives ordinary work, investigates, implements where tools permit, and reports evidence honestly.
- Do not claim a capability is complete until its defined acceptance behavior has actually been demonstrated.

## Essential retained foundation

1. **world-seed** — portable governance, onboarding, templates, project generation, verification, and the project-quality acceptance path.
2. **Authorized operator configuration** — private collaboration preferences and machine context where needed; never embedded in the public seed.
3. **Personal data** — retained only when the owner explicitly wants it, stored separately from project repositories.
4. **Intake Dock / Miracle Depot or successor** — optional, compartmentalized staging and handoff capability where useful.
5. **Recovery capability** — retained as a valuable factory feature and brought to the required level after the factory's project-quality milestone.

The old World and recovery worktrees are disposable test material. Salvage a useful discovery, test, or implementation when it directly improves World Seed; do not preserve old architecture merely because it exists. Bucky contains historical World backups, but those archives do not make old projects mandatory recovery targets.

**Episteme, Praxis, Renaissance, and the other experimental projects are not designated products to rehabilitate or preserve.** Do not spend time recovering them unless a specific piece of evidence or implementation is needed for World Seed and the scope is explicit. Their eventual reset or retirement must follow the agreed GitHub inventory and human approval gate.

**Organs is separate infrastructure.** Evaluate reusable runtime plumbing as optional, factory-managed capability under [RUNTIME_PLUMBING.md](RUNTIME_PLUMBING.md). Do not make it a mandatory dependency without evidence that the generated project's mission needs it.

## Acceptance gates

### A. Foundation and generator

1. Bootstrap World Seed from documented source in a clean environment.
2. Reconcile the reusable Project Seed capabilities into a single canonical World Seed factory without runtime dependency on Project Seed.
3. Generate a fresh project from World Seed alone, with the selected mission, coherent core canon, usable onboarding, portable defaults, correct provenance, and no accidental operator-specific data.
4. Verify required files, links, manifests, template versioning, tests, and declared behavior. Handle invalid input and conflicts safely.
5. Ensure a fresh builder can follow the generated instructions without relying on chat history or undocumented operator intervention.
6. Verify initiative behavior under an open-ended mission: without being handed a detailed implementation task or repeatedly prompted for the next step, the fresh builder must inspect relevant evidence, identify and justify a useful in-scope action, advance it within its authority, verify the result, and leave a durable next-step record. Record pass/fail evidence; mission language alone does not pass this check.
7. Verify that the builder selects work for demonstrated human value rather than output volume: it must name the problem and intended beneficiaries, compare plausible alternatives, cite supporting and disconfirming evidence, state expected benefit alongside cost, uncertainty and foreseeable harm, and define the smallest informative test and observable success criteria. It must be willing to recommend further research, an existing solution, or no build when those are better than producing another project. Record this rationale and later compare the prediction with observed outcomes; idea counts and completed artifacts alone are not success measures.

### B. Project-quality proof

6. Choose a genuinely useful, bounded mission and use World Seed to generate a new project for it.
7. Have a fresh builder follow the generated onboarding and advance the project beyond an empty scaffold.
8. Evaluate the result against explicit quality criteria: mission/canon coherence, sensible architecture, working implementation, meaningful tests, clear documentation, reproducible setup, and honest limitations.
9. Record defects caused by the factory, fix the factory rather than patching only the disposable output where appropriate, and repeat the acceptance run until the result meets the agreed bar.

### C. GitHub reset and recovery

10. Prepare an exact keep/reset/archive/delete inventory. Keep World Seed and only those other assets the owner explicitly designates. Do not infer permission to delete from an old project being a failed experiment.
11. Execute destructive GitHub changes only after the exact inventory and final authorization are confirmed.
12. Back up the worthy generated project, restore it into an isolated clean location, compare it against a manifest, and run the relevant checks. Record what the recovery mechanism does and does not preserve.

### D. Continuity and honesty

13. Leave a compact durable record of decisions, evidence, failures, and the next justified action.
14. Keep proposed, implemented, tested, verified, and demonstrated distinct. Report limitations plainly.

## GitHub reset policy

The desired reset is to clear the way for a real new project after World Seed demonstrates it can create one worth keeping. It is not a mission to rescue the experimental repositories.

Before resetting GitHub, inventory the exact repositories and distinguish World Seed and explicitly retained essentials from disposable experiments. Prefer reversible archival where uncertainty remains. Never delete repositories, branches, or history based on an inferred list. The owner must explicitly authorize the exact irreversible actions after reviewing the inventory.

## Working rule

Every action should close a concrete gap toward a sturdy project factory or provide evidence about project quality. Prefer the next small productive implementation step over another broad audit or an expanding recovery detour.

**Rule #1:** If we aren't having fun, we're doing it wrong. Make the factory humane, joyful, curious, and evidence-driven.
