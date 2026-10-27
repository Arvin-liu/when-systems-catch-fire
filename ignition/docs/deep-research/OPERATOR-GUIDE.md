# Deep Research Capability — Operator & API Guide

Covers how to run, test, and integrate the deep-research capability
(`deep-research/0.1`). All commands run from the repository root.

## Prerequisites

- Python 3.13 (managed runtime tested).
- The capability modules live under `tools/`; tests live under `tests/`. The
  test files and `tools/deep_research/*.py` add `tools/` to `sys.path`
  automatically, so no install step is required.

## Generators (Round 1 & 5)

```bash
# Round 1 — 13 fail-closed schemas + 15 positive + 12 negative fixtures
python3 tools/deep_research/generate_schemas.py
python3 tools/deep_research/generate_fixtures.py
python3 tools/deep_research/generate_negative_fixtures.py

# Round 5 — 27 frozen anti-overfit fixtures (16 episode + 11 queue),
# self-validated against the live evaluator/queue runtime
python3 tools/deep_research/generate_round5_fixtures.py
#   -> tests/fixtures/deep_research/round5/*.json  (+ ROUND5_METRICS.json on test run)
```

## Queue smoke (Round 2)

```bash
python3 tools/deep_research/queue_runtime.py   # prints "queue_runtime.py smoke OK"
```

## Bounded pilot (Round 6)

```bash
python3 tools/deep_research/run_round6_pilot.py
#   -> data/operations/iterations/115/candidate/workbuddy-takeover/round6-trace/
#      episode.json, queue.json, PILOT-REPORT.json
```

## Test matrix

```bash
python3 tests/test_deep_research_round1.py   # 19
python3 tests/test_deep_research_round2.py   # 24
python3 tests/test_deep_research_round3.py   # 18
python3 tests/test_deep_research_round4.py   # 13
python3 tests/test_deep_research_round5.py   # 4 methods / 27 subTests
python3 tests/test_deep_research_round6.py   # 2

# Baseline Research OS kernel suites (custom runner)
python3 tests/test_research_os.py
python3 tests/test_research_os_checkpoint_c.py
python3 tests/test_research_os_resumability.py
```

## CLI surface (`tools/deep_research/cli.py`)

| Subcommand | Purpose |
|------------|---------|
| `inspect` | inspect a serialized episode |
| `pause` / `resume` | pause / resume an episode (→ `PAUSED_RESUMABLE`) |
| `replay` | replay an episode event log (transparent audit) |
| `claim-add` | add a candidate claim (closes a PR #190 gap) |
| `obligation-add` / `obligation-set` | add / set an evidence obligation status |
| `episode` | run one episode from a question |
| `queue-step` | run one queue step (select → run → ingest) |
| `run-until-stop` | run the queue until a campaign stop condition fires |

## API (programmatic)

**`queue_runtime.SerialQueue`** (Round 2)
- `add_candidate(candidate, queue_item_id=...)` → queue item
- `select_next(now_iso=..., model_proposal=..., ttl_seconds=...)` → next runnable
  item (claims a lease for `self.owner`, marks `ACTIVE`); a model proposal can
  reorder but cannot override a hard gate (unexpired lease held by another, or
  non-runnable status)
- `recover(now_iso=...)` → returns ACTIVE items with expired/missing lease to
  `QUEUED`, preserving `checkpoint_commit`
- `ingest_result(result, now_iso=...)` → marks the item `COMPLETED`; **never**
  stops the queue
- `should_stop(now_iso=...)` → `(should_stop, reason)` over the 7 campaign
  conditions

**`episode_loop.EpisodeController`** (Round 3–4)
- `freeze_scope(ep, brief)` → `QUESTION_FROZEN`
- `plan_obligations(ep, obligations)` → `EVIDENCE_GATHERING`
- `do_search(ep, adapter, query, discovered=...)` / `do_open(...)`
  / `do_calc(...)` → executor observations under contract; records exact source
  identity + inspected scope
- `evaluate(ep)` → records `sufficiency_decision` via the transparent evaluator
- `finalize(ep, decision)` → only finalizes to a terminal state when the
  evaluator decides so
- `checkpoint(ep)` → writes the per-episode machine trace

**`episode_loop.SufficiencyEvaluator`** (Round 4)
- `evaluate(ep)` → `{decision, registry_pack, hard_gates, sufficiency_vector,
  failed_gates, reason}`; `evaluate_sufficiency(ep)` is the controller default.

## Integration note

The capability owns **no public-web tooling**. Adapters are offline-safe; a
genuine live pilot requires wiring a live adapter into
`adapters.build_default_adapters()` (see `CODEX-HANDOFF.md`).
