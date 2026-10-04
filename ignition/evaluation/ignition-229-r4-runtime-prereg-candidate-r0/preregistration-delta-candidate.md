# Candidate delta for a separately reviewed R4 runtime preregistration

Status: **candidate only; not accepted, frozen, or executed**.

Base: frozen R4 preregistration `b7267180cb2afe735cdcb0e75583d2e356cadf98`.

## Observed limitation

The local Codex CLI is exactly `0.159.2`. Its local model catalog lists `gpt-6-astra` as API-supported and lists `medium` reasoning. The runtime did not establish an empty model-facing tool catalog, a hard 300-second process timeout, or capture and enforcement of a 16,384-byte raw response limit before decoding. Backend acceptance of the requested model/effort was not observable without a live call, and no canary call is permitted by the frozen one-attempt matrix.

## Minimal candidate change

For a new preregistration only, replace the unverified `codex exec` tool surface with a small, pinned, one-request-per-process Responses API executor that:

1. Pins the executor source hash, request serializer version, endpoint, model, and reasoning settings. It requests `gpt-6-astra` with `medium`; a response's observable model/effort metadata is recorded only if returned.
2. Sends an explicitly empty tool list and a no-tool selection, with no shell, browser, MCP, app, or network tools available to the successor. The executor process itself may contact only the model endpoint required to make the request.
3. Uses the exact frozen successor input bytes for one unit, starts a fresh process and temporary workspace per unit, and sends no prior response, receipt, matrix, validator expectation, or evaluator material.
4. Captures the HTTP response body as raw bytes, enforces the 16,384-byte cap while streaming and before JSON/UTF-8 decoding, and stores those exact bytes plus SHA-256 before parsing.
5. Applies an externally supervised 300-second wall-clock limit and records timeout/exit status. Timeout, refusal, oversized output, malformed output, and all mechanical failures consume the sole unit attempt.
6. Keeps the fixed L01-A through L06-C order, one call per unit, zero retries, frozen prompts/bindings/policies/schemas/validators, and existing claim ceiling unchanged.

This changes the runtime/client contract and requires a new preregistration hash set, exact request-envelope definition, independent runtime-gate verification, and Owner/GPT approval before any call. The proposal is not evidence that this executor exists, that the model endpoint accepts the request, or that a future run may start. Do not probe or execute it under the current R4 authorization.

## Frozen semantics preserved in this candidate

- The 18-unit matrix and its order are unchanged.
- No frozen prompt, schema, policy, typed binding, reference payload, expected trace, outcome contract, or validator is edited.
- The claim ceiling remains reference-assisted mechanical interface/serialization conformance only.
- No evaluator, Task230, merge, Ready transition, second live experiment, or repaired run is authorized.
