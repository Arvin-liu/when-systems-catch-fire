# Q35 → Q36 Intervention / Outcome / Rollback Interface

> Contract for how Q36 (observation / prediction / intervention / failure dynamics) consumes Q35 governed actions. Repository governance only; Q35 does not execute real-world external actions.

A Q36 **intervention** is a governed Q35 action with an authority grant, an execution trajectory and a responsibility attribution. Q36 does not invent a new authority model; it issues intervention *requests* that the Q35 gate authorizes (or fails closed).

## Interface objects

- **Intervention request** → maps to a Q35 `action` with `phase=intent`, an `action_type` such as `observe`, `predict`, `intervene`, bound to a Q34 `committed_current` claim (or a legitimate DEFER/REJECT basis) and a valid authority grant.
- **Outcome / observation** → a Q35 `action` with `phase=observed_outcome` plus a trajectory event recording the observed effect, digests and conclusion.
- **Rollback / recovery** → a Q35 `action` with `phase=rollback` and a **new** append-only trajectory event (never silent deletion), referencing the original action via `rollback_ref`.
- **Responsibility state** → Q35 attribution (`ATTRIBUTED_WITHIN_REPOSITORY_SCOPE` / `SHARED_RESPONSIBILITY` / `UNRESOLVED_MANY_HANDS` / `INSUFFICIENT_EVIDENCE` / `OUTSIDE_PROJECT_AUTHORITY`). Q36 must preserve `UNRESOLVED_MANY_HANDS` honestly and never force a single fake owner.

## Call order

```
Q34 committed claim → Q36 intervention request (intent)
  → Q35 authority/duty gate (grant, scope, separation-of-duty, claim ceiling, Q33 rights)
  → Q35 execution trajectory (append-only, hash-linked, exact-head bound)
  → Q36 outcome / verification / responsibility state
  → Q36 failure dynamics (residual / anomaly as new governed actions)
```

## Hard boundaries

- Q35 authorization never bypasses the Q33 rights/publication gate.
- Q36 interventions that exceed the committed claim ceiling fail closed or are downgraded.
- No real-world legal/moral responsibility is asserted; internal records are repository governance artifacts.
