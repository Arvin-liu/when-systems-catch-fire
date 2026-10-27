# CODEX-HANDOFF.md — Deep Research Queue (WorkBuddy Takeover, Rounds 1–7)

Exact resume instructions for the next executor (Codex) continuing Task 115's
deep-research-queue capability from the WorkBuddy takeover branch.

## Identity

- **Repository:** `Arvin-liu/when-systems-catch-fire`
- **WorkBuddy takeover branch (HEAD):** `workbuddy/task115-deep-research-queue-round1-7-takeover-r1-20260804`
- **Frozen parent (Qwen Round 0):** `qwen38max/task115-deep-research-queue-checkpoint-d-r1-20260803` → exact head `f4fe6faded65c16c98230ad34ca17e4374d59613`
- **Capability version:** `deep-research/0.1`
- **Ledger:** `data/operations/iterations/115/candidate/workbuddy-takeover/ROUND-LEDGER.jsonl`
- **Checkpoints:** `ROUND-{1..6}-CHECKPOINT.md` in the same directory.

## What is already built & verified (Rounds 1–6)

1. **Round 1** — 13 fail-closed schemas (`schemas/deep-research/`, `deep-research/0.1`) + records + 27 fixtures (15 positive / 12 negative). Commit `0c07b798`.
2. **Round 2** — serial, crash-resumable `SerialQueue` (ranking, lease idempotence/duplicate-prevention/expiry, crash recovery, ingest-never-stops, 7 campaign stops). Commit `3d88af6a`.
3. **Round 3** — `EpisodeController` + offline-safe adapters (prompt-injection quarantine, exact provenance, bounded hashed calc) + CLI/API + claim/obligation ops. Commit `e0176d67`.
4. **Round 4** — transparent `SufficiencyEvaluator`: 10 hard gates + 8-dim sufficiency vector, no scalar authorizes stop. Commit `a2413475`.
5. **Round 5** — 27 frozen anti-overfit fixtures (self-validating) + replay/regression + **separate** metrics + FP/FN vs independent GT. Commit `7ceb4280`.
6. **Round 6** — bounded sleep-timing pilot through the real interfaces; offline → `BLOCKED_WITH_EVIDENCE` with full machine trace under `round6-trace/`. Commit `965e796e`.

**Test status:** 99 local tests PASS (R1–R6) + 3 baseline Research OS kernel
suites PASS + queue smoke OK. No regression.

## Open items to resolve

### O1 — Live public-web tooling (resume the Round 6 pilot)
The runtime owns **no public-web tool**. Adapters are offline-safe; a genuine
live pilot cannot run. To resume:
```bash
# 1. Wire a live adapter into the builder:
#    edit tools/deep_research/adapters.py :: build_default_adapters()
#    (e.g. add a "web" implementation that performs an authorized fetch)
# 2. Re-run the pilot:
python3 tools/deep_research/run_round6_pilot.py
#    With live access, obligation obl-1 (PRIMARY_SOURCE, HIGH) can be
#    SATISFIED and the SufficiencyEvaluator re-run; the pilot may then end as
#    sufficient / insufficient / budget-pause instead of blocker.
# 3. Re-run the full matrix (see OPERATOR-GUIDE.md) and re-commit.
```

### O2 — Contradiction / entailment gate (fix the Round 5 FP)
`r5-006-conflicting-estimands` returns `STOP_SUFFICIENT_CANDIDATE` because no
contradiction-detection gate exists (1 false-positive stop of 16). To fix:
```bash
# 1. Add a hard gate to tools/deep_research/episode_loop.py ::
#    SufficiencyEvaluator.hard_gates that flags two contrary material claims
#    both asserted without resolution.
# 2. Regenerate + re-run:
python3 tools/deep_research/generate_round5_fixtures.py
python3 tests/test_deep_research_round5.py
#    The regression test asserts exactly 1 known FP; once the gate lands it
#    should drop to 0 — update EPISODE_GT_STOP["r5-006-..."] accordingly.
```

## How to run everything

See `docs/deep-research/OPERATOR-GUIDE.md` for the exact commands (generators,
queue smoke, pilot, per-round tests, CLI subcommands, and the
`SerialQueue` / `EpisodeController` / `SufficiencyEvaluator` API).

## Draft PR

A stacked **Draft** PR exists: **head** = the WorkBuddy takeover branch,
**base** = Qwen Round 0 branch. It retains `R2_EMPIRICAL_CALIBRATION_PENDING`
and states failed/pending CI honestly. Do **not** merge / mark Ready / tag /
terminalize. See `GPT-OWNER-REVIEW-PACKET.md`.
