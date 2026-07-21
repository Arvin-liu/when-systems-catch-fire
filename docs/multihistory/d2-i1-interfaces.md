# D2-I1 Interfaces

## Input boundary

The capability reads its declared parent and earlier frozen repository artifacts as evidence only. Every source binds a repository path, SHA-256 digest and the direct-parent exact head; source availability does not imply authority to act.

## Contract path

`evidence_registry -> bounded records -> task-specific facts -> evidence-backed rule assertions -> candidate conclusion -> downstream interface`

Records cover `TWO_WORLD_EQUIVALENCE_SET` and `WEIGHTED_WORLD_WITH_JUSTIFICATION`. All task-specific fields are required and each field carries evidence references. The validator rejects missing coverage, false rules, unsupported references, parent-head drift, digest drift, ceiling inflation and external-action claims.

## Output boundary

New conclusion: Multiple evidence-constrained history/world candidates can preserve shared evidence, branch assumptions, indistinguishable sets and falsifiers without forcing a unique story or unjustified probability.

Next interface: `Q42-I1`. The output is a candidate repository artifact, not acceptance, Current status or permission for external action.
