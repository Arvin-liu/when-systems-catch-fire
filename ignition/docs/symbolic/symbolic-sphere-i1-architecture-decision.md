# SYMBOLIC-SPHERE-I1 Architecture Decision — repair-r1

Status: local repair candidate. Direct repair predecessor is `121Q39-REPAIR-R1` at frozen head `99ab601a48dd45972b238e468bc8e3002d648c98`. Remote state is `NOT_CHECKED_LOCAL_ONLY`.

## Decision

SYMBOLIC-SPHERE no longer accepts caller-supplied booleans as evidence that its semantic rules passed. Its validator resolves every evidence object from existing local Git history, verifies the exact commit tree entry, blob identity and SHA-256 over actual bytes, then recomputes task-specific symbolic semantics.

Each repository reference record contains at least:

- `repository_relative_path`
- `commit_sha`
- `blob_sha`
- `sha256`
- `record_type`
- `declared_role`

The repair pilot also names an `object_id`. The referenced JSON bytes contain the actual object and `object_type`; `declared_role` must equal that actual type.

## Recomputed semantic gates

- `symbolic_object_ref` resolves to a `MATERIAL_OBJECT` in the same record scope.
- Every `actor_position` resolves an explicit `ACTOR`.
- Every `meaning_projection` binds an existing actor position and the record's symbolic object.
- Power modalities are restricted to `ACCESS_CONTROL`, `RESOURCE_ALLOCATION`, `INSTITUTIONAL_AUTHORITY`, `NAMING_AUTHORITY`, `OWNERSHIP`, and `POPULARITY`.
- `front_face` and `suppressed_face` keep different identities, statements and actor-position sets.
- `benefit_cost_distribution` retains beneficiaries, cost bearers and typed distribution evidence.
- Every counter-reading targets a meaning projection and binds its own `COUNTER_READING_EVIDENCE` rather than reusing the target assertion as free-text support.
- An unsatisfied material-evidence constraint returns a stable nonzero result. The bundle must also downgrade its conclusion to `INSUFFICIENT_MATERIAL_EVIDENCE`; downgrade does not turn the validator result into a pass.
- Conclusion status independently blocks truth upgrades from ownership, popularity or naming authority and blocks complete causal-proof upgrades from symbolic analysis.

## Stable failure boundary

The CLI returns stable nonzero results for missing required records, invalid parent binding, unresolved or escaping repository paths, unresolvable commits, missing targets, blob mismatch, SHA-256 mismatch, unsupported reference or symbolic record types, declared-role mismatch, actor/meaning/power inconsistency, face impersonation, incomplete distribution, unbound counter-readings, missing material evidence, truth upgrade, causal overclaim and external action.

The pilot remains repository-local synthetic material. Passing establishes only that the declared repository references and bounded symbolic-analysis structure are internally consistent. It does not establish external facts, truth, legitimacy, popularity, ownership, naming authority or causality.
