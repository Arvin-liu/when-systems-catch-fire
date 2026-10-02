# Typed Route Interface Contract R1

Status: normative engineering contract for Task229-R3. Its claim ceiling is a deterministic interface definition with synthetic conformance only.

## Separation of responsibilities

The interface has three distinct stages:

1. A binding builder serializes an explicit, target-blind mapping from one source-case record into typed present values and explicit missing IDs.
2. A deterministic reference interpreter evaluates the frozen policy using that binding and emits route trace R1.
3. A successor may use the visible case prose to write explanatory answer text. Prose does not participate in route selection.

The R3 code reads policy bytes and bindings. It does not edit Task228 policies, use evaluator scores or target criteria, or run a successor or evaluator.

## Typed binding and missingness

Every binding carries the case and source-record identities, the SHA-256 of the exact source-case bytes, policy ID and exact policy-file SHA-256, builder version and source SHA-256, the sorted present-input ID list, the sorted policy-required-but-missing ID list, and the values for present inputs.

A present value has `present: true`, a JSON value, an explicit `value_type`, and an exact unit. An absent input is not an object in `bindings`; it appears only in `missing_input_ids`. Absence is never `null`, `false`, an empty string, or zero. Null is accepted only if the policy's required-input declaration explicitly permits the null type. No coercion is allowed.

The explicit mapping declaration uses an array of input records so duplicate IDs can be detected. It gives one mapping per policy-required input. A present declaration names an explicit JSON Pointer in the source-case object. An absent declaration has `present: false` and `source_pointer: null`, with no value field. Missing declarations, unknown IDs, duplicate IDs, type or unit mismatches, ambiguous pointers, or coercions fail closed.

The R1 policy type and unit contract is read from each frozen policy's `selector.required_inputs` entries. Each selector and stop condition input must be declared there. Conflicting declarations or a condition whose literal conflicts with the declared type or unit make the policy invalid for execution.

## Deterministic route semantics

Each condition evaluates to `MATCH`, `NO_MATCH`, or `MISSING_INPUT`. Only `eq` is supported. Equality is strict over both JSON type and value. For a set of conditions, any `NO_MATCH` makes the set `NO_MATCH`; otherwise any `MISSING_INPUT` makes it `MISSING_INPUT`; only an all-`MATCH` set matches. Empty condition sets, unknown operators, unknown input IDs, ambiguous type declarations, and type/unit errors fail closed.

The interpreter evaluates all stop conditions, then all selector rules. One matched stop and no matched selector selects `stop`. One matched selector and no matched stop selects `selector`. No matches selects `fallback`, even if required inputs are missing. More than one matching stop, more than one matching selector, or a stop-selector conflict fails closed as `ROUTE_AMBIGUOUS`.

`evaluated_input_ids` is the sorted set of present required inputs available to the selector and stop conditions. `missing_input_ids` is the sorted set of required policy inputs absent from the binding. The lists are disjoint; an absent ID can never appear in `evaluated_input_ids`.

## Prose and trace boundary

The typed binding is the sole authority for routing. Case prose remains visible to the successor for an explanatory answer. If the successor detects a prose/binding inconsistency, it records `PROSE_BINDING_CONFLICT` and fails closed without emitting a route trace. It must preserve the bound value and must not reinterpret it.

Trace R1 binds the policy bytes and canonical binding digest. A selector trace names the exact selector rule and `action_ref`. A stop trace names the exact stop ID and has a null action ID. A fallback trace has null rule and action IDs and is valid only when no stop or selector fully matches. Ambiguous or prose-conflict executions have no valid route trace.

## Frozen provenance and limits

The machine contract pins the six Task228 policy hashes, historical input-map commit/path/hash, and original validator commit/path/hash. Those are read-only inputs. The historical input map migration proof may serialize its frozen values into R1 bindings and compare every value to the source map; it may not reconstruct the map from prose.

This contract does not establish live successor behavior, reference compatibility, transfer, policy effect, causal effect, revision generation, Cognitive Evolution, cross-model transfer, Model-RSI, or training benefit. Task230 remains unauthorized.
