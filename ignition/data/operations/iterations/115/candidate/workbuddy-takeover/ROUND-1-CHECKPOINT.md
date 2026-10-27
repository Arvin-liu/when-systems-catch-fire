# Round 1 Checkpoint — Deep Research Capability Contract + Machine Schemas

**Campaign:** POINTFIRE-WORKBUDDY-DEEP-RESEARCH-QUEUE-ROUND1-7-TAKEOVER-R1-20260804
**Round:** 1 / 7
**Parent (frozen Qwen Round 0 head):** `f4fe6faded65c16c98230ad34ca17e4374d59613`
**Round 1 deliverable commit:** `0c07b798caf296bb85872dedff4542015ef60497`
**Branch:** `workbuddy/task115-deep-research-queue-round1-7-takeover-r1-20260804`

## What Round 1 produced

Round 1 establishes the **Deep Research Capability contract** — the 13 machine
record schemas that Rounds 2–7 (queue runtime, inner loop, gates, fixtures,
pilot, validation) build on. It reuses the inherited Research OS kernel
vocabularies and executor contract rather than redefining authority.

### 13 machine schemas (`schemas/deep-research/`)
Generated canonically by `tools/deep_research/generate_schemas.py` (never
hand-edited). Each emits `<name>.schema.json` + `index.json`.

| # | Record | Key fail-closed rule |
|---|--------|----------------------|
| 1 | research-topic-candidate | executor-proposed rankings; `status` owner-adjudicated |
| 2 | research-brief | `frozen` required; scope needs population/object/timeframe/outcomes |
| 3 | research-plan | obligations + subquestions derived from frozen brief |
| 4 | evidence-obligation | `obligation_class` must be a valid kernel obligation class |
| 5 | source-record | **if `opened=true` then `inspected_scope` required** |
| 6 | research-action | `action_code` must be a valid kernel action code |
| 7 | executor-observation | **prohibits `self_approved` / `mark_episode_complete` / `claim_ceiling`** |
| 8 | claim-evidence-record | `claim_ceiling` valid kernel ceiling; owner-adjudicated |
| 9 | research-trace-event | append-only, `payload_sha256` 64-hex |
| 10 | research-sufficiency-decision | **`STOP_SUFFICIENT_CANDIDATE` requires `hard_gates_passed=true`** |
| 11 | research-episode-result | `final_state` valid kernel episode state |
| 12 | research-queue-item | `status` valid queue status; resumable `checkpoint_commit` |
| 13 | research-campaign | independent campaign-level stop conditions |

### `tools/deep_research/records.py` — constructors + validators
- `make_record(name, **overrides)` builds + validates (fail-closed, rejects
  unknown fields because schemas are `additionalProperties: False`).
- `validate_executor_observation(obj)` **delegates prohibited-key / required-field
  enforcement to the kernel** `research_os.executor_contract.validate_return`
  (the single authority for "executor may never self-approve / mark complete /
  raise a claim ceiling"), then validates the structural schema.
- Explicit **field-origin classification**: `DETERMINISTIC`, `EXECUTOR_PROPOSED`,
  `OWNER_ADJUDICATED`, `KERNEL_ENUM`, `PROHIBITED`. Invariant proven by tests:
  an `executor-observation` carries **no** owner-adjudicated field, and the three
  prohibited keys are classified `PROHIBITED` (never writable by the executor).

### Fixtures (canonical generators)
- `tools/deep_research/generate_fixtures.py` → 15 positive example records
  (`tests/fixtures/deep_research/round1/positive/`).
- `tools/deep_research/generate_negative_fixtures.py` → 12 must-reject records
  (`tests/fixtures/deep_research/round1/negative/`), each tagged with `_record`
  + `_expect`.

### Tests (`tests/test_deep_research_round1.py`) — 19 tests, all PASS
- 13 schemas present + valid Draft 2020-12 + `$id`/`version` correct + index match.
- Vocabulary reuse: obligation-class / action-code / claim-ceiling / episode-state
  enums equal the inherited kernel registries (no duplicate authority).
- 15 positive fixtures validate; 12 negative fixtures rejected (fail-closed).
- Executor prohibited keys rejected by the kernel delegate.
- Constructor + origin invariants (no owner-adjudicated executor field; prohibited
  keys classified PROHIBITED; claim_ceiling owner-adjudicated; unknown field
  rejected).
- Generator canonicalness: on-disk files equal generator output.

## Test results
- `tests/test_deep_research_round1.py`: **19/19 PASS**
- `tests/test_research_os.py`: ALL CORE TESTS PASSED (regression: green)
- `tests/test_research_os_checkpoint_c.py`: ALL CHECKPOINT C TESTS PASSED
- `tests/test_research_os_resumability.py`: ALL RESUMABILITY/REPLAY TESTS PASSED

## Regeneration
```
python3 tools/deep_research/generate_schemas.py
python3 tools/deep_research/generate_fixtures.py
python3 tools/deep_research/generate_negative_fixtures.py
```

## Next
Round 2 — serial resumable queue runtime (consumes these schemas).
