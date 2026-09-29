# Task228 normative policy contract R1

Status: `RECONCILED_CANDIDATE`  
Scope: Task228 reference-instrument construction and later independent semantic audit only.  
Dialect: `task228-policy-contract-r1`.

## Precedence and frozen decisions

For Task228, the frozen Task227 protocol intent and this Owner/GPT adjudication govern over historical schema or implementation details. Task227 remains a read-only historical record. This contract does not alter its schema, validator, policies, reviews, scores, lock, aggregates, or dispositions.

The three Owner/GPT decisions are normative:

- Preserved baseline evidence is M0-only. E1 cannot establish the identity or content of a preserved M0 action.
- Evidence location is structured and verified against frozen source bytes, not inferred from locator prose or required to appear as an undocumented literal substring.
- Action parameters use explicit `literal` or `input_ref` binding. An `input_ref` has exactly the referenced input's declared type and unit.

## Allowed inputs and evidence boundary

A policy is family-specific. Its only source artifacts are that family's frozen `m0.md` (M0) and `revision-evidence-e1.md` (E1). The validator binds these exact paths and SHA-256 values through the Task227 freeze manifest and independently re-hashes the bytes. No sibling-family source, Task227 reference policy, transfer output, score, target-compatibility artifact, or A/B/C target may be used to select policy behavior.

Every `evidence_basis` entry has a unique ID, source type, exact family source path, frozen-source SHA-256, structured locator, support statement, and claim type (`observed`, `derived`, or `method_rule`). The locator has inclusive 1-based `start_line` and `end_line` and `excerpt_sha256`. The verifier first checks the source SHA-256, decodes the bytes as strict UTF-8, slices LF-delimited lines including their original terminator bytes, and hashes the exact concatenated slice. CRLF retains both CR and LF. A final unterminated line is included as-is. The range must be in bounds. An optional `display_excerpt` must equal the extracted bytes decoded as UTF-8; it is never the authority.

Every evidence ID is unique within a policy and must be referenced by at least one policy element or declared input. Every evidence reference must resolve. Provenance is a complete typed index: there is exactly one provenance row for each typed policy element, and its evidence-reference set equals the element's direct reference set.

## Canonical policy shape and provenance coverage

Every Task228 policy declares `contract_version: "task228-policy-contract-r1"`, a unique policy ID, one of the three frozen family IDs, and its researcher-authored `mapping_id`. Evidence, inputs, rules, actions, regions, preservation rows, stop rows, fallback, scope claims, and provenance are explicit objects. Semantic rows carry nonempty direct evidence-reference lists. The typed provenance index has exactly one link for each of these object kinds: `required_input`, `selector_rule`, `action`, `licensed_region`, `out_of_scope`, `preserved_rule`, `fallback`, `stop_condition`, `licensed_claim`, and `not_established_claim`. Nested report fields and parameters are covered by their parent action's direct evidence references; they are not separate provenance element types. The declaration hash and compiler identity are recorded at the provenance root.

## Selector inputs, conditions, and actions

Required inputs declare a unique ID, human-readable meaning, scalar type (`number`, `string`, `boolean`), unit (`string` or null), and evidence references. Conditions are typed against those declarations and must repeat the exact unit. There is no implicit conversion.

Task228 condition operators and semantics:

- `eq` / `neq`: exact equality / inequality for a scalar of the declared type.
- `lt`, `lte`, `gt`, `gte`: ordered comparison for numeric inputs only.
- `in` / `not_in`: membership / non-membership in a nonempty list of scalar values, all of the declared type.
- `between`: inclusive numeric interval `[low, high]` with `low <= high`.
- `present` / `absent`: the input is supplied with a non-null value / is not supplied or is null; `value` is null for these operators.

A condition list is a conjunction (AND); separate rules express alternatives. At runtime, missing or null required input goes to the universal fallback. Explicit out-of-scope matches take precedence and go to fallback. Otherwise, exactly one matching licensed rule selects its linked action. Zero or multiple matches go to fallback; the contract does not infer rule priority. Stop conditions are checked before selector routing when their required input values are present; a matched stop condition takes its declared safe outcome. These rules make overlaps and missingness deterministic without claiming that the input domain is exhaustive.

Each selector rule maps one-to-one to an action row; their condition arrays are byte-structurally equal after JSON parsing. Every licensed region maps one-to-one to a selector rule and copies that rule's conditions exactly. The only empty out-of-scope condition array means the complement of all licensed regions and must be the sole out-of-scope row. Every out-of-scope route points to the fixed `fallback` identifier.

Action categories are explicit operational verbs: `KEEP_BASELINE`, `APPLY_EVIDENCE_RULE`, `COLLECT_MEASUREMENT`, `REPEAT_OR_REACQUIRE`, `ROUTE_FOR_REVIEW`, `RECONCILE`, `UNSCORABLE`, and `REPORT`. Task228 excludes the historical `OTHER` category because its semantics are not operationally defined in the frozen contract. Every action has at least one required report field. Parameters are scalar and non-null:

- A `literal` declares `value_type`, `value`, unit or null, and evidence references. The JSON scalar must have that type.
- An `input_ref` declares `input_id`, `value_type`, unit or null, and evidence references. The ID must name a required input; type and unit must exactly match. Parameter evidence references must contain all source references of the named input.

Parameter names are unique within an action. Empty parameter arrays are allowed only for `KEEP_BASELINE` and `UNSCORABLE`. Task228 does not support generic list parameters; a future typed-container contract would require an explicit container and item type. Literal nulls are disallowed.

