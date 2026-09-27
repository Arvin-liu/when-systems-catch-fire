# Repair round 3 — final pre-freeze candidate set

Status: preliminary candidate set for fresh blind review. This is not a science freeze, successor input, or experimental output. F02 is carried forward unchanged from repair round 1; only F01 and F03 are revised.

## FAMILY01 — Canopy temperature

### A — visible case facts

Calibrated radiometric camera and matched shielded air sensor; same marked canopy; valid stable paired D readings 2.7/2.6 °C. Ground cover is reflective silver film with measured reflectance 0.72; the camera bearing is toward the sun at 21° off nadir. Required M0 calibration, time, mask, geometry, and sensor-quality fields are valid.

### A — sealed target and action for reviewers only

M0 licenses `SOIL_MOISTURE_CONFIRMATION`. The E1-bounded additional measurement-control sequence is: on the same marked canopy with the same camera, rotate the view away from the sun to 8° off nadir, acquire the scan, immediately take a contact-leaf reference, and record the pair for comparison before relying on the thermal reading. Then complete M0's soil-moisture confirmation regardless of the comparison; do not infer stress or irrigation. Applicability is restricted to the observed stable reflective-silver-film / toward-sun / 21° off-nadir context. No universal reflectance, angle, or D threshold is introduced.

E1 support: OBS-01/02 provide the stable high-D reflective-film/toward-sun context; OBS-03 is the same marked canopy and film viewed away from the sun at 8° off nadir with lower D and contact excess; OBS-04 is the ordinary-surface comparison. The target includes no scan outcome or plant-health outcome.

### B — preserved old scope

Calibrated setup, ordinary mineral-soil surface with reflectance 0.14, toward-sun bearing at 21° off nadir, and valid stable paired D readings 2.7/2.6 °C. M0 licenses `SOIL_MOISTURE_CONFIRMATION`; the reflective-film selector is absent, so preserve that path. No plant-water, contact, or disposition outcome is included.

### C — unresolved edge

Partially covered reflective surface with reflectance range 0.18–0.69 and bearing varying between scans; valid D readings 2.2/1.4 °C. The pair straddles M0's 2.0 °C trigger, so M0 licenses `REPEAT_THERMAL_SCAN`. The stable reflective-context branch does not apply; preserve repeat/reacquisition under stable coverage and view, without a stress or irrigation inference.

## FAMILY02 — Turbidity to suspended solids (unchanged from round 1)

### A — visible case facts

Valid blank/cell/duplicate QC; turbidity 150 NTU; composition 21% mineral grains, 46% organic flocs, remainder mixed fines. No gravimetric result is supplied.

### A — sealed target and action for reviewers only

M0 licenses `REPORT_ESTIMATE` at 214.5 mg/L from 1.35×150+12, with M0's stated uncertainty. Within E1's observed floc-rich composition envelope and 100–300 NTU range, use only the empirical local relation from OBS-04/05/06 (91/171/251 mg/L at 100/200/300 NTU); interpolation yields 131 mg/L at 150 NTU. Treat this as bounded empirical interpolation, not a universal formula, and keep the independent gravimetric result sealed. No rule outside E1's observed composition and turbidity envelope is added.

### B — preserved old scope

QC-valid 250 NTU with composition in the observed mineral-dominant pattern. M0 licenses `REPORT_ESTIMATE` at 349.5 mg/L; preserve the mineral-dominant M0 path. The independent gravimetric reference remains sealed.

### C — unresolved edge

Valid turbidity but irreproducible composition aliquots do not stably place the sample in either observed composition pattern. Request composition reconciliation or gravimetry; do not use the floc-rich point estimate.

## FAMILY03 — Cold-chain screening

### A — visible case facts

Two independently registry-verified lots are available for one stability-review slot: one is formulation group P and one is group S. Both have complete calibrated 15-minute logger records and valid clock/custody checks; every segment and shipment mean is below 8.0 °C. Both have complete aligned high-rate traces. The group-P trace has a 9-minute excursion peaking at 13.7 °C; the group-S trace has a 10-minute excursion peaking at 14.0 °C. No activity assay, degradation, or disposition result is supplied. Choose which lot receives the single `STABILITY_REVIEW` slot.

### A — sealed target and action for reviewers only

M0 alone licenses `SCREEN_PASS` for both lots and does not prioritize either. For verified group P only, a complete high-rate pulse inside the observed E1 group-P context maps to `STABILITY_REVIEW`; select the group-P lot for the available review slot, while retaining the M0 mean-only pass as the baseline result. The group-S pulsed control remains within M0's pass path in this observed comparison. Make no confirmed-degradation claim and add no universal pulse threshold.

E1 support: group-P pulse observations OBS-01/02/03 include 9–13-minute pulses with peaks 13.7–14.4 °C and reduced assay activity; matched group-S pulsed control OBS-04 has a 10-minute, 14.0 °C pulse and activity within the reference; group-P OBS-05 is a no-pulse control. Case A exposes no assay result.

### B — preserved old scope

Verified group P; complete calibrated 15-minute means below 8.0 °C; complete high-rate trace without an above-12 °C pulse. M0 licenses `SCREEN_PASS`; preserve it. No assay, degradation, or disposition outcome is supplied.

### C — unresolved edge

Verified group P; complete M0 interval and shipment means below 8.0 °C; high-rate trace has a custody gap across handoff, so pulse duration is unresolved. M0 alone licenses `SCREEN_PASS`; require `RECONCILE_LOGGER`, then `UNSCORABLE` if the required trace remains unresolved. No assay or degradation result is supplied.

## Source boundary and review request

F01/F03 source support is limited to their Task220 `m0.md` and `revision-evidence-e1.md`. F02 is unchanged from its round-1 proposal. Do not read Task220 held-outs, sealed targets/maps, or prior experimental outputs. Fresh reviewers must assess G1–G4 independently; no criterion may be relaxed. F01's exact E1-angle protocol and F03's P/S matched contrast are the intended G2 discriminators, but any generic-intuition leakage finding is controlling.
