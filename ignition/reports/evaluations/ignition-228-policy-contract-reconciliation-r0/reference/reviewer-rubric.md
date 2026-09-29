# Task228 independent policy review rubric R1

This rubric implements `task228-policy-contract-r1`. Reviewers must not add operational thresholds, scientific exclusions, or source requirements that are absent from the normative contract. Record each machine rule as `PASS` or `FAIL`; a reviewer cannot waive a machine failure. Semantic findings must cite the candidate element and its M0/E1 evidence IDs. Do not inspect held-out targets, transfer outputs, Task227 policy scores, dispositions, or the other auditor's sheet.

## Machine predicates

The reviewer records the validator output for each exact rule ID below. Every candidate must pass every row.

| Rule ID | Review question |
|---|---|
| `SCHEMA_VALIDITY` | Does the policy pass the Draft 2020-12 Task228 schema with no undeclared fields? |
| `FAMILY_SOURCE_BINDING` | Are the family, exact M0/E1 source paths and frozen hashes correct, and do structured inclusive line ranges hash to the exact source bytes? |
| `UNIQUE_IDENTIFIERS` | Are all identifiers unique in their declared type, parameter names unique per action, and typed provenance pairs unique? |
| `EVIDENCE_REFERENCES` | Does every reference resolve, is every evidence item used, and does every source belong to this family and M0/E1? |
| `TYPED_CONDITIONS` | Do condition operators, values, scalar types, and units obey the exact contract? |
| `SELECTOR_ACTION_BIJECTION` | Does each selector map to one action and do their condition arrays match exactly? |
| `LICENSED_REGION_BIJECTION` | Does each selector map to one licensed region with exactly equal conditions? |
| `OUT_OF_SCOPE_COMPLEMENT` | Do explicit exclusions route to fallback, with an empty complement used only as the sole out-of-scope row? |
| `PRESERVATION_SEMANTICS` | Do preservation modes follow their condition rules, and is `m0_action_retired` false? |
| `PRESERVED_EVIDENCE_M0_ONLY` | Does every preserved-rule evidence list contain only M0 references? |
| `TYPED_PARAMETER_BINDING` | Are parameters non-null scalar literals or exact input references with matching type, unit, and source evidence? |
| `FALLBACK_UNIVERSALITY` | Is fallback unconditional and does it define a safe outcome, instruction, and required reporting? |
| `STOP_CONDITION_STRUCTURE` | Does each stop have nonempty typed conditions and an explicit safe outcome and instruction? |
| `SCOPE_REGION_LICENSING` | Are licensed claims limited to licensed regions and not-established claims limited to known regions? |
| `PROVENANCE_COVERAGE` | Is there exactly one provenance link for every contract-listed typed element, with identical direct evidence references? |

## Independent semantic review

For each of six candidates, answer `PASS`, `FAIL`, or `NOT_ESTABLISHED` for each dimension and give concise evidence-backed reasoning:

1. **Evidence support:** the cited frozen M0/E1 bytes support each observation, operational interpretation, and bounded derived claim.
2. **Operational completeness:** a user can apply the declared scalar inputs, conditions, actions, fallback, stops, and reporting without inventing an unstated procedure.
3. **Bounded applicability:** the policy does not turn a small observed pattern into a universal cutoff, corrected formula, or population-wide rule.
4. **Preservation:** the listed M0 actions remain available under the stated preservation semantics; no new rule silently retires them.
5. **Fallback and edge safety:** missing/null, excluded, zero-match, and multiple-match conditions go to the universal fallback; explicit stops are safe.
6. **Provenance meaning:** mapping declarations identify which M0/E1 observations support each typed policy element; evidence locators resolve to the exact frozen bytes.
7. **No unsupported universalization:** claims stay within the source-supported population and state what is not established.
8. **Target-blind lineage:** declarations and compiler provenance rely only on this family's M0, raw E1, and this contract; no target, Task227 outcome, or transfer result informed choices.
9. **Contract consistency:** the candidate's runtime meaning matches the contract, including exclusion precedence, exact-one-match selection, and fallback on missing, zero, or multiple matches.

## Decision

A candidate semantic pass requires `PASS` on all nine dimensions and `PASS` on all 15 machine predicates. A family or overall instrument readiness decision requires all six candidates to pass. Preserve disagreements in their original sheets; do not reconcile them or request a third audit. An auditor who cannot decide a dimension records `NOT_ESTABLISHED`, which is not a pass.
