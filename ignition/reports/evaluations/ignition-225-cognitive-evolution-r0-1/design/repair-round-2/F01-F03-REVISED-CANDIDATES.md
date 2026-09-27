# Repair round 2 — revised failing families only (PRE-FREEZE)

F02 is unchanged from round 1 because its four-part A gate passed with a bounded empirical interpolation caveat. This file revises only F01 and F03, which failed G2 in round 1. The target/action descriptions below are reviewer-only design annotations; successor-visible case files must contain only the listed visible case facts.

## FAMILY01 — Canopy temperature

### A visible case facts

Calibrated camera and air sensor; same marked canopy; valid stable paired D readings 2.7/2.5°C. The surface is reflective silver film and the camera bearing is toward the sun and oblique. No VWC, plant-water status, contact result, or changed-bearing scan is present.

### A target for reviewers, not visible to successor

M0-only licenses `SOIL_MOISTURE_CONFIRMATION` and does not license an extra reflection-control action. The bounded M1 operation is a controlled discriminator before relying on the stable high D: keep the same marked canopy and instrument, obtain a second scan at a changed bearing away from the sun, take a contemporaneous contact-leaf reference, and record the pair for comparison. After the discriminator, retain the M0-required soil-moisture confirmation regardless; do not infer stress or irrigation. Applicability is limited to the observed reflective-film/toward-sun/stable-high context; no universal reflectance, angle, or D threshold.

E1 support is the same-canopy bearing change and lower D/contact excess in OBS-03 relative to OBS-01/02, plus the ordinary-surface comparison in OBS-04. The target is the measurement-control protocol; no discriminator result or physical-health outcome is shown in A.

### B preserved-scope case

Ordinary low-reflectance mineral-soil surface, toward-sun oblique bearing, valid stable pair D=2.7/2.5°C. M0 licenses `SOIL_MOISTURE_CONFIRMATION`; the M1 reflective-film selector is absent, so the old path is preserved. No VWC, plant-water, contact, or disposition outcome is supplied.

### C unresolved case

Partially covered reflective surface with bearing changing during capture; valid readings D=2.5/1.4°C. M0's pair-difference rule (>0.8°C) licenses `REPEAT_THERMAL_SCAN`. The stable reflective-context branch does not apply; repeat/reacquire under stable coverage and view, with no inferred stress/irrigation result.

## FAMILY03 — Cold-chain screening

### A visible case facts

Registry-verified group-P coded stability-study shipment. The complete calibrated 15-minute logger has segment and shipment means below 8.0°C. A complete aligned high-rate trace records a 10-minute excursion above 12°C with peak 13.9°C across three scheduled intervals; the excursion profile and group identity are shown, but no assay, activity, degradation, or disposition result is supplied. The non-pulse samples remain at 5.6°C; the interval means are 7.26°C, 7.81°C, and 7.26°C for the three intervals spanning the excursion, so all remain below M0's 8.0°C cutoff.

### A target for reviewers, not visible to successor

M0-only licenses `SCREEN_PASS` from the complete mean-only records and has no pulse-duration or group-P selector. The bounded M1 mapping is verified group-P identity plus a complete high-rate pulse inside E1's observed group-P context → `STABILITY_REVIEW` only; preserve the separate fact that the mean-only screen returned pass and make no confirmed-degradation claim. Do not generalize to every formulation, logger, or pulse.

E1 support is group-P pulse observations OBS-01/02/03, the matched group-S pulsed control OBS-04, and the group-P no-pulse control OBS-05. A shows no assay result.

### B preserved-scope case

Registry-verified group P; complete calibrated 15-minute means below 8.0°C; complete high-rate trace with no above-12°C pulse. M0 licenses `SCREEN_PASS`; M1 preserves it. No activity/degradation outcome is supplied.

### C unresolved case

Registry-verified group P; complete M0 interval and shipment means below 8.0°C; the high-rate trace has a custody gap across the handoff, so pulse duration cannot be determined. M0 alone licenses `SCREEN_PASS`; M1 requires `RECONCILE_LOGGER`, then `UNSCORABLE` if the required trace remains unresolved. No assay/degradation result is supplied.

Source scope: only Task220 FAMILY01 and FAMILY03 M0/E1. No held-out, sealed target, or prior Task225 candidate file is used as evidence.
