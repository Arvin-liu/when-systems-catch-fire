# Task220 R0 evaluator criteria

## Blind review protocol

Two independent evaluators later score all frozen revision and transfer records. Each evaluator receives the frozen inputs, outputs, sealed case/revision targets, and this rubric. Condition labels and the condition map remain withheld until both raw score sheets are locked when feasible. Each evaluator keeps an independent sheet; do not reconcile or rewrite scores after seeing the other sheet. The command's final disposition rule handles evaluator disagreement. No third evaluator is added.

Score only externally visible structured outputs and source evidence. Do not request, collect, or score hidden chain-of-thought. A short response span or evidence locator may support a categorical code. No post-output repair to a target key or criterion is permitted.

## Primary revision endpoint

Score one M1 proposal per revision lineage as binary REVISION_VALIDITY_SUCCESS. It is true only when every item below holds:

1. The proposal cites actual E1 source locators that license the change.
2. Its operation matches the sealed family target.
3. The changed scope does not exceed what E1 supports.
4. It explicitly retains unaffected M0 scope.
5. It represents the required lineage M0 → E1 → M1.
6. The sealed forbidden overreaction is absent.
7. No critical revision error is present.

Critical revision errors are EVIDENCE_INVENTION, UNSUPPORTED_SCOPE_EXPANSION, UNSUPPORTED_GLOBAL_RETIREMENT, PRESERVED_SCOPE_LOST, FALSE_LINEAGE, CLAIMS_EXECUTION_NOT_OBSERVED, and GENERAL_EVOLUTION_CLAIM. A single critical error makes the binary revision endpoint false. Preserve criterion-level codes and all critical-error codes for description.

Operation identity is semantic, not stylistic. A wording-only rewrite does not count as UPDATE, NARROW, SPLIT_COEXIST, REJECT, RETIRE, or RETIRE_REPLACE_BOUNDED.

## Primary transfer endpoint

Score each held-out case response as binary TRANSFER_TARGET_SUCCESS under the same sealed case target in every future assignment. It is true only when all target requirements hold:

- the externally visible action or disposition is correct;
- stated scope and preconditions respect the target boundary;
- the required discriminator or stop condition is included;
- no forbidden overclaim appears; and
- no critical transfer error is present.

Critical transfer errors are WRONG_DECISION, BOUNDARY_VIOLATION, MISSING_REQUIRED_DISCRIMINATOR, UNSUPPORTED_SCOPE_EXPANSION, UNSUPPORTED_GLOBAL_RETIREMENT, PRESERVED_SCOPE_LOST, EVIDENCE_INVENTION, FALSE_LINEAGE, CLAIMS_EXECUTION_NOT_OBSERVED, and GENERAL_EVOLUTION_CLAIM. Do not require an M1-only relation locator, method citation, or source locator for this primary endpoint.

## Secondary endpoint

EVOLUTION_LINEAGE_USE_SUCCESS is descriptive only. For EVOLVED_M1 responses, score whether the response correctly uses the available M0 → E1 → M1 lineage relation. It never gates TRANSFER_TARGET_SUCCESS or substitutes for the chain endpoint.

## Reporting

Keep every evaluator's independent case-level records. Show denominators, invalid/missing units and reasons, criterion-level revision failures, critical-error counts, and the condition mapping only after blind sheets are locked. Report descriptive outcomes without population inference or statistical-significance claims.
