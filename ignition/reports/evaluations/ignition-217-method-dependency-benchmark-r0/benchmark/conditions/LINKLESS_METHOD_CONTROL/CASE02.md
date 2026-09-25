# Supplemental record CASE02

Representation note: this excerpt preserves the same atomic records and source context as the companion trace, but its relation field is absent.

## Independently listed records
[A01] Candidate record: a cache purge can be submitted for the banner key.
[A02] Candidate record: defer the purge and run named-region revision probes.
[A03] Boundary record: during mixed regional revision state, a purge may refill an edge from an older origin snapshot.
[A04] Context record: the boundary applies to a rollout whose region markers have not converged.
[A05] Expected observation: every named region reports the target revision and the origin warm marker is stable on two probes.
[A06] Failure interpretation: any old or unavailable region marker means convergence has not been demonstrated.
[A07] Disposition record: withhold the purge until the stated observation is satisfied; the current record does not establish that condition.

No source record in this excerpt joins the listed records into an ordered selection, test, interpretation, and disposition chain.

## Recorded relations retained in this control
[R01] A04 activates the boundary recorded in A03.
[R03] A05 is the observation required before reconsidering A01.
[R04] A06 interprets a stale or unavailable probe as incomplete, not as success.
[R05] A07 records bounded non-application.
