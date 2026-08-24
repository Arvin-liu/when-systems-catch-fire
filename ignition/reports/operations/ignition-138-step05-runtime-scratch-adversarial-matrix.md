# IGNITION-20260824-138 — Step 05 Runtime Scratch Adversarial Matrix

The R3 filesystem boundary was exercised against the required negative and
positive cases. The task workspace must have no write bits; a scratch parent
inside the task workspace, formal repository or control repository is
rejected before process start. Symlink escape is rejected. The domain contract
rejects auth/config mutation, secret materialization and secret-like runtime
environment names. The child guard filters parent-only runtime markers and
still rejects recursive depth.

The positive path proves a helper write occurs in the transient scratch domain,
the workspace digest and permissions remain unchanged, the `repo.read`
ceiling stays narrow, and normal cleanup returns `CLEANED`. Cleanup failure is
recorded as `FAILED`; unknown or left-behind process groups remain
`REQUIRES_RECONCILIATION` and are not silently deleted. Safe argv construction
hard-rejects dangerous bypass, `--add-dir` and `workspace-write` values.

Matrix evidence is distributed across the provider-neutral domain tests,
deterministic filesystem harness, bounded transport tests, child guard tests,
Codex R3 adapter tests and the dedicated safety-matrix tests. No case uses
skip, xfail, ignore, workspace chmod widening or a dangerous bypass.

The live-bridge targeted set ran 88 tests with zero failures, errors or skips.

Claim ceiling: adversarial filesystem/permission policy and deterministic
adapter/transport evidence only; no real Codex inference, validated live
completion, production readiness, external truth, Owner acceptance or
epistemic acceptance is inferred.
