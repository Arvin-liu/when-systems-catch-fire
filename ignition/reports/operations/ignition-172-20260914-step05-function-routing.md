# IGNITION-172 Step05 — full function asset routing overlay

This logical step is based on the exact frozen parent `03a2b33cced830418cc310a59b519fca8d10f2fa` on the existing Task172 branch and Draft PR #218.

- Authority: `data/foundation/function-assets/identity-cards.jsonl`; `6158` canonical rows, one routing row per canonical ID.
- Taxonomy: 1988 UNESCO primary lock, 24 fields / 245 four-digit disciplines / 2178 six-digit subdisciplines. The overlay never invents a four-digit equivalence; empty discipline facets remain explicit unresolved routing information.
- Classification states: `{'CLASSIFIED': 1315, 'MULTIDISCIPLINARY': 283, 'OUT_OF_UNESCO_SCOPE': 4560}`. Field tags are the conservative Gate R classifier projection; unresolved and out-of-scope rows remain retained and auditable.
- Routing use: `4885` negative/quarantined/withdrawn boundary rows are restricted to historical/negative review routes. `1881` rows have field facets; field counts are `{'12': 709, '22': 136, '23': 3, '24': 29, '32': 8, '33': 170, '52': 35, '53': 66, '54': 2, '55': 277, '56': 95, '57': 47, '58': 7, '59': 39, '61': 198, '62': 35, '63': 11, '71': 14}`.
- Evidence boundary: all rows are `FULL_ROUTING_MANUAL_REVIEW_REQUIRED`; routing is not evidence, proof, maturity, truth or publication promotion. Canonical identity, M/E, disposition and claim ceiling remain in their authority registries.
- Determinism: sorted canonical IDs, frozen source hashes and no network/retrieval/write side effect beyond the generated overlay and step receipt.

Decision: `STEP05_FULL_FUNCTION_ASSET_ROUTING_OVERLAY_READY; MANUAL_REVIEW_REQUIRED; NO_CANONICAL_MUTATION`.
