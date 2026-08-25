# IGNITION-20260826-140 Step 00 — Fresh baseline and Task139 semantic audit

The formal baseline was independently refreshed from `origin/main` and
`git ls-remote`: both are
`ff0adcc2bd736217691bc7c24db82df7577d12e8`. The supplied Documents directory
is not a Git worktree; this task uses the clean isolated branch
`codex/ignition-140-observation-plane-reconciliation-live-completion-r1-20260826`.

The repository-local Current preflight passed for Current Facts, Current
Snapshot, task lineage, volatile fact registry, Current State sync and Current
Surface semantics. Two deterministic projection checks were byte-identical.
The focused live/ledger/current suite ran 46 tests with 0 failures, 0 errors
and 0 skips. No live inference was started.

## Findings

Task139 is marked `PRESENTATION_ONLY`, but its behavior changed process
transport, host durable-capture ownership, the append-only live-attempt ledger
and the ledger-derived Current projection. Step02 will preserve the historical
receipt and add a correction/provenance record; it will not rewrite Task139.

Task139 sequence 4 recorded two public probes and `live_dispatch_calls=0`.
Its low-level `return_code: 0` is explicitly the last public-probe transport
value. There was no capture capsule and no live process, so no Agent process
return code or completion may be inferred from that zero.

The three open historical reconciliations are kept distinct:

- Hermes136 timed out with unknown external effect because PID/PGID and a
  durable disposable-workspace path were not captured. Equal workspace
  digests do not prove no effect.
- Codex138 second is known to have been dispatched, but host observation lost
  the process/result/capture/validator evidence. Its outcome remains unknown.
- Task139 stopped before live dispatch during filesystem-domain preflight.
  This can later close as `CLOSED_NO_LIVE_DISPATCH` without treating the probe
  zero as process success.

The complete machine audit is
`ignition/data/operations/iterations/140/step00-baseline-audit.json`.

Claim ceiling: repository-local baseline and semantic audit only; no external
truth, validated live completion, production readiness, Owner acceptance or
epistemic upgrade is inferred.
