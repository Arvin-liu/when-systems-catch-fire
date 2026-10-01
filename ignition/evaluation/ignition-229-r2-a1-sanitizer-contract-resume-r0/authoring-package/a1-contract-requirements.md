# R2-A1 synthetic-only contract requirements

This file and `metadata-key-contract.json` are prospective A1 inputs. The exact JSON manifest is the only source for removable key names. The frozen sanitization procedure, original response schema, blind schemas, and deny-token manifest are copied byte-for-byte from the verified R2 authoring package. This package contains no real R1 response, real case, target, policy text, evaluator content, condition-to-outcome result, or historical Attempt-1 content.

## Exact key rules

For JSON object keys only, canonicalize with lowercase, then replace each hyphen with an underscore. Do not trim whitespace, strip punctuation, stem words, change singular/plural forms, or use substring or prefix/suffix matching. Remove the complete value for a key only when its canonical key is exactly `route_trace`. Remove a key by name only when its canonical key is in the exact 11-key list in `metadata-key-contract.json`. No implementation may add a private alias set. Every unlisted field remains present and is then validated against the unchanged original frozen response schema; schema-invalid input fails closed.

## Frozen synthetic coverage

`synthetic-contract-fixtures.json` freezes all inputs and expected outcomes before builder/checker authoring. It covers every exact removable key; lowercase, uppercase, and mixed-case forms; underscore and hyphen spellings; whole-object route trace removal; nested removals; every literal deny token in synthetic response text; preservation of all scored fields except exact-token replacement; each required near miss; additional route-trace near misses; fail-closed behavior under the original schema; and canonical deterministic packet bytes.

Near-miss keys are not added to or removed from the response schema. The unchanged schema has `additionalProperties: false`; an unlisted field that survives sanitization therefore has an expected `SCHEMA_INVALID_SURVIVING_UNLISTED_KEY` outcome.

## Process and gate constraints

Author exactly one new builder and one new checker from scratch in two fresh isolated CLI processes. Each process sees only this frozen target-blind package and its own role prompt. The checker process must not see builder source; the builder process must not see checker source. Both programs must read `metadata-key-contract.json` as data on every invocation and report its raw SHA-256, exact key sets, and supported canonicalization rules. Both must be Python standard-library-only. Neither may import, execute, patch, or reuse any R1/R2 builder or checker.

The synthetic gate runs both programs against every frozen fixture. Successful outputs must match their frozen canonical bytes; the builder must be deterministic over two repeated invocations per successful fixture; the checker must independently accept each successful packet and reject every intentional mutation. Every frozen near miss must fail schema validation exactly as specified. The gate checks exact contract equality, contract-driven behavior, no private key aliases, scored-field preservation, full-packet zero-token leakage, and no real-data access. A test-only alternate manifest probe must demonstrate that both programs remove a synthetic key named only in that manifest while preserving an unlisted `provenance` key so the original schema rejects it. No implementation source may change after any later real-data access.
