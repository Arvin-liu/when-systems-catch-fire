# D2-I1 Architecture Decision — Evidence-Constrained Multi-History / Multi-World Projection

Status: stacked Draft candidate. Direct parent is `F15-D1-I1` at the frozen exact head declared in the task receipt.

## Decision

Multiple evidence-constrained history/world candidates can preserve shared evidence, branch assumptions, indistinguishable sets and falsifiers without forcing a unique story or unjustified probability.

The contract uses typed evidence bindings and bounded fields. Each material assertion names repository evidence, its digest and the parent exact head. Required rule assertions are deterministic inputs to a fail-closed production CLI; missing, duplicated, unsupported or false assertions block the bundle.

## Core objects

- `world_candidates`
- `divergence_point`
- `shared_evidence`
- `branch_specific_assumptions`
- `indistinguishable_set`
- `falsifiers`
- `justified_weights`
- `unresolved_paths`
- `narrative_ceiling`
- `claim_ceiling`

## Fail-closed rules

- `every_world_evidence_bound`
- `no_forced_unique_story`
- `indistinguishable_not_ranked_fact`
- `weights_need_justification`
- `possibility_not_probability`
- `falsifier_required`
- `unresolved_paths_preserved`
- `narrative_ceiling_preserved`

## Explicit non-claims

- generated possibility is not real probability
- indistinguishable paths are not ranked facts
- no evidence-free story
- no forced unique narrative

The pilot is repository-local and self-authored. It performs no real-world external action, does not modify Main, and cannot establish L7, a new truth layer or universal causal truth.
