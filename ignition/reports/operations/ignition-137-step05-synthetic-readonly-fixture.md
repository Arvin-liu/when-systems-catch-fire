# IGNITION-20260824-137 — Step 05 Synthetic Read-Only Fixture

Task137 now uses a fresh disposable fixture containing `README.txt`,
`nonce.txt`, and `table.json`. The nonce is a per-attempt synthetic 24-character
lowercase hex value. The table rule is explicit: retain rows with
`eligible=true` and `score>=50`, then sort by `(score, id)`. The expected
selection is `row-a`, `row-d`, `row-c`, with count `3`.

The child must return exactly four JSON keys:
`nonce`, `selected_ids`, `count`, and `workspace_digest_claim`. The latter is
the path-independent digest of the complete three-file tree captured before
dispatch. The validator re-reads `nonce.txt` and `table.json`, recomputes the
selection and count, checks the digest and read-only tree, rejects extra keys,
and rejects any forbidden side effect. The validator does not treat the
executor's claimed answer as an authority.

Targeted tests passed: `13 tests / 0 failures / 0 errors / 0 skips`, including
wrong answer, extra output key, table drift, workspace mutation, and digest
change cases.

Claim ceiling: deterministic synthetic fixture validation only; it says
nothing about real user data, external truth, production readiness, or Goal
completion.
