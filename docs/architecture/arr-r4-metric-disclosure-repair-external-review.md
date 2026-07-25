# ARR R4 — Metric Disclosure & Relay Receipt Repair R1 (External Review Package)

- task_id: `ARR-R4-METRIC-DISCLOSURE-RELAY-RECEIPT-REPAIR-R1-RELAY-20260725`
- control_commit: `e0926ccb53b4bdf7b08bd54c92f440a98c7f7201` (relay/current: "advance CURRENT to R4 metric disclosure and receipt repair")
- repair branch: `repair/adaptive-relational-runtime-r4-metric-disclosure-relay-receipt-r1`
- predecessor R4: PR #127 (`analysis/adaptive-relational-runtime-r4-waic-self-reflection-r1`), DRAFT, UNMERGED, head `1d30f64`, 5 commits
- terminal_verdict: `ARR_R4_METRIC_DISCLOSURE_AND_RELAY_RECEIPT_REPAIR_DRAFT_AWAITING_EXTERNAL_REVIEW`
- authorization boundary: narrow R4 metric-disclosure + relay-receipt repair only.

This package is the **public, non-private** summary of the narrow repair authorized by
external R4 review. It closes the four findings raised in that review without touching
PR #127, the frozen R4 head, or the R3 corpus.

## 1. The four external-review findings this repair answers

1. **Operational "27/27 pass" overclaim.** The public report said "operational 27/27 pass"
   while `operational_coverage=17` and `governance_items=3` — the 27 items were never
   exhaustively / mutually-exclusively allocated. *Fix:* a closed set of exactly 27 item IDs,
   each assigned to exactly one primary dimension (17 OPERATIONAL / 4 SEMANTIC / 3 EVIDENCE /
   3 GOVERNANCE), with fail-closed invariants (`expected == classified == sum == 27`,
   `unclassified == 0`). See `CAPABILITY_COVERAGE_REINTERPRETATION.json` and
   `arr-r4-public-aggregate.json → capability_reinterpretation.dimensions`.
2. **Governance name collision.** `BOUNDARY_HELD=27` / `CONSENT_OR_RIGHTS_LIMITED=809` (the
   mutually-exclusive primary governance status enum) collided conceptually with
   `boundary_held=836`. *Fix:* the enum stays primary; the orthogonal
   `governance_safety_invariant.safety_boundary_held_objects=836` invariant is reported
   separately and never conflated. The malformed `boundary_held` map key is removed.
3. **"All six resolved" is wrong.** M3/M4 are only *diagnosed* as R3 aggregation defects (not
   fixed); M5 is only an *identified* reporting defect. *Fix:* every contradiction now carries
   an explicit `lifecycle` record (`disposition_assigned`, `classification_resolved`,
   `underlying_defect_present`, `underlying_defect_repaired`, `followup_required`,
   `followup_route`) so *attributed* is distinguished from *repaired*. M3/M4/M5 record
   `underlying_defect_present=true, underlying_defect_repaired=false`.
4. **Predecessor relay receipt 404.** The predecessor R4 receipt branch used non-canonical
   filenames and omitted `FINAL_STATE.json` / `COUNTERS.json`, so every contracted path 404'd.
   *Fix:* the predecessor branch is backfilled with the canonical 14-file relay receipt
   contract (ordinary commits, no history rewrite). See `RECEIPT_BACKFILL_AUDIT.md` on that
   branch.

## 2. What changed (engine)

- `capability_classifier.py` (new): closed-set 27-item exact-one-primary classifier, fail-closed.
- `runner.py`: wires the classifier; removes the malformed `dimension_dimension_disclosure_defect`;
  adds a `terminal_verdict` parameter (DEFAULT + REPAIR verdict); `FINAL_EXTERNAL_REVIEW_REQUEST.md`
  is now verdict- and repair-aware.
- `metric_consistency.py`: adds `lifecycle` to all six contradictions.
- `report.py`: public projection carries `lifecycle` and `terminal_verdict` from analysis.
- `schemas.py`: `MetricContradiction.lifecycle` field.

## 3. Test evidence

- 311 passed, 2 skipped on `tests/adaptive_relational_runtime/` after the repair.
- Closed-set contract tests: exactly 27 ids, exactly-one-primary-dimension, no id maps to two
  dimensions, dimension counts 17/4/3/3, sum = 27, fail-closed on unknown id.
- Governance separation tests: `boundary_held` absent from `governance_coverage`;
  `governance_safety_invariant` orthogonal.
- Contradiction lifecycle tests: M1/M2/M6 `underlying_defect_present=false`; M3/M4/M5 `true`,
  `underlying_defect_repaired=false`.
- Private-leak regression: public projection contains no private object keys (`syn_`/`g_` + 8 digits).

## 4. Artifacts

- Public: `docs/architecture/arr-r4-public-aggregate.json` (regenerated, new schema), this doc,
  `arr-r4-self-reflection.md` (§3/§4 corrected), `project-current-state.md` (repair sub-section).
- Private evidence (1111 branch `agent/adaptive-relational-runtime-r4-metric-disclosure-relay-receipt-r1`):
  the 20 files under `/tmp/r4-repair-evidence` (`CAPABILITY_COVERAGE_REINTERPRETATION.json`,
  `METRIC_CONTRADICTION_LEDGER.json`, `FINAL_EXTERNAL_REVIEW_REQUEST.md`, etc.).
- Relay receipt (1111 branch `relay/receipts/arr-r4-metric-disclosure-relay-receipt-repair-r1-20260725`):
  the canonical 14-file contract.

## 5. Red-line adherence

No R5 started; no PROMOTE/EVOLVE/Ready/merge/Main change/force push; PR #127, the frozen R4 head
and the R3 corpus are untouched. CI gate: `foundation-validation` must be green at the exact repair
head (q33 / r3 don't trigger on this path). `EXTERNAL_ACCEPTANCE_CLAIMED=0`.
