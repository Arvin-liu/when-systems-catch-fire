# Supplemental record CASE05

Representation note: structured synthetic records; relation rows connect source-linked records.

<!-- ATOM_BLOCK_BEGIN -->
## Atomic records
[A01] Procedure record V0: package records that share a request identifier into one group.
[A02] Procedure record V1: group records by signatory class.
[A03] Counterexample record: a prior mixed-signatory archive had a cross-access event; the raw event record omits grouping key and procedure version.
[A04] Revision-history record: V1 was recorded after V0; the version log contains no universal-retirement field.
[A05] Current archive record: one request identifier contains a public guide and restricted annex with two signatory classes.
[A06] Verification-field record: output groups can be inspected for request identifier, signatory class, and supplied file labels.
[A07] Execution-status record: no procedure is selected and no archive output exists.
<!-- ATOM_BLOCK_END -->

## Recorded relations
[R01] A03 --COUNTEREXAMPLE_REVISES_SCOPE--> A02 :: The cross-access counterexample is the recorded reason V1 applies to mixed-signatory archives; it does not retire V0 for single-class records.
[R02] A04 --ORDERS_VERSION_RECORDS--> A01 :: The version log records V0 before V1; it does not encode a case-specific procedure selection.
[R03] A05 --IDENTIFIES_CURRENT_SHAPE--> A06 :: The current archive identifiers and labels are available for output verification.
[R04] A05 --VERIFICATION_FIELDS_FOR--> A06 :: Request identifier and signatory-class labels can be compared with output groups after any proposed procedure.
[R05] A07 --EXECUTION_STATUS_FOR--> A01 :: The archive record distinguishes a proposed grouping procedure from a completed export.
