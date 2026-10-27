# Round 6 Checkpoint — Bounded Sleep-Timing Pilot

**Round:** 6 / 7
**Parent (frozen Qwen Round 0):** `f4fe6faded65c16c98230ad34ca17e4374d59613`
**Round 6 deliverable commit:** `965e796edf6e2b3887219c89558537b7b4dde6ae`
**Branch:** `workbuddy/task115-deep-research-queue-round1-7-takeover-r1-20260804`

## What Round 6 produced

TASK.md Round 6 freezes an exact question on sleep timing / delayed circadian
phase for 7–8h sleepers and requires the pilot to run through the **implemented
queue/capability interfaces** and preserve a **full machine trace**, ending
legitimately as sufficient / insufficient / budget-pause / blocker / escalation.
It also says: start only when "required tool access is available without
unresolved approval blocking," and do **not** start/continue public-web work
when an approval window is waiting unattended.

### Outcome: `BLOCKED_WITH_EVIDENCE` (honest, expected)

The deep-research capability's adapters are **offline-safe by design**
(Rounds 1–3): `WebAdapter`/`PdfAdapter.open()` with no supplied content returns
`NONE` access + an offline error and never reaches the public web. **No live
public-web tool is wired into the runtime in this sandbox.** Therefore the
Round 6 precondition "required tool access is available" is **NOT met**, and a
genuine live evidence-gathering pilot must not start. The pilot instead:

- drives the **real** interfaces end-to-end — `Round 2 SerialQueue.select_next`
  (claims the lease, marks the item `ACTIVE`) → `Round 3 EpisodeController`
  (`freeze_scope` → `plan_obligations` → `do_search` → `do_open` → `evaluate`)
  → `Round 4 SufficiencyEvaluator`;
- preserves a **complete machine trace**: `episode.json` (full event log +
  blockers), `queue.json` (campaign + items + stats), and `PILOT-REPORT.json`
  (frozen question, boundaries, outcome, exact evidence, resume commands);
- records one structured `blocker` on the episode and finalizes to the terminal
  `BLOCKED` state;
- **corroboration:** the in-episode `SufficiencyEvaluator` *independently*
  returned `BLOCKED_WITH_EVIDENCE` (the opened source resolved to `NONE` access,
  tripping the `blocked_evidence_route` hard gate) — the blocker is not merely
  asserted at the wrapper level.

### `tools/deep_research/run_round6_pilot.py` (NEW)
- `FROZEN_QUESTION` is the **exact** TASK.md Round 6 text; `BOUNDARIES` carries
  the seven research boundaries.
- `run_pilot(trace_dir)` is importable (used by the test) and deterministic;
  `main()` writes the canonical trace under
  `data/operations/iterations/115/candidate/workbuddy-takeover/round6-trace/`.
- Self-checks: trace files exist, outcome `BLOCKED_WITH_EVIDENCE`, episode
  terminal state `BLOCKED`.

### `tests/test_deep_research_round6.py` (NEW) — 2 tests, all PASS
- Pilot runs through the real interfaces and ends `BLOCKED_WITH_EVIDENCE` with a
  preserved machine trace; the opened source is `NONE` access (offline
  fail-closed); exact evidence documents the offline adapters + missing live
  tool; the in-episode evaluator corroborates; Round 7/Codex resume commands
  are specified.
- The frozen question equals the exact TASK.md text.

### Carried to Round 7 (Codex handoff)
`PILOT-REPORT.json → resume_commands_for_round7_codex` specifies: wire a live
public-web adapter into `build_default_adapters()`, re-run the pilot, and on
live access the opened `obl-1` obligation can be `SATISFIED` so the pilot may
then end as sufficient / insufficient / budget-pause instead of blocker.

## Test results
- `tests/test_deep_research_round1.py`: **19/19 PASS**
- `tests/test_deep_research_round2.py`: **24/24 PASS**
- `tests/test_deep_research_round3.py`: **18/18 PASS**
- `tests/test_deep_research_round4.py`: **13/13 PASS**
- `tests/test_deep_research_round5.py`: **4/4 methods (27 subTests) PASS**
- `tests/test_deep_research_round6.py`: **2/2 PASS**
  → **99/99 across R1–R6, no regression**
- `tools/deep_research/queue_runtime.py` smoke: OK
- `tests/test_research_os.py`: ALL CORE TESTS PASSED
- `tests/test_research_os_checkpoint_c.py`: ALL CHECKPOINT C TESTS PASSED
- `tests/test_research_os_resumability.py`: ALL RESUMABILITY/REPLAY TESTS PASSED

## Next
Round 7 — closure candidate + stacked Draft PR: architecture/operator docs, exact
round/commit/remote-CI ledger, schemas + version map, API/CLI guide, stop-
algorithm explanation, evaluation results + failure analysis, the Round 6 pilot
report + machine trace, unresolved obligations, `CODEX-HANDOFF.md` (exact resume
commands), `GPT-OWNER-REVIEW-PACKET.md`, machine-readable candidate state. Then
one Draft PR (head: WorkBuddy takeover branch; base: Qwen Round 0 branch; remain
Draft; retain `R2_EMPIRICAL_CALIBRATION_PENDING`; state failed/pending CI
honestly). Do not merge / mark Ready / tag / terminalize.
