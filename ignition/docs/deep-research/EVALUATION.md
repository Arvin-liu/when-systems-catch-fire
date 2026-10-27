# Deep Research Capability — Evaluation Results & Failure Analysis

## Test matrix (all passing locally)

| Suite | Tests | Result |
|-------|-------|--------|
| `test_deep_research_round1` | 19 | PASS |
| `test_deep_research_round2` | 24 | PASS |
| `test_deep_research_round3` | 18 | PASS |
| `test_deep_research_round4` | 13 | PASS |
| `test_deep_research_round5` | 4 methods / 27 subTests | PASS |
| `test_deep_research_round6` | 2 | PASS |
| **Total (R1–R6)** | **99** | **PASS, no regression** |
| `test_research_os` (baseline kernel) | — | ALL CORE TESTS PASSED |
| `test_research_os_checkpoint_c` | — | ALL CHECKPOINT C TESTS PASSED |
| `test_research_os_resumability` | — | ALL RESUMABILITY/REPLAY TESTS PASSED |
| `queue_runtime.py` smoke | — | OK |

## Round 5 — separate metrics (uncollapsed)

The 27 frozen fixtures are replayed deterministically; metrics are reported
**separately** (no single aggregate score). From `ROUND5_METRICS.json`:

- **Episode decision distribution:** CONTINUE_RESEARCH 9, STOP_SUFFICIENT_
  CANDIDATE 3, ESCALATE_GPT_OWNER 3, BLOCKED_WITH_EVIDENCE 1.
- **Episode stop confusion vs an independent ground-truth label:** TP 6, FP 1,
  FN 0, TN 9.
- **Queue stop confusion vs an independent ground-truth label:** TP 7, FP 0,
  FN 0, TN 2. The hard anti-overfit property holds — **zero** false-positive
  stops from a long report / executor `success`, and **zero** false negatives
  on the seven legitimate campaign stop conditions.
- **Per-fixture separate indicators:** `brief_present`, `obligation_coverage`,
  `source_family_count`, `abstract_only_count`, `none_access_count`,
  `injection_detected`, `contrary_sought`, plus every sufficiency-vector
  dimension. See `ROUND5_METRICS.json` for the full table.

## Failure analysis

### F1 (known, carried to Round 7 / Codex) — contradiction gate
`r5-006-conflicting-estimands` asserts two contradictory material claims. The
evaluator has **no contradiction-detection gate**, so it currently returns
`STOP_SUFFICIENT_CANDIDATE` — a **false-positive stop (1 of 16)**. The metric
*intentionally* surfaces this gap rather than hiding it (the ground-truth label
marks it `continue`). Fix: add a contradiction/entailment gate to
`SufficiencyEvaluator.hard_gates` and re-run Round 5; the regression test
asserts exactly one known FP and will flip to 0 once the gate lands.

### F2 (expected, honest) — live pilot blocked offline
Round 6 froze the exact sleep-timing question and drove it through the real
queue + episode + evaluator interfaces, preserving a full machine trace. The
deep-research adapters are **offline-safe by design** and no live public-web
tool is wired into the runtime in this sandbox, so the Round 6 precondition
"required tool access is available" is **not met**. The pilot terminates as
`BLOCKED_WITH_EVIDENCE` (corroborated independently by the evaluator's
`blocked_evidence_route` gate) with exact evidence. This is the legitimate
"blocker" end state and is **not** a code defect. Resume requires wiring a live
adapter (see `CODEX-HANDOFF.md`).

### Not regressed
The Round 3/4 evaluator and Round 2 queue behavior are unchanged by Rounds 5–6;
the 99-test matrix and the three baseline kernel suites pass.
