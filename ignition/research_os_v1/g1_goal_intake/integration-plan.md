# Later integration plan (proposal only)

This adapter is not integrated with a canonical Goal lifecycle. Any later integration requires a separate Owner and Chat review after this candidate and the independent Stage08 stream are closed.

Before considering runtime use, a future authorized design must define:

1. A trusted, read-only source for current Intent, Goal, parent, and Completion Contract records, with explicit version and ancestry verification.
2. A real Owner authentication and trust-root mechanism independent of request JSON and snapshot provenance fields.
3. A stable adapter API contract and migration/compatibility policy for the existing Steering types.
4. A separate authorization boundary for Goal activation, approval receipts, task dispatch, and independent completion evaluation.
5. End-to-end tests against authorized episode contracts, with hidden-answer isolation, freeze-before-holdout, deterministic replay, and post-freeze no-edit controls where applicable.

Until each item is separately authorized and implemented, this package remains an offline proposal preflight. Its reports cannot start a successor, establish G1 passage, alter Current, or authorize a scientific claim.
