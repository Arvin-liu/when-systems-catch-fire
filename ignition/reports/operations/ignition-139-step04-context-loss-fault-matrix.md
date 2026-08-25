# IGNITION-139 Step 04 — Context-loss and oversized-output fault matrix

The new deterministic capture matrix contains 16 cases and all cases pass.
It separates two states that the old outer-tool path conflated:

- a complete host capsule with a bounded/truncated model-facing view is
  independently recoverable; and
- an incomplete capsule (durable cap, spool failure, or privacy rejection)
  must remain `OBSERVATION_INCOMPLETE` and require reconciliation.

The matrix also proves that malformed public JSONL does not erase raw stream
digests, a result event before large trailing logs remains recoverable, process
exit/timeout/signal state is explicit, duplicate finalization is idempotent, and
secret-like or hidden-reasoning output is rejected before it reaches the public
projection. The public view is cleared when the capture/privacy boundary fails.

No real external Agent was invoked. Claim ceiling remains repository-local
capture/recovery evidence only.
