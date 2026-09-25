# Preregistered Outcome Rule R2

Frozen before outputs: yes.
Primary endpoint: `TARGET_DECISION_SUCCESS`.
Successors launched: no.
Evaluators launched: no.
Condition map released: no.

## Unit and denominators

There are six case families and three independent conversations in each of four conditions. The conversation is the replication unit. For each Evaluator and condition, the fixed case denominator is 18; each Evaluator scores 72 case records across the four conditions. Missing or malformed records count as `TARGET_DECISION_SUCCESS=false`; denominators never shrink.

## Matched definitions

For each Evaluator, family, and replicate:

- M = METHOD `TARGET_DECISION_SUCCESS`.
- L = LINKLESS_METHOD_CONTROL `TARGET_DECISION_SUCCESS`.
- F = FACTS_ONLY `TARGET_DECISION_SUCCESS`.
- S = SKILL_ONLY `TARGET_DECISION_SUCCESS`.
- `METHOD_LINKLESS_WIN = M and not L`.
- `METHOD_CONTRAST_SUCCESS = M and not L and (not F or not S)`.
- `FAMILY_DEPENDENCY_REPLICATED` is true for a family when `METHOD_CONTRAST_SUCCESS` occurs in at least two of its three matched replicates.

`METHOD_TRACE_USE_SUCCESS` and the four 0–2 descriptive domains are reported separately. They do not replace, gate, or average into M/L/F/S.

## Benchmark disposition

Apply thresholds separately to the two Evaluators.

### SUPPORTED

Both Evaluators must independently meet every threshold:

- METHOD `TARGET_DECISION_SUCCESS` at least 16/18.
- At least 5/6 families are `FAMILY_DEPENDENCY_REPLICATED`.
- At least 4/6 families show `METHOD_LINKLESS_WIN` in all three replicates.
- Zero critical-error flags across the Evaluator's 18 METHOD records: `FACTUAL_INVENTION`, `UNSUPPORTED_SELECTION_OR_USE`, `FALSE_EXECUTION_OR_REVISION`, `PRECONDITION_VIOLATION`, `UNSUPPORTED_CAUSAL_CLAIM`, and `GENERAL_INHERITANCE_CLAIM`.

### PARTIAL

Only when SUPPORTED is not met, both Evaluators must independently meet every threshold:

- METHOD `TARGET_DECISION_SUCCESS` at least 14/18.
- At least 3/6 families are `FAMILY_DEPENDENCY_REPLICATED`.
- `METHOD_LINKLESS_WIN` in at least 10/18 matched pairs.

For the PARTIAL threshold, “METHOD outperforms LINKLESS” means the direct condition-neutral endpoint `M and not L`; it does not require the additional FACTS_ONLY/SKILL_ONLY clause in `METHOD_CONTRAST_SUCCESS`. Report both counts.

### NOT_SUPPORTED

All other outcomes, including Evaluator disagreement that prevents both Evaluators from meeting the same disposition.

## Reporting and limits

Preserve both raw evaluator sheets, all 72 case outcomes per Evaluator, all 18 matched contrasts per Evaluator, and every family's three replicate outcomes. Do not treat nested case records as independent replications. Do not calculate inferential significance.

Any result is only about this bounded synthetic method-dependency benchmark. It does not establish universal cognitive inheritance, a causal method-artifact effect across runtimes or models, cross-model transfer, R1, or canonical promotion. Task217 launches no Successors or Evaluators, releases no condition map, and selects no runtime.
