# Supplemental record CASE03

Representation note: structured synthetic records; relation rows connect source-linked records.

<!-- ATOM_BLOCK_BEGIN -->
## Atomic records
[A01] Candidate-diagnostic record: status query using the original immutable request key.
[A02] Candidate-operation record: resubmit control using the same idempotency key.
[A03] Gateway record: the original key received a QUEUED response.
[A04] Connection record: the client ended before storing a receipt body.
[A05] Status-field record: a query can return pending, terminal accepted, terminal not accepted, or unavailable.
[A06] Key record: RQ-18 is immutable and reuse does not create a second request.
[A07] Follow-up record: no status query or later submission is present in the event log.
<!-- ATOM_BLOCK_END -->

## Recorded relations
[R01] A06 --IDENTIFIES--> A03 :: The immutable key identifies the stored QUEUED response.
[R03] A05 --DISCRIMINATES_STATUS_FOR--> A03 :: The status fields distinguish pending, terminal, and unavailable states for the original request.
[R04] A06 --KEY_IDENTITY_FOR--> A02 :: RQ-18 names the same request identity; this record does not establish the request's present status or the safe next operation.
[R05] A07 --EXECUTION_STATUS_FOR--> A01 :: The event log separates a proposed diagnostic from a query already performed.
