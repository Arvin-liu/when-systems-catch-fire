# Step10 preflight and handoff

## Scope

This is the final Builder / Research-Experiment Preparation step. The branch
starts from Task189 exact head `ca641a87ad7bc16d18a65f37cbe37b9a5cb733c8`,
targets stacked Draft base
`eval/IGNITION-20260919-189-r0-4-independent-evaluation`, and keeps all
Task190 surfaces research/evaluation-only.

The per-step exact heads and one-commit/one-fast-forward ledger are in
`step-ledger.json`. The machine-readable preflight is in
`step10-validation-receipt.json`.

## Validation boundary

The task-local validator and all four fixture expectations passed. Step09 path
accounting passed its two-pass fixed point with zero candidate fragments and
zero canonical claim IDs.

A direct local full-history clone was attempted over HTTPS and SSH and was
blocked by the environment's GitHub TLS/connection failure. Exact-head PR CI is
the authoritative replacement: the existing workflows use
`actions/checkout@v4` with `fetch-depth: 0`, and Foundation validation uses
the PR head SHA.

The PR must remain Draft, Open, and unmerged. After all exact-head CI workflows
are successful, the PR body is the final handoff record for the Step10 commit
SHA, CI run IDs, and the stop state:

`READY_FOR_METHOD_USE_TRACE_SUCCESSOR_TRIAL`.

## Fixed declarations

`R0_4_PROTOCOL_ADOPTED_PROVISIONALLY_AS_EXPERIMENTAL_BASELINE`

`PARTIAL_BOUNDED_METHOD_TRANSFER_EVIDENCE_ACCEPTED`

`GENERAL_COGNITIVE_INHERITANCE_NOT_ESTABLISHED`

`R1_NOT_AUTHORIZED`

`CROSS_MODEL_TRANSFER_NOT_RUN`

`SUCCESSOR_NOT_RUN`

`EVALUATOR_NOT_RUN`

`NO_CANONICAL_PROMOTION`
