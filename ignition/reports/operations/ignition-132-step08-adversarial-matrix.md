# IGNITION-20260822-132 Step 08 — Adversarial / Negative Fixture Matrix

Status: PASS

The Step 08 matrix contains 14 explicit fixtures. It covers stale canonical Current source, stale lifecycle, forged Snapshot, architecture-task promotion, witness/task mismatch, matching SHA with mismatched task identity, rollback, unknown-task-without-contract, stale compiler output, legal historical Task131 documents, unreachable publication refs, missing publication witness, attempted epistemic promotion, and idempotent rerun.

Expected results and reason codes are recorded in `ignition/data/operations/iterations/132/fixtures/release-task-identity-negative-fixtures-r1.json`. The matrix keeps the historical Task131 receipt legal while rejecting its use as the current formal identity. It also treats the absence of the Task132 publication witness before final publication as a fail-closed condition.

Validation: `PYTHONPATH=ignition python3 -m unittest ignition.tests.test_task_identity_adversarial_fixtures`.

Claim ceiling: repository-local adversarial release identity and evidence-gate validation only; no external truth, authority, production readiness, Owner acceptance, or epistemic acceptance is inferred.
