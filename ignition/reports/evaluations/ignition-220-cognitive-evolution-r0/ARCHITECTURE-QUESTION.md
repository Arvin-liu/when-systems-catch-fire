# Architecture question — bounded cognitive evolution R0

## Frozen question

> Given an initial method M0 and a source-bound failure/counterexample that exposes a boundary defect, can an independent revision agent produce a bounded M1 that (a) changes only what the evidence licenses, (b) preserves unaffected M0 scope, (c) records explicit M0→evidence→M1 lineage, and (d) enables a fresh successor to make better held-out decisions than M0 alone or M0 plus raw failure evidence without an explicit revision artifact?

The observable chain is:

`M0 → actual evidence/counterexample → revision operation → M1 → fresh successor use → held-out outcome`

This separates four questions:

1. **Representation:** can the revision be represented with provenance and scope?
2. **Revision validity:** is M1 licensed by the frozen failure evidence?
3. **Transfer utility:** does M1 improve fresh-successor decisions on held-out cases?
4. **Preservation:** does M1 avoid changing unaffected M0 scope?

The three frozen family operations are boundary narrowing, split/coexistence, and bounded retire-and-replace under decisive contradiction. A revision must be a semantic, source-bound change; wording-only rewriting does not qualify.

## Claim ceiling

Even a `SUPPORTED` R0 outcome would support only `BOUNDED_COGNITIVE_EVOLUTION_R0` for this synthetic benchmark. It would not establish autonomous self-improvement, general cognitive inheritance, causal cross-runtime effects, cross-model evolution, R1, or production capability.
