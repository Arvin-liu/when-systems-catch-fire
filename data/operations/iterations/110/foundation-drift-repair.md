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
