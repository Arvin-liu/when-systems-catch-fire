# IGNITION-20260822-134 Step 12 — Residual adversarial matrix

Status: `PASS`

The 18-case matrix exercises the residual comparator against an inherited unchanged tuple, object/count growth, same-count replacement, failure-dimension growth, baseline/current count-set mismatches, forged baseline/current fingerprints, three new-residual classifications, source-command changes with and without valid migration metadata, resolution, a live object carrying `RESOLVED_CURRENT`, an unclassified shrink, and a duplicate residual ID. The runner returned `RESIDUAL_ADVERSARIAL_MATRIX_OK cases=18 passed=18` and the existing five-entry ledger still returned `RESIDUAL_LEDGER_OK entries=5 inherited_unchanged=3 resolved=2`.

After the Step 12 fixture, runner, test, receipt and report were present, the Current path manifest was regenerated and independently checked at `tracked=2997`, `manifest=2997`, `missing=0`, `stale=0`, `unresolved=0`, `category_changed=0`, `anti_backflow=0`. Current Facts, Current Snapshot and Current State sync remained deterministic after that path update.

Two silent-absorption paths were closed in the gate itself. A source-command migration now has to name the exact old/new commands and current Task134 task ID. A non-empty shrink now requires `PARTIALLY_RESOLVED`; an `OPEN_INHERITED` entry cannot change its object/dimension tuple without an explicit status. Existing historical, environmental, and long-test observations were not rewritten or widened by this step.

Claim ceiling: repository-local residual delta adversarial evidence only; no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.
