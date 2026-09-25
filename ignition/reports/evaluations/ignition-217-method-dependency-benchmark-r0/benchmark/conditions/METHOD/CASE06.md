# Supplemental record CASE06

Representation note: six ordered Method-Use Trace segments are expressed as task-local linked records; the existing global schema is unchanged.

## Atomic records
[A01] Candidate procedure Q: self-service code scan for entries with exact roster identifiers.
[A02] Candidate procedure D: staffed roster review for aliases and walk-ins.
[A03] Source record Q-1: scan completion observations from a cohort of exact identifier matches.
[A04] Source record D-1: desk resolution observations from a different cohort of aliases and walk-ins.
[A05] Evidence boundary: Q-1 and D-1 are not a head-to-head comparison and do not rank universal performance.
[A06] Expected observation: an exact roster identifier is verified by its event code; an alias or walk-in is routed to a documented roster review.
[A07] Disposition record: retain both cohort-bounded procedures; leave an unexplained mismatch unresolved pending roster evidence.

## Recorded relations
[R01] A03 supports A01 only for the exact-identifier cohort.
[R02] A04 supports A02 only for aliases and walk-ins.
[R03] A05 blocks a universal-winner inference.
[R04] A06 maps the present entry boundary to the two procedures.
[R05] A07 preserves coexistence and unresolved mismatches.
