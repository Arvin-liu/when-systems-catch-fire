# CASE03 ambiguity proof — R1

## Evidence before the cut relation

FACTS and both byte-identical atom blocks record QUEUED, a lost receipt, no terminal status, an immutable non-duplicating key, and two available controls. LINKLESS retains R01 and R03–R05. Those relations identify the request, expose possible query statuses, preserve the key identity, and record that no follow-up occurred; they do not establish which next operation is licensed by this failure sequence.

## Two materially different licensed actions

1. Query status under RQ-18 before any further operation.
2. Resubmit using RQ-18 to retrieve or reconcile the existing idempotent request.

Both are consistent with FACTS, retained atoms, and retained relations. Reusing the key cannot create a second request, while the existing request's terminal state is unknown; the record does not state which control should come first.

## Missing relation

R02 classifies QUEUED followed by a lost receipt as acknowledgement status unknown and maps that failure class to a status query first, with a new submission permitted only after terminal NOT_ACCEPTED.

TWO_WAY_AMBIGUITY_DEMONSTRATED=YES
