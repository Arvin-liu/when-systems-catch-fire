# Neutral revision prompt — Task220 R0

You are given one frozen initial method M0 and one source-bound packet E1 containing observations from a failure or counterexample. Use only the provided M0, E1, and output schema.

Produce one externally auditable proposed M1. Identify the M0 claim or relation affected, cite the exact E1 source locators that support a change, state the operation, mark the changed and preserved scopes, preserve unresolved boundaries, and represent M0 → E1 → M1 lineage. Leave unrelated M0 components intact. If E1 does not license a change for a scope, do not invent one.

The operation vocabulary distinguishes UPDATE, NARROW, SPLIT_COEXIST, REJECT, RETIRE, and RETIRE_REPLACE_BOUNDED. A wording-only rewrite is not a revision; if that is all the evidence supports, say so explicitly. Rejecting or retiring a claim in one scope does not silently remove its other supported uses.

Use only exact source locators present in E1. Separate observation from inference. Do not invent measurements, sources, execution, validation, or successor outcomes. State a bounded uncertainty and the observation that would resolve it when needed. Do not expose hidden chain-of-thought; provide only the structured fields in the output schema.

Return exactly one JSON object conforming to the supplied schema. Do not add prose outside the object. Do not browse other repository paths, search for held-out cases or scoring targets, contact another agent, or execute a method. This is a proposal only; no experiment is being run.
