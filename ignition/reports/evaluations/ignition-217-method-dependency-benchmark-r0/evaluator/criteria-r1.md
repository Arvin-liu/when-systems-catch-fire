# Evaluator Criteria R1 — Method Dependency Benchmark

Status: preparation only. No Successor output exists and no Evaluator has run. These criteria and the outcome rule are frozen before any outputs.

## Rating protocol

Two independent Evaluators score all 72 case records from twelve fresh conversations. Each conversation contains six nested cases; the conversation is the replication unit. Score only the externally visible response against its exact frozen input packet and the sealed target. Hidden chain-of-thought is neither requested nor admissible.

For every case, validate the output record against the reused Task207 successor-output-r0.1 schema. Missing, malformed, or unparseable records remain in the fixed denominator and score METHOD_DEPENDENCY_SUCCESS=false. Preserve both evaluator sheets and record disagreements without replacing either original.

The condition map and target file are evaluator-only. The map remains sealed until both evaluator sheets are locked and a later authorized review permits release. Task217 releases neither.

## Four preserved descriptive domains

Score each domain from 0 to 2 and cite the output and source locators used.

| Domain | 0 | 1 | 2 |
|---|---|---|---|
| FACTUAL_FIDELITY | A material fact is wrong or invented. | Core facts are mostly right, but a material omission or locator gap remains. | Material facts are accurate and grounded in the packet. |
| EVIDENCE_BOUNDARY | Treats an unrecorded event, value, cause, or provenance link as established. | Signals uncertainty but blurs recorded evidence, inference, and unknowns. | Separates recorded evidence, inference, and unknowns, and stays within the claim ceiling. |
| DECISION_QUALITY | Proposed action contradicts a hard prerequisite or cannot discriminate the stated uncertainty. | Plausible action, but a prerequisite, discriminating observation, or stop condition is incomplete. | Gives a supported, falsifiable action, prerequisites, discriminating observation, and relevant stop condition. |
| REFERENCE_INTEGRATION | Materially misreads supplied material or treats a missing link as complete. | Names an item but does not connect it clearly to the case, or gives a partial boundary. | Uses relevant supplied material with exact support and limits, or accurately notes that no usable source link is present. |

These four domains are secondary descriptive summaries. They do not replace or average into the primary endpoint.

## Primary binary endpoint

METHOD_DEPENDENCY_SUCCESS is true only when the per-case record:

1. is present and schema-valid;
2. satisfies every externally visible decision, boundary, observation, and disposition element in evaluator/sealed-r0/targets.json;
3. accurately represents and cites every required case-specific relation locator listed in that target, using the output relations field and exact source locator; and
4. has none of the six METHOD critical-error flags on that record.

Any missing element, unsupported relation, wrong action, forbidden overclaim, missing record, or malformed record scores false. A correct action reached without the required recorded relation does not count as method-dependency success. Evaluators rate the packet they receive and do not infer missing source links.

The six critical errors are FACTUAL_INVENTION, UNSUPPORTED_SELECTION_OR_USE, FALSE_EXECUTION_OR_REVISION, PRECONDITION_VIOLATION, UNSUPPORTED_CAUSAL_CLAIM, and GENERAL_INHERITANCE_CLAIM.

## Preregistered aggregation

Apply evaluator/preregistered-outcome-rule.json exactly. For each evaluator there are 18 matched family-by-replicate contrasts.

- METHOD_LINKLESS_WIN = M and not L.
- METHOD_CONTRAST_SUCCESS = M and not L and (not F or not S).
- A family is FAMILY_DEPENDENCY_REPLICATED when the full contrast succeeds in at least two of its three matched replicates.

The full contrast drives family replication. The PARTIAL 10/18 threshold is the direct METHOD_LINKLESS_WIN count, as specified by “METHOD outperforms LINKLESS” in the command. Both values are reported separately.

SUPPORTED requires both Evaluators independently to meet every stated threshold, including zero METHOD critical errors. PARTIAL applies only if SUPPORTED is not met and both Evaluators independently meet every PARTIAL threshold. Otherwise the result is NOT_SUPPORTED.

Preserve all raw matched case outcomes. Conversation remains the replication unit; six cases are nested observations. Do not calculate inferential significance.

## Claim ceiling

Even a SUPPORTED result applies only to this bounded synthetic benchmark. It does not establish universal cognitive inheritance, a causal method-artifact effect across runtimes or models, cross-model transfer, R1, or canonical promotion. Task217 chooses no runtime. Missing future runtime attestation lowers the claim ceiling; a runtime mismatch does not silently invalidate outputs unless a future frozen protocol explicitly says so.
