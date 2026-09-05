# IGNITION-20260905-156 result

Result status: `RESEARCH_COMPLETE / BINDING_CHALLENGER_SUPPORTED_AS_RESEARCH_INVARIANT_CANDIDATE / DRAFT_PR_PENDING / NON_CURRENT`

Task156 executed a frozen prospective synthetic-but-repository-shaped cross-contract experiment from the exact Task155 head `9bed8e42ee824fc0c0a10717b6163fe7052423e8`. The final freeze commit is `4321dcb2f9f434ed7936d5cb5c8648089eeb4964`; the corpus has 48 pairs / 96 instances across F1–F6, 36 calibration pairs and 12 holdout pairs. M0, M3, M3R and M4B were scored twice from independent clean clones before unblind; both 384-row score outputs have SHA-256 `c53ed43394aa7ece8fd138b1e272b745b3e59a4a908a16b17c4ce37a22db96e3` and do not load the answer key.

Final holdout result: M3 has 6 incremental detections beyond M0; M3R has 8 across all six families and gains 2 over M3 without adding a fourth edge; M4B adds 4 over M3R across `lifecycle_epoch`, `claim_action_object` and `approval_action_object`, with zero additional matched-control false positives. The largest M3R historical-lineage-inspired family share is 0.25. Exact actionability is 1.0; invalid fixtures and matched-control false positives are 0.

The final unblind produced 808 metamorphic checks with 0 violations and 75 counterfactual-minimality rows. Every counterfactual is `REQUIRES_NEW_LOCAL_PREDICATE / REVIEW_ONLY`; no local contract was mutated. `SIGNATURE_WITHOUT_CONTESTABILITY`, `BUDGET_AS_HARM_LICENSE` and `ABSTENTION_AS_AVOIDANCE` remain insufficiently discriminated; synthetic F1/F2 support does not upgrade CC-012/CC-026 into historical failure classes.

The bounded candidate is existing-field binding over `(object_id, version, scope, lifecycle_epoch)` plus existing claim/approval references. It is a replaceable research review lens only. No production validator, gate, runtime, authority, capability, lifecycle, schema, registry, canonical layer, Current status, Owner acceptance, external truth or epistemic acceptance was established. Known stale `1111/instructions/CURRENT.md` and `1111/relay/current` pointers were preserved unchanged.

Two invalidated freeze attempts and their evidence are retained under `data/research/cross-contract-prospective-fixtures-2026-09-05/invalidated-freeze-*`; see the task report for exact amendment history and validation evidence. Formal PR and independent 1111 receipt evidence are recorded separately once pushed, and both must remain Draft.
