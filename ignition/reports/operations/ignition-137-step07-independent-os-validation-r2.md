# IGNITION-20260824-137 — Step 07 Independent OS Validation R2

`LiveIndependentValidator` now accepts an executor result only in
`RETURNED_UNVALIDATED` state and emits a separate
`ignition-137-independent-validation-receipt-r2`. That receipt binds the
task, dispatch, attempt, executor, adapter, capability-lease digest,
workspace reference and before/after digests, result digest, executor receipt
digest, and its own validator receipt digest.

Validation independently checks lease integrity/freshness, permission
intersection, strict four-key output, the fixture's recomputed answer,
unchanged workspace, read-only/no-forbidden external surface evidence,
receipt integrity, and exact child depth one. A validation PASS is possible
only after every check passes; executor PASS text or exit code alone cannot
produce it.

Targeted tests passed: `13 tests / 0 failures / 0 errors / 0 skips`. Stale
lease, forged/wrong/copy-reused result, wrong workspace, and executor
substitution fixtures all fail closed.

Claim ceiling: this is an independent synthetic validator contract. It does
not itself prove that a real external process has run.
