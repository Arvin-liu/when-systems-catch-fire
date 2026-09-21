# Step07 — Future Successor Task Manifest

This is a frozen preparation manifest, not an execution command. It defines the
six future same-model Successor conversation slots for Task198:

- `FACTS_ONLY`: A/B
- `METHOD_TRACE`: A/B
- `BROKEN_METHOD_TRACE_CONTROL`: A/B

Each slot has a predeclared case order, a distinct future branch name, a local
output directory, and a packet-manifest hash. The packet manifest is the sole
source of the exact read allowlist; the future runner must verify that final
byte hash before reading any packet content. No evaluator criteria are in a
Successor allowlist.

The six slots remain `NOT_RUN`. The manifest does not authorize execution,
external search, a cross-model trial, a commit or push from a future
Successor, canonical promotion, MetaRSI/Model-RSI work, or weight training.
No file is written to `Arvin-liu/1111` by this step.

The normal terminal state reserved for each future local-only run is
`SUCCESSOR_TRIAL_LOCAL_ONLY_COMPLETE`; the final Task198 preparation stop is
`READY_FOR_REPLICATED_METHOD_USE_SUCCESSOR_TRIALS`.
