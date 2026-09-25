# Control-equivalence note — CASE01

## Retained METHOD atoms

- A01: Candidate record: Route Alder emits the most recent signed document and its signature timestamp.
- A02: Candidate record: Route Birch emits the version chronology and file digests and can include an approval-event pointer.
- A03: Selection criterion: a checkpoint audit needs the content digest joined to the approval event for that checkpoint.
- A04: Context record: source version labels, checkpoint identifiers, and signature markers must be intact before export.
- A05: Expected observation: the delivered manifest associates each included content digest with a checkpoint and approval event.
- A06: Failure interpretation: a missing digest-to-event join leaves the approved content unresolved; an unsigned later correction is not an approval event.
- A07: Disposition record: keep a correction without an approval event pending; do not infer that a later file was part of an earlier checkpoint.

## Relation inventory

METHOD contains these relations: R01, R02, R03, R04, R05.
LINKLESS_METHOD_CONTROL retains: R02, R03, R04, R05.
Removed relation: R01.

## Why the cut is meaningful

The criterion and both candidate descriptions remain as atoms, but the relation that binds the checkpoint objective to the candidate is absent. The successor cannot source-license route selection from the remaining trace.

The control does not simply omit the target decision as a fact: there is no final-answer atom in either artifact. It preserves candidate/action, context, observation, failure or counterexample, and disposition atoms; the missing relation is the predeclared bridge that licenses the target choice or bounded disposition. No false contradiction or nonsense text is added.
