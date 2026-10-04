# Capture semantics

## Layers

1. `request-body.sha256` hashes the exact canonical UTF-8 JSON bytes passed to the HTTPS request before any network activity. `runtime-context.json` records Python/runtime revision, source hash, requested model/effort, request hash, one-request count, and zero retries. The request body itself is not copied into a receipt.
2. `transport-response.bin` is the HTTP response entity body returned by Python `http.client`, after HTTP transfer framing such as chunk delimiters has been removed. It is persisted and hashed before decoding. The adapter requests `Accept-Encoding: identity` and rejects a non-identity `Content-Encoding`. This is not a raw TCP/TLS capture.
3. The transport body is strict-UTF-8-decoded and duplicate JSON object keys/non-finite values are rejected. Only one completed assistant `message` with one `output_text` block is accepted. Refusal, tool call, non-text item, multiple assistant messages, multiple content blocks, wrong model echo, or non-completed status is a non-pass.
4. JSON string escapes are decoded by the JSON parser. The resulting Unicode output text is encoded with strict UTF-8. Those bytes are named `successor_payload_bytes`, then persisted and hashed before the payload-size check. The transport and payload hashes are not interchangeable.
5. The worker checks the frozen 16,384-byte maximum after full payload capture. An oversized payload remains fully preserved and gets `SUCCESSOR_PAYLOAD_TOO_LARGE`; bytes are never sliced or dropped. The worker does not JSON-parse or schema-validate the successor payload.

## Incomplete captures

The HTTP entity body guard is 1 MiB. The adapter reads at most one byte beyond that bound to detect overflow, records the available prefix as an incomplete capture, classifies `TRANSPORT_BODY_LIMIT_EXCEEDED`, and does not parse it. No output from an incomplete capture can pass. There is no retry.

HTTP errors retain their available response entity body and status metadata, then stop before envelope interpretation. Response metadata is restricted to content headers, date, and request ID; authorization headers are never recorded.
