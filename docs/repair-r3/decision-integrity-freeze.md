# repair-r3 Freeze Summary — decision_integrity (CP2)

- **Capability:** decision_integrity
- **R3 branch:** `repair-r3/decision-integrity-r3-semantic-evaluator`
- **R3 frozen head (this commit):** see annotated tag `archive/decision-integrity-repair-r3-frozen-head`
- **Parent r3 head merged:** `archive/symbolic-sphere-repair-r3-frozen-head` (01c84147) via `--no-ff` merge 294d6695
- **R2 start head:** 1a51d1b3fd1bab4eb1c80a7429e0b629bcae69a9

## Defect closed
RB09-CALLER-ASSERTED-SEMANTICS — the shared capability gate no longer trusts
caller-asserted `facts[rid]` / `rule_assertions[rid].status`. Every rule predicate
is recomputed by a per-capability evaluator (`evaluate_decision_integrity`) from
record `value` fields + authoritative Git-resolved evidence bytes.

## R0–R3 recap
- R0(repro): `tests/repro_rb09_capability.py` + `tests/repro_rb09_decision_integrity_r2_evidence.txt` demonstrate the r2 engine accepted a schema-valid but semantically-false bundle.
- R1(impl): wired `CONFIG["evaluator"] = evaluate_decision_integrity` and `CONFIG["evidence_matrix"] = get_matrix("decision_integrity")` into `tools/decision/validate_decision_integrity_gate.py`; added `reference_integrity_check` + `run()` wrapper.
- R2(test): `tests/test_r3_decision_integrity.py` — positive pilot exits 0; semantically-false (flipped value) exits 30 (EVALUATOR_RULE_FAILED, 30+index); single-blob laundering exits non-zero.
- R3(sync): removed ad-hoc `data/operations/iterations/DECISION-INTEGRITY-REPAIR-R2.json` (schema violation), so `validate_iteration_sync.py` passes.

## Regression / foundation validation
- `tools/validate_iteration_sync.py` -> **exit 0** (repository_synchronization_closure=PASS, implementation_consistency=PASS) at this frozen head.
- Evaluator layer contract: MISSING_EVALUATOR->exit1, EVALUATOR_COVERAGE_INVALID->exit6, EVALUATOR_RULE_FAILED->exit30+index, ResolvedEvidence + register_evaluator present.

## Hard prohibitions honored
No push, no PR, no force-push/rebase/amend/squash, no merge into main or any
repair-r1/repair-r2 branch, no modification of r1/r2 frozen heads or tags, no Q33
code touched, single builder.
