# Task 110 — §7 Corrected Planner Rerun: Original (109) vs Corrected (110) Queue

> Rerun of the **frozen task-109 priority model** (`data/operations/iterations/109/priority_model.json`,
> weights unchanged) with the new generic completion-state reconciliation layer (§5) added.
> Differences below are caused **only** by lifecycle reconciliation, never by score manipulation.

## 1. Original task-109 recommendation (immutable historical artifact)

- Source: `data/operations/iterations/109/next_iteration_recommendation.md` + `ranked_queue.json`
- `recommended_next = C-01` (aggregate 73.20), `claim_id = SRC-REGISTRY-104-METADATA`
- `reserves = [CF-apple_gravity_failure, CF-cross_domain_synergy_risk]`
- Defect: C-01's obligation was **already completed by task 103** (`SUPPORTED_WITHIN_SCOPE`).
  The planner had no lifecycle awareness, so it re-recommended completed work.

## 2. Corrected task-110 recommendation (this run, `110/corrected_queue.json`)

- `recommended_next = CF-apple_gravity_failure` (aggregate 67.90, IMPLEMENTATION_DEFECT)
- `reserves = [CF-cross_domain_synergy_risk, CF-technology_economic_growth_failure]`
- `prior_recommendation_invalidated = {recommended_next: C-01, state: COMPLETED_SUPPORTED, invalidated: true}`

### Lifecycle reclassification (excluded from active queue)

| candidate | claim_id | 109 portfolio `selection_decision` | reconciled lifecycle_state | authoritative completion |
|-----------|----------|-------------------------------------|----------------------------|--------------------------|
| C-01 | SRC-REGISTRY-104-METADATA | PRIMARY | **COMPLETED_SUPPORTED** (excluded) | task 103 `SUPPORTED_WITHIN_SCOPE` |
| C-04 | FUNCTION-OS-V02-CORRECTNESS | DEFERRED | **COMPLETED_SUPPORTED** (excluded) | task 105 `SUPPORTED_WITHIN_BOUNDED_DOMAIN` |
| C-03 | DOI-OPENALEX-CROSS-CHECK | RESERVE | UNASSESSED (eligible) | none — genuinely unfinished |

## 3. Is C-03 the highest eligible substantive evidence candidate? (contract §7 — honest answer)

- **No, not the single highest overall.** After reconciliation, the three highest-ranked
  eligible candidates are `CF-apple_gravity_failure`, `CF-cross_domain_synergy_risk`,
  `CF-technology_economic_growth_failure` (all IMPLEMENTATION_DEFECT, 67.90).
- **C-03 ranks 4th overall (67.50)**, but it is the **highest eligible CORE_CAPABILITY_VALIDATION
  (evidence-program) candidate** — i.e. the highest eligible *substantive external-evidence pilot*.
- The unchanged priority model and unchanged scores are preserved; only lifecycle state changed
  the active queue composition. The owner/controller explicitly authorized C-03 as task 110's
  substantive pilot (contract §8), independent of its numeric rank. This authorization is NOT
  based on the flawed task-109 top recommendation (which was C-01, now invalidated).

## 4. Deterministic reproducibility

- Rerun is byte-stable: `python3 tools/iteration_planner/planner.py` with `ITERATION_OUT_DIR=110`
  produces identical `110/ranked_queue.json` / `corrected_queue.json` (no RNG, no network, no git).
- Model weights identical to `109/priority_model.json` (no silent change).
- The original `109/` outputs are **not modified**; this diff is a new task-110 projection.

## 5. Corrected active-queue top-10 (post-reconciliation)

`CF-apple_gravity_failure, CF-cross_domain_synergy_risk, CF-technology_economic_growth_failure,
C-03, arn-gap-001, arn-gap-002, arn-gap-003, mcf-gap-001, mcf-gap-002, psd-gap-001`

(Full machine output: `110/ranked_queue.json`, `110/completion_registry.json`,
`110/completed_register.json`.)
