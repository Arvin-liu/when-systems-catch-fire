# Step09 — Path Accounting and Fixed Point

The Task198 preparation surface is confined to the task-local path prefix in
`path-accounting.json`. The declared inventory covers the three fresh cases,
the six condition/replicate packets, the sealed criteria and evaluator package,
the future-only task manifest, the protocol freeze, their validators, and the
prior preparation receipts.

The accounting digest is over sorted path names relative to the exact Task197
source commit. It is intentionally a name-only fixed point: the accounting
JSON carries the inventory digest, while its sidecar hashes the finalized JSON
bytes. This makes the final two-pass check finite and independently testable.

`canonical_claim_ids`, canonical promotion, Foundation, Current, Fire Seeds,
R1, MetaRSI, Model-RSI, and weight-training artifact sets are all empty. Any
unregistered path or any mutation outside the task-local prefix is a hard stop.

No Successor or Evaluator conversation is run by this step. The preparation
stop remains `READY_FOR_REPLICATED_METHOD_USE_SUCCESSOR_TRIALS`.
