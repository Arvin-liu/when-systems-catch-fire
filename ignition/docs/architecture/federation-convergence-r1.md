# Cross-Executor Convergence R1

`ProgressLedger` sorts public `FederatedProgressEvent` records by task,
sequence, executor and stable event key.  Duplicate keys are ignored; late
events are retained for audit but cannot regress the canonical highest-sequence
view.  A late terminal event is explicitly classified as `LATE_TERMINAL`, and
post-terminal non-terminal progress is classified rather than silently
promoted.

`ReceiptRegistry` retains only digest, terminal status, validator refs and
artifact ref names.  A receipt is `VERIFIED` only when a
`COMPLETED_VALIDATED` receipt carries validation refs; executor-reported
completion without evidence is `UNVERIFIED`.  Raw vendor event streams,
session histories, prompts, hidden reasoning and token telemetry never enter
the registry or memory projection.

`MemoryProjection` is the only bridge into the existing
`OperationalMemoryStore`.  It accepts public progress summaries, validated
receipt evidence, failures, approval decisions and recovery decisions.  The
in-process absorber deduplicates event keys and memory IDs so duplicate/retry
events cannot be absorbed twice.  The resulting operational memory retains its
existing claim ceiling: recall is not Knowledge truth, proof or permission.
