# Task228 target-blind instrument authoring guide R1

## Allowed construction inputs

For one candidate, use only its family's frozen `m0.md`, raw `revision-evidence-e1.md`, this normative contract, and an explicit researcher-authored mapping declaration. Do not open or use A/B/C targets, Task227 policy files, Task227 scores or dispositions, transfer outputs, or target-compatibility artifacts. Do not run a builder model or any transfer/revision session.

The declaration is the human-authored semantic transformation. The compiler only verifies its input bindings and serializes the declared rows into canonical JSON; compiler determinism does not make the semantic mapping itself deterministic or scientifically proven.

## Declaration and evidence locators

Each declaration names one family and candidate, exact source paths and frozen hashes, evidence items, scalar input meanings, selector/action/region rows, preserved M0 actions, fallback, stops, scope ceiling, and evidence references for every typed element. Each evidence item has an inclusive 1-based line range. Hash the exact concatenated LF-delimited byte lines with line terminators retained. CR in CRLF remains part of the preceding line. Include a final unterminated line as-is. Verify the whole source SHA-256 before reading its UTF-8 text. A display excerpt, if supplied, must equal those exact bytes and is not authoritative.

The declaration must distinguish an observed category from an invented threshold. It must state when a value is an explicit researcher-defined category for organizing source observations. Do not claim that a narrow E1 contrast establishes a universal rule. Every candidate keeps each named M0 baseline action available and retains `m0_action_retired: false`.

## Runtime contract

Inputs are required scalar values of type `number`, `string`, or `boolean`, each with a unit (`null` if dimensionless). Conditions use the contract's explicit operator set and exact input unit; there is no conversion. Condition arrays are conjunctions. Explicit out-of-scope matches take precedence. Exactly one licensed rule selects its linked action; missing/null required values, zero matches, or multiple matches use the universal fallback. Stops are checked before selector routing when their required values are present. No rule priority is inferred.

Parameters are explicitly typed `literal` or `input_ref` values. A reference must match the exact required-input type and unit and include that input's source references. Null and generic array parameters are unavailable. Fallback covers all excluded and unresolved states. The claim ceiling must state both the bounded licensed scope and that transfer, revision generation, causal effects, general inheritance, Cognitive Evolution, cross-model transfer, R1, Model-RSI, and training benefit are not established.

## Deterministic build and validation

Run `tools/build_reference_instruments.py --check` to rebuild all six candidates in memory and compare their bytes with checked-in JSON. Normal build mode writes only the six declared candidate files under `policies/`. Then run `tools/validate_policy.py --schema-only`, validate every policy with the required family binding, and run the conformance suite. The compiler's provenance records the declaration SHA-256 and compiler version. It must read only the declared source paths and must not enumerate target directories.

Machine validity proves serialization, frozen-source binding, typed consistency, referential integrity, and listed cross-field structure. It does not prove semantic support. Two independent read-only auditors must each review all six candidates with `reference/reviewer-rubric.md` and must not see each other's audit.
