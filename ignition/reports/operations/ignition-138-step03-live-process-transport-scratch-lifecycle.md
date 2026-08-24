# IGNITION-20260824-138 — Step 03 Bounded Process Transport Scratch Lifecycle

The existing literal-argv, explicit-cwd, bounded stdout/stderr and
process-group transport now accepts an attempt-specific `RuntimeScratchLease`.
The lease is created as an empty 0700 directory, records only metadata
digests (relative names, types, modes and sizes; never runtime file contents),
and carries an explicit owner, TTL and fail-closed cleanup policy.

When a lease is supplied, transport requires explicit HOME/TMPDIR (and any
additional declared runtime keys) overrides. Every override must resolve
inside scratch; parent-agent values remain filtered by the existing env
allowlist. The task cwd is still supplied independently and is never made
writable by this layer.

Normal process-group termination cleans the scratch and returns a
`runtime-scratch-receipt-r1` with `runtime_scratch_ref=ATTEMPT_RUNTIME_SCRATCH`
and `content_persisted=false`. A cleanup exception returns
`runtime_scratch_cleanup_status=FAILED`; `UNKNOWN` or `CHILD_LEFT_BEHIND`
process groups return `REQUIRES_RECONCILIATION` and do not delete a possibly
active child domain. Preflight permission, overlap, symlink and environment
failures clean the empty lease when safe and fail closed.

The transport regression set ran 14 tests, and the combined live bridge
targeted set ran 55 tests, all with zero failures, errors and skips. Coverage
includes literal argv, timeout and signal escalation, child-left-behind,
bounded output, scratch helper writes, task workspace preservation, cleanup
failure, unknown-group reconciliation, env escape, protected-parent overlap,
and symlink escape. No live inference was started.

Claim ceiling: provider-neutral bounded transport and runtime-scratch
lifecycle evidence only; no Codex adapter completion, validated live result,
production readiness, external truth, Owner acceptance or epistemic
acceptance is inferred.
