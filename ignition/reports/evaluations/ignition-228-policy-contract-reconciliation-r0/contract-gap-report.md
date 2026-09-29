# Task228 contract-gap report

## Terminal state

`TASK228_OWNER_ADJUDICATION_REQUIRED`

Phase 01 evidence binding and Phase 02 exhaustive validator forensics are complete. Phase 03 has a 20-row source matrix. Reconciliation stops here because three unresolved contract questions can affect which policies count as scientifically admissible. No Task228 normative-contract candidate, schema, validator, reviewer rubric, authoring guide, or reference-instrument candidate was adopted.

## Frozen result discrepancy

The exact Task227 Owner Packet is checksum-valid: all 100 manifest entries pass. Both raw reviewer sheets and the locked aggregate support **3/6 usable** (REF-01, REF-04, REF-05); the official frozen validator audit supports **0/6 pass**. Those are distinct endpoints and remain unchanged.

Task227 PR #237 is OPEN + DRAFT + UNMERGED at exact head `7d979b1aa523030b16f773a973477cbfca1e4513`; its four required current-head workflows are successful. The 52-file Task227 freeze and all six frozen M0/E1 sources match their manifest hashes.

## Exhaustive validator findings

The non-mutating harness checks the six original policy bytes against the frozen Task227 schema and validator, then runs the official validator unchanged to compare its first failure and pass/fail result. Three required tests pass. Every policy hash remained unchanged.

- REF-01: 10 failures; official first failure is preserved-rule refs must reference M0.
- REF-02: 13 failures; first failure is duplicate evidence IDs.
- REF-03: 3 failures; first failure is preserved-rule refs must reference M0.
- REF-04: 6 failures; first failure is preserved-rule refs must reference M0.
- REF-05: 4 failures; first failure is preserved-rule refs must reference M0.
- REF-06: 4 failures; first failure is unknown typed link `fallback:FALLBACK`.
- The exhaustive pass also found 22 evidence locator strings across all six files that are not literal substrings of their bound M0/E1 source files, plus typed scope-provenance IDs that do not match the validator's type map.
- The diagnostic reports selector/action mapping, condition equality, licensed-region mapping/equality, complement semantics, M0 retirement, fallback universality, stop structure, and licensed scope checks separately; none failed in these six policies.
- Task227 enforces selector condition type/unit checks, but it does not define or encode a typed action-parameter-to-input relation. That is an open contract field, not an inferred failure.

The detailed evidence is in `validator-failure-taxonomy.json`, `validator-failure-taxonomy.csv`, and `per-policy-validator-audit.md`.

## Owner decisions required

1. **Preserved-rule evidence origin.** The protocol requires preservation of M0 actions. The schema and authoring/review language permit evidence references without an M0-only constraint, while the validator rejects every preserved-rule reference whose source type is E1, including mixed M0+E1 context citations. Decide whether the field must be M0-only, or whether each preserved rule should require a baseline M0 reference and allow a separate E1 context reference. This affects proof of preservation and must not be guessed from the six outcomes.
2. **Source-locator grammar.** The validator requires a complete locator string to appear literally in one source file. The protocol, schema, reviewer criteria, and prompts do not define that syntax; the frozen policies use compound section/observation anchors, and 23 such strings fail literal matching. Decide whether literal substring matching is normative or specify a structured, revision-bound locator grammar and its verifier.
3. **Typed action parameters.** Task227 declares typed selector inputs and stores action parameters only as name/value pairs. It has no rule linking an action parameter to a selector input type or unit. Decide whether parameter types/units must be declared and which values must match an input. Do not add this rule or treat its absence as acceptable without a normative decision.

The additional ID differences (duplicate evidence IDs; `scope_claim` versus `scope_exclusion`; lowercase `fallback` versus `FALLBACK`) can be specified as deterministic serialization conventions only after they are kept separate from the three substantive decisions above. No convention was applied to a candidate contract.

