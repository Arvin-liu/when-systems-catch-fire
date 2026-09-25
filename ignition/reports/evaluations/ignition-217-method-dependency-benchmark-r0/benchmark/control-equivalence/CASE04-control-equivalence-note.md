# Control-equivalence note — CASE04

## Retained METHOD atoms

- A01: Candidate explanation: elevated root-zone salt concentration.
- A02: Candidate explanation: canopy heat exposure.
- A03: Candidate observation: a root-zone conductivity reading collected after four minutes of recirculation.
- A04: Selection rationale: the incoming feed value alone does not distinguish accumulated root-zone salt from canopy heat.
- A05: Boundary record: do not change feed concentration from leaf appearance or feed-tank conductivity alone.
- A06: Expected observation: compare the timed root-zone value with the recorded inlet value; a difference of at least 0.6 mS/cm supports accumulation, while a smaller difference leaves the two explanations unresolved.
- A07: Disposition record: request the timed root-zone observation and keep the cause unresolved until it is recorded.

## Relation inventory

METHOD contains these relations: R01, R02, R03, R04, R05.
LINKLESS_METHOD_CONTROL retains: R02, R03, R04, R05.
Removed relation: R01.

## Why the cut is meaningful

Both explanations and the exact sampling atoms remain, but the relation that identifies this observation as the discriminator between them is absent.

The control does not simply omit the target decision as a fact: there is no final-answer atom in either artifact. It preserves candidate/action, context, observation, failure or counterexample, and disposition atoms; the missing relation is the predeclared bridge that licenses the target choice or bounded disposition. No false contradiction or nonsense text is added.
