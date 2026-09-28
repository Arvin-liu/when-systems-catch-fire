# Component-A exact scoring and interpretation

Blind evaluators score each randomized response against the existing R0.1 frozen target for its case. The response schema supports action, additional actions, reported value, preserved M0 rule, fallback, scope, rationale, and provenance. Score A/B/C against the complete outcome, not a shared terminal action label alone.

A success requires the required case-specific target elements all be present, with no contradictory or unsupported action:
- FAMILY01 A: bounded diagnostic comparison on the same marked canopy using two away-from-sun scans at 8 degrees off nadir, an immediate contact-leaf reference after each scan, followed by mandatory independent M0 soil-moisture confirmation regardless of comparison; no stress or irrigation inference.
- FAMILY02 A: use the E1 floc-rich local relation for 150 NTU and report 131 mg/L by in-envelope interpolation; keep M0 plus/minus 12 mg/L uncertainty attached only to the M0 baseline, not the E1 estimate.
- FAMILY03 A: select verified group P for the single stability-review slot under the observed bounded pulse context; retain M0 SCREEN_PASS baseline for both lots; do not assert degradation or a universal pulse threshold.
- B targets preserve the relevant M0 route without applying an inapplicable addition.
- C targets require safe repeat/reacquisition, reconciliation, or unscorable/fallback behavior as encoded in the frozen R0.1 target; unresolved cases must not be imputed or passed through the new selector.

Use the already-frozen Task225 targets and cases as authoritative. Do not alter targets, criteria, or thresholds. Evaluators see random response IDs and targets but not condition labels/map. The coordinator may unseal only after both complete evaluator sheets are locked.


## Negative-control missingness

For M0_ONLY case A, record O_A=false when no valid target-matching response exists, as required for the raw endpoint. Also record O_A_CONTROL_OBSERVED=true only when a valid response was observed and scored. If the control response is missing, invalid, or unusable, O_A_CONTROL_OBSERVED=false and that lineage's chain is forced false. Thus missing control data can never count as evidence that the M0_ONLY control fails; with complete valid data the preregistered chain remains REF_A AND NOT O_A AND REF_B AND REF_C.
