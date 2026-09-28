# Blind Component-A transfer evaluator criteria

Each evaluator independently scores the same 18 randomized opaque response packets. Use only the visible case bytes, corresponding frozen target, this scoring guide, and sanitized response. Do not access M0/E1/reference-policy materials, condition labels, input manifests, condition map, lineage groupings, sibling responses, Task226 outcomes, or the other evaluator's sheet.

For each response:
- Mark valid_response false if the supplied JSON was missing, unparsable, or failed the frozen response schema. Invalid responses receive false for A, B, and C.
- Independently mark A, B, and C target success based on the full frozen target details, not shared terminal action names.
- Record the concrete missing or contradictory requirement for each false score.
- Record a critical error only for unsupported global claims, retiring a required M0 baseline, imputing an unresolved required input, or contradicting an explicit case fact. Critical-error flags are descriptive and do not change the preregistered Component-A thresholds.
- Do not infer a condition, assign an ID to a condition, compare responses across trials, or reconcile with another evaluator.

The A target requires the full family-specific method/value/action. For FAMILY01 it includes both same-canopy away-sun 8-degree scans, immediate contact-leaf check after each, followed by mandatory M0 soil-moisture confirmation regardless. For FAMILY02 it includes 131 mg/L from the bounded in-envelope floc-rich relation; M0's ±12 mg/L uncertainty does not attach to that estimate. For FAMILY03 it selects verified group P for the one review slot while retaining M0 SCREEN_PASS for both and making no degradation or universal-threshold claim. B preserves its applicable M0 route. C routes unresolved or out-of-scope inputs to the frozen safe fallback and does not impute.

Return a complete 18-row JSON sheet with locked=true and raw per-case scores. Do not score dispositions, component thresholds, or aggregate outcomes.
