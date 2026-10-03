# Task229-R4 Fresh Interface Conformance Preregistration

Status: frozen preregistration package; no live execution has started.

## Question

When a live successor is given the frozen R3 successor prompt, frozen Task228 policy, explicit R1 typed binding, and allowed visible case prose, can it emit a response whose route/interface fields conform mechanically to the frozen R3 deterministic reference contract?

R4 measures interface execution conformance only. It does not score answer correctness or quality, target compatibility, policy effect, transfer, causal effect, revision quality, generalization, Cognitive Evolution, Model-RSI, or training benefit.

## Frozen entering state

- Formal repository: Arvin-liu/when-systems-catch-fire.
- PR #244: Open, Draft, Unmerged; head 9ef9a1b6ce47702a88af39f437dc3bbee33772fb.
- R3 final marker: TASK229_R3_TRANSFER_INTERFACE_CONTRACT_REPAIRED.
- R3 receipt: Arvin-liu/1111 commit d8ac3cf567c6a77a754044a28259253810334f69.
- R3 next direction: NEXT_DIRECTION=PREREGISTER_FRESH_INTERFACE_CONFORMANCE_TASK229_R4.
- The R3 receipt records R4 not started and Task230 not started.
- All six policy byte hashes match the R3 contract. The R3 receipt records synthetic conformance 49/49 and historical binding migration 18/18.

R4 starts from the exact R3 head in a new branch and subtree. It does not change R3 or PR #244.

## Frozen sources and case prose

The allowed-input manifest pins every source path and SHA-256. The six policies are read-only. The historical input map is used only to build R1 bindings from its case_inputs_by_lineage entries for L01-L06 and A/B/C. The generated execution package does not copy route_expectations_by_lineage.

No historical case prose is used. The frozen R3 prompt still receives its required case_prose field; every run receives the same fixed neutral sentence:

No narrative case details are supplied beyond the explicit typed binding.

This choice is recorded explicitly. It keeps the preregistered interface question intact while avoiding historical prose that is unnecessary for testing typed binding and reference-trace serialization. No prose is derived from targets, scores, labels, or evaluator comments.

The frozen prompt also requires reference_execution_json as a structured successor input. That payload contains the deterministic R3 reference result and route trace. The separate expected route-trace digest is held in the validator-side run matrix and is not supplied as a separate target or as prose.

## Run matrix

The matrix contains 18 units: six frozen Task228 policies, each paired with its three frozen case slots A/B/C for lineages L01-L06. Order is fixed by ascending lineage, then A, B, C. Each unit receives one invocation in a fresh ephemeral process. There are no retries, replacements, selective reruns, or additional repetitions.

The R3 migration proof confirms 18/18 value and missingness preservation. Six units contain policy-required missing inputs; those IDs remain absent from bindings and must remain in the route trace missing_input_ids.

Each unit freezes its run ID, case and policy IDs, policy SHA-256, binding SHA-256, source-case provenance SHA-256, prompt/schema digests, model/provider slot, controllable decoding settings, tool availability, retry policy, timeout, output limit, reference status, and expected deterministic route-trace digest.

## Execution and outcome rules

The future executor uses the exact frozen R3 prompt, response schema, route-trace schema, policies, bindings, and reference payloads. It captures raw response bytes and hashes them before parsing. It then validates UTF-8, the response schema, and the route trace using the R3 validator plus exact field comparison.

A unit passes only if the response schema is valid, the response is ROUTED, interface_error is null, and every route-trace field equals the deterministic R3 reference. Response text is checked only for the schema's non-empty-string requirement; no semantic answer-quality review is permitted.

The mechanical outcome contract defines a single primary label per invocation, a fixed field-comparison order, exact full/partial/no-establishment thresholds, and the stop rule for protocol deviations. Timeouts, refusals, and infrastructure errors consume their only attempt and are never excluded or replaced.

The planned live model slot is OpenAI Codex CLI 0.159.2 requesting gpt-6-astra at medium reasoning effort. Runtime version and accepted model/effort must be recorded. If the exact runtime or settings cannot be established before the first call, stop without invoking a successor and create a new preregistration version.

## Leakage and claim limits

Only successor_inputs in execution-inputs.jsonl are sent to a successor. The validator-side run matrix, expected digests, receipts, other responses, and preregistration analysis are withheld. No evaluator, target answer, score, target success label, or sealed target criterion is supplied or run.

A live-interface pass establishes only mechanical conformance under this exact prompt and matrix. It does not establish that an answer is correct, that a policy helps, or that a route is compatible with a target.

The preregistration access log is in leakage-boundary.md. Its disclosed broad/truncated reads must be dispositioned by Owner/GPT before any positive R4 result is claimed.

## Current state

R4_EXECUTION_STARTED=false
LIVE_SUCCESSOR_RUNS=0
EVALUATOR_RUNS=0
TASK230_STARTED=false

Preregistration marker: TASK229_R4_PREREGISTRATION_COMPLETE_EXECUTION_NOT_STARTED

Next direction: NEXT_DIRECTION=EXECUTE_FROZEN_TASK229_R4_INTERFACE_CONFORMANCE

The next direction is a pointer only and does not authorize execution.
