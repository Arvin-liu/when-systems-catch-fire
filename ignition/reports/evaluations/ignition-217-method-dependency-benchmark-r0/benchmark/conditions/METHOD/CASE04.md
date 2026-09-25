# Supplemental record CASE04

Representation note: six ordered Method-Use Trace segments are expressed as task-local linked records; the existing global schema is unchanged.

## Atomic records
[A01] Candidate explanation: elevated root-zone salt concentration.
[A02] Candidate explanation: canopy heat exposure.
[A03] Candidate observation: a root-zone conductivity reading collected after four minutes of recirculation.
[A04] Selection rationale: the incoming feed value alone does not distinguish accumulated root-zone salt from canopy heat.
[A05] Boundary record: do not change feed concentration from leaf appearance or feed-tank conductivity alone.
[A06] Expected observation: compare the timed root-zone value with the recorded inlet value; a difference of at least 0.6 mS/cm supports accumulation, while a smaller difference leaves the two explanations unresolved.
[A07] Disposition record: request the timed root-zone observation and keep the cause unresolved until it is recorded.

## Recorded relations
[R01] A04 links the candidate explanations to A03 as the discriminator.
[R02] A05 blocks an unsupported immediate feed change.
[R03] A03 specifies the location and timing required for A06.
[R04] A06 interprets the possible observation without assigning a cause from missing data.
[R05] A07 records the unresolved disposition.
