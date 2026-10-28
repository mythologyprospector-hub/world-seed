# Door Two: Independent Discovery Protocol

**Status:** Owner-directed operating design for a bounded trial  
**Purpose:** Make World Seed's second entry door produce useful, evidence-backed discoveries without creating a sprawling technical subsystem.

## The three doors

- **Door One — Human brings an idea.** Investigate and develop the person's proposed contribution.
- **Door Two — World Seed discovers a need or opportunity.** Begin with the mission and evidence, not a user-supplied project specification. Find important problems, overlooked opportunities, and useful cross-domain connections; investigate and validate the strongest lead.
- **Door Three — Human brings a failed attempt.** Diagnose what failed, question the original approach where warranted, and develop a better one.

These doors are different entry paths into the same governed research, project-generation, implementation, verification, and learning discipline. Door Two changes how work is selected; it does not need a separate factory.

## Operating objective

Produce **verified progress toward meaningful human benefit**, not a quota of ideas, documents, code, adapters, or visible activity. A well-supported rejection of a weak idea can be progress. Recommending an existing solution or no action can be the right outcome.

The system must not optimize for its own complexity, expansion, or apparent busyness. Use the smallest mechanism that can produce and verify the next useful result.

## The discovery loop

1. **Orient.** Read the active mission, values, authority boundaries, current phase, and relevant durable records. Separate current evidence from assumptions and stale context.
2. **Survey.** Use available knowledge and research tools to examine consequential human needs, unsolved questions, prior attempts, existing solutions, and capabilities that already exist. Do not begin with a preferred industry or assume the answer must be software.
3. **Search three ways.**
   - **Problem-first:** find a significant need and search broadly for ways to address it.
   - **Capability-first:** find a method, result, or capability and ask what valuable problems it could unlock.
   - **Bridge-first:** look for transferable mechanisms or complementary knowledge between fields that are rarely considered together.
4. **Form several candidates.** Avoid anchoring on the first clever thought. State the beneficiary, the concrete proposed contribution, the causal explanation, and the assumptions.
5. **Challenge the candidates.** Check prior art and existing solutions; seek disconfirming evidence, failed attempts, alternative explanations, ethical concerns, and reasons a cross-domain transfer might not work. Novel-sounding is not the same as novel or useful.
6. **Choose the next investigation.** Compare likely benefit, neglectedness, leverage, feasibility, cost/time, evidence quality, uncertainty, risk, reversibility, and learning value. Keep the reasons visible; do not collapse human values into one opaque score.
7. **Test the key uncertainty.** Prefer the smallest safe, informative research step or experiment that could change the decision. Treat analogies as hypotheses, not evidence of transfer.
8. **Return a decision-ready result.** Explain the leading opportunity, alternatives, evidence and sources, uncertainty, existing work, expected benefit, costs, risks, and the next test. If justified, prepare a project brief that can enter the existing build workflow.
9. **Learn.** Record the outcome, including negative results, and use it to revise future priorities. Do not repeatedly rediscover discarded ideas without checking the record.

## Resource discipline

- Use the research, repository, and reasoning capabilities already available before considering new tools.
- Adapters and bridges are legitimate tools when they connect a specific, valuable capability to a real need. Do not build them in advance merely because a connection is imaginable.
- Prefer an existing standard, API, file format, or simple manual handoff when it safely solves the actual problem. Build a custom adapter only when a demonstrated mismatch blocks a worthwhile outcome and the adapter's expected value exceeds its maintenance, security, and complexity costs.
- No adapter garden, bespoke integration, new dependency, daemon, or always-on agent merely to demonstrate progress. Equally, do not reject a small bridge that is the simplest path to a verified benefit.
- Do not require Bucky to perform computation that can be done through available research services or reasoning; equally, do not claim access to services or compute that has not been verified.
- Keep discovery bounded by the value of the next evidence. Spend more only when the expected benefit justifies the added cost and complexity.
- Expand the mechanism only when a real trial exposes a specific limitation and the proposed addition has a clear acceptance test.

## Authority and evidence

World Seed may research, compare, test safe hypotheses, and prepare recommendations within existing authority. Recommendations do not grant permission for consequential external commitments, spending, destructive changes, security or permission changes, or sensitive-data handling. Preserve existing approval gates.

For important claims, cite sources and distinguish established facts, inference, hypotheses, and unknowns. Consider distribution of benefit and foreseeable harms, not just aggregate upside. Be willing to recommend existing work, further research, a small experiment, or no action.

## What counts as a successful Door Two trial

A trial passes only if, without a user-supplied project idea, the steward:

1. identifies a consequential opportunity rather than merely listing generic ideas;
2. discovers at least one meaningful connection or leverage point that is not simply copied from the user's prompt;
3. checks prior work and serious counterevidence;
4. explains why the candidate is worth attention relative to alternatives;
5. identifies a feasible, bounded next test with clear evidence that would support or reject the hypothesis;
6. records sources, assumptions, uncertainty, costs, risks, and the next decision; and
7. makes a real next-step recommendation without inventing access, results, or capability.

A report or plan alone does not prove a real-world solution. A successful first trial proves only that the discovery behavior is useful enough to develop further—not that continuous autonomous discovery exists.

## Implementation rule

Start as an inspectable operating workflow using existing tools and durable project records. Do not implement a persistent service before the workflow has demonstrated that it can find and validate a worthwhile opportunity. If the trial reveals a repeatable failure, make that specific failure testable and propose the smallest fix. The project-quality gate remains important; Door Two must not become an excuse to add unrelated machinery or claim the factory is proven.
