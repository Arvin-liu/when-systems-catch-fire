# Repair round 1 — read-only A case proposals (PRE-FREEZE / FAILED)

These are the designer's first repair-round proposals, retained as audit history. They are not frozen science and were not shown to experimental successors.

## FAMILY01 — Canopy temperature

### A — revised-boundary case

- Visible case: calibrated camera and air sensor; same marked block; valid paired D=2.6/2.5°C; silver film with measured reflectance 0.72; toward-sun bearing at 21° off nadir. No VWC, plant-water status, contact result, or changed-bearing scan.
- M0-only: pair difference 0.1°C is within M0's 0.8°C limit and both values meet its 2.0°C trigger, so M0 licenses `SOIL_MOISTURE_CONFIRMATION`. It has no reflectance or view selector.
- Candidate M1 relation/action: only for this observed reflective-film/toward-sun context with a valid stable high pair, require a same-canopy away-from-sun bearing scan and contact-leaf reference before relying on the ordinary thermal trigger. Do not infer stress or irrigation.
- Proposed E1 support: OBS-01/02 show excess over contact reference in the reflective/toward-sun context; OBS-03 changes bearing on the same canopy and shows lower D/contact excess; OBS-04 is the low-reflectance comparison. No universal reflectance cutoff or revised D threshold.

### B — preserved scope

Ordinary mineral soil, reflectance 0.15, toward-sun bearing, stable D=2.5/2.4°C. M0 licenses `SOIL_MOISTURE_CONFIRMATION`; M1 preserves that path because the reflective-film selector is absent. Proposed source analogy: E1 OBS-05 positive control.

### C — unresolved/fallback

Partially covered reflective surface with bearing changing between scans; D=2.3/1.4°C. M0's pair-difference rule licenses `REPEAT_THERMAL_SCAN`. M1 does not apply the stable reflective-context branch; retain repeat/reacquire under stable coverage/view. Proposed source analogy: E1 OBS-06.

## FAMILY02 — Turbidity to suspended solids

### A — revised-boundary case

- Visible case: valid blank/cell/duplicate QC; turbidity 150 NTU; composition 21% mineral grains, 46% organic flocs, remainder mixed fines. No gravimetric result.
- M0-only: 1.35×150+12=214.5 mg/L with M0's stated uncertainty; composition is not an input.
- Candidate M1 relation/action: within the observed floc-rich composition envelope and 100–300 NTU range, use the local relation from E1 OBS-04/05/06: 91/171/251 mg/L at 100/200/300 NTU; linear interpolation gives 131 mg/L at 150. Bounded to the observed envelope; not a universal formula. Keep independent gravimetry sealed.

### B — preserved scope

QC-valid 250 NTU, composition within the observed mineral-dominant pattern, sealed independent gravimetric reference. M0 licenses `REPORT_ESTIMATE` at 349.5 mg/L; M1 preserves the mineral-dominant M0 path. Proposed source analogy: E1 OBS-01..03.

### C — unresolved/fallback

Valid turbidity but composition aliquots are not reproducible and do not stably place the sample in either observed composition pattern. Request composition reconciliation or gravimetry; do not use a floc-rich point estimate. Proposed source analogies: E1 OBS-07/08.

## FAMILY03 — Cold-chain screening

### A — revised-boundary case

- Visible case: verified group-P identity; complete calibrated 15-minute logger with segment and shipment means below 8.0°C; complete high-rate trace with a 10-minute pulse peaking at 13.8°C. No activity-assay result.
- M0-only: the below-8.0°C means license `SCREEN_PASS`; M0 has no pulse-duration statistic.
- Candidate M1 relation/action: verified group P plus a complete high-rate pulse inside the observed E1 group-P envelope maps to `STABILITY_REVIEW`; do not claim confirmed degradation or generalize to every formulation/logger.
- Proposed E1 support: OBS-01/02/03 are group-P pulses with reduced assay activity; OBS-04 is a matched group-S pulse with activity retained; OBS-05 is a stable group-P no-pulse control. No universal pulse threshold.

### B — preserved scope

Verified group P, complete continuous profile, all M0 means below 8.0°C, no high-rate pulse. M0 licenses `SCREEN_PASS`; M1 preserves it. Proposed source analogy: E1 OBS-05.

### C — unresolved/fallback

Verified group P and complete M0 interval logs below 8.0°C, but a high-rate trace gap across handoff leaves pulse duration unknown. M0 alone passes; M1 requires `RECONCILE_LOGGER`, then `UNSCORABLE` if unresolved. Proposed source analogy: E1 OBS-06.

Sources used by the designer: Task220 FAMILY01–03 `m0.md` and `revision-evidence-e1.md` only. No Task220 held-out or sealed material was read.
