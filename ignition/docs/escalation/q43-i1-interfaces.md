# Q43-I1 Interfaces

## Input boundary

The capability reads its declared parent and earlier frozen repository artifacts as evidence only. Every source binds a repository path, SHA-256 digest and the direct-parent exact head; source availability does not imply authority to act.

## Contract path

`evidence_registry -> bounded records -> task-specific facts -> evidence-backed rule assertions -> candidate conclusion -> downstream interface`

Records cover `REPOSITORY_LOCAL_REVERSIBLE` and `HIGH_RISK_REQUEST_ONLY`. All task-specific fields are required and each field carries evidence references. The validator rejects missing coverage, false rules, unsupported references, parent-head drift, digest drift, ceiling inflation and external-action claims.

## Output boundary

New conclusion: Actions can be classified by risk, reversibility, evidence, authority and expertise so only repository-local reversible actions are automatic and high-risk external actions become request-only escalations.

Next interface: `Q44-I1`. The output is a candidate repository artifact, not acceptance, Current status or permission for external action.
