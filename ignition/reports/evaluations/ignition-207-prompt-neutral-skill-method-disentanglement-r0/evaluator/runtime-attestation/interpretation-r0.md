# Runtime Attestation Receipt R0 — Use and Interpretation

This contract prepares later experiments to record what runtime configuration was requested, what the runtime reported, and which fields an independent source actually verified. It does not run a model, select a model, authorize cross-model work, or establish a cognitive-inheritance claim.

## Required capture

Create one receipt per independent conversation. Bind the opaque packet ID, conversation ID, exact prompt/packet/schema hashes, requested and observed provider/model/version/deployment/API fields, sampling settings, response format, tool-configuration hash, runtime/client versions, pseudonymous host image hash, UTC interval, request count, tool-trace hash, response hash, and hashes for verification evidence. Keep credentials, raw tokens, authorization headers, and secret environment values out of the receipt and evidence bundle.

`requested_configuration` records the assignment or command. `observed_configuration` records what a runtime/provider response or independent execution log actually says. Copying the requested values into the observed fields is not observation. A client log or operator command is provenance about that client or command; by itself it does not independently verify the provider's resolved model identity.

## Status rules

- `COMMAND_ASSIGNED_NOT_INDEPENDENTLY_VERIFIED`: configuration was assigned or declared, but there is no qualifying independent evidence for the resolved runtime fields. This preserves the Task206 boundary.
- `PARTIALLY_INDEPENDENTLY_VERIFIED`: at least one field has qualifying independent evidence, but the complete identity/configuration set is not covered.
- `INDEPENDENTLY_VERIFIED`: an independent verifier, separate from configuration and trial execution, checked every applicable identity/configuration field against hash-bound independent evidence. A validator can check completeness and declared source types; it cannot authenticate a remote signature or prove an evidence provider trustworthy on its own.
- `UNVERIFIED`: no field has independent verification.
- `INCOMPLETE_RECEIPT`: required fields or hashes are absent, malformed, inconsistent, or contain a secret value.

For later cross-model comparison, independently verify provider, model ID and version, applicable deployment/API identity, runtime mode, system/developer prompt hashes, sampling, response format, tool configuration, and the independent evidence source for each. A receipt marked `INDEPENDENTLY_VERIFIED` is evidence about configuration only. Cross-model execution still requires its own authorization and protocol; this receipt grants neither.

## Canonical hash

`receipt_sha256` is SHA-256 over the receipt JSON encoded as UTF-8 after parsing and re-serializing with sorted keys, no insignificant whitespace, `ensure_ascii=false`, and with the `receipt_sha256` property omitted. Evidence objects point to separate files/URIs and include each content SHA-256. A detached signature may be referenced by path or URI; do not place private keys or signature secrets in the receipt.

## Validation interpretation

The validator checks JSON Schema shape, self-hash, secret-like property names, status/evidence consistency, independent-verifier completeness, and verification coverage. It does not contact a provider or independently authenticate evidence. A PASS means only that the receipt is internally complete under this contract; it does not grant R1, cross-model authorization, evaluator acceptance, or canonical status.

No real runtime receipt is included in this preparation. Task206 remains `COMMAND_ASSIGNED_NOT_INDEPENDENTLY_VERIFIED` as frozen in the adjudication input.
