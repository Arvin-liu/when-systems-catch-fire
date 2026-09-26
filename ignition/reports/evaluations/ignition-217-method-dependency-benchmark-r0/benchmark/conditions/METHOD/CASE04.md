# Supplemental record CASE04

Representation note: structured synthetic records; relation rows connect source-linked records.

<!-- ATOM_BLOCK_BEGIN -->
## Atomic records
[A01] Hypothesis record: elevated salt concentration in the root zone.
[A02] Hypothesis record: canopy heat or humidity stress.
[A03] Measurement-definition record: a root-zone conductivity reading can be collected after recirculation; the exact interval is selected by the operating protocol.
[A04] Existing-value record: the feed-tank value of 1.4 mS/cm predates refill.
[A05] Instrument record: root-zone port, recirculation timer, and canopy humidity sensor are available.
[A06] Calibration-record index: the protocol has an inlet-comparison rule; its threshold and interpretation are kept in the referenced calibration record.
[A07] Current-record status: no post-refill root-zone reading or cause is present.
<!-- ATOM_BLOCK_END -->

## Recorded relations
[R01] A01 --SELECTS_DISCRIMINATOR--> A03 :: To distinguish the competing root-salt and canopy-stress explanations, request a root-zone conductivity reading after four minutes of recirculation and compare it with the recorded inlet value.
[R02] A04 --TEMPORAL_LIMIT_FOR--> A01 :: The pre-refill feed value does not record the current root-zone state.
[R03] A05 --SUPPORTS_MEASUREMENT--> A03 :: The listed port and timer make a post-refill reading technically available; they do not select a measurement or interval.
[R04] A06 --INTERPRETS--> A03 :: A difference of at least 0.6 mS/cm supports root-zone accumulation. A smaller difference leaves both explanations unresolved; do not change feed concentration from the current observations.
[R05] A07 --RESULT_STATUS_FOR--> A03 :: The current record contains no post-refill measurement result.
