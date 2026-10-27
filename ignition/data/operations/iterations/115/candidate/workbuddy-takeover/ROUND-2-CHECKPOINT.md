# Round 2 Checkpoint — Serial, Crash-Resumable Queue Runtime

**Round:** 2 / 7
**Parent (frozen Qwen Round 0):** `f4fe6faded65c16c98230ad34ca17e4374d59613`
**Round 2 deliverable commit:** `3d88af6a3323f6c27468e15a027d9909403debb8`
**Branch:** `workbuddy/task115-deep-research-queue-round1-7-takeover-r1-20260804`

## What Round 2 produced

A deterministic outer queue that invokes **one active research episode by
default**. It consumes the Round 1 record schemas but contains **no
episode-execution logic** (that is Round 3).

### `tools/deep_research/queue_runtime.py`
Pure functions + a `SerialQueue` convenience wrapper:

- **Ranking** — `rank_score` is a pure, inspectable function: benefit factors
  (materiality, expected_information_gain, tractability, access, freshness,
  diversity) minus penalty factors (cost, risk). Reads factors from the nested
  `topic_candidate` when given a queue item. `rank_candidates` sorts by score
  desc, tie-break by `queue_item_id` asc → fully deterministic.
- **Selector** — `select_next` picks the top gate-passing candidate. An optional
  `model_proposal` may reorder among equally-passing candidates but **cannot
  override a hard gate** (`passes_selection_gate`: BLOCKED/SKIPPED/COMPLETED and
  unexpired leases held by another owner are never selectable). Claiming a lease
  for the owner transitions the item to `ACTIVE`.
- **Lease** — `claim_lease` is idempotent for the same owner (refresh, stable
  `claim_id`), blocks a second distinct owner on an unexpired lease (duplicate
  prevention), and allows takeover once expired. `release_lease` clears.
- **Crash recovery** — `recover` returns ACTIVE items with a missing/expired
  lease to `QUEUED`, **preserving `checkpoint_commit`** so an episode resumes
  rather than restarts blind.
- **Ingestion** — `ingest_result` marks the matching item `COMPLETED`, records
  its per-episode checkpoint identity (`machine_trace_ref`/`report_ref`), and
  **never stops the queue**.
- **Campaign stopping** — `should_stop` enforces all 7 independent conditions:
  `OWNER_STOP`, `DEADLINE`, `MAX_EPISODES`, `BUDGET`, `QUEUE_EMPTY` (only when
  `queue_empty_stops` is set), `SAFETY_BLOCKER`, `LOW_INFORMATION`. A long
  report, many URLs, or an executor `success` are **absent** from the stop
  logic — they can never stop the queue.

### Round 1 schema correction (carried in this round)
`research-campaign` `stop_conditions.budget` was mistyped as `object`; it is now
`number` (token/money/credit budget). Regenerated; Round 1 canonicalness test
still passes.

### Tests (`tests/test_deep_research_round2.py`) — 24 tests, all PASS
- Ranking determinism + tie-break.
- Selector picks highest; respects hard gate (BLOCKED); model proposal cannot
  override gate (lease held by other); model proposal reorders equal scores.
- Lease idempotency (refresh, stable id); duplicate prevention (other owner
  blocked); expiry allows takeover; release.
- Crash recovery → QUEUED, preserves checkpoint; leaves BLOCKED alone.
- Ingestion completes + records checkpoint; **long report / 200 URLs /
  success never stops** and queue continues to next pending item.
- Every stop type: owner, deadline, max-episodes, budget, queue-empty,
  safety-blocker, low-information; and no-stop-when-conditions-absent.

## Test results
- `tests/test_deep_research_round1.py`: **19/19 PASS**
- `tests/test_deep_research_round2.py`: **24/24 PASS**
- `tests/test_research_os.py`: ALL CORE TESTS PASSED
- `tests/test_research_os_checkpoint_c.py`: ALL CHECKPOINT C TESTS PASSED
- `tests/test_research_os_resumability.py`: ALL RESUMABILITY/REPLAY TESTS PASSED

## Next
Round 3 — inner research loop, tool adapters, and CLI/API invocation surface.
