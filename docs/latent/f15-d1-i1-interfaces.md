# F15-D1-I1 Interfaces

## Input boundary

The capability reads its declared parent and earlier frozen repository artifacts as evidence only. Every source binds a repository path, SHA-256 digest and the direct-parent exact head; source availability does not imply authority to act.

## Contract path

`evidence_registry -> bounded records -> task-specific facts -> evidence-backed rule assertions -> candidate conclusion -> downstream interface`

Records cover `IDENTIFIABLE_CANDIDATE` and `NON_IDENTIFIABLE_EQUIVALENCE_SET`. All task-specific fields are required and each field carries evidence references. The validator rejects missing coverage, false rules, unsupported references, parent-head drift, digest drift, ceiling inflation and external-action claims.

## Output boundary

New conclusion: Latent-system candidates and equivalent decompositions can remain candidate objects until distinguishing evidence passes an explicit identifiability gate.

Next interface: `D2-I1`. The output is a candidate repository artifact, not acceptance, Current status or permission for external action.
