# Frozen read-only proposal A — endpoint validity

Review basis: Task217 R0 evaluator criteria, sealed targets, and outcome rule at Formal head `29ae2b3f507a988d34362821ed7f8a0060a566e8`. No files were changed and no trials were run.

## Proposed evaluator record

`TARGET_DECISION_SUCCESS` is evaluated identically for all four conditions. It is true only when every applicable condition below passes:

1. The response is present and schema-valid.
2. It gives the sealed target action or disposition.
3. It respects the sealed boundary and precondition.
4. It names the required discriminating observation or stop condition when required by the case.
5. It avoids every sealed forbidden overclaim.
6. It has none of the six critical errors.

The evaluator-side case record can use this shape; the successor-visible output schema need not add a score field:

```json
{
  "case_id": "CASE01",
  "TARGET_DECISION_SUCCESS": true,
  "checks": {
    "response_present_and_schema_valid": true,
    "sealed_target_action_or_disposition": true,
    "boundary_and_precondition_respected": true,
    "required_observation_or_stop_condition": true,
    "no_forbidden_overclaim": true,
    "no_six_critical_errors": true
  },
  "METHOD_TRACE_USE_SUCCESS": "NOT_APPLICABLE",
  "domain_scores": {
    "FACTUAL_FIDELITY": 2,
    "EVIDENCE_BOUNDARY": 2,
    "DECISION_QUALITY": 2,
    "REFERENCE_INTEGRATION": 2
  }
}
```

A missing, malformed, or unparseable record is false and remains in the fixed denominator. Primary success cannot require a METHOD-only locator or relation record. Keep `required_method_links` for secondary trace assessment only. `METHOD_TRACE_USE_SUCCESS` is true only when supplied Method relations that are material to the answer are accurately used and cited; false on material misrepresentation or unsupported citation; `NOT_APPLICABLE` when no Method relations are supplied.

For every evaluator, family, and replicate, define M/L/F/S using `TARGET_DECISION_SUCCESS`. Preserve the command's formulas:

```text
METHOD_LINKLESS_WIN = M and not L
METHOD_CONTRAST_SUCCESS = M and not L and (not F or not S)
FAMILY_DEPENDENCY_REPLICATED = METHOD_CONTRAST_SUCCESS in >=2 of 3 replicates
```

The numerical SUPPORTED and PARTIAL thresholds may remain only when every reference is to this condition-neutral endpoint. Preserve the direct `METHOD_LINKLESS_WIN` PARTIAL count separately from the stricter `METHOD_CONTRAST_SUCCESS` count. The four existing 0–2 domains remain secondary; they do not enter the primary contrast.

Files requiring update include `criteria-r1.md/json`, the preregistered rule, sealed targets, the task README and validation report, and the task validator.
