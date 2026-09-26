# Supplemental record CASE02

Representation note: structured synthetic records; relation rows connect source-linked records.

<!-- ATOM_BLOCK_BEGIN -->
## Atomic records
[A01] Candidate-operation record: the purge control refreshes the selected edge-cache key.
[A02] Candidate-operation record: the wait-and-probe control records regional revision markers and the origin warm marker.
[A03] Current-state record: two named regions report B-12 and three report B-11.
[A04] Origin record: an older origin snapshot remains available during the rollout window.
[A05] Probe-field record: a regional marker and origin warm marker can be recorded at a stated time.
[A06] Probe-coverage record: a preview from one region is not a record for the other named regions.
[A07] Operation-log record: no cache-action result is present for this incident.
<!-- ATOM_BLOCK_END -->

## Recorded relations
[R01] A03 --STATE_SET_FOR--> A04 :: The regional-marker set and origin-snapshot record describe the same rollout interval.
[R02] A03 --BOUNDARY_TO_NONAPPLICATION--> A01 :: Mixed regional markers with an older origin snapshot make a purge inapplicable now. Defer it until every named region reports B-12 and the origin warm marker is stable on two probes; an old or unavailable marker fails this condition.
[R03] A05 --OBSERVED_FIELDS_FOR--> A02 :: The regional marker and origin warm marker are fields returned by a probe.
[R04] A06 --LIMITS_COVERAGE_OF--> A05 :: A single-region preview does not establish the state of every named region.
[R05] A07 --EXECUTION_STATUS_FOR--> A01 :: The incident log distinguishes a proposed operation from an operation result.
