# Task216 owner-adjudication input

## Command-provided scientific adjudication

The Task217 command declares these fixed inputs for this task:

- PROMPT_NEUTRAL_SKILL_METHOD_DISENTANGLEMENT = PARTIAL
- PROMPT_NEUTRAL_CONDITION_ASSOCIATION = OBSERVED
- METHOD_SPECIFIC_DECISION_ADVANTAGE = NOT_ESTABLISHED
- CAUSAL_METHOD_ARTIFACT_EFFECT = NOT_ESTABLISHED
- GENERAL_COGNITIVE_INHERITANCE = NOT_ESTABLISHED
- R1 = NOT_AUTHORIZED
- CROSS_MODEL_TRANSFER = NOT_AUTHORIZED_YET
- CANONICAL_PROMOTION = NOT_AUTHORIZED

These are treated here as Task217 command premises.

## Pinned engineering evidence read

Source: Arvin-liu/1111 PR #116, Open + Draft + unmerged, head 3cdbb8a8c8d41cec1af10aa63e85cacfb78b5818.

- 09-OWNER-READ-ME.md reports a high ceiling: FACTS, SKILL, and METHOD each reached 6/6 bounded success for both evaluators; the four generic domains are near ceiling. METHOD did not show a stable decision-quality advantage over the broken control.
- 03-CANONICAL-AGGREGATE.json reports 24/24 matched records, with exact evaluator record agreement on 22/24; the two recorded differences are one Decision Quality and one Reference Integration score.
- 07-RUNTIME-CONFOUND.json reports eight unavailable runtime attestations and insufficient core runtime metadata to assess confounding. Its permitted ceiling is prompt-neutral condition association with runtime uncontrolled.
- 08-DOUBLE-RECOMPUTE-RECEIPT.json reports byte-identical output from two independent recomputations using identical input hashes.

## Provenance boundary

The cited engineering packet says it did not make a final scientific classification and sets NEXT_STEP=OWNER_GPT_SCIENTIFIC_ADJUDICATION. It is evidence for the engineering summaries above, not the source of the command's later adjudication codes. The Task217 command itself supplies those codes. No Task216 packet is copied here as canonical truth and PR #116 is not modified.
