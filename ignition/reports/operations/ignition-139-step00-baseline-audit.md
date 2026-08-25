# IGNITION-139 Step 00 — Baseline and observation-path audit

The formal worktree starts from the independently checked `origin/main` baseline
`12205be8ad94916a39253e0eba2106bf5da9da12`. No live inference was started.

The existing Current preflight was green before implementation: task-lineage,
Current-state sync, volatile-fact registry, Current semantic gate, and two-pass
Current projection determinism all passed. The focused live/ledger/Current test
set ran 36 tests with 0 failures, 0 errors, and 0 skips.

## Historical fact that must become canonical

The Task138 second Codex dispatch was a real attempt. Its host result exceeded
the available model context, and the receipt could not be recovered. Return
code, structured result, lease receipt, and validator input were unavailable.
The correct ceiling is therefore `ATTEMPT_HAPPENED_OBSERVATION_INCOMPLETE` /
`REQUIRES_RECONCILIATION`; it is neither success nor a known startup failure.

The current identity contract still described that same invocation as forbidden
because no auth-source route was available. This is the Step139 split-brain to
repair. Historical Task136–138 source records remain append-only and are not
rewritten.

## Existing transport finding

`LiveProcessTransport` streams OS pipes into in-memory bounded bytearrays and
returns `LiveProcessResult` only after process handling. Its output cap stops the
process group, and adapters parse the returned stdout after the process exits.
There is no host-side durable spool initialized before dispatch, no resumable
capture capsule, and no recovery path independent of the outer model/tool
context. Runtime scratch is attempt-specific and correctly ephemeral, but it is
not an observation journal. The generic Event Ledger is append-only, but it does
not bind live attempt, lease, workspace, capture completeness, or validator
evidence.

Step139 therefore proceeds in this order: durable capture contract, append-only
attempt ledger, transport integration, deterministic context-loss fault tests,
historical import, and only then Current projection repair and any one-time live
admission.

Claim ceiling: repository-local audit evidence only. No external Agent
completion, production readiness, Owner acceptance, or epistemic acceptance is
claimed.
