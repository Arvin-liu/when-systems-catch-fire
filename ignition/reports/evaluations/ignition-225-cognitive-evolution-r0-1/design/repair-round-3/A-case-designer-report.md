# Repair round 3 — A case-designer report (read-only)

The designer used only the permitted Task220 FAMILY01/FAMILY03 M0 and E1 evidence files and made no workspace edits.

## Proposals

| Family / case | Visible facts | Reviewer-only mapping |
|---|---|---|
| F01 A | Valid M0 setup; same marked block and camera; two scans 12 minutes apart, D=2.7/2.6°C; 21° off-nadir, without sun bearing, surface, contact-reference, VWC, or plant-status facts. Include an opaque E1 locator. | M0 selects `SOIL_MOISTURE_CONFIRMATION`. E1 maps to OBS-01's reflective-film/toward-sun context. Revised action: bounded `REFLECTION_CONTROL`—scan away from sun at 8° off-nadir and take a contemporaneous contact-leaf reference. No result or health status. |
| F01 B | Valid M0 setup; D=0.9/0.8°C; opaque E1 locator. | M0 selects `ROUTINE_MONITORING`; E1 maps to the ordinary-surface comparison. No reflection-control override. |
| F01 C | Valid M0 setup; D=2.2/1.4°C; opaque E1 locator. | M0 selects `REPEAT_THERMAL_SCAN` because the pair straddles 2.0°C. E1 maps to the partial, variable-geometry record, which does not qualify for bounded control. |
| F03 A | Complete, calibrated shipment logger and custody; ordinary product identifier; 15-minute shipment and segment means at or below 8.0°C; opaque E1 locator. Omit formulation group and high-rate trace. | M0 selects `SCREEN_PASS`. E1 verifies group P plus a complete high-rate pulse within the observed envelope. Revised action: `STABILITY_REVIEW` only, with no assay or degradation claim. |
| F03 B | Same M0-valid logger facts; means at or below 8.0°C; opaque E1 locator. | E1 maps to group-P continuous-profile control; no pulse selector, so retain `SCREEN_PASS`. |
| F03 C | Same M0-valid logger facts; means at or below 8.0°C; opaque E1 locator. | E1 maps to the pulsed group-S comparison. The group-P selector fails, so retain `SCREEN_PASS`. |

## Designer's G1–G4 assessment

G1 is met for A in both families because M0 licenses a different action: soil-moisture confirmation versus F01 bounded control, and screen-pass versus F03 review. G2 can pass if the case facts omit semantically revealing fields and the exact mapping requires consulting E1 through the locator. G3 is bounded to E1: F01 uses only the observed film/toward-sun context and the 8° away-from-sun/contact-reference protocol; F03 requires verified group P and a pulse within the observed range, with no universal threshold. For G4, F03's selector-to-review pathway is new to M1; the `STABILITY_REVIEW` action name exists in M0, but M0 does not select it for this mean-in-range, group-P pulse condition.

This is a proposal distinct from the root-authored round-3 candidate. Its F03 A omits the group and trace selectors, so it is not the candidate submitted to B/C/D review under the command's F03 selector requirement.
