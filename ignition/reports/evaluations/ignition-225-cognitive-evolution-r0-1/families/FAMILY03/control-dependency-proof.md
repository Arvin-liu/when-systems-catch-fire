# FAMILY03 control-dependency proof

## A — revised-boundary case

- M0's complete calibrated 15-minute means are below 8.0 °C, so both lots receive `SCREEN_PASS`; M0 cannot prioritize group P.
- The target selects group P, whose complete 9-minute/13.7 °C pulse lies inside the observed P context, for the one `STABILITY_REVIEW` slot. The matched group-S control is 10 minutes/14.0 °C, so generic peak/duration intuition does not select P.
- E1 OBS-01/02/03 support group-P pulse review; OBS-04 is the matched group-S pulsed control; OBS-05 is the group-P no-pulse control. A contains no assay outcome.
- Retain the M0 pass as baseline. The added review is triage only and makes no degradation claim.
- G1 has the M0 pass versus M1 review difference; G2 is protected by the matched P/S comparison with no outcome; G3 is source-bounded to the observed P pulse envelope; G4 is the missing group/pulse mapping in M0.

## B — preserved scope

Verified group P with a complete profile lacking an above-12 °C pulse retains the M0 `SCREEN_PASS`.

## C — unresolved edge

The M0 means still pass, but the trace gap prevents pulse assessment. Reconcile custody/trace; if unresolved, return `UNSCORABLE`. Do not impute a pulse or pass it through the M1 selector.
