# Q36-INT Interfaces — Q34 / Q35 / Q33 / Q36-OBS / Q39 / Q43

> Read-only input contract produced by `121Q36-INT-I1`. Q36-INT builds the intervention–failure-dynamics
> half only; it consumes Q34/Q35/Q33/Q36-OBS governance artifacts and exposes typed failure/rollback
> records. It never executes real-world external actions and never invents a new authority model.

## Consumed interfaces (inputs)

### Q34 commitment → intervention claim

- `intervention_request.q34_claim_ref` references a Q34 claim id.
- The validator resolves the claim state via the Q34 claims registry (`--claims`, same format as `data/agent/q34-claims-registry.json`).
- An intervention whose claim is not `committed_current` fails closed with exit `6 Q34_CLAIM_NOT_COMMITTED`.
  Hypothesis / rejected claims cannot ground an intervention conclusion.

### Q35 authority → intervention authorization / execution

- `intervention_request.{q35_actor_ref, q35_grant_ref, q35_action_ref, q35_trajectory_event_digest}` bind the request to a Q35 governed action.
- Missing/malformed references fail closed with exit `7 Q35_AUTHORITY_INVALID`.
- The Q35 grant must be unexpired (`grant_expires_at` >= now) and its scope must cover the intervention target; otherwise exit `7`.
- High-risk interventions require separation of duty: proposer ≠ authorizer ≠ executor ≠ verifier; otherwise exit `19 SEPARATION_OF_DUTY_VIOLATION`.
- Q36-INT does not re-adjudicate the grant itself — that is the Q35 gate's job (`tools/agent/validate_responsibility_gate.py`).

### Q33 rights gate call order

- Every `intervention_request.source_ref` and outcome source is checked against the Q33 rejected-source list (`--q33-rejects`, same format as `data/agent/q33-publication-rejects.json`).
- A Q33-rejected source fails closed with exit `8 Q33_GATE_BYPASS`.

### Q36-OBS observation/residual → intervention read-only signal

- `intervention_request.q36_obs_ref` / `q36_residual_ref` reference validated Q36-OBS records.
- Residuals are read as **signals**, never as causal identifications (`do_not_infer_cause: true` is part of the contract).
- An unvalidated or stale-exact-head Q36-OBS observation fails closed with exit `5 OBS_NOT_VALIDATED`.

## Produced interfaces (outputs)

### Q36-INT → Q39 failure memory (defined, not built)

- `failure_mode_record` carries: failure type, severity, reversibility, residual impact, responsibility state,
  known/unknown cause, competing explanations, escalation target, claim ceiling.
- `stop_rollback_record` carries irreversible residue + verification result.
- These are the Q39 interface surface. Q39 itself is NOT implemented in this iteration (no F15/D1/D2 materialization).

### Q36-INT → Q43 graded intervention (defined, not built)

- `failure_mode_record.escalation_target` may name a Q43 graded-intervention/professional-escalation route.
- Q43 is only *defined* here; it is not implemented.

## Suggested call order

```
Q36-OBS validated observation/residual (read-only)
  → Q34 scope-valid committed claim
  → Q35 authority gate (grant, scope, separation-of-duty, claim ceiling, Q33 rights)
  → Q36-INT safety envelope / plan freeze
  → controlled execution trajectory (repo-local, append-only, exact-head bound)
  → outcome / effect evaluation (baseline + uncertainty, no causal overclaim)
  → stop / rollback / failure record (append-only; never rewritten to success)
  → Q39 / Q43 interface (defined)
```
