# R2-A1 independent packet checker specification

Implement one deterministic Python standard-library-only `checker.py` from scratch in a separate fresh CLI process. Do not import or execute builder code. Use only the files in this frozen package. The `metadata-key-contract.json` bytes are normative and are read as data at runtime; do not embed any exact metadata or route-trace key names in code.

## Interface

`checker.py --response PATH --case-id A|B|C --response-id ID --case PATH --criteria PATH --deny-token-manifest PATH --response-schema PATH --metadata-key-contract PATH --packet PATH`

Also support `--contract-report PATH` as a standalone mode that emits a JSON report containing the SHA-256 of the exact manifest bytes, its canonicalization operations, and its whole-object and metadata removal key arrays exactly as loaded. This mode must not read any other input.

## Independent verification

1. Independently parse the original response envelope, contract, deny-token manifest, schema, case bytes, criteria bytes, and candidate packet. Strictly decode UTF-8 and verify case/criteria decode/re-encode equality and SHA-256.
2. Derive the exact recursive route-trace and metadata removals only from the runtime contract data; validate the sanitized envelope against the unchanged original schema, fail closed on remaining unknown fields, and select exactly one requested case response.
3. Apply exact literal deny-token replacement to response string leaves using the frozen order (descending token length, then lexical order). Do not import or call builder code.
4. Deep-compare the candidate packet against the independently derived expected packet. Require exact response ID and case ID, exact case/criteria bytes and hashes, canonical serialization including one final LF, complete absence of a route-trace field, unchanged scored fields except exact-token redaction, and zero literal deny-token matches anywhere in the full serialized packet.
5. Reject every mismatch without modifying the candidate packet. Diagnostics are concise and never echo source or packet content.

This checker does not score or interpret responses. It has no access to any real R1 response, real case, target, policy, evaluator artifact, condition-to-outcome result, historical Attempt-1 content, or repository path beyond explicitly supplied synthetic fixture paths.
