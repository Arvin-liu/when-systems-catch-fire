# Missingness and retry rules R0

- One replacement attempt is permitted only when a logged network/API/tool failure occurs before any semantic model response exists.
- The failed transport attempt and replacement metadata are both retained.
- No retry is permitted after a refusal, schema-invalid output, malformed semantic output, wrong or dangling policy trace, target failure, or evaluator omission.
- Every missing, invalid, refused, or unusable session remains in the fixed denominator and scores false for the affected raw endpoint.
- `M0_ONLY_CONTROL_OBSERVED_i=true` only when the M0-only session produced a semantic response whose common envelope parses and contains exactly A, B, and C. Missing or invalid control output never supplies a successful negative control.
- Missing or invalid evaluator rows score false for that evaluator and target and remain in the raw sheet.
- M0_PLUS_E1 is descriptive only and does not enter the main thresholds.
