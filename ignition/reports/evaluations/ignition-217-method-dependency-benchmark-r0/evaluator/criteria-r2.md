# Evaluator Criteria R2 — Method Dependency Benchmark

Status: repaired preparation freeze. No Successor output exists and no Evaluator has run. Score only the externally visible response against the same sealed case target in all four conditions. Do not inspect hidden reasoning.

## Rating protocol

Two independent Evaluators score all 72 case records from twelve fresh conversations. Each conversation contains six nested cases; the conversation is the replication unit. Validate each returned record against the reused `successor-output-r0.1` schema. A missing, malformed, or unparseable record remains in the fixed denominator and receives `TARGET_DECISION_SUCCESS=false`.

The target decision is condition-neutral. Evaluators do not require a source locator or relation locator that is available only in METHOD. The condition map and targets are evaluator-only and remain sealed; Task217 releases neither.

## Primary endpoint — TARGET_DECISION_SUCCESS

Score `TARGET_DECISION_SUCCESS` identically in FACTS_ONLY, SKILL_ONLY, METHOD, and LINKLESS_METHOD_CONTROL. It is true if and only if all six checks pass:

1. A response is present and schema-valid.
2. Its externally visible action or disposition matches the sealed target for that case.
3. It respects the sealed boundary and precondition.
4. It names the required discriminating observation or stop condition when the case requires one.
5. It avoids every sealed forbidden overclaim.
6. It has none of the six critical errors: `FACTUAL_INVENTION`, `UNSUPPORTED_SELECTION_OR_USE`, `FALSE_EXECUTION_OR_REVISION`, `PRECONDITION_VIOLATION`, `UNSUPPORTED_CAUSAL_CLAIM`, or `GENERAL_INHERITANCE_CLAIM`.

The evaluator records each check separately, then computes the primary endpoint as their conjunction. Correct visible decisions can score true without citing any METHOD relation. A missing, malformed, or unparseable record scores false without changing the denominator. A source locator, `R##` relation locator, or relation-citation count never gates this primary endpoint.

## Secondary endpoint — METHOD_TRACE_USE_SUCCESS

Record `METHOD_TRACE_USE_SUCCESS` separately. When the assigned packet contains Method relations, score true only when the response accurately uses and cites every supplied relation designated as material by the sealed R2 target, and does not cite or rely on a removed or absent relation. Score false for an omission or misrepresentation of a designated supplied relation, or for reliance on an absent relation. Use `NOT_APPLICABLE` when the packet contains no Method relations. This endpoint is descriptive and never changes `TARGET_DECISION_SUCCESS` or its contrasts.

## Four preserved descriptive domains

Score each domain from 0 to 2 and cite the response/source records used. These scores are secondary and do not enter the primary endpoint.

| Domain | 0 | 1 | 2 |
|---|---|---|---|
| FACTUAL_FIDELITY | A material fact is wrong or invented. | Core facts are mostly right, but a material omission or locator gap remains. | Material facts are accurate and grounded in the packet. |
| EVIDENCE_BOUNDARY | Treats an unrecorded event, value, cause, or provenance link as established. | Signals uncertainty but blurs recorded evidence, inference, and unknowns. | Separates recorded evidence, inference, and unknowns, and stays within the claim ceiling. |
| DECISION_QUALITY | Proposed action contradicts a hard prerequisite or cannot discriminate the stated uncertainty. | Plausible action, but a prerequisite, discriminating observation, or stop condition is incomplete. | Gives a supported, falsifiable action, prerequisites, discriminating observation, and relevant stop condition. |
| REFERENCE_INTEGRATION | Materially misreads supplied material or treats a missing link as complete. | Names an item but does not connect it clearly to the case, or gives a partial boundary. | Uses relevant supplied material with exact support and limits, or accurately notes that no usable source link is present. |

## Preregistered aggregation

Apply `preregistered-outcome-rule-r2.json` exactly. For each evaluator, there are 18 matched family-by-replicate contrasts. Let M/L/F/S denote `TARGET_DECISION_SUCCESS` for METHOD / LINKLESS_METHOD_CONTROL / FACTS_ONLY / SKILL_ONLY respectively.

- `METHOD_LINKLESS_WIN = M and not L`.
- `METHOD_CONTRAST_SUCCESS = M and not L and (not F or not S)`.
- A family is `FAMILY_DEPENDENCY_REPLICATED` when the full contrast succeeds in at least two of its three matched replicates.

The R0 numerical thresholds are retained only with the endpoint switch above. The PARTIAL 10/18 threshold is the direct `METHOD_LINKLESS_WIN` count; it does not require the added FACTS_ONLY/SKILL_ONLY clause. Report both counts. Apply dispositions separately to each Evaluator, preserve all raw matched outcomes, and do not calculate inferential significance. Six cases are nested within each conversation and are not six independent replications.

## Claim ceiling

Even a SUPPORTED result applies only to this bounded synthetic benchmark. It does not establish universal cognitive inheritance, a causal method-artifact effect across runtimes or models, cross-model transfer, R1, or canonical promotion. Task217 chooses no runtime. Missing future runtime attestation lowers the claim ceiling; a runtime mismatch does not silently invalidate outputs unless a future frozen protocol explicitly says so.
