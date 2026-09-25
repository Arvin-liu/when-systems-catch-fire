# Control-equivalence note — CASE03

## Retained METHOD atoms

- A01: Candidate record: status lookup by the original immutable request key.
- A02: Candidate record: a new submission under a new request key.
- A03: Observed response: the original request returned QUEUED before the client connection ended without storing a receipt body.
- A04: Failure interpretation: a missing receipt after QUEUED is an acknowledgement-unknown state, not a terminal rejection.
- A05: Expected observation: a status query under the same key returns pending, terminal accepted, terminal not accepted, or remains unavailable.
- A06: Boundary record: another submission is not licensed while the original key has a non-terminal or unavailable status.
- A07: Disposition record: reconcile the original key first; only a recorded terminal NOT_ACCEPTED state permits a new submission.

## Relation inventory

METHOD contains these relations: R01, R02, R03, R04, R05.
LINKLESS_METHOD_CONTROL retains: R01, R03, R04, R05.
Removed relation: R02.

## Why the cut is meaningful

The queued/lost-receipt and acknowledgement-unknown atoms are retained, as are both candidate actions, but the relation selecting status lookup over new submission is severed.

The control does not simply omit the target decision as a fact: there is no final-answer atom in either artifact. It preserves candidate/action, context, observation, failure or counterexample, and disposition atoms; the missing relation is the predeclared bridge that licenses the target choice or bounded disposition. No false contradiction or nonsense text is added.
