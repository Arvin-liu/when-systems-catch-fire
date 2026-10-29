# IGNITION-20260826-140 Step 13 — Targeted regression and projection closure

## Result

The targeted live/Current/identity/release/privacy suite completed naturally
with **91 tests, 0 failures, 0 errors and 0 skips**. It includes the typed
Observation/Reconciliation Plane tests added in Task140 and the existing
transport, execution, ledger, Current, release and privacy gates.

The first run was not relabeled as green: it naturally reported 4 failures.
Those failures were stale test contracts for the six-record ledger and the new
`ARCHITECTURE_CHANGED` Task140 identity, plus one Task139 release-candidate
source binding. The tests and the canonical task-identity source were repaired
to match current semantics, then the identical suite passed without skip,
xfail, ignore or expected-failure additions.

The repository's projection preflight then completed with **25/25 checks
passing**, `release_admission=true`, `side_effect_detected=false` and the
preflight contract explicitly bound to Task140. Deterministic source projections
were regenerated to fixed point: Function assets `5944`, Nonfunction claims
`17172`, Knowledge Experience `414` cards / `315` changes / `332` layered /
`23448` search rows, Human Surface `48` entries, Fire Seeds `64` seeds over
`393` sources, and repository path accounting `3359/3359` with all 10 checks
passing.

Current remains fail-closed: six attempts, zero validated completions, zero
unreconciled attempts, two observation-incomplete records, and an OPEN
`LIVE_EXTERNAL_INVOCATION` obligation. Step13 started no live process and did
not authorize a same-family retry or a second family without a safe admission.

Machine evidence: [`step13-targeted-regression.json`](../../data/operations/iterations/140/step13-targeted-regression.json),
[`live-current-projection-r2.json`](../../data/operations/iterations/140/live-current-projection-r2.json),
[`step12-independent-validation.json`](../../data/operations/iterations/140/step12-independent-validation.json).

Claim ceiling: targeted repository-local regression and deterministic
projection/preflight evidence only; no validated live completion, external truth,
production readiness, Owner acceptance, publication or epistemic acceptance is
inferred.
