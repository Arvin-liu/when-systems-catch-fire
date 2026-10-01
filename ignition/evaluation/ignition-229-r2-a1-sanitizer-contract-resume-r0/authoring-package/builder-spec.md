# R2-A1 packet builder specification

Implement one deterministic Python standard-library-only `builder.py` from scratch. Use only the files in this frozen package. The `metadata-key-contract.json` bytes are normative and are read as data at runtime; do not embed any exact metadata or route-trace key names in code.

## Interface

`builder.py --response PATH --case-id A|B|C --response-id ID --case PATH --criteria PATH --deny-token-manifest PATH --response-schema PATH --metadata-key-contract PATH --output PATH`

Also support `--contract-report PATH` as a standalone mode that emits a JSON report containing the SHA-256 of the exact manifest bytes, its canonicalization operations, and its whole-object and metadata removal key arrays exactly as loaded. This mode must not read any other input.

## Processing

1. Read all JSON and text input bytes as strict UTF-8. Parse the response envelope and manifests as JSON. Require strict UTF-8 decode/re-encode byte equality for case and criteria bytes; record their SHA-256 hashes.
2. Validate the contract shape/version and use only its ordered key-canonicalization operations. Canonicalization applies only to object keys. Recursively walk objects and arrays: remove a field's complete value when its canonical key is exactly in `whole_object_removal_canonical_keys`; otherwise remove it only when the canonical key is exactly in `exact_metadata_removal_canonical_keys`; recursively process every retained object/array child. Do not invent aliases.
3. Validate the sanitized response envelope against the supplied unchanged original frozen response schema. Fail closed on any remaining unknown property or any other schema/shape error. Require exactly three distinct case IDs A/B/C and select exactly one response for the requested case.
4. Redact only exact literal strings listed in `deny-token-manifest.json` from response string leaves, longest token first and then lexical order. Preserve every other response value and array order. Do not transform case or criteria bytes.
5. Emit one packet with the fixed schema version and fields in the frozen R2 packet contract. Use canonical UTF-8 JSON: `ensure_ascii=false`, sorted object keys, compact separators, exactly one trailing LF. Before writing, scan the entire serialized packet for every exact deny token and fail closed on any match. Do not log packet or source content. Identical inputs produce byte-identical output.

Exit nonzero without creating a packet on invalid input. Diagnostics must be concise and must not echo source values. Do not access the network, external sources, real R1 files, cases, targets, policies, evaluator artifacts, historical Attempt-1 content, or any repository path outside the package and explicit CLI input paths.
