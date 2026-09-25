# Supplemental record CASE06

Representation note: structured synthetic records; relation rows connect source-linked records.

<!-- ATOM_BLOCK_BEGIN -->
## Atomic records
[A01] Procedure record Q: process a set of entry identifiers and optional event tokens and return status fields.
[A02] Procedure record D: process entry identifiers and optional event tokens one row at a time and return status fields with an evidence note.
[A03] Historical timing record: a result is recorded for cohort H1.
[A04] Historical timing record: a separate result is recorded for cohort H2; entry categories and procedure assignment are not in this record.
[A05] Comparison record: H1 and H2 are separate cohorts without a head-to-head comparison.
[A06] Current-entry record: roster identifier status, entry type, event-token status, and mismatch status are recorded for each entry.
[A07] Check-in status record: no current entry has a resolved check-in event.
<!-- ATOM_BLOCK_END -->

## Recorded relations
[R01] A03 --SOURCE_RECORD_FOR--> A05 :: H1 is the source cohort for its recorded timing observation.
[R02] A04 --SOURCE_RECORD_FOR--> A05 :: H2 is a separate source cohort for its recorded timing observation.
[R03] A05 --DOES_NOT_RANK--> A01 :: Separate cohorts do not establish a universal procedure winner.
[R04] A06 --MAPS_COHORT_TO_PROCEDURE--> A01 :: Route exact roster identifiers with a valid event code to Q; route aliases and walk-ins to D. Keep unexplained mismatches unresolved pending roster evidence.
[R05] A07 --LIMITS_STATUS_CLAIM_FOR--> A06 :: The current status record contains no completed check-in event.
