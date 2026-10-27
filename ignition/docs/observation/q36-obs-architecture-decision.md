# Q36-OBS-I1 Architecture Decision — Observation–Prediction Calibration

> Task: `121Q36-OBS-I1` · Executor: Kimi-K3 Max (BUILDER_ONLY) · Parent: `121Q35-I1R@ea1408e6525ceac8ea0c9c5377aca269579d6ff4`

## Scope split (route adjudication, inherited)

Q36 was adjudicated into two focused candidates:

1. **Q36-OBS** — observation–prediction calibration (this iteration).
2. **Q36-INT** — intervention / failure dynamics (future iteration, NOT built here).

Q36-OBS answers only: **"what did the prediction say before the outcome was revealed, and how did it perform after the outcome appeared?"**
Q36-INT will answer: **"whether and how to intervene, and how the intervention fails / rolls back."** Nothing in this iteration executes interventions, automatic control, real-world actions, or failure-recovery loops.

## Responsibility boundaries (no gate duplication)

| Layer | Decides | Q36-OBS relationship |
|---|---|---|
| Q34 commitment gate | Whether a prediction claim may become a project commitment (`committed_current` vs `hypothesis`/`rejected`) | Q36-OBS consumes Q34 claim state; a prediction whose underlying claim is not `committed_current` cannot be declared a Current prediction conclusion. |
| Q35 responsibility gate | Who is authorized to issue, run, or verify a prediction-calibration task (actor/grant/trajectory/separation of duty) | Q36-OBS prediction issuance and evaluation reference Q35 actor + grant + trajectory event digests; no new authority model is invented. |
| Q33 rights/publication gate | Whether input/output material may be published | Q36-OBS calls the Q33 gate before binding any external observation source; rejected sources fail closed. |
| Q36-OBS | Freeze-before-reveal, outcome binding, deterministic calibration, residual/anomaly preservation | New capability built here. |

Calibration/residual is **not** causal identification. Repository consistency is **not** real-world validity. No L7, no unified truth layer, no automatic causal adjudicator, no intervention authority.

## Typed contract objects (built in P1)

```
observation-spec          (what was measured; event time vs available time separated)
prediction-commitment     (frozen before reveal; immutable; supersession-only correction)
outcome-binding           (prediction ↔ outcome matching with independent evidence status)
evaluation-calibration    (deterministic metrics; sample size + scope + baseline mandatory)
residual-anomaly          (failure/anomaly preserved; do-not-infer-cause flag; Q39/Q36-INT interface)
```

All five objects carry `exact_head` / artifact digests and Q34/Q35 references. The validator is fail-closed with stable exit codes, in the style of `tools/discovery/validate_commitment_gate.py` (Q34) and `tools/agent/validate_responsibility_gate.py` (Q35).

## Call order

```
Q34 committable prediction claim
  → Q35 authorized prediction task (actor/grant/trajectory)
  → Q33 rights gate on observation sources
  → freeze prediction before reveal (immutable issued_at, input cutoff)
  → bind independent outcome after reveal
  → deterministic calibration / residual computation
  → preserve failures + applicability scope
  → read-only interfaces toward Q36-INT / Q39
```

## Legacy LAB salvage disposition

Legacy branch `lab/121q36-temporal-causality-night@0529baaa354a99eae91621f2a70c9b5b53454208` is preserved as annotated tag `archive/lab-121q36-temporal-causality-night`. It was branched from a pre-Q34 base (its diff vs the Q35 head deletes the Q33/Q34/Q35 gates), so wholesale merge/cherry-pick is impossible. Salvage matrix: `docs/observation/q36-legacy-lab-salvage-matrix.json`. Selectively reimplemented concepts are limited to Q36-OBS scope; temporal-causality assertions that imply causal adjudication belong to Q36-INT or are rejected as out of scope.

## Hard boundaries (repeated from instruction)

- No independent review; no Ready; no merge of PR #65/#66/Q36 PR; no Main modification.
- No rewriting of Q34/Q35 frozen heads; no Q36-INT; no F15/D1/D2 materialization.
- No claim of universal real-world predictive capability or proven causal mechanism.
- No credit spent repairing unrelated baseline debt; no validator weakening; no fabricated historical predictions.
