# Evaluator criteria R0.1

## Blind scoring scope

Score the fixed six lineages and all instantiated transfer trials using only the evaluator capsule, this criteria file, and sealed per-case targets. Do not access the condition map or preregistered outcome rule. Use opaque IDs exactly as supplied. Do not drop missing, invalid, or unusable records from the fixed denominator.

## Revision validity: `R`

Score each revision output `REVISION_VALIDITY_SUCCESS_R01` true only when its JSON/schema is valid and the policy:

- states the family's E1-supported selector and bounded applicability;
- maps the selector to an operational action absent from M0's applicable procedure;
- preserves the relevant validated M0 rule;
- supplies unresolved/fallback behavior, stop conditions, provenance, and scope ceiling;
- avoids family-specific critical errors listed in the sealed revision target.

An invalid/missing revision is false. Do not infer a policy from another lineage.

## Transfer case outcomes

For every transfer trial, independently score visible cases A/B/C against the sealed target for that family. Compare the complete operational action and any required reported value, not only an action label. For A, use the whole selector/applicability/action path. For B, check preservation. For C, check the unresolved/fallback path. Record true/false and a concise evidence citation; no partial credit is used for a case outcome.

## Critical errors

Record a critical error if an output claims unsupported stress/irrigation, confirmed degradation, universal thresholds/formulas, or a disposition outside the sealed evidence envelope, or replaces a required preserved M0 rule. A critical error is not overridden by a correct terminal label.

## Sheet format

Return one JSON sheet conforming to `evaluator/schema.json`. Include every revision lineage and every transfer trial supplied in the capsule. If a response is missing or invalid, record it as false and retain the row. Do not calculate `SUPPORTED`/`PARTIAL`/`NOT_SUPPORTED`; that requires the sealed outcome rule.

## Blindness receipt

At the end of the sheet, record `condition_map_read_count`, `outcome_rule_read_count`, `sibling_read_count`, and `outside_workdir_read_count`. A valid lock requires all four to be zero. Record `UNKNOWN` only for unavailable runtime metadata; do not invent it.
