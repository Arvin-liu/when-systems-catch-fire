# Bounded Thinking Operation Selector

The selector recommends one next thinking operation for a caller-declared, already-bounded run. It can return READ_MORE, VERIFY, DECOMPOSE, REFRAME_OR_CLARIFY, CAPACITY_OR_EXECUTOR_ESCALATE, REQUEST_OWNER_DECISION, or a terminal STOP.

It reads only one typed JSON request from stdin and the two local JSON Schemas. It emits one JSON recommendation. It does not execute an operation, call a tool, select a Goal, change the task frame, alter source evidence, infer hidden reasoning, grant authority, or authorize permissions. A recommendation to request an Owner decision does not contact the Owner.

## Invoke

Run:

    python3 -B ignition/tools/toolbox_bounded_thinking_operation.py --stdin

Provide one UTF-8 JSON object matching ignition/schemas/operations/toolbox-bounded-thinking-operation-input-r0.schema.json. Input is limited to 262144 bytes. Duplicate JSON keys, unknown fields, inconsistent first-failure ordering, unaffordable operations, and undeclared capabilities fail closed.

The sample at ignition/tests/fixtures/toolbox-bounded-thinking-operation/verify-needed-r0.json returns a VERIFY recommendation. Cost units and value bands are caller-declared planning inputs, not measured resource costs or calibrated probabilities. The selector requires a positive expected-value declaration and sufficient caller-declared budget for every non-STOP recommendation.

The synthetic F13 transfer fixture starts with a freshness obligation and no follow-up verification obligation. After a caller records that the fresh read revealed a required verification, the selector is run again on the updated state and recommends VERIFY. The selector never executes either operation or automatically advances to the next step.

## Rule order

1. Missing authority recommends REQUEST_OWNER_DECISION; it cannot be replaced with capacity escalation.
2. An unresolved frame recommends REFRAME_OR_CLARIFY.
3. A capability deficit recommends CAPACITY_OR_EXECUTOR_ESCALATE only after authority is present.
4. Required open verification recommends VERIFY; if unavailable, the terminal status is VERIFICATION_CEILING.
5. The remaining declared decomposition, freshness, and obligation deficits recommend DECOMPOSE or READ_MORE.
6. Repeating the same operation on the same observable state after failure or no state change stops with an explicit gap.
7. SUFFICIENT is emitted only when the caller declares no open obligations and no blocking deficits. It is not Goal completion or evidence that the declared state is true.

Each non-STOP recommendation is a proposal only. The caller must run an authorized operation separately, record its observable outcome and first failure, then submit the updated state if another decision is needed. The tool is experimental, default-off, and its Workbench pilot evidence is synthetic; this implementation has no claim about live-model reasoning quality or broad efficiency.

## Comparison and rollback

The existing adaptive toolbox route planner selects tools for typed input/output contracts; this selector chooses an operation class inside an already admitted run. They are complementary and do not replace each other. Comparative task quality and measured resource cost remain unknown.

To disable it, remove its experimental candidate card, entry point and references on the isolated toolbox branch, regenerate the identity-card JSON and TOOLBOX.md projections, and rerun the focused tests. Preserve the prior commit and evidence files as history.
