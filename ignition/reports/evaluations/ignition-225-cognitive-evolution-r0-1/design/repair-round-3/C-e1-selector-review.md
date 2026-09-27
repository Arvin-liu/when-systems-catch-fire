# Role C — E1 selector/source-boundary review

**Scope.** Reviewed the round 3 candidate sheet and only Task220 FAMILY01/02/03 `m0.md` and `revision-evidence-e1.md`. This review applies the supplied rubric: G3 requires an E1-supported selector that adds no rule beyond the evidence envelope; G4 requires an M1 selector → bounded applicability → action, absent from M0, that resolves the case ambiguity. No held-outs, sealed maps, prior experimental outputs, or prior Task225 design files were read.

## FAMILY01 — Canopy temperature

**G3: supported, narrowly. G4: supported, with a repeatability clarification recommended.**

- The case’s 2.7/2.6 °C pair is stable (0.1 °C apart) and both values meet M0’s ≥2.0 °C confirmation trigger. It matches the high-D context of OBS-01/02: reflective silver film at reflectance 0.72, toward-sun at 21° off nadir, with contact excesses of 1.6/1.5 °C. Yet OBS-01/02 have VWC 23.0/22.7% (above the source’s 16% review threshold), no wilt, and water potentials −0.55/−0.52 MPa. This supports selecting that measured surface/view context for a measurement-control check, rather than revising M0’s global D threshold.
- The proposed 8° off-nadir away-from-sun comparison is directly source-bound: OBS-03 is the same marked canopy and film in that geometry, with D 1.0/0.9 °C and contact excess 0.2 °C. E1 also records immediate contact checks. The evidence supports a paired diagnostic comparison for this observed context; it does not isolate a universal causal effect of angle or establish a reflectance cutoff. The candidate correctly restricts applicability to the observed reflective-film/toward-sun/21° context and keeps soil-moisture confirmation mandatory regardless of the comparison.
- The new control sequence and contact reference are absent from M0 and address the measurement ambiguity while preserving M0’s confirmation action. One precision gap remains: the candidate says “acquire the scan” in the singular, while OBS-03 reports two D scans and M0’s routine uses a paired scan. For a repeatable comparison, specify two away-sun scans (and contact reference immediately after each), or explicitly label one scan/contact pair as a qualitative check that cannot establish repeatability. This does not invalidate the narrow selector, but the current wording is less fully evidenced than the paired source protocol.

**Arithmetic/profile check:** OBS-01/02 are within-pair differences of 0.1 °C; case A’s values exactly match OBS-01. OBS-03 values and 8° geometry match the proposed comparison. The stated VWC comparison is above, not below, 16%.

## FAMILY02 — Turbidity to suspended solids

**G3: supported. G4: supported.**

- At 150 NTU, M0’s point estimate is `1.35 × 150 + 12 = 214.5 mg/L`. E1’s floc-rich observations are 91 mg/L at 100 NTU (OBS-04), 171 at 200 (OBS-05), and 251 at 300 (OBS-06). The case composition, 21% mineral grains and 46% organic flocs, exactly matches OBS-04 and lies within the observed floc-rich pattern across those records. The case turbidity is inside their 100–300 NTU span.
- Linear interpolation between the 100- and 200-NTU E1 points gives `91 + (150−100) × (171−91)/(200−100) = 131 mg/L`. This is a source-supported empirical interpolation for the stated composition/turbidity envelope. The candidate appropriately avoids promoting it to a universal formula and keeps the independent gravimetric result sealed.
- Composition plus in-envelope turbidity is the M1 selector; the bounded action is to use the E1 local interpolation while retaining M0’s estimate as the baseline comparison. Composition is not an M0 input, so this supplies a source-bound response to the demonstrated matrix ambiguity.

**Uncertainty boundary:** M0’s ±12 mg/L band belongs to its original mineral-dominant calibration. E1 does not state an uncertainty band for the floc-rich interpolation. The candidate attaches M0’s stated uncertainty to the M0 baseline estimate; keep that attachment explicit and do not carry the ±12 band over to 131 mg/L.

## FAMILY03 — Cold-chain screening

**G3: supported. G4: supported.**

- The candidate’s group-P profile (9-minute pulse peaking at 13.7 °C) exactly matches OBS-02. The group-S comparison (10 minutes, 14.0 °C) exactly matches OBS-04. E1 reports their retained activities as 90.1% for P (below the 95% reference) and 98.7% for S (within reference). OBS-01/03 provide two additional P pulse cases (11/13 minutes; peaks 14.2/14.4 °C) below reference, while P OBS-05 is the no-pulse control at 99.0%.
- Both candidate lots pass M0’s mean-only screen: the case states all segment and shipment means are below 8.0 °C, and E1 says all listed shipment and eight-hour means are at or below 8.0 °C. M0 does not encode a maximum or pulse statistic and does not prioritize between such lots.
- The M1 selector is verified group P with a complete high-rate pulse within the observed P profile context; the bounded action is `STABILITY_REVIEW` for P when only one review slot is available. The matched pulsed group-S observation remains on the M0 pass path for this observed comparison. This selector/action is absent from M0 and resolves the allocation ambiguity without claiming confirmed degradation or creating a universal pulse cutoff. Case A exposes no assay result, as required for the decision.

**Profile check:** Candidate P and S durations/peaks agree exactly with OBS-02/04; neither lot’s listed 15-minute means trigger M0’s >8.0 °C review rule.

## Summary

F02 and F03 meet G3/G4 within the explicit E1 envelopes. F01’s context selector and conservative follow-up are also source-supported and bounded; specify the away-sun scan repeat/contact cadence to align the added protocol with the paired evidence and M0’s measurement practice. No source supports a universal reflectance/angle, turbidity-composition, or pulse threshold.
