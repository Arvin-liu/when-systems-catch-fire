# Supplemental record CASE01

Representation note: six ordered Method-Use Trace segments are expressed as task-local linked records; the existing global schema is unchanged.

## Atomic records
[A01] Candidate record: Route Alder emits the most recent signed document and its signature timestamp.
[A02] Candidate record: Route Birch emits the version chronology and file digests and can include an approval-event pointer.
[A03] Selection criterion: a checkpoint audit needs the content digest joined to the approval event for that checkpoint.
[A04] Context record: source version labels, checkpoint identifiers, and signature markers must be intact before export.
[A05] Expected observation: the delivered manifest associates each included content digest with a checkpoint and approval event.
[A06] Failure interpretation: a missing digest-to-event join leaves the approved content unresolved; an unsigned later correction is not an approval event.
[A07] Disposition record: keep a correction without an approval event pending; do not infer that a later file was part of an earlier checkpoint.

## Recorded relations
[R01] A03 licenses selection of A02 over A01 for checkpoint-level reconstruction.
[R02] A04 is the precondition for applying the selection rule.
[R03] A05 is the discriminator to inspect after export.
[R04] A06 interprets a missing join without inventing approval.
[R05] A07 bounds the disposition of the later correction.
