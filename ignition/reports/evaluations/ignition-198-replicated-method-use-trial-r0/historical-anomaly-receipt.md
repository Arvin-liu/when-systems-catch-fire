# Step01 — Historical Task190 Transfer Hash Anomaly Quarantine

Task198 fixes the historical status of the Task190 `TRANSFER-01` manifest
anomaly as:

`TASK190_TRANSFER_HASH_ANOMALY_HISTORICAL_ONLY`

The Task190 manifest declares case-source SHA-256
`86a6c180fc6f2d7b3eba827b6192294131132628b043864b1dfcf03515e18c3b`, while
the exact-base `case-source.md` bytes hash to
`d84b69036c76553e066a04f035b2f1208d10ee092da04194df34cddfb4c1e466`.

This is a retained and disclosed historical artifact. Task198 does not mutate
the Task190 manifest, does not silently repair old evidence, and does not
invalidate Task197 bounded evidence beyond the disclosed metadata scope.
`TRANSFER-01` is not reused as a new replicated case.

For every Task198 case, the builder must compute manifest, source, and
provenance SHA-256 values directly from the final bytes and require equality
before any future Successor or Evaluator action. A mismatch is a hard stop.

The companion JSON records the exact historical artifact hash and the fixed
future validation rule. Step01 itself runs no Successor and no Evaluator.
