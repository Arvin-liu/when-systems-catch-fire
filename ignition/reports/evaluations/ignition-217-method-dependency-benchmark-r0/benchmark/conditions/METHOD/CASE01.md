# Supplemental record CASE01

Representation note: structured synthetic records; relation rows connect source-linked records.

<!-- ATOM_BLOCK_BEGIN -->
## Atomic records
[A01] Candidate record: Route Alder returns a signed-document field, signature-timestamp field, and approval-event reference, but no per-file digest.
[A02] Candidate record: Route Birch returns a version sequence and per-file digest; its optional approval-event field has unverified output behavior.
[A03] Audit objective record: reconstruct content membership at each approval checkpoint.
[A04] Source precondition record: version labels, checkpoint identifiers, and signature markers are available for comparison.
[A05] Output-field record: a delivered manifest may expose multiple source identifiers; the current preview does not establish how its fields join.
[A06] Preview limitation record: at least one optional field's delivered behavior is not verified by the current preview.
[A07] Version record: version 4 is marked unsigned; the observed C-17 document is version 3.
<!-- ATOM_BLOCK_END -->

## Recorded relations
[R01] A03 --SELECTS_FOR_AUDIT--> A02 :: Propose Route Birch as the checkpoint-level verification candidate because its chronology and per-file digest can identify content; assert membership only if the delivered digest joins to the checkpoint and approval event, and keep the unsigned correction outside the approved record.
[R02] A04 --PRECONDITION_FOR--> A03 :: Version, checkpoint, and signature identifiers must be intact before interpreting a checkpoint export.
[R03] A05 --OBSERVATION_FOR--> A02 :: The delivered package can be compared with the source records after a proposed export.
[R04] A06 --LIMITS_INTERPRETATION_OF--> A05 :: A field not verified in a preview must be checked in the delivered package before describing that field.
[R05] A07 --PROVENANCE_FOR--> A03 :: The observed C-17 version and unsigned-correction marker remain separate provenance entries.
