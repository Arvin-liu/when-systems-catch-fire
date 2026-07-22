# SYMBOLIC-SPHERE-I1 Interfaces — repair-r1

## Input boundary

Input is a `1.1.0` symbolic bundle with an exact Q39 repair-r1 parent binding, explicit repository reference records, two task record types and a bounded conclusion. A repository reference is admissible only when its path is canonical repository-relative syntax, its commit exists locally, the path is a non-symlink blob in that commit, its declared blob and SHA-256 match actual Git bytes, and its declared role matches the selected object's actual type.

## Semantic boundary

`reference_records -> material symbolic object -> explicit actor positions -> corresponding meaning projections -> allowed power modalities -> distinct front/suppressed faces -> benefit/cost distribution -> independently evidenced counter-readings -> material-evidence constraint -> bounded conclusion`

The validator derives these relations from structured records. There are no `facts` or `rule_assertions` booleans that a caller can set to bypass validation.

## Output boundary

`GATE_PASS` means repository-local reference integrity and the bounded symbolic semantics passed. It is not truth, legitimacy, external fact verification or causal proof. If material evidence is missing, the validator returns `MISSING_MATERIAL_EVIDENCE` even when the bundle correctly downgrades its conclusion.

`DECISION-INTEGRITY-I1` is not started or modified by this repair.
