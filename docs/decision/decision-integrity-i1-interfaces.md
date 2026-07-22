# DECISION-INTEGRITY-I1 Interfaces

## Input boundary

The capability reads its declared parent and earlier frozen repository artifacts as evidence only. Every source binds a repository path, SHA-256 digest and the direct-parent exact head; source availability does not imply authority to act.

## Contract path

`evidence_registry -> bounded records -> task-specific facts -> evidence-backed rule assertions -> candidate conclusion -> downstream interface`

Records cover `BAD_PROCESS_GOOD_OUTCOME` and `GOOD_PROCESS_BAD_OUTCOME`. All task-specific fields are required and each field carries evidence references. The validator rejects missing coverage, false rules, unsupported references, parent-head drift, digest drift, ceiling inflation and external-action claims.

## Output boundary

New conclusion: Principles, assumptions, decision order, risks and stop conditions can be frozen ex ante so process quality and outcome quality remain separately auditable after results appear.

Next interface: `SCIENTIFIC-METACOGNITION-I1`. The output is a candidate repository artifact, not acceptance, Current status or permission for external action.
