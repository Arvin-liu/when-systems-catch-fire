# 080 Resume Instructions

- branch: `records/ignition-080-full-semantic-adjudication-20260713`
- status: `PARTIAL_RESUMABLE_SOURCE_TEXT_ADJUDICATION`
- next_pending_stable_id: `T13`
- next_pending_batch: `2`
- queue_file: `data/foundation/work-queues/080-semantic-review-queue.jsonl`
- adjudication_file: `data/foundation/adjudications/080-source-text-adjudications.jsonl`
- escalation_file: `data/foundation/escalations/080-highest-model-queue.jsonl`
- run_state: `data/foundation/adjudications/080-run-state.json`
- resume rule: process only `PENDING` or `IN_PROGRESS_STALE`; never overwrite an unchanged accepted review
