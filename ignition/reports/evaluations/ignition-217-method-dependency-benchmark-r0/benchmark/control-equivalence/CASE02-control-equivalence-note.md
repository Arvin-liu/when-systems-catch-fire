# Control-equivalence note — CASE02

## Retained METHOD atoms

- A01: Candidate record: a cache purge can be submitted for the banner key.
- A02: Candidate record: defer the purge and run named-region revision probes.
- A03: Boundary record: during mixed regional revision state, a purge may refill an edge from an older origin snapshot.
- A04: Context record: the boundary applies to a rollout whose region markers have not converged.
- A05: Expected observation: every named region reports the target revision and the origin warm marker is stable on two probes.
- A06: Failure interpretation: any old or unavailable region marker means convergence has not been demonstrated.
- A07: Disposition record: withhold the purge until the stated observation is satisfied; the current record does not establish that condition.

## Relation inventory

METHOD contains these relations: R01, R02, R03, R04, R05.
LINKLESS_METHOD_CONTROL retains: R01, R03, R04, R05.
Removed relation: R02.

## Why the cut is meaningful

The boundary and both actions remain as atoms, but the relation that maps the mixed-state boundary to non-application is absent. Without it, the artifact does not license the case target.

The control does not simply omit the target decision as a fact: there is no final-answer atom in either artifact. It preserves candidate/action, context, observation, failure or counterexample, and disposition atoms; the missing relation is the predeclared bridge that licenses the target choice or bounded disposition. No false contradiction or nonsense text is added.
