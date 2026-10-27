# IGNITION-20260825-139 Step 08 — Live-observation semantic gate

## Result

`PASS`: all 12 deterministic semantic fixtures produced their expected
fail-closed outcome. Eight adversarial cases failed as required; four positive
cases passed only when the boundary was explicit.

The gate binds the canonical Task139 ledger and Current projection before
running fixtures. It therefore rejects the split-brain claim that the Task138
second Codex dispatch was forbidden, rejects success language over an
incomplete capsule, and rejects exit code zero without independent validator
PASS. The exact-binding positive case requires task, executor, capability
lease, workspace, capture, structured result and validator identity to remain
bound.

## Covered boundaries

- Historical Task138 wording remains allowed only under explicit historical classification.
- Duplicate dispatch/attempt identities cannot overwrite the append-only ledger.
- Raw private/prompt material is rejected by the formal ledger projection.
- A complete capture remains recoverable after bounded context loss; absent capture produces `OBSERVATION_INCOMPLETE` with reconciliation required.
- Plain GitHub CLI remains `TOOL_ONLY`; a reasoner runtime cannot close an external-Agent obligation.
- Structural Governance Surface authority escalation fails closed.

Machine evidence is in [`step08-live-observation-semantic-gate.json`](../../data/operations/iterations/139/step08-live-observation-semantic-gate.json), with the executable gate at [`validate_live_observation_semantics.py`](../../tools/validate_live_observation_semantics.py).

## Next gate

Step09 must re-attest the actual local executor census and compute an
executor-neutral `why_executor` selection. No inference was started by Step08;
the existing open reconciliation obligation remains unchanged.

Claim ceiling: Task139 repository-local live-observation semantic-boundary
evidence only; no validated live completion, external truth, production
readiness, Owner acceptance or epistemic acceptance is inferred.
