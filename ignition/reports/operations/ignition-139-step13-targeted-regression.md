# IGNITION-20260825-139 Step 13 — Targeted regression and projection repair

## Result

`PASS`: after the first candidate natural full run exposed 31 genuine
projection/accounting failures, the repaired targeted surface completed with
**83 tests, 0 failures, 0 errors, and 0 skips**. The 51 Task139
live/Current/identity/surface tests completed in `182.902s`; the 32 Foundation
closure and path tests completed in `1513.465s` inside a temporary isolated
venv using the exact `requirements-foundation.txt` versions.

The default system interpreter was also tested for comparison. Its Foundation
run had one environmental failure because `sympy` was not installed; that is
recorded as `ENVIRONMENT_BLOCKED`, not as a repository pass or a softened
validator result. The canonical isolated dependency contract passed the same
32 tests.

## First natural candidate failure

The first candidate full regression was allowed to terminate naturally at
candidate head `80556d968ce6b53054c778a02fd74166dd9ab805`:

- `1202 tests / 31 failures / 0 errors / 0 skips`
- `3033.542s`, no watchdog, no process kill, no arbitrary timeout
- failure status: `FAIL_GENERATED_PROJECTION_REPAIR_REQUIRED`
- pre-run tree was clean; the only post-run residual was the canonical ledger
  lock created by a test that read the real ledger directly

The failure clusters were stale Function/Nonfunction projections and path
classification, stale Current Facts/Snapshot/compiler blocks, sealed
State-Changelog and Task identity bindings, stale Human/Knowledge hashes, the
direct-execution import boundary, and the canonical-ledger test lock. The
receipt and stream digests remain in
[`step13-targeted-regression.json`](../../data/operations/iterations/139/step13-targeted-regression.json);
that failed run is not relabeled as green.

## Repairs

The canonical generators were rerun to a fixed point. Generated Current
Snapshot blocks now have an explicit boundary in nonfunction claim discovery,
so compiler output cannot feed back into the canonical claim census. Task139
baseline, changelog, identity, runner-contract and progress bindings were
updated. The direct projection determinism entry point now resolves its own
`ignition` import root, and the live projection test uses a temporary ledger
copy so a check cannot leave a lock in the formal repository.

The resulting deterministic values are:

- Function assets: `5911` machine / `24` human.
- Nonfunction claims: `17023` machine / `24` human.
- Knowledge Experience: `414` cards, `315` changes, `332` layered entries,
  `23266` search rows.
- Repository path classification: `3295` tracked and `3295` manifest paths.
- Live ledger: `5` records, hash-chain head
  `8ebe46858519650684d476609cea03f09340d5afb18bee1a9260a7e107851e9d`.
- Current live projection: `5` attempts, `3` unreconciled, `2`
  observation-incomplete, `0` validated completions, digest
  `2769e67813ecae3b6dc321088fb44c845b6895c3c48ee841db289e7eac824f73`.

## Live boundary and next gate

No new live invocation occurred in Step 13. The Task139 live obligation stays
`OPEN`, the next action is `RECONCILE_UNRECOVERED_ATTEMPTS`, and retry remains
`NOT_AUTHORIZED`. The Task138 second Codex attempt and the Task139 incomplete
observation remain ledger facts; neither is rewritten as success or as “did
not run”.

Step 14 must now rerun the candidate exact-head natural offline full suite.
Step 15 must independently validate the fresh remote-main clone and complete
the publication/witness sequence.

Claim ceiling: targeted repository-local regression and deterministic
projection/preflight evidence only. No validated live completion, external
truth, production readiness, Owner acceptance, publication or epistemic
acceptance is inferred.
