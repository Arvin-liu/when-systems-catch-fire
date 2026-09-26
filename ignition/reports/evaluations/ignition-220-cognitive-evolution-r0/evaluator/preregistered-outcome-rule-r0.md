# Task220 R0 preregistered outcome rule

This rule is frozen before any revision, transfer, or evaluator output exists. It applies separately to each of two independent evaluators and uses fixed denominators.

## Units and notation

- Three families × two independent revision replicas = six lineages.
- Each lineage has held-out cases A revised-boundary, B preserved-old-scope, and C edge-unresolved.
- Each lineage has three matched future transfer assignments: M0_ONLY, M0_PLUS_E1, and EVOLVED_M1. The same three case bytes are used in every matched assignment.
- If all six revision outputs are syntactically usable, the design has 18 future transfer conversations, 18 case responses per assignment, and 54 case-condition responses in total.

For one lineage, evaluator, and case:

- R = REVISION_VALIDITY_SUCCESS.
- E_A, E_B, E_C = EVOLVED_M1 TRANSFER_TARGET_SUCCESS for cases A, B, and C.
- O_A = M0_ONLY TRANSFER_TARGET_SUCCESS for case A.
- F_A = M0_PLUS_E1 TRANSFER_TARGET_SUCCESS for case A.

O_A and F_A are control-condition success values. They are not overreaction or critical-error flags.

## Evolution-chain endpoint

Compute each lineage mechanically:

- REVISED_BOUNDARY_GAIN = E_A AND NOT O_A AND NOT F_A.
- PRESERVATION_SUCCESS = E_B.
- EDGE_BOUNDARY_SUCCESS = E_C.
- EVOLUTION_CHAIN_SUCCESS = R AND REVISED_BOUNDARY_GAIN AND PRESERVATION_SUCCESS AND EDGE_BOUNDARY_SUCCESS.

No case can compensate for another. Missing or unusable records are visible protocol outcomes, never silently omitted or replaced. Keep six lineages in every denominator.

## Per-evaluator disposition

### SUPPORTED

An evaluator assigns SUPPORTED only if every item holds:

- REVISION_VALIDITY_SUCCESS ≥ 5/6.
- EVOLUTION_CHAIN_SUCCESS ≥ 5/6.
- Each of the three families has at least one successful lineage.
- At least two of three families have both revision replicates successful.
- Among successful EVOLVED_M1 lineages, there are zero UNSUPPORTED_GLOBAL_RETIREMENT errors and zero PRESERVED_SCOPE_LOST errors.

### PARTIAL

If that evaluator does not meet SUPPORTED, it assigns PARTIAL only if every item holds:

- REVISION_VALIDITY_SUCCESS ≥ 4/6.
- EVOLUTION_CHAIN_SUCCESS ≥ 3/6.
- At least two of three families have one or more successful lineages.
- Across all six matched lineages, EVOLVED_M1 has more REVISED_BOUNDARY_CASE successes than M0_ONLY and more than M0_PLUS_E1.

For the last item, compare raw A-case success counts: sum(E_A) > sum(O_A) and sum(E_A) > sum(F_A), each with denominator six.

### NOT_SUPPORTED

Otherwise that evaluator assigns NOT_SUPPORTED. Do not adjust thresholds, denominators, case keys, or endpoint definitions after outputs exist.

## Overall R0 disposition

Apply the following only after both independent evaluator sheets and per-evaluator dispositions are locked:

- BOUNDED_COGNITIVE_EVOLUTION_R0 = SUPPORTED only if both evaluators independently assign SUPPORTED.
- BOUNDED_COGNITIVE_EVOLUTION_R0 = PARTIAL only if both evaluators independently satisfy the PARTIAL predicates (an evaluator meeting SUPPORTED also satisfies the lower PARTIAL numeric predicates).
- BOUNDED_COGNITIVE_EVOLUTION_R0 = NOT_SUPPORTED otherwise, including when evaluator disagreement prevents both from reaching the same disposition threshold.

## Descriptive measures and claim ceiling

Also report, per evaluator and by family: E vs O and E vs F case-level wins/losses/ties; old-scope preservation; edge-boundary success; revision and transfer critical-error counts; and EVOLUTION_LINEAGE_USE_SUCCESS. These are descriptive counts for this synthetic set, not population inference or statistical-significance evidence.

Even SUPPORTED is limited to BOUNDED_COGNITIVE_EVOLUTION_R0 for this synthetic protocol. It does not establish autonomous self-improvement, general cognitive inheritance, causal cross-runtime effects, cross-model evolution, R1, or production capability.

Revision agents, transfer Successors, and Evaluators launched at this freeze: 0. Task220 selects no runtime, model, provider, reasoning effort, or speed mode. R1 and cross-model transfer remain unauthorized.