## Stop boundary and next step

Do not reconcile the contract, produce or validate the six target-blind reference instruments, run transfer, revision-generation, or full-chain sessions, or open a Task228 Formal Draft PR until Owner/GPT answers the three questions and the normative matrix is updated. The current task establishes only the specific human/machine contract divergence and its blocker; it establishes no transfer, revision-generation, or cognitive-evolution capability.

## Owner/GPT adjudication and Phase 04 resolution

The 2026-09-29 A1 amendment resolves all three prior Owner questions prospectively for Task228 only:

1. **Preserved-rule evidence origin — resolved as `KEEP_VALIDATOR_RULE`.** `preserved_rules[].evidence_refs` must resolve exclusively to M0 evidence. E1 can support new selectors, actions, and bounded coexistence rows, but cannot establish what the baseline M0 action was. `m0_action_retired` remains false.
2. **Source locator — resolved as `SERIALIZATION_ONLY_NORMALIZATION` plus `ALIGN_SCHEMA_OR_REVIEWER_TO_PROTOCOL`.** Task228 replaces the undocumented literal-substring convention with a structured locator bound to the exact family source path, frozen source SHA-256, inclusive 1-based line range, and SHA-256 of the exact extracted source bytes. The line-slicing convention is LF-delimited byte lines with line terminators retained; CR bytes in CRLF are retained; a final non-LF-terminated line is included as-is. UTF-8 is decoded strictly after source-byte integrity is verified. The optional display excerpt is non-authoritative and must equal the extracted bytes if present.
3. **Action-parameter/input binding — resolved as `ALIGN_SCHEMA_OR_REVIEWER_TO_PROTOCOL`.** Every parameter is either a typed literal or a typed input reference. Input references must name a declared required input and match its type and unit exactly. No coercion, null parameter, generic untyped list, or simultaneous literal/input-reference fields are accepted. Parameter evidence references must support the literal or include the referenced input's source references.

The reconciled contract, schema, validator, rubric, and authoring guide are authored together in this Task228 subtree. The validator implements only the explicit machine predicates enumerated in the contract. The reviewer rubric repeats those predicates and adds the contract's required evidence-support / no-overgeneralization semantic judgment; a reviewer cannot waive a machine failure. Intentional differences from the historical Task227 schema/validator are listed in the contract. Task227 policies, scores, locks, aggregates, and results remain byte-unchanged.

Phase 04 is not treated as a scientific success based on Task227 pass rates. It is complete only when the contract/schema/validator/rubric align and positive plus adversarial conformance fixtures pass. Reference-instrument readiness, if reached, remains a separate later gate.

## Phase 04–05 execution result

The A1 resolutions are now encoded in the Task228 normative contract, Draft 2020-12 schema, validator, reviewer rubric, and authoring guide. The locator verifier checks the exact frozen M0/E1 source hash and inclusive LF-delimited byte slice (preserving CRLF bytes and a final unterminated line). Preserved-rule evidence remains M0-only. Parameters are typed scalars or exact type/unit-matched input references. The validator's stable rule IDs mirror the rubric.

The six explicit researcher-authored mapping declarations use only the family M0 and raw E1 source rows. A deterministic compiler reads only the six declared M0/E1 paths and serializes six candidates. Each candidate preserves the named M0 actions, has a bounded E1-derived route, universal fallback, measurement-quality stop, source-bound evidence, typed provenance, and scope ceiling. No A/B/C target or Task227 outcome was opened for candidate construction.

Verification completed: Task228 schema valid; candidate validator 6/6 pass; positive/adversarial conformance tests 4/4 pass; Task227 diagnostic regression tests 3/3 pass; compiler rebuild is byte-identical. No substantive requirement was relaxed to improve a frozen Task227 policy's pass rate. The dual independent semantic audits remain pending, so no reference-instrument-ready conclusion is made yet.
