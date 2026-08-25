# IGNITION-20260825-139 Step 07 — Current / Human / AI durable-observation sync

## Result

`PASS` for the branch-local Task139 Current projection. Current identity now
advances to Task139 with `PRESENTATION_ONLY` impact; the architecture boundary
remains Task136 and map `0.13.0` remains Current. The lifecycle remains
`IN_PROGRESS` because Steps08–15 are still open.

The canonical live fact is now ledger-derived: four historical attempts exist,
with Hermes136 `TIMED_OUT_EFFECT_UNKNOWN`, Codex137 `FAILED_VALIDATION`,
Codex138 first `STARTUP_FAILURE`, and Codex138 second
`OBSERVATION_INCOMPLETE`. The second Codex dispatch did happen; outer-context
overflow prevented recovery of its return code, structured result, lease,
workspace observation and validator input. The live ceiling remains
`LIVE_EXTERNAL_INVOCATION_OPEN_NO_VALIDATED_COMPLETION`, and reconciliation is
required before any retry.

## Current split-brain repair

The append-only `LiveAttemptLedger` is the canonical historical source. Current
Facts, Current Snapshot and all seven compiler-owned Current blocks now consume
the deterministic live projection. Historical Task138 reports remain
unchanged, while Current prose no longer presents the second invocation as
forbidden. This keeps the event fact and the incomplete evidence distinct.

No persistent component, typed topology relation, layout geometry, identity
epoch or map version changed. `CURRENT_WITH_OPEN_OBLIGATIONS` and
`EPISTEMICALLY_ACCEPTED=0` remain unchanged.

## Gates

- Current-state sync receipt: `PASS` for all 11 required surfaces.
- Current task lineage and volatile fact registry: `PASS`.
- Current Snapshot deterministic check: `PASS`.
- Current Surface compiler two-pass generation: `PASS`.
- Current Surface semantic gate, including unmanaged-current negative checks: `PASS`.
- Live federation regression: `113 tests / 0 failures / 0 errors / 0 skips`; Codex R3 runtime scratch and durable capture parents are separate, so ephemeral cleanup cannot remove or contaminate the durable spool.
- Publication authority remains `REMOTE_REF_OBSERVATION`; no publication assertion is embedded.

The complete decision record is [`current-state-sync-receipt.json`](../../data/operations/iterations/139/current-state-sync-receipt.json), and the machine
artifact is [`step07-current-state-sync.json`](../../data/operations/iterations/139/step07-current-state-sync.json).

## Next gate

Step08 must establish the semantic-negative and observation-projection gates.
Only after the durable-capture and Current gates are green may Task139 perform
at most one new bounded synthetic/read-only executor invocation. Steps13–15
remain responsible for targeted validation, natural candidate/fresh-clone full
regression and publication/witness closeout.

Claim ceiling: Task139 repository-local Current/Human/AI durable-observation
synchronization evidence only; no validated live completion, external truth,
production readiness, Owner acceptance, publication or epistemic acceptance is
inferred.
