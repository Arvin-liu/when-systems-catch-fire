# Step04 — TRANSFER-01 Condition Contrast

Input freeze: `8b90854dc20a58415dfbf5e0984aa596450db5ea`

Bounded transfer disposition: `BOUNDED_METHOD_TRANSFER_SUPPORTED`

| Condition | T-SOURCE-BOUND-SELECTION | T-APPLICATION-LINEAGE | T-NON-TEMPLATE-REASONING | T-CLAIM-CEILING |
| --- | --- | --- | --- | --- |
| FACTS_ONLY (195) | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | PASS |
| METHOD_TRACE (196) | PASS | PASS | PASS | PASS |

The FACTS_ONLY response accurately reports the P0, gate-alpha, replay, and missing gate-beta observations. It proposes matched-context evidence and keeps `method_source_available=false` and `method_selected=null`.

The METHOD_TRACE response selects the supplied `method:two-hypothesis-replay-probe-r0`, explains why it fits the changed gate-alpha/replay context, holds the recorded input constant, compares the two channels, computes the supplied right-channel difference, retains the missing beta reading, and explicitly rejects causal attribution.

The transfer-case manifest contains a disclosed metadata anomaly: its declared case-source SHA differs from the SHA of the exact-base `case-source.md`. The actual bytes and exact-base Git blob are independently frozen and are the bytes used by the Successor manifests/response lineage; the discrepancy is retained as an input anomaly, not silently corrected.

This is a single-run, non-randomized, non-repeated descriptive contrast. It does not show that METHOD_TRACE caused an improvement, does not establish general method transfer, and does not establish general cognitive inheritance or cross-model transfer.

Fixed ceilings remain `GENERAL_COGNITIVE_INHERITANCE_NOT_ESTABLISHED`, `R1_NOT_AUTHORIZED_BY_EVALUATOR`, `CROSS_MODEL_TRANSFER_NOT_RUN`, `OWNER_GPT_ADJUDICATION_NOT_RUN`, and `NO_CANONICAL_PROMOTION`.
