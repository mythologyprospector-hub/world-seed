# World Seed Discovery Mode

**Status:** Owner-approved strategic direction; design proposal  
**Date:** 2026-10-24  
**Scope:** Canonical product/architecture intent only. This document does not claim implementation exists.

## Purpose

World Seed must support two ways to begin a project:

1. **Builder Mode — build a supplied idea.** A human brings a project, need, or question. World Seed investigates it, develops the best defensible approach, and routes it through the existing project-generation and build workflow.
2. **Discovery Mode — discover what should be built.** A human supplies the mission and governing values, not a predetermined project. World Seed researches the opportunity space, identifies and tests promising opportunities, recommends the most valuable achievable next contribution, and can then route an approved candidate through the same build workflow.

The working name for the discovery intelligence is **the Digital Djinn**. This is a human-facing nickname, not a required runtime service name, API, or claim of autonomous authority. The canonical capability name is **World Seed Discovery Mode**.

## Guiding principle

**Search the space of human possibility, not merely the space of requests humans already know how to make.**

The mission is to help humanity learn, discover, understand, create, cooperate, and solve difficult problems. Discovery Mode should not privilege a field merely because a person happened to ask about it. It should deliberately search across disciplines and look for overlooked problems, transferable methods, enabling capabilities, and useful connections between domains.

This is not a claim that an AI is naturally unbiased or omniscient. The process must actively seek diverse sources, test its assumptions, record uncertainty, and evaluate its discoveries against evidence.

## Two entry paths, one build discipline

Builder Mode and Discovery Mode are different ways to select and define work, not two separate project factories. Both should hand a sufficiently justified project into the same World Seed generation, onboarding, implementation, verification, governance, and durable-record process.

Neither path makes a generated scaffold equivalent to a finished project. The generated project must still satisfy its own mission and evidence-backed acceptance criteria.

## Discovery method

Discovery Mode should use a repeatable loop. The stages are responsibilities, not a claim that each already exists as software.

1. **Establish the mission and real constraints.** Load the authorized mission, values, approval boundaries, relevant repository constellation, and current machine/tool context. Separate observed facts from stale profile claims and unknowns.
2. **Survey the opportunity space.** Research human needs, scientific unknowns, existing solutions, open research, known bottlenecks, and capabilities already available. Include software, research, datasets, experiments, infrastructure, education, and other useful outcomes—not only applications.
3. **Search in multiple directions.**
   - *Problem-first:* begin with a significant need and search across domains for solutions.
   - *Capability-first:* begin with a discovery or method and investigate what new problems it might help solve.
   - *Bridge-first:* seek useful transfers and combinations between disciplines that are not usually examined together.
4. **Generate candidate opportunities.** Produce a diverse portfolio rather than a single unchallenged favorite. State the proposed contribution, intended beneficiaries, causal reasoning, assumptions, relevant prior work, and expected enabling effects.
5. **Investigate and challenge.** Search for prior art, related work, counterevidence, failed approaches, conflicting findings, ethical concerns, and reasons the candidate may not work. Distinguish a novel-sounding description from a genuinely new contribution.
6. **Assess benefit and achievability.** Compare expected human benefit, neglectedness, leverage, cross-domain potential, feasibility, cost, time, evidence strength, uncertainty, foreseeable harms, and the capabilities unlocked for later work. Preserve the individual dimensions and rationale; do not hide value judgments inside one opaque score.
7. **Design the smallest informative test.** When a key uncertainty can be tested cheaply, propose or conduct a bounded experiment or prototype before recommending a costly commitment. A cross-domain analogy is a hypothesis, not proof that a method transfers.
8. **Recommend the next project.** Provide a ranked or tiered portfolio, explain why the leading candidate is the best current choice, identify trade-offs and alternatives, and state what new evidence would change the recommendation.
9. **Hand off through existing governance.** Produce a project brief with mission, problem, intended benefit, evidence and source provenance, alternatives considered, assumptions, acceptance criteria, risks, resource requirements, and first useful milestone. Route it through the shared World Seed build workflow and existing human approval gates.
10. **Learn from outcomes.** Record what happened, compare results with expectations, capture failures as well as successes, and revisit candidates when new evidence or capabilities change the opportunity landscape.

## Cross-domain discovery is a first-class requirement

Do not organize the search solely around conventional academic or engineering categories. Use domains as useful indexes, not as walls. Look for shared structures, transferable methods, complementary capabilities, missing interfaces, and combinations that may make an otherwise intractable problem tractable.

Evaluate proposed bridges rigorously. A useful record identifies:
- the source domain and the target problem/domain;
- the concrete method, mechanism, or evidence proposed to transfer;
- why the transfer might work;
- known differences that could invalidate the analogy;
- relevant prior art and counterexamples;
- the cheapest meaningful validation step; and
- the observed result, including negative results.

A “fair draw” means no domain receives priority simply because it is familiar to the requester. It does **not** mean every domain receives equal resources regardless of evidence or need. Prioritization should reflect potential benefit, neglectedness, leverage, feasibility, uncertainty, and the mission.

## Bucky and the reality of possibility

The machine context known as **Bucky** is important because opportunity assessment must be grounded in what the current environment can actually do. The system should gather and refresh authorized, relevant evidence about available hardware, operating system, storage, installed tools, models, connected services, network access, resource limits, costs, and existing projects before making environment-dependent claims.

