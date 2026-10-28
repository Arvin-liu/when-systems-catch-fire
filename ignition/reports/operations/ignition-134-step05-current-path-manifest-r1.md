# IGNITION-20260822-134 Step 05 — Current path manifest regeneration and determinism

Status: `PASS`

The manifest was regenerated from the live classification engine after the Step 04 audit. Before regeneration, the Task134 working tree had 2,978 tracked paths and 2,720 manifest rows with `missing=258`; after the Step 05 artifacts were present and the manifest was generated, the live tree and manifest both contain 2,980 paths.

Two consecutive generations were byte-identical. The final check reports:

- missing: `0`;
- stale: `0`;
- unresolved: `0`;
- duplicate: `0`;
- category drift: `0`;
- anti-backflow violations: `0`.

The adversarial fixture check staged one temporary tracked path without regenerating and observed the required failure. The fixture was then removed and was not included in the formal commit. The authoritative allowlist remains unchanged.

This is a Current projection repair; Task107/127/133 historical observations remain in Git history and receipts. Claim ceiling: repository-local Current path-manifest generation and determinism evidence only.
