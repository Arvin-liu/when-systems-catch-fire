# 080 Full Semantic Adjudication Report

- status: `PARTIAL_RESUMABLE_SOURCE_TEXT_ADJUDICATION`
- model_class: `GPT-5.4-equivalent`
- branch: `records/ignition-080-full-semantic-adjudication-20260713`
- base_head: `5d28eb5c5654e9acc78ef206f2923b23db66f28f`
- fixed_queue_total: `617`
- newly_completed_this_run: `25`
- cumulative_verified_registry: `30/622`
- remaining_pending: `592`
- highest_model_escalations: `2`

## Batch 1

- completed_batch: `1`
- ids: `MF1, MF2, MF3, MF4, MF5, A1, A2, A3, A4, A5, A6, A7, A8, A9, T1, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12`
- type_counts: `{'FORMAL_PROPOSITION': 2, 'MECHANISM_MODEL': 3, 'NATURAL_LANGUAGE_CANDIDATE': 5, 'OPTIMIZATION_PROBLEM': 1, 'PREDICATE': 7, 'PROBABILISTIC_MODEL': 1, 'RELATION': 3, 'STATE_TRANSITION': 3}`
- claim_counts: `{'ALGORITHMIC_CLAIM': 2, 'DEFINITION': 12, 'EXPLANATORY_HYPOTHESIS': 6, 'MATHEMATICAL_PROPOSITION': 3, 'STRUCTURAL_ANALOGY': 2}`
- logic_risk_count: `19`
- formalization_incomplete_count: `25`

## Resume

- next_pending_stable_id: `T13`
- next_pending_batch: `2`
- only resume from queue rows with `PENDING` or `IN_PROGRESS_STALE`
- do not recount any reviewed object whose `legacy_blob_sha` is unchanged
- if a source blob changes, append a new versioned adjudication row and mark the previous one superseded