Keep these categories distinct:
- **Available locally:** verified tools and resources that can run on the current machine.
- **Available through a connected service:** remote capabilities whose access, limits, terms, and costs are verified.
- **Potentially obtainable:** plausible resources that require setup, funding, permission, or additional hardware.
- **Unavailable or unverified:** capabilities not established by current evidence.

Do not treat Bucky's limitations as universal limits on what humanity could accomplish. Conversely, do not recommend a plan as locally achievable merely because a sufficiently powerful computer somewhere could run it. Make the proposed execution environment, dependencies, cost, and bottlenecks explicit. Machine facts are mutable; provenance and observation time matter. Never publish private machine or operator details into the portable public seed.

## Opportunity evaluation

Avoid pretending that “best for humanity” is an objective number that can be computed without judgment. For each serious candidate, preserve a concise evidence-backed assessment across:

- **Potential benefit:** scale, depth, duration, and distribution of the expected benefit.
- **Need and neglectedness:** who is affected, what existing solutions miss, and whether the problem is underserved.
- **Leverage:** whether the work enables many other projects, discoveries, or people to make progress.
- **Cross-domain potential:** whether it connects knowledge or capabilities that are currently separated.
- **Feasibility:** a credible path from current state to demonstrated result.
- **Cost and time:** effort, compute, money, dependencies, and time to first useful evidence.
- **Evidence and uncertainty:** source quality, prior results, unknowns, and confidence calibration.
- **Risk and reversibility:** foreseeable harms, privacy and security concerns, externalities, and whether early steps are safely reversible.
- **Learning value:** how much a bounded experiment could teach us even if the candidate fails.
- **Capability unlocked:** what new opportunities become possible if the project succeeds.

Present trade-offs and uncertainty explicitly. Use tiers or Pareto comparisons when candidates excel on different dimensions. A candidate with enormous theoretical benefit but no credible near-term path can remain in a longer-horizon portfolio beside a smaller, achievable contribution.

## Human authority and safety

Discovery Mode may research, propose, compare, and prepare work within granted authority. It must not turn a recommendation into permission for consequential action. Preserve established human approval gates for consequential external commitments, destructive operations, repository lifecycle changes, security/permission changes, sensitive-data handling, and other actions requiring authorization.

The system must:
- protect human dignity, autonomy, privacy, and security;
- honor licenses, terms, attribution, and applicable law;
- expose assumptions and sources instead of manufacturing certainty;
- seek disconfirming evidence and report failed tests;
- avoid optimizing for its own expansion or complexity as an end in itself;
- consider distribution of benefits and foreseeable harms, not just aggregate upside;
- be willing to recommend existing solutions, a small experiment, further research, or no action;
- never claim to have built, verified, or demonstrated a capability without evidence.

## Relationship to AkashaOS

**AkashaOS** is the larger ambition: a continually improving discovery-and-creation system that finds worthwhile possibilities, determines what can realistically be achieved, and helps make those possibilities real. World Seed is the intended home for the reusable project-selection and project-genesis capability that makes this ambition concrete.

The metaphor of the Digital Djinn describes the helpful discovery role; it does not imply magical knowledge. The system works from existing human knowledge, research, connected tools, experiments, and accumulated evidence, then expands what is possible by finding and validating useful connections and capabilities.

## Implementation sequencing and acceptance

This document records an approved direction, not a claim that Discovery Mode is implemented. It does not itself reopen the current factory acceptance gate or authorize skipping the existing project-quality trial. Unless the owner explicitly reprioritizes that gate, implementation should follow the first successful World Seed factory trial so the discovery capability is built on a demonstrated, reliable project-generation foundation.

When implementation is authorized, acceptance should require evidence that:
1. Both entry modes are documented and converge on the same governed build pipeline.
2. Discovery can start from a mission without a supplied project specification.
3. Candidate reports cite sources, distinguish fact from hypothesis, expose uncertainty, and compare alternatives.
4. The process deliberately evaluates cross-domain bridges and records validation, including failed attempts.
5. Environment-dependent recommendations use verified machine/service context and label unknowns.
6. Recommendations explain benefit, feasibility, cost, risks, and enabling effects without relying on an opaque single score.
7. The project brief is sufficient for the existing generator/builder to proceed without inventing missing requirements.
8. Consequential actions remain behind the existing approval gates.
9. Outcomes and lessons are durably recorded and can change future recommendations.
10. Tests cover evidence provenance, uncertainty, candidate diversity, unsafe or unsupported claims, and the human approval boundary.

The first implementation should be a narrow, inspectable research-and-recommendation workflow, not an unbounded autonomous agent or an expensive always-on service. Use the tools and resources actually available; keep the design modular so stronger research or model capabilities can be added when justified.

## Open questions for evidence-driven design

These are design questions for later investigation, not blockers to recognizing the strategic direction:
- Which existing World Seed components can already provide mission context, machine facts, source research, project briefs, and generator handoff?
- What research tools and external services are actually available and authorized, and what are their cost and privacy boundaries?
- What is the smallest useful end-to-end discovery trial that can demonstrate cross-domain opportunity selection and a credible build handoff?
- Which parts should be deterministic schemas and gates, and which require model judgment?
- How should the candidate portfolio balance urgent achievable benefits against high-upside, longer-horizon opportunities?

Resolve these through repository inspection and small experiments rather than speculation.
