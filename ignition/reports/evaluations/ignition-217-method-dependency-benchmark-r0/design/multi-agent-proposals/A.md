# Agent A — Architecture alignment proposal

Read-only proposal. No repository files were changed.

## Exact claim

For bounded synthetic cases, a source-linked complete method trace is needed to justify method-specific selection, use, outcome, and revision claims. A local procedural skill can support an action where its preconditions hold but carries no method lineage. An incomplete trace must remain bounded nonapplication or unknown. This tests dependence for warranted method-use and evolution claims, not whether a model can produce a correct answer without a method artifact.

## Mapping

- Representation: Cognitive IR R0 has METHOD but no SKILL. Task207's local procedural-skill schema cleanly separates local steps, preconditions, stop conditions, and observable fields from selection rationale and history. Preserve source hashes, locators, uncertainty, and claim boundaries.
- Cognitive Method: test whether a trace reconstructs context-gated selection and use. The R0 method slots are observable artifact records, not hidden reasoning traces.
- Cognitive Evolution: connect anomaly or failure and reframing to a revised representation/method, independent evaluation, disposition, and migration lineage. A code or text diff alone does not establish evolution.

## Essential links

Candidate to selection; selection to context and constraints; use to candidate/context and expected observation; outcome/failure to use; revision/disposition to candidate. Each segment also needs source reference, hash, locator, uncertainty, and an observation-only ceiling.

## Task216 evidence and limits

At PR #116's pinned head, the owner packet reports METHOD Reference Integration 2.0 versus SKILL 1.667 and FACTS 1.0. Against BROKEN_METHOD the difference was zero for evaluator K and 0.167 for evaluator L; bounded success was 6/6 for METHOD and BROKEN_METHOD under K, and 6/6 versus 5/6 under L. Runtime metadata is insufficient to assess confounding and the packet says final scientific adjudication remains pending there. This supports a method-dependency endpoint, not necessity for general task success.

The benchmark cannot establish causal method effects, general cognitive inheritance, model improvement, cross-model transfer, or cognitive-evolution success.
