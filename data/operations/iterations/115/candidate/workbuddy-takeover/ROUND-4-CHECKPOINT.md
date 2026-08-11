# Round 4 Checkpoint — Transparent Stopping: Hard Gates + Sufficiency Vector

**Round:** 4 / 7
**Parent (frozen Qwen Round 0):** `f4fe6faded65c16c98230ad34ca17e4374d59613`
**Round 4 deliverable commit:** `a2413475851feacef41277e71e5cdc1fe69daf1f`
**Branch:** `workbuddy/task115-deep-research-queue-round1-7-takeover-r1-20260804`

## What Round 4 produced

Replaces the Round 3 obligation-coverage placeholder (`_placeholder_sufficiency`)
with a transparent, inspectable stopping algorithm (TASK.md Round 4): **hard
gates** that block `STOP_SUFFICIENT_CANDIDATE` for any material condition, plus a
**multidimensional sufficiency vector**, with **no scalar score alone
authorizing completion**.

### `tools/deep_research/episode_loop.py` (MODIFIED)
- `SufficiencyEvaluator` — `hard_gates(ep)` returns an inspectable list of 10
  gates; `sufficiency_vector(ep, thresh)` returns 8 dimensions; `evaluate(ep)`
  returns a decision record `{decision, registry_pack, hard_gates,
  sufficiency_vector, failed_gates, reason}`.
- **Hard gates** (any failure blocks `STOP_SUFFICIENT_CANDIDATE`):
  `scope_frozen`, `unsupported_material_claim`,
  `open_burden_bearing_severe_obligation`, `unresolved_source_identity`,
  `citation_attribution_mismatch`, `false_independence_same_family`,
  `high_stakes_evidence_route_failure`, `unresolved_prompt_injection`,
  `blocked_evidence_route`, `missing_required_calc_without_ceiling_reduction`.
- **Sufficiency vector** (≥ the 8 required dimensions): obligation coverage,
  claim support / citation faithfulness, independent evidence-family coverage,
  contrary / null evidence coverage, method / data / recomputation coverage,
  claim-ceiling stability, unresolved-gap severity, marginal information gain.
  Each dimension carries `{value, threshold, met}`; all must be met.
- **Decision mapping** (transparent, non-scalar):
  - any hard gate failed → `ESCALATE_GPT_OWNER` (prompt injection / high-stakes
    route failure), `BLOCKED_WITH_EVIDENCE` (load-bearing NONE-access source),
    else `CONTINUE_RESEARCH`;
  - all gates pass + all vector dims met → `STOP_SUFFICIENT_CANDIDATE`;
  - gates pass but vector short and no marginal gain → `STOP_INSUFFICIENT_EVIDENCE`;
  - otherwise `CONTINUE_RESEARCH`.
- **Registry-driven thresholds** — `_SUFFICIENCY_THRESHOLDS` keyed by strategy
  pack (unknown packs fall back to `SYSTEMATIC_EVIDENCE_SYNTHESIS`); a custom
  threshold dict can be supplied to the evaluator.
- `evaluate_sufficiency(ep, thresholds=None)` is the controller's default
  evaluator; `_placeholder_sufficiency` kept as a backward-compatible alias.
- `EpisodeController.evaluate` now records `ep["sufficiency_decision"]` for the
  machine trace.

### `tools/deep_research/cli.py` (MODIFIED)
- `queue_step` includes `sufficiency_decision=ep.get("sufficiency_decision")`
  in the ingested `research-episode-result` (the episode-result schema already
  admits an object-typed `sufficiency_decision`; the queue's low-information
  stop logic reads it).

### Tests (`tests/test_deep_research_round4.py`) — 13 tests, all PASS
- Hard gates block: unfrozen scope, unsupported material claim, open severe
  obligation, single-family false independence, prompt injection (→ escalate),
  high-stakes route failure (→ escalate), blocked evidence route (→ BLOCKED).
- Fully-evidenced episode (satisfied obligation + material claim + 2 independent
  FULL_TEXT families + contrary sought) → `STOP_SUFFICIENT_CANDIDATE` with all
  gates passed and all vector dims met.
- No scalar alone authorizes: an open severe obligation blocks `STOP_SUFFICIENT`
  even when the rest of the vector looks strong.
- Registry-driven thresholds: a strategy-pack-specific threshold relaxes the
  obligation/gap dimensions and flips the decision to sufficient.
- `run_plan` routing: sufficient → `CANDIDATE_COMPLETE` (non-terminal by
  design); open severe obligation with no actions → honest `BLOCKED`; prompt
  injection → `ESCALATED_TO_GPT_OWNER`.

## Test results
- `tests/test_deep_research_round1.py`: **19/19 PASS**
- `tests/test_deep_research_round2.py`: **24/24 PASS**
- `tests/test_deep_research_round3.py`: **18/18 PASS**
- `tests/test_deep_research_round4.py`: **13/13 PASS** (74/74 across R1–R4, no regression)
- `tools/deep_research/queue_runtime.py` smoke: OK
- `tests/test_research_os.py`: ALL CORE TESTS PASSED
- `tests/test_research_os_checkpoint_c.py`: ALL CHECKPOINT C TESTS PASSED
- `tests/test_research_os_resumability.py`: ALL RESUMABILITY/REPLAY TESTS PASSED

## Next
Round 5 — ≥24 frozen offline anti-overfit / error-stop fixtures (many URLs
without reading, same-family repeats, summary-only-as-full-text, unsupported
citations, absent contrary evidence, conflicting estimands, unavailable data
with ceiling reduction, numerical mismatch, high-stakes escalation, prompt
injection, queue crash/resume + duplicate lease, deadline/attempt/budget stops,
low-information-gain-with-severe-obligation, genuinely-sufficient-should-stop)
with deterministic replay + regression tests.
