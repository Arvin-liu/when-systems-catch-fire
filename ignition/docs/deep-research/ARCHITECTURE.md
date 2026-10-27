# Deep Research Capability — Architecture

**Capability version:** `deep-research/0.1`
**Built on:** Research OS kernel (`research_os.kernel`) — the single authority
for state transitions and the executor no-self-approval contract.
**Branch:** `workbuddy/task115-deep-research-queue-round1-7-takeover-r1-20260804`
**Parent (frozen Qwen Round 0):** `f4fe6faded65c16c98230ad34ca17e4374d59613`

## Layers

```
┌─────────────────────────────────────────────────────────────┐
│ CLI / API surface          tools/deep_research/cli.py         │
├─────────────────────────────────────────────────────────────┤
│ Evaluation (transparent)  episode_loop.SufficiencyEvaluator  │  Round 4
│   - 10 hard gates                                            │
│   - 8-dim sufficiency vector (no scalar authorizes stop)     │
├─────────────────────────────────────────────────────────────┤
│ Episode controller         episode_loop.EpisodeController    │  Round 3
│   freeze → plan → search/open/calc → challenge → revise →    │
│   evaluate → finalize → checkpoint                           │
├─────────────────────────────────────────────────────────────┤
│ Queue runtime              queue_runtime.SerialQueue         │  Round 2
│   deterministic ranking+selector; lease idempotent/duplicate │
│   prevention/expiry; crash recovery; ingest (never stops);   │
│   7 campaign stop conditions                                 │
├─────────────────────────────────────────────────────────────┤
│ Tool adapters (offline-safe) adapters.Web/Pdf/Attachment/    │  Round 3
│   Calc  — executor observations under contract; prompt-      │
│   injection quarantine; exact source identity + inspected-   │
│   scope provenance; bounded hashed calc                     │
├─────────────────────────────────────────────────────────────┤
│ Record / schema layer      records.py + schemas/deep-research│  Round 1
│   (14 records, deep-research/0.1) — fail-closed constructors │
│   + validators; field-origin classification                 │
├─────────────────────────────────────────────────────────────┤
│ Research OS kernel         research_os.kernel (inherited)    │
│   state machine; executor_contract.validate_return           │
└─────────────────────────────────────────────────────────────┘
```

## Data flow

```
topic_candidate
  → ResearchQueueItem (QUEUED)
  → SerialQueue.select_next (claims lease, ACTIVE)
  → EpisodeController.freeze_scope (QUESTION_FROZEN) + plan_obligations
  → do_search / do_open / do_calc  (executor observations, offline-safe)
  → evaluate (SufficiencyEvaluator)
  → finalize (CANDIDATE_COMPLETE / INSUFFICIENT_EVIDENCE_COMPLETE /
              BLOCKED / ESCALATED_TO_GPT_OWNER) or CONTINUE
  → checkpoint (per-episode machine trace)
  → SerialQueue.ingest_result (item COMPLETED; NEVER stops the queue)
  → SerialQueue.should_stop (7 campaign conditions only)
```

## Fail-closed design invariants

- **No self-approval.** The loop never marks an episode complete or raises a
  claim ceiling on its own; those are kernel/owner decisions.
- **Offline-safe adapters.** `open()` with no supplied content returns `NONE`
  access + an offline error; a source is never silently treated as read.
- **Prompt-injection quarantine.** Injected content is recorded with
  `ABSTRACT_ONLY` + `injection_detected`, never executed as instruction, and
  escalates via the `unresolved_prompt_injection` hard gate.
- **Exact provenance.** Every source carries `source_id`, `access_level`, and
  `inspected_scope`; citation-attribution mismatches are caught.
- **Bounded calculation.** `CalcAdapter` allows only a pure arithmetic subset
  with input/output hashes; no file/network/arbitrary-code execution.
- **Anti-overfit queue.** A long report, many URLs, or an executor `success`
  result can NEVER stop the queue; only the seven campaign conditions can.

## State machine (kernel, relevant slice)

`INTAKE → QUESTION_FROZEN → EVIDENCE_GATHERING → ANALYSIS → CHALLENGE →
ANALYSIS → REVISION → {CANDIDATE_COMPLETE (non-terminal), INSUFFICIENT_
EVIDENCE_COMPLETE (terminal), BLOCKED (terminal), ESCALATED_TO_GPT_OWNER
(terminal)}`. `BLOCKED` is reachable from `ANALYSIS`/`EVIDENCE_GATHERING`;
`PAUSED_RESUMABLE` is reachable from most active states.

## File map

| Path | Round | Purpose |
|------|-------|---------|
| `schemas/deep-research/*.schema.json` (14) + `index.json` | 1 | fail-closed record schemas |
| `tools/deep_research/records.py` | 1 | constructors + validators (delegate executor-observation to kernel) |
| `tools/deep_research/queue_runtime.py` | 2 | serial, crash-resumable queue |
| `tools/deep_research/adapters.py` | 3 | offline-safe tool adapters |
| `tools/deep_research/episode_loop.py` | 3–4 | controller + transparent evaluator |
| `tools/deep_research/cli.py` | 3 | CLI/API surface |
| `tools/deep_research/generate_round5_fixtures.py` | 5 | ≥24 frozen anti-overfit fixtures (self-validating) |
| `tools/deep_research/run_round6_pilot.py` | 6 | bounded sleep-timing pilot + machine trace |
| `tests/test_deep_research_round1..6.py` | 1–6 | round regression suites |
| `tests/fixtures/deep_research/round1`, `round5` | 1,5 | frozen fixtures |
| `data/operations/iterations/115/candidate/workbuddy-takeover/` | — | ledger, checkpoints, pilot trace, handoff |
