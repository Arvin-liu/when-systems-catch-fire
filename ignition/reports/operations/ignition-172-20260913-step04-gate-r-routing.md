# IGNITION-172 Step04 — Gate R routing schema and precision pilot

Gate T exact-head CI is complete for parent `6d704d570827bf8d6ebb65fb65bcdd236056b4d3`. This step freezes a bounded routing sidecar and a precision-oriented pilot; it does not perform mass taxonomy routing or scholarly corpus admission.

- Primary taxonomy authority: 24 fields / 245 disciplines / 2178 subdisciplines.
- Pilot: 250 function assets + 500 nonfunction claims = 750 rows.
- Classification states: `{'CLASSIFIED': 182, 'MULTIDISCIPLINARY': 26, 'OUT_OF_UNESCO_SCOPE': 103, 'UNRESOLVED': 439}`.
- All 750 rows remain `PILOT_MANUAL_REVIEW_REQUIRED`.
- Hard-check violations: `0`.
- Live retrieval, abstract/full-text persistence, and corpus admission: disabled.
- Gate C remains required before any mass Formal ingestion.

Routing is a read-only projection. It cannot mutate canonical identity, M/E, disposition, ceiling, truth, proof, evidence maturity, or scholarly admission. Ambiguous and negative records remain bounded/manual-review states.
