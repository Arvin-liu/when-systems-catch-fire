# Target-blind reference policy validity criteria

Review each of the six policies independently. Use only that policy, its family's M0 and E1, and policy-schema.json. Do not open or infer from held-out A/B/C cases, targets, Task226 analysis, R7 responses or scores, or other policies while scoring. No repair is permitted.

For each policy record pass/fail and concise evidence for:
1. schema validity and operational completeness;
2. evidence grounding: every new rule and value is supported by supplied E1 source locators;
3. operational selector: each rule references declared observable inputs and a declared action;
4. bounded applicability: each licensed region copies exactly one linked selector rule's conditions; excluded regions route to the unconditional fallback, and licensed scope claims refer only to licensed regions;
5. preservation safety: the M0 action is explicitly preserved and not retired or improperly conditionalized; `unconditional` and `selector_miss` have empty when lists, while `additive_coexistence` matches a selector condition set;
6. explicit fallback and edge behavior, with stop outcomes for unresolved inputs;
7. no unsupported universalization or fabricated outcome;
8. provenance and scope ceiling.

A policy is USABLE only when both independent reviewers mark all eight dimensions pass and both conclude it is evidence-supported, operational, bounded, preservation-safe, edge-explicit, and free of unsupported universalization. Otherwise USABLE=false. Keep denominator six. Report raw judgments; do not reconcile and do not add an evaluator.
