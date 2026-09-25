# Supplemental record CASE03

Representation note: six ordered Method-Use Trace segments are expressed as task-local linked records; the existing global schema is unchanged.

## Atomic records
[A01] Candidate record: status lookup by the original immutable request key.
[A02] Candidate record: a new submission under a new request key.
[A03] Observed response: the original request returned QUEUED before the client connection ended without storing a receipt body.
[A04] Failure interpretation: a missing receipt after QUEUED is an acknowledgement-unknown state, not a terminal rejection.
[A05] Expected observation: a status query under the same key returns pending, terminal accepted, terminal not accepted, or remains unavailable.
[A06] Boundary record: another submission is not licensed while the original key has a non-terminal or unavailable status.
[A07] Disposition record: reconcile the original key first; only a recorded terminal NOT_ACCEPTED state permits a new submission.

## Recorded relations
[R01] A03 supports the acknowledgement-unknown interpretation in A04.
[R02] A04 licenses A01 before considering A02.
[R03] A05 discriminates the terminal state under the original key.
[R04] A06 bounds any further submission.
[R05] A07 records the conditional disposition.
