# Control-equivalence note — CASE06

## Retained METHOD atoms

- A01: Candidate procedure Q: self-service code scan for entries with exact roster identifiers.
- A02: Candidate procedure D: staffed roster review for aliases and walk-ins.
- A03: Source record Q-1: scan completion observations from a cohort of exact identifier matches.
- A04: Source record D-1: desk resolution observations from a different cohort of aliases and walk-ins.
- A05: Evidence boundary: Q-1 and D-1 are not a head-to-head comparison and do not rank universal performance.
- A06: Expected observation: an exact roster identifier is verified by its event code; an alias or walk-in is routed to a documented roster review.
- A07: Disposition record: retain both cohort-bounded procedures; leave an unexplained mismatch unresolved pending roster evidence.

## Relation inventory

METHOD contains these relations: R01, R02, R03, R04, R05.
LINKLESS_METHOD_CONTROL retains: R01, R02, R03, R05.
Removed relation: R04.

## Why the cut is meaningful

The cohort-specific source records and evidence-boundary atom remain, but the relation assigning each cohort to its procedure is severed.

The control does not simply omit the target decision as a fact: there is no final-answer atom in either artifact. It preserves candidate/action, context, observation, failure or counterexample, and disposition atoms; the missing relation is the predeclared bridge that licenses the target choice or bounded disposition. No false contradiction or nonsense text is added.
