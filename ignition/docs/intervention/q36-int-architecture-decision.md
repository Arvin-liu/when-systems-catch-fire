# Q36-INT-I1 Architecture Decision — Intervention–Failure Dynamics & Rollback Closed Loop

> Task: `121Q36-INT-I1` · Executor: Kimi-K3 Max (BUILDER_ONLY) · Parent: `121Q36-OBS-I1@a8eab57bf2a2465c48d5d624e22681a1ad1bc20c`

## Scope split (route adjudication, inherited)

Q36 was adjudicated into two focused candidates:

1. **Q36-OBS** — observation–prediction calibration (frozen as checkpoint 3, PR #67).
2. **Q36-INT** — intervention–failure dynamics & rollback closed loop (this iteration).

Q36-OBS observes and calibrates; it never executes an intervention. Q36-INT answers only:
**"under what Q34-committed claim and Q35-authorized grant may a repository-local controlled
intervention occur, how is it frozen/executed/observed, what happens when it fails, and how is
it stopped / rolled back / preserved in history?"** Q36-INT does **not** prove real-world causal
mechanisms, does **not** build an automatic controller, does **not** execute real-world external
actions, and does **not** form an L7 / truth layer.

## Responsibility boundaries (no gate duplication)

| Layer | Decides | Q36-INT relationship |
|---|---|---|
| Q34 commitment gate | Whether a claim may become a project commitment (`committed_current` vs `hypothesis`/`rejected`) | Q36-INT intervention requests bind to a Q34 `committed_current` claim; an uncommitted/hypothesis claim cannot ground an intervention. |
| Q35 responsibility gate | Who is authorized to propose/authorize/execute/verify a governed action (actor/grant/trajectory/separation of duty) | Q36-INT issues intervention *requests*; the Q35 gate authorizes (or fails closed). Q36-INT does NOT re-adjudicate the grant — it calls the Q35 gate. |
| Q33 rights/publication gate | Whether input/output material may be published | Q36-INT respects the Q33 gate; intervention results built on Q33-rejected sources fail closed. |
| Q36-OBS | Validated observation, residual, uncertainty, applicability scope (read-only input) | Q36-INT consumes Q36-OBS validated observations/residuals as read-only signals; residuals are NOT causal identifications (`do_not_infer_cause: true`). |
| Q36-INT | Freeze target/mechanism/safety-envelope/expected-effect/stop-conditions/rollback-plan; record execution, failure, stop, rollback; preserve history | New capability built here. |

Calibration/residual is **not** causal identification. Intervention effect is **not** a unique causal proof.
Repository-consistency is **not** real-world validity. No L7, no unified truth layer, no automatic causal
adjudicator, no real-world intervention authority, no auto legal/moral responsibility裁决器.

## Typed contract objects (built in P0b/P1)

```
intervention-request        (binds Q34 claim + Q35 grant/trajectory + Q36-OBS observation/residual; external_action=false)
safety-envelope             (allowed scope, max magnitude, side effects, forbidden surfaces, stop/abort, rollback readiness)
intervention-plan           (state machine: proposed→authorized→dry_run→executing→…→rolled_back)
execution-event             (pre-state digest, command, executor, surfaces, change magnitude, artifact digests, trajectory hash)
outcome-evaluation          (expected vs observed, baseline/comparator, uncertainty, causal status: NOT_IDENTIFIED/…, do-not-overclaim-causality)
failure-mode-record         (type, trigger, severity, reversibility, residual impact, responsibility state, Q39 interface, claim ceiling)
stop-rollback-record        (trigger, rollback plan ref, trajectory append-only, pre/post digests, irreversible residue, history preservation)
```

All objects carry `exact_head` / artifact digests and Q34/Q35 references. The validator is fail-closed
with stable exit codes, in the style of `tools/observation/validate_observation_prediction_gate.py` (Q36-OBS),
`tools/agent/validate_responsibility_gate.py` (Q35) and `tools/discovery/validate_commitment_gate.py` (Q34).

## Call order

```
Q36-OBS validated observation/residual (read-only)
  → Q34 scope-valid committed claim
  → Q35 authority gate (grant, scope, separation-of-duty, claim ceiling, Q33 rights)
  → Q36-INT safety envelope / plan freeze
  → controlled execution trajectory (repo-local, append-only, exact-head bound)
  → outcome / effect evaluation (baseline + uncertainty, no causal overclaim)
  → stop / rollback / failure record (append-only; never rewritten to success)
  → Q39 failure-memory interface (defined) / Q43 graded-intervention interface (defined, not built)
```

## Legacy LAB salvage disposition

Legacy branch `lab/121q36-temporal-causality-night@0529baaa…` was preserved as annotated tag
`archive/lab-121q36-temporal-causality-night` by Q36-OBS-I1 (it diverges from the Q34/Q35/Q36-OBS
gates and cannot be merged). Legacy branch `lab/121q39-failure-memory-night@95d637fc…` is preserved
as annotated tag `archive/lab-121q39-failure-memory-night` by this task (matches `lab/*failure*`);
Q36-INT defines only the Q39 failure-memory *interface*, it does not reimplement Q39. Neither legacy
branch is wholesale merged or cherry-picked. Salvage matrix: `docs/intervention/q36-legacy-lab-salvage-matrix.json`.

## Hard boundaries (repeated from instruction)

- No independent review; no Ready; no merge of PR #65/#66/#67/Q36-INT PR or Main.
- No rewriting of Q34/Q35/Q36-OBS frozen heads; no Q37/Q39/Q43 implementation; no F15/D1/D2 materialization.
- No real-world external actions (`external_action=true` fails closed).
- No claim that residuals/intervention results are a unique causal mechanism or a universal real-world capability.
- No credit spent repairing unrelated baseline debt; no validator weakening; no fabricated success/rollback.
