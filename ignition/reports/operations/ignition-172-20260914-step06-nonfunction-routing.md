# IGNITION-172 Step06 — full nonfunction claim routing overlay

This logical step is based on the exact frozen parent `03a2b33cced830418cc310a59b519fca8d10f2fa` on the existing Task172 branch and Draft PR #218.

- Authority: `data/foundation/nonfunction-claims/claim-registry.jsonl`; `18003` canonical rows, one routing row per canonical ID.
- Taxonomy: 1988 UNESCO primary lock, 24 fields / 245 four-digit disciplines / 2178 six-digit subdisciplines. The overlay never invents a four-digit equivalence; empty discipline facets remain explicit unresolved routing information.
- Classification states: `{'CLASSIFIED': 7684, 'MULTIDISCIPLINARY': 2110, 'OUT_OF_UNESCO_SCOPE': 1885, 'UNRESOLVED': 6324}`. Field tags are the conservative Gate R classifier projection; unresolved and out-of-scope rows remain retained and auditable.
- Routing use: `9885` negative/quarantined/withdrawn boundary rows are restricted to historical/negative review routes. `11904` rows have field facets; field counts are `{'12': 3749, '22': 663, '23': 6, '24': 132, '32': 82, '33': 504, '52': 10, '53': 202, '54': 25, '55': 661, '56': 464, '57': 252, '58': 126, '59': 851, '61': 683, '62': 2471, '63': 302, '71': 21, '72': 700}`.
- Evidence boundary: all rows are `FULL_ROUTING_MANUAL_REVIEW_REQUIRED`; routing is not evidence, proof, maturity, truth or publication promotion. Canonical identity, M/E, disposition and claim ceiling remain in their authority registries.
- Determinism: sorted canonical IDs, frozen source hashes and no network/retrieval/write side effect beyond the generated overlay and step receipt.

Decision: `STEP06_FULL_NONFUNCTION_CLAIM_ROUTING_OVERLAY_READY; MANUAL_REVIEW_REQUIRED; NO_CANONICAL_MUTATION`.
