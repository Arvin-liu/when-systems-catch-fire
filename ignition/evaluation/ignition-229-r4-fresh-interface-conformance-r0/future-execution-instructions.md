# Future Task229-R4 Executor Instructions

This document is a frozen future-execution package. Do not run it during preregistration. The next-direction string is a pointer, not execution authorization.

## Before the first unit

1. Obtain explicit authorization for R4 execution.
2. Verify the formal parent is exactly 9ef9a1b6ce47702a88af39f437dc3bbee33772fb and verify every allowed-input SHA-256.
3. Verify the exact Codex CLI version is 0.159.2 and that gpt-6-astra at medium reasoning effort is accepted. Record requested and accepted settings; do not claim a backend model echo if the runtime does not provide one. Any mismatch stops before a live call and requires a new preregistration.
4. Confirm PR #244 remains Open, Draft, Unmerged, with unchanged head 9ef9a1b6ce47702a88af39f437dc3bbee33772fb.
5. Confirm no forbidden source was opened and the disclosed access events have been recorded. Do not tune or change this package.

## Fixed invocation order

Run each of the 18 run IDs in run-matrix.json once, in its listed order. Use a fresh ephemeral CLI process and a separate read-only temporary workspace for each unit. Use UTF-8 stdin with shell disabled. Make no tools, shell, network, evaluator, or persistent history available.

For each unit, load only its successor_inputs record from execution-inputs.jsonl. Verify the exact policy and binding hashes before use. Parse the frozen policy and binding strings as strict UTF-8 JSON. Supply the exact frozen prompt template and response schema. The case_prose value is identical for every unit.

The reference_execution_json is a required structured input in the frozen R3 prompt. Do not add the validator-side expected digest, run matrix, receipt, or any prior response to the successor context. Never use one unit's output to alter another unit's input.

Use the frozen medium effort. Do not override temperature or top_p; the selected runtime does not expose preregistered controls for them. No seed is available. Enforce a 300-second timeout and a 16384-byte maximum raw response; reject oversized output without truncating it. Do not retry, replace, or repeat a unit.

## Capture and validation order

For each invocation:

1. Capture and persist raw response bytes.
2. Compute and persist SHA-256 before decoding or interpreting.
3. Record process exit, timeout, runtime version, accepted model/effort, session identity, and input hashes.
4. Decode strict UTF-8 and validate the response against the frozen R3 response schema.
5. Validate route trace with the exact frozen R3 validator.
6. Compare every route field against the validator-side deterministic reference and assign the first applicable label from mechanical-outcome-contract.json.
7. Write a run-level receipt without answer-quality judgments.

If a protocol/source/hash deviation occurs, stop immediately; do not invoke remaining units. Do not repair, tune, or rerun under this preregistration. Timeouts, refusals, and infrastructure failures consume their one attempt and remain non-pass outcomes.

## Closeout

Aggregate only the 18 frozen unit outcomes under the preregistered threshold definitions. Do not run a target evaluator. Do not make compatibility, quality, policy-effect, transfer, causal, generalization, training, or Task230 claims.

Before claiming any positive R4 result, obtain and record Owner/GPT disposition of the preregistration access events in leakage-boundary.md. Task230 remains unauthorized.
