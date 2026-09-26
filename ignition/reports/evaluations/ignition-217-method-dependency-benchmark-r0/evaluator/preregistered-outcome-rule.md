# Preregistered Outcome Rule R0

Frozen before outputs: yes.
Successors launched: no.
Evaluators launched: no.
Condition map released: no.

## Unit and denominators

There are six case families and three conversations in each of four conditions. Each conversation answers all six families. The conversation is the replication unit. For each independent Evaluator, there are 18 matched family-by-replicate contrasts. Missing or malformed case records count as METHOD_DEPENDENCY_SUCCESS=false; denominators never shrink.

## Per-record and matched definitions

For a given evaluator, family, and replicate:

- M = the METHOD condition METHOD_DEPENDENCY_SUCCESS for the matched case family and replicate.
- L = the LINKLESS_METHOD_CONTROL condition METHOD_DEPENDENCY_SUCCESS for the matched case family and replicate.
- F = the FACTS_ONLY condition METHOD_DEPENDENCY_SUCCESS for the matched case family and replicate.
- S = the SKILL_ONLY condition METHOD_DEPENDENCY_SUCCESS for the matched case family and replicate.
- METHOD_LINKLESS_WIN = M and not L.
- METHOD_CONTRAST_SUCCESS = M and not L and (not F or not S).
- FAMILY_DEPENDENCY_REPLICATED = true for a family when METHOD_CONTRAST_SUCCESS occurs in at least two of its three matched replicates.

## Benchmark disposition

Apply thresholds separately to each of the two Evaluators.

### SUPPORTED

Both Evaluators must independently find all of the following:

- METHOD success at least 16/18.
- At least 5/6 families are FAMILY_DEPENDENCY_REPLICATED.
- At least 4/6 families show METHOD_LINKLESS_WIN in all three replicates.
- Zero METHOD critical-error flags across the 18 METHOD records: FACTUAL_INVENTION, UNSUPPORTED_SELECTION_OR_USE, FALSE_EXECUTION_OR_REVISION, PRECONDITION_VIOLATION, UNSUPPORTED_CAUSAL_CLAIM, GENERAL_INHERITANCE_CLAIM.

### PARTIAL

Only when SUPPORTED is not met, both Evaluators must independently find all of the following:

- METHOD success at least 14/18.
- At least 3/6 families are FAMILY_DEPENDENCY_REPLICATED.
- METHOD_LINKLESS_WIN in at least 10/18 matched pairs.

For this PARTIAL threshold, “METHOD outperforms LINKLESS” means the direct matched endpoint M and not L. It does not require the additional FACTS_ONLY/SKILL_ONLY clause in METHOD_CONTRAST_SUCCESS. Report both counts.

### NOT_SUPPORTED

All other outcomes, including cases where the two Evaluators fall on different disposition thresholds.

## Reporting and limits

Preserve both raw evaluator sheets, all 72 case outcomes per Evaluator, all 18 matched contrasts per Evaluator, and each family’s three replicate outcomes. Do not treat nested case records as independent replicates. Report descriptive raw counts and calculate no inferential significance test.

Any result is only about this bounded synthetic method-dependency benchmark. It does not establish universal cognitive inheritance, a causal method-artifact effect across runtimes or models, cross-model transfer, R1, or canonical promotion. Task217 launches no Successors or Evaluators, releases no condition map, and selects no runtime.
