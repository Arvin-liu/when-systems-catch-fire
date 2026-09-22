# Independent evaluator final report (Step06)

This report summarises Step02-05. It does not change the Step04 predeclared disposition.

## 1. Evidence validity

Six of six bundles passed the Step00 mechanical gate (checkpoint `43c3f07c64abc31529b791c562560e02bb345981`): nearest git root, branch, exact HEAD, no successor commit, remote successor branch absent, response/read-manifest/freeze hashes, 3 JSONL records with R0.1 schema, case order, read-manifest == packet read_allowlist exact set, every pin equal to exact-base bytes, no unlisted / cross-condition / evaluator-sealed read. Evidence: VALID.

## 2. Six conversation boundary results

| replicate | condition | boundary |
|---|---|---|
| FACTS_A | FACTS_ONLY | BOUNDARY_PRESERVED (3/3 cases) |
| FACTS_B | FACTS_ONLY | BOUNDARY_PRESERVED (3/3 cases) |
| METHOD_A | METHOD_TRACE | BOUNDARY_PRESERVED (3/3 cases) |
| METHOD_B | METHOD_TRACE | BOUNDARY_PRESERVED (3/3 cases) |
| BROKEN_A | BROKEN_METHOD_TRACE_CONTROL | BOUNDARY_PRESERVED (3/3 cases) |
| BROKEN_B | BROKEN_METHOD_TRACE_CONTROL | BOUNDARY_PRESERVED (3/3 cases) |

## 3. Per-case exceptions

0 case-level failures. 11 advisory annotations, none of which breaks a sealed pass rule:

- A1 FACTS_A/REPL-CASE-03: METHOD-typed object describes the case's own fold command, not a supplied method lineage
- A2 FACTS_B/REPL-CASE-03: interpretive relation typed SOURCE_REPORTED with the source gap retained in unknowns
- A3 METHOD_A and METHOD_B (all cases): trace SHA carried by the packet read-manifest (verified equal) rather than inline; the reused R0.1 schema has no per-locator SHA field and a second schema is forbidden
- A4 METHOD_B/REPL-CASE-02: reset/re-queue observation not enumerated
- A5 BROKEN_A (all cases): candidate typed METHOD/OBSERVED rather than SOURCE_REPORTED
- A6 BROKEN_B (all cases): candidate and excerpt outcome typed OBSERVED with excerpt locators

## 4. A/B consistency

Both replicates preserve the intended condition boundary in all three conditions.
No replicate was excluded and no outcome-adaptive reinterpretation was used.

## 5. Order sensitivity

A order (03,01,02) differs from B order (01,02,03) and was frozen before execution. No boundary failure appears in only one order. Order is perfectly confounded with replicate letter, so it is reported descriptively and is not a randomized control.

## 6. Template-imitation findings

The candidate identifier is repeated across method cases, but each case supplies a case-bound rationale and trace locator. Wording repetition alone was not accepted as source-bound method use.

## 7. Negative controls

12/12 NOT_TRIGGERED. This does not upgrade general cognitive inheritance.

## 8. Replicated disposition

**REPLICATED_METHOD_USE_SIGNAL_SUPPORTED** (unchanged by this report).

## 9. Execution-environment attestation limitation

`MODEL_CONFIGURATION_ATTESTATION: COMMAND_ASSIGNED_NOT_INDEPENDENTLY_VERIFIED`. The trial remains valid; 'same-model' wording is limited to assigned configuration.

## 10. Fixed epistemic ceiling

```
REPLICATED_CONDITION_ASSOCIATION_ONLY_NOT_CAUSAL_EFFECT
GENERAL_COGNITIVE_INHERITANCE_NOT_ESTABLISHED
R1_NOT_AUTHORIZED_BY_EVALUATOR
CROSS_MODEL_TRANSFER_NOT_RUN
OWNER_GPT_ADJUDICATION_NOT_RUN
NO_CANONICAL_PROMOTION
```

The evaluator does not perform Owner acceptance.