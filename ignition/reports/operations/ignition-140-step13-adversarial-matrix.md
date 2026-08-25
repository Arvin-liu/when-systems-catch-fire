# IGNITION-20260826-140 Step 13 — Adversarial / negative matrix

## Result

The required fail-closed matrix completed with **20 cases, 17 negative and 3
positive, all PASS**. It started **0 live processes**. The matrix exercises the
architecture-impact correction, typed probe/transport/process scope, durable
capture and completion gates, reconciliation unknown ceiling, executor-kind
admission, one-attempt-per-family retry policy, Task125 historical lineage,
soft-governance authority ceiling, and deterministic replay.

The negative cases reject probe return `0` masquerading as a live process
return, completion without a live dispatch, terminal unknown upgraded to
success, open-reconciliation retry, exit `0` without a result or validator,
wrong result/validator binding, workspace mutation, incomplete capture, raw
private ledger output, `gh` promoted to an Agent, reasoner runtime promoted to
an Agent, same-family blind retry, continuation after a validated completion,
Task125 marked executed, and authority inflation. The positive cases preserve
terminal unknown, permit a fresh identity after all old reconciliation is
terminalized, and prove projection/reconciliation replay idempotence.

Machine evidence: [`step13-adversarial-matrix.json`](../../data/operations/iterations/140/step13-adversarial-matrix.json).

The matrix is synthetic and repository-local. It did not start a live process,
does not establish a validated completion, and does not infer external truth,
production readiness, Owner acceptance or epistemic acceptance.
