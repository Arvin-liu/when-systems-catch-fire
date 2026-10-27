# Q36-OBS Interfaces — Q34 / Q35 / Q33 / Q36-INT / Q39

> Read-only interface contract produced by `121Q36-OBS-I1`. Q36-OBS builds the observation–prediction calibration half only; it exposes typed outputs and never executes interventions.

## Consumed interfaces (inputs)

### Q34 commitment → Q36 prediction claim

- `prediction_commitment.q34_claim_ref` references a Q34 claim id.
- The validator resolves the claim state via a Q34 claims registry (`--claims`, same format as `data/agent/q34-claims-registry.json`).
- A prediction whose claim is not `committed_current` fails closed with exit `6 Q34_CLAIM_NOT_COMMITTED`. Hypothesis / rejected claims cannot ground a Current prediction conclusion.

### Q35 authority → prediction issuance / evaluation

- `prediction_commitment.{q35_actor_ref, q35_grant_ref, q35_trajectory_event_digest}` bind issuance to a Q35 governed action.
- `outcome_binding.evaluator_ref` names the Q35 actor or deterministic verifier performing the binding.
- Missing/malformed references fail closed with exit `7 Q35_AUTHORITY_INVALID`. Q36-OBS does not re-adjudicate the grant itself — that is the Q35 gate's job (`tools/agent/validate_responsibility_gate.py`).

### Q33 rights gate call order

- Every `observation_spec.source_ref` is checked against the Q33 rejected-source list (`--q33-rejects`, same format as `data/agent/q33-publication-rejects.json`).
- A Q33-rejected source fails closed with exit `8 Q33_GATE_BYPASS`. The full Q33 gate (`tools/governance/fail_closed_publication_gate.py`) remains the authority for classification/gate decisions; Q36-OBS consumes its reject surface.

## Produced interfaces (outputs, read-only)

### Q36-OBS → Q36-INT (future)

Q36-INT may consume, without modification:

- **validated observations** — `observation_spec` records with `quality_status` and provenance;
- **prediction residuals** — `residual_anomaly` records with `escalation_target: "q36_int"`;
- **uncertainty statements** — `prediction_commitment.uncertainty` and interval/distribution values;
- **applicability scope** — `prediction_commitment.applicability_scope` and `evaluation_calibration.scope_summary`.

Q36-INT must not treat residuals as causal identifications (`do_not_infer_cause: true` is part of the contract).

### Q36-OBS → Q39 failure memory (future)

- `residual_anomaly` records with `escalation_target: "q39_failure_memory"` carry: residual type, magnitude/direction, expected vs unexpected status, known data-quality explanation, unresolved-anomaly flag, claim ceiling.
- F15/D1/D2 are **not** materialized in this iteration; the residual record is the interface surface only.

## Suggested call order

```
Q34 committable prediction claim
  → Q35 authorized prediction task
  → Q33 rights gate on observation sources
  → freeze prediction before reveal
  → bind independent outcome after reveal
  → deterministic calibration / residual
  → preserve failures + applicability scope
  → Q36-INT / Q39 read-only interfaces
```