## Applicability, preservation, fallback, and stops

An empty `applicability.out_of_scope[].conditions` denotes the complement of the licensed regions, not a universal licensed region. Explicit excluded patterns and any zero-match / multiple-match / missing-input case route to the universal fallback.

A preserved-rule row must identify a baseline action, keep `m0_action_retired: false`, and cite only M0 evidence:

- `unconditional`: `when` is empty; baseline action remains available regardless of selector result.
- `selector_miss`: `when` is empty; baseline action remains available when no new selector uniquely applies.
- `additive_coexistence`: `when` is nonempty and exactly equals one selector rule's conditions; the baseline action remains alongside that new action.

The fallback has `when: []` and a safe, explicit outcome/instruction/report set. It covers all excluded, unresolved, missing, and unmatched inputs. Stop conditions have nonempty typed conditions and a declared safe outcome (`STOP`, `UNSCORABLE`, `RECONCILE`, `REACQUIRE`, or `ESCALATE`). Fallback is the general catch-all; stops express known explicit conditions.

## Scope ceiling

Licensed claims may reference only licensed region IDs. `not_established` claims may reference known licensed or excluded region IDs. Claims require evidence references. The text must bound any generalization to the source-supported population and state what is not established. No Task228 policy or candidate establishes transfer, revision generation, causal effect, general inheritance, Cognitive Evolution, cross-model transfer, R1, Model-RSI, or training benefit.

## Exact machine-validity gate

`tools/validate_policy.py` enforces the schema and the following stable rules, each mirrored by the reviewer rubric:

| Rule ID | Machine predicate |
|---|---|
| `SCHEMA_VALIDITY` | Draft 2020-12 schema is valid and the policy passes it. |
| `FAMILY_SOURCE_BINDING` | Family, M0/E1 paths, frozen SHA-256 values, actual source bytes, and structured line locators agree. |
| `UNIQUE_IDENTIFIERS` | Evidence, input, rule, action, region, preservation, stop, claim, parameter, and typed provenance IDs have the required uniqueness. |
| `EVIDENCE_REFERENCES` | Every reference resolves; every evidence item is used; source/type restrictions are satisfied. |
| `TYPED_CONDITIONS` | Inputs, values, operators, and units match the exact contract semantics. |
| `SELECTOR_ACTION_BIJECTION` | Selector/action IDs map one-to-one and conditions are identical. |
| `LICENSED_REGION_BIJECTION` | Each selector has exactly one licensed region with identical conditions. |
| `OUT_OF_SCOPE_COMPLEMENT` | Exclusion routes resolve; the empty complement appears alone. |
| `PRESERVATION_SEMANTICS` | Mode conditions are correct and the M0 action is not retired. |
| `PRESERVED_EVIDENCE_M0_ONLY` | Every preserved-rule reference is M0. |
| `TYPED_PARAMETER_BINDING` | Literal values match explicit scalar types; input references exactly match input type/unit and source refs. |
| `FALLBACK_UNIVERSALITY` | The fallback condition list is empty and safe fields are present. |
| `STOP_CONDITION_STRUCTURE` | Stop rows are unique, typed, nonempty, and have explicit outcomes/instructions. |
| `SCOPE_REGION_LICENSING` | Licensed and not-established region references obey the ceiling. |
| `PROVENANCE_COVERAGE` | Typed provenance covers every listed element exactly once and matches its direct evidence refs; nested reports and parameters use their parent action's evidence. |

The machine gate does not decide whether an observation scientifically supports a derived policy meaning; that interpretive support is explicitly reviewed by humans under the same contract.

## Machine validity and human semantic audit

Machine validity is necessary and limited to serialization, immutable-source binding, typed consistency, referential integrity, and cross-field structure listed above. It does not imply semantic support or instrument readiness. Each independent semantic auditor separately assesses evidence support, operational completeness, bounded applicability, preservation, fallback/edge safety, provenance meaning, unsupported universalization, target-blind lineage, and consistency with this contract. A semantic pass cannot waive a machine failure; machine pass cannot replace a semantic audit. Instrument readiness requires all six candidates to pass the machine gate and both independent audits to pass all six, plus byte-stable rebuild and zero target access.

## Intentional differences from Task227 implementation

These are prospective Task228 contract/schema/validator choices. They do not edit or reinterpret Task227 artifacts:

1. `source_locator` free text becomes a frozen-source SHA-256 plus inclusive line range and excerpt SHA-256, with exact byte-slicing semantics.
2. The Task227 validator's M0-only preserved-rule check is retained and promoted into the written Task228 contract; preserved-rule references cannot mix in E1.
3. Action parameters change from untyped `{name, value}` values to explicit typed `literal` or `input_ref`; references match required-input type, unit, and evidence.
4. Unspecified `stable`, `complete`, `reproducible`, `matches`, and `OTHER` tokens are excluded. Their meanings are not broadened by this repair; equivalent known states can be supplied as typed inputs and compared using `eq`.
5. Action parameter lists are scalar-only in this dialect. Null and generic array parameters are not accepted.
6. Provenance must cover every typed element exactly once and match its direct evidence-reference set.
7. At runtime, exclusion wins; exactly one licensed match selects; missing, zero-match, or multiple-match input routes to fallback. No implicit priority is introduced.

The changes either encode the adjudicated contract more explicitly or narrow undefined serialization/operation forms. No Task227 result is used to relax a substantive scientific requirement.
