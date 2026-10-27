# Task 110 Foundation drift reproduction and repair

## Reproduction

- Fresh clone: `when-systems-catch-fire` at `main@0bbd31a82406e1922509aa052885d214b6efff85`.
- Command: `python3 tools/foundation/adjudicate_nonfunction_claims.py --check`
- Observed exit: `1`.
- Exact first-line failure: `NONFUNCTION_CLAIM_OUTPUT_DRIFT`.
- Drifted generated surfaces in the fresh clone: `claim-registry.jsonl`, `source-discovery.jsonl`, `adjudication-ledger.jsonl`, `evidence-lineage.jsonl`, `dependency-graph.jsonl`, `inference-risk-report.jsonl`, `unresolved-quarantine.jsonl`, `closure-summary.json`, `discovery-coverage.json`, `claim-inventory.csv`, and `docs/foundation/nonfunction-claim-adjudication-index.md`.
- The fresh-clone generator completed successfully in non-check mode and produced deterministic output. The changed counts were generated from the repository's tracked inputs; no OpenAlex request, task-110 adjudication result, or scientific claim was used as an input to this reproduction.

## Classification

`PRE_EXISTING_DETERMINISTIC_GENERATED_ARTIFACT_STALENESS_EXPOSED_ON_CURRENT_MAIN`, with a task-110 path-accounting extension after the new task-110 files entered the formal worktree. This is not a semantic change to claim meaning, mathematical/empirical maturity, M/E, disposition, or claim ceiling. The repair is limited to regenerating the generator-owned outputs at the current exact content head.

## Repair proof

- The same generator was run once in the task-110 formal worktree after the sealed OpenAlex first run and its outputs were staged only as generated artifacts.
- Immediate check: `python3 tools/foundation/adjudicate_nonfunction_claims.py --check` → `NONFUNCTION_CLAIM_GENERATION_DETERMINISTIC files=14`, exit `0`.
- The generated output is kept separate from the sealed OpenAlex raw and first-run adjudication evidence.
- No result-driven registry correction or OpenAlex rerun was performed.

## Full Foundation workflow repair

The complete `python3 tools/foundation/validate_foundation.py` was also run from
a fresh `main@0bbd31a82406e1922509aa052885d214b6efff85` checkout before the repair.
The same deterministic generated-artifact failures reproduced there:
`migrate_legacy.py --check`, the function census, and deep function adjudication.
They were not caused by OpenAlex results and did not change claim meaning, M/E or
disposition.

The authorized generator-only repair was first run before the final Evidence
Program validator repair. When commit `462a493b` added the deterministic
per-run threshold resolver and the exact preregistration-shaped result
emitter, those tracked Python files legitimately entered the repository-scoped
generator inputs. The Foundation checks therefore exposed one more generated
artifact drift; it was repaired by rerunning the same generators, not by
changing any claim or adjudication.

The final generator-only repair order was:

```text
python3 tools/foundation/build_function_asset_census.py
python3 tools/foundation/adjudicate_function_assets.py
python3 tools/foundation/adjudicate_nonfunction_claims.py
python3 tools/foundation/migrate_legacy.py
```

After the final migration regeneration, the checks passed at a byte-stable fixed
point: `migrate_legacy.py --check`, `build_function_asset_census.py --check`,
`adjudicate_function_assets.py --check`, `adjudicate_nonfunction_claims.py --check`,
`validate_nonfunction_claim_closure.py`, and the full foundation validator
`63/63 ALL_FOUNDATION_VALID`. The generated function census now accounts for the
task-110 tracked surfaces (6,989 discovered records at the final validator
head) as repository-scoped
classification; this is not an external-truth or maturity promotion.
