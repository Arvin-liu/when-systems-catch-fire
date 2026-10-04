# Task229-R4 Runtime Preregistration Revision R1

Status: runtime contract frozen for review; no provider call or R4 unit has run.

## Marker

`TASK229_R4_RUNTIME_PREREGISTRATION_R1_FROZEN_EXECUTION_NOT_STARTED`

## Frozen base and scope

- Formal repository: `Arvin-liu/when-systems-catch-fire`.
- Parent: PR #246, open, Draft, unmerged; frozen head `b7267180cb2afe735cdcb0e75583d2e356cadf98`.
- R1 branch: `work/IGNITION-20261004-229-R4-runtime-prereg-r1`.
- R1 subtree: `ignition/evaluation/ignition-229-r4-runtime-prereg-r1/`.
- R4 scientific package: the unchanged R0 subtree at the frozen parent. R1 adds only a runtime adapter, request/capture/timeout contracts, synthetic local fixtures, and forward instructions.
- R4 matrix remains the frozen 18 units, one attempt each, in its exact order. R1 changes no prompt, policy, binding, case prose, response schema, route schema, reference result, expected digest, outcome rule, or evaluator.

## Runtime choice

Use one fresh Python process per request, with `runtime_supervisor.py` outside the worker process. The worker sends one direct HTTPS `POST https://api.openai.com/v1/responses` request, then exits. No SDK, CLI session, conversation, prior response, prompt cache key, shell, MCP, browser, local tool, or provider tool is available to the model.

Every request freezes `model=gpt-6-astra`, `reasoning.effort=medium`, `tools=[]`, `tool_choice=none`, and `store=false`. No temperature, top-p, seed, background, conversation, previous-response, or output-format override is sent. The exact canonical request-body bytes are hashed before the network call. The API key is read from `OPENAI_API_KEY` and is never written to a receipt or printed. A later live invocation also requires the explicit environment gate documented in the future instructions.

The model input is assembled without paraphrase from the exact R3 prompt bytes, exact R3 response-schema bytes, and the unit's four frozen `successor_inputs` fields. The framing and canonical UTF-8 JSON encoding are fixed in `runtime_executor.py`. The frozen unit record and validator-side expected fields are never added to model context.

## Capture and limits

The transport capture is the HTTP response entity-body octet sequence returned after HTTP transfer framing is removed, before JSON decoding. The request sets `Accept-Encoding: identity`; any non-identity content encoding is rejected. This capture is not a TCP/TLS wire capture. A 1 MiB transport entity-body guard is separate from the 16,384-byte successor-payload limit.

The runtime writes and hashes `transport-response.bin` before parsing its JSON envelope. It then requires one completed assistant message with exactly one `output_text` block, UTF-8 encodes that exact decoded text as `successor_payload_bytes`, writes and hashes the full extracted bytes, and only then applies the 16,384-byte cap. This extraction necessarily decodes the JSON envelope's string escapes and re-encodes the resulting Unicode text as UTF-8; transport and successor-payload hashes therefore identify different byte layers. Oversized payloads are fully captured and rejected without truncation. The runtime does not parse the successor payload as JSON or run a schema validator.

The external supervisor enforces a 300-second wall timeout, starts a new process group, sends SIGTERM then SIGKILL to the entire group on timeout, classifies timeout as a consumed attempt, and never retries. A failed transport, timeout, refusal, malformed/ambiguous response, unsupported content encoding, or oversize payload remains a non-pass. No unit is replaced or repeated.

## Target-blind canary

Pattern A is frozen in `runtime-canary-contract.json`: one synthetic request in its own fresh process before any R4 unit, with no Task229 case, Task228 policy, binding, reference trace, expected route, evaluator, or target material. It tests endpoint/request acceptance and capture behavior only. It is not one of the 18 units and cannot tune R4 inputs or thresholds. If it fails or the requested model/effort cannot be recorded as accepted under the frozen rule, stop before all R4 units.

Canary calls in this preregistration task: `0`. The canary is a future gate and requires a separate explicit execution authorization.

## State and claim ceiling

At R1 closeout: `R4_EXECUTION_STARTED=false`, `LIVE_SUCCESSOR_RUNS=0`, `CANARY_CALLS=0`, `EVALUATOR_RUNS=0`, `TASK230_STARTED=false`. A green local test or exact-head CI result establishes only the reproducibility and completeness of this runtime preregistration package. It is not provider acceptance, a canary result, an R4 result, Owner acceptance, or authority to execute.

No R4 live unit, evaluator, or Task230 may be run from this task. PR #244 and PR #246 remain open, Draft, unmerged, and unchanged. This PR must remain Draft and unmerged.

## Required review residual

The parent R4 disclosure history is preserved in `leakage-boundary.md`. R1 records its additional control/package/repository reads there. Unknown/truncated scope remains unknown. Owner/GPT disposition of the newly disclosed R1 accesses is required before any later positive R4 result.
