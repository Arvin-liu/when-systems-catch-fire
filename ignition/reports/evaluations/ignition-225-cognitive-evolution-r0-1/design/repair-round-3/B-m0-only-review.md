# B — M0-only adversarial review (repair round 3)

## Scope

Reviewed the round-3 candidate sheet and only the Task220 FAMILY01, FAMILY02, and FAMILY03 `m0.md` files. No Task220 E1 file, held-out, sealed target/map, prior experimental output, or earlier Task225 design file was opened. The candidate sheet itself contains its reviewer-only target text, which was considered only for the requested G1 comparison.

## Findings

| Family | M0-only action for A | G1 assessment |
| --- | --- | --- |
| F01 | `SOIL_MOISTURE_CONFIRMATION`. The valid pair differs by 0.1 °C (not over the 0.8 °C repeat limit) and both D values are at least 2.0 °C. M0 therefore gives one applicable action; neither repeat nor routine monitoring remains compatible with these facts. | No two materially distinct M0 actions remain. The target adds an away-view scan and contact-leaf reference, then retains the same soil-moisture confirmation regardless of comparison. That is a materially different full workflow, so G1 passes if the target is scored as the whole ordered sequence. It does not differ at the M0 action-label level: both include `SOIL_MOISTURE_CONFIRMATION`. |
| F02 | `REPORT_ESTIMATE` at 214.5 mg/L (1.35 × 150 + 12). QC is stated valid and 150 NTU is in range. Composition is not an M0 selector. M0's ±12 mg/L band is stated for its original calibration matrix. | No two materially distinct M0 actions remain. The target changes the calculation basis and reported estimate to 131 mg/L, which is materially different from 214.5 mg/L. G1 passes if the reported method/value is part of the action; it does not differ by the action label alone, since both outputs are called `REPORT_ESTIMATE`. |
| F03 | `SCREEN_PASS` for both lots. Their required 15-minute records and checks are complete and every segment and shipment mean is below 8.0 °C. M0 has no formulation-group or high-rate-pulse selector, so it cannot prioritize either lot. | No two materially distinct M0 actions remain. For the group-P lot, the target's `STABILITY_REVIEW` differs from M0's `SCREEN_PASS`, so G1 passes. `STABILITY_REVIEW` is in M0's action catalog, but it is not licensed for these presented selectors: M0 selects it only when a segment or shipment mean exceeds 8.0 °C. Thus it is absent from the applicable M0 output, not absent from the global action list. |

## Sequencing and action-label audit

- **F01:** The target's ordering is explicit: perform the added view/contact comparison first, then complete M0's soil-moisture confirmation regardless of comparison. Keep these as distinct steps in scoring. If the scored action is reduced to the final M0 label, the added measurement-control action disappears and the M0/target distinction becomes ambiguous.
- **F02:** M0 and the target share the `REPORT_ESTIMATE` label despite using different calculation bases and yielding 214.5 versus 131 mg/L. Treating a bare label as the full action would hide the intended difference. Also preserve that M0's ±12 mg/L band is tied to its original calibration matrix; it is not a composition-specific validation claim.
- **F03:** No M0 ordering defect is apparent. The complete high-rate traces are outside M0's decision procedure; the stated interval means and valid checks lead directly to `SCREEN_PASS` for each lot. The key distinction is applicability: the review action exists in M0 but its stated trigger is not met.

## Summary

None of the three A cases leaves two materially distinct M0 actions compatible with the supplied facts. F03 has a clear M0-versus-target action-label difference. F01 and F02 distinguish the full target workflow or computed result from M0, respectively, but reuse the M0 terminal action label; G1 should be judged on the complete sequence/value rather than the label alone.
