# Task228 candidate revision v2 — Auditor A raw audit sheet

Validator and compiler checks were rerun in the isolated package. All six validators returned `TASK228_POLICY_SCHEMA=PASS` and `TASK228_POLICY_VALID=PASS`; the compiler check returned `TASK228_REFERENCE_REBUILD=BYTE_IDENTICAL`.

## POLICY_F01_A

**Machine predicates — PASS:** `SCHEMA_VALIDITY`; `FAMILY_SOURCE_BINDING`; `UNIQUE_IDENTIFIERS`; `EVIDENCE_REFERENCES`; `TYPED_CONDITIONS`; `SELECTOR_ACTION_BIJECTION`; `LICENSED_REGION_BIJECTION`; `OUT_OF_SCOPE_COMPLEMENT`; `PRESERVATION_SEMANTICS`; `PRESERVED_EVIDENCE_M0_ONLY`; `TYPED_PARAMETER_BINDING`; `FALLBACK_UNIVERSALITY`; `STOP_CONDITION_STRUCTURE`; `SCOPE_REGION_LICENSING`; `PROVENANCE_COVERAGE`.

**Semantic dimensions:**

1. **Evidence support — PASS.** `F01A_ROUTE_CONTACT_CONTEXT`; `F01_E1_TRIGGER`, `F01_E1_CONTROLS`, and `F01_E1_LIMITS` support review of the observed silver-film/toward-sun pattern without a thermal correction.
2. **Operational completeness — PASS.** The validity, surface, and bearing inputs select the named pattern; the action specifies contact/VWC review and the report fields identify what to record.
3. **Bounded applicability — PASS.** `POLICY_F01_A_BOUNDED_CLAIM` limits routing to the explicitly coded pattern; `F01_E1_LIMITS` rejects universal cutoffs or global M0 changes.
4. **Preservation — PASS.** `F01_M0_ACTIONS` supports all four unconditional preserved actions; each keeps `m0_action_retired: false`.
5. **Fallback and edge safety — PASS.** `POLICY_F01_A_INVALID_MEASUREMENT_STOP` safely reacquires; fallback covers missing, excluded, zero-match, and multiple-match cases.
6. **Provenance meaning — PASS.** Candidate elements map to family M0/E1 evidence; structured locators validate against the frozen bytes.
7. **No unsupported universalization — PASS.** `POLICY_F01_A_LIMITS` disclaims universal reflective-surface rules, corrected thresholds, and global M0 changes.
8. **Target-blind lineage — PASS.** `MAP_F01_A` is declared target-blind; provenance hash matches the mapping declaration, and the compiler reads only declared M0/E1 paths.
9. **Contract consistency — PASS.** The single licensed match selects its linked action; the complement, stop, and universal fallback follow contract routing.

## POLICY_F01_B

**Machine predicates — PASS:** `SCHEMA_VALIDITY`; `FAMILY_SOURCE_BINDING`; `UNIQUE_IDENTIFIERS`; `EVIDENCE_REFERENCES`; `TYPED_CONDITIONS`; `SELECTOR_ACTION_BIJECTION`; `LICENSED_REGION_BIJECTION`; `OUT_OF_SCOPE_COMPLEMENT`; `PRESERVATION_SEMANTICS`; `PRESERVED_EVIDENCE_M0_ONLY`; `TYPED_PARAMETER_BINDING`; `FALLBACK_UNIVERSALITY`; `STOP_CONDITION_STRUCTURE`; `SCOPE_REGION_LICENSING`; `PROVENANCE_COVERAGE`.

**Semantic dimensions:**

1. **Evidence support — PASS.** `F01B_REACQUIRE_CONTEXT`; `F01_E1_PARTIAL` and `F01_E1_LIMITS` support reacquiring the observed incomplete-coverage, variable-reading context.
2. **Operational completeness — PASS.** The coverage boolean and researcher-coded reading category select reacquisition; reporting names coverage, bearing, paired readings, mask status, and contact variation.
3. **Bounded applicability — PASS.** `MAP_F01_B` limits the route to the source-observed pattern and rejects invented coverage or variation cutoffs.
4. **Preservation — PASS.** `F01_M0_ACTIONS` supports all four unconditional preserved actions; none is retired.
5. **Fallback and edge safety — PASS.** The invalid-measurement stop reacquires; missing, excluded, zero-match, and multiple-match cases use fallback.
6. **Provenance meaning — PASS.** `F01_E1_PARTIAL`, `F01_E1_LIMITS`, `F01_E1_QUALITY`, and M0 evidence support the assigned elements; locators validate.
7. **No unsupported universalization — PASS.** `POLICY_F01_B_BOUNDED_CLAIM` adds no numeric threshold; `POLICY_F01_B_LIMITS` disclaims universal reflective-surface rules and global M0 changes.
8. **Target-blind lineage — PASS.** `MAP_F01_B` and hash-linked compiler provenance identify the allowed family M0/E1 and contract basis.
9. **Contract consistency — PASS.** The single licensed match selects reacquisition; all other unresolved or unmatched cases fall back.

## POLICY_F02_A

**Machine predicates — PASS:** `SCHEMA_VALIDITY`; `FAMILY_SOURCE_BINDING`; `UNIQUE_IDENTIFIERS`; `EVIDENCE_REFERENCES`; `TYPED_CONDITIONS`; `SELECTOR_ACTION_BIJECTION`; `LICENSED_REGION_BIJECTION`; `OUT_OF_SCOPE_COMPLEMENT`; `PRESERVATION_SEMANTICS`; `PRESERVED_EVIDENCE_M0_ONLY`; `TYPED_PARAMETER_BINDING`; `FALLBACK_UNIVERSALITY`; `STOP_CONDITION_STRUCTURE`; `SCOPE_REGION_LICENSING`; `PROVENANCE_COVERAGE`.

**Semantic dimensions:**

1. **Evidence support — PASS.** `F02A_GRAVIMETRIC_REVIEW`; `F02_E1_ORGANIC`, `F02_E1_QC`, and `F02_E1_LIMITS` support review of the named organic-floc observations.
2. **Operational completeness — PASS.** The measurement-valid and researcher-coded composition inputs select review; report fields specify composition assay, turbidity duplicates, M0 estimate, and gravimetric result.
3. **Bounded applicability — PASS.** `POLICY_F02_A_BOUNDED_CLAIM` confines the route to the named E1 category and supplies no composition cutoff or formula.
4. **Preservation — PASS.** `F02_M0_ACTIONS` supports all four unconditional preserved actions; none is retired.
5. **Fallback and edge safety — PASS.** Invalid measurements stop for reacquisition; missing, excluded, zero-match, and multiple-match cases use fallback.
6. **Provenance meaning — PASS.** `F02_E1_ORGANIC`, `F02_E1_QC`, `F02_E1_LIMITS`, and M0 evidence support the elements; nested report references are included in action evidence.
7. **No unsupported universalization — PASS.** `POLICY_F02_A_LIMITS` disclaims universal composition boundaries, a new calibration, and global M0 replacement.
8. **Target-blind lineage — PASS.** `MAP_F02_A` and the declaration-hash/compiler provenance bind the candidate to permitted M0/E1 sources and the contract.
9. **Contract consistency — PASS.** The single matching rule selects review; complement routing and fallback are contract-consistent.

## POLICY_F02_B

**Machine predicates — PASS:** `SCHEMA_VALIDITY`; `FAMILY_SOURCE_BINDING`; `UNIQUE_IDENTIFIERS`; `EVIDENCE_REFERENCES`; `TYPED_CONDITIONS`; `SELECTOR_ACTION_BIJECTION`; `LICENSED_REGION_BIJECTION`; `OUT_OF_SCOPE_COMPLEMENT`; `PRESERVATION_SEMANTICS`; `PRESERVED_EVIDENCE_M0_ONLY`; `TYPED_PARAMETER_BINDING`; `FALLBACK_UNIVERSALITY`; `STOP_CONDITION_STRUCTURE`; `SCOPE_REGION_LICENSING`; `PROVENANCE_COVERAGE`.

**Semantic dimensions:**

1. **Evidence support — PASS.** `F02B_RECONCILE_ALIQUOTS`; `F02_E1_UNREPRODUCIBLE` and `F02_E1_LIMITS` support reconciliation of OBS-08’s aliquot-dependent composition and gravimetric spread.
2. **Operational completeness — PASS.** The two boolean observations select reconciliation; reporting requires separate aliquot composition, turbidity, and gravimetric records.
3. **Bounded applicability — PASS.** `POLICY_F02_B_BOUNDED_CLAIM` limits the route to the OBS-08 pattern and supplies no point estimate.
4. **Preservation — PASS.** `F02_M0_ACTIONS` supports all four unconditional preserved actions; none is retired.
5. **Fallback and edge safety — PASS.** Invalid measurements stop for reacquisition; missing, excluded, zero-match, and multiple-match cases use fallback.
6. **Provenance meaning — PASS.** `F02_E1_UNREPRODUCIBLE`, `F02_E1_LIMITS`, `F02_E1_QC`, and M0 evidence support the elements; nested references are covered by action evidence.
7. **No unsupported universalization — PASS.** `POLICY_F02_B_LIMITS` disclaims universal composition boundaries, new calibration, and global M0 replacement.
8. **Target-blind lineage — PASS.** `MAP_F02_B` and hash-linked compiler provenance bind the candidate to the allowed sources and contract.
9. **Contract consistency — PASS.** The single licensed match selects reconciliation; the complement, stop, and fallback follow contract semantics.

## POLICY_F03_A

**Machine predicates — PASS:** `SCHEMA_VALIDITY`; `FAMILY_SOURCE_BINDING`; `UNIQUE_IDENTIFIERS`; `EVIDENCE_REFERENCES`; `TYPED_CONDITIONS`; `SELECTOR_ACTION_BIJECTION`; `LICENSED_REGION_BIJECTION`; `OUT_OF_SCOPE_COMPLEMENT`; `PRESERVATION_SEMANTICS`; `PRESERVED_EVIDENCE_M0_ONLY`; `TYPED_PARAMETER_BINDING`; `FALLBACK_UNIVERSALITY`; `STOP_CONDITION_STRUCTURE`; `SCOPE_REGION_LICENSING`; `PROVENANCE_COVERAGE`.

**Semantic dimensions:**

1. **Evidence support — PASS.** `F03A_PRODUCT_STABILITY_REVIEW`; `F03_E1_PULSED_P`, `F03_E1_CONTRAST`, and `F03_E1_LIMITS` support review of the observed group-P pulse pattern and its contrasts.
2. **Operational completeness — PASS.** Validity, recorded group, and researcher-coded pulse pattern select review; report fields require formulation, trace, interval record, and assay context.
3. **Bounded applicability — PASS.** `POLICY_F03_A_BOUNDED_CLAIM` limits routing to the named E1 group-P pattern and asserts no pulse threshold or degradation finding.
4. **Preservation — PASS.** `F03_M0_ACTIONS` supports all four unconditional preserved actions; none is retired.
5. **Fallback and edge safety — PASS.** Invalid measurements stop for reacquisition; missing, excluded, zero-match, and multiple-match cases use fallback.
6. **Provenance meaning — PASS.** `F03_E1_PULSED_P`, `F03_E1_CONTRAST`, `F03_E1_LIMITS`, and M0 evidence support the elements; locators validate.
7. **No unsupported universalization — PASS.** `POLICY_F03_A_LIMITS` disclaims universal pulse thresholds, confirmed degradation rules, and global M0 replacement.
8. **Target-blind lineage — PASS.** `MAP_F03_A` and the matching provenance hash identify the allowed mapping, compiler, and M0/E1 source basis.
9. **Contract consistency — PASS.** The sole licensed match selects review; stop, complement, and fallback routing match the contract.

## POLICY_F03_B

**Machine predicates — PASS:** `SCHEMA_VALIDITY`; `FAMILY_SOURCE_BINDING`; `UNIQUE_IDENTIFIERS`; `EVIDENCE_REFERENCES`; `TYPED_CONDITIONS`; `SELECTOR_ACTION_BIJECTION`; `LICENSED_REGION_BIJECTION`; `OUT_OF_SCOPE_COMPLEMENT`; `PRESERVATION_SEMANTICS`; `PRESERVED_EVIDENCE_M0_ONLY`; `TYPED_PARAMETER_BINDING`; `FALLBACK_UNIVERSALITY`; `STOP_CONDITION_STRUCTURE`; `SCOPE_REGION_LICENSING`; `PROVENANCE_COVERAGE`.

**Semantic dimensions:**

1. **Evidence support — PASS.** `F03B_RECONCILE_TRACE_AND_ASSAY`; `F03_E1_TRACE_GAP` and `F03_E1_LIMITS` support reconciliation of OBS-06’s trace gap and assay disagreement without inferring pulse or degradation.
2. **Operational completeness — PASS.** The trace-completeness and assay-reconciliation inputs select reconciliation; report fields specify logger, trace, assay, clock, and custody records.
3. **Bounded applicability — PASS.** `POLICY_F03_B_BOUNDED_CLAIM` restricts the route to the OBS-06 pattern and makes no pulse or degradation inference.
4. **Preservation — PASS.** `F03_M0_ACTIONS` supports all four unconditional preserved actions; none is retired.
5. **Fallback and edge safety — PASS.** Invalid measurements stop for reacquisition; missing, excluded, zero-match, and multiple-match cases use fallback.
6. **Provenance meaning — PASS.** `F03_E1_TRACE_GAP`, `F03_E1_LIMITS`, and M0 evidence support the elements; nested references are covered by action evidence.
7. **No unsupported universalization — PASS.** `POLICY_F03_B_LIMITS` disclaims universal pulse thresholds, confirmed degradation, and global M0 replacement.
8. **Target-blind lineage — PASS.** `MAP_F03_B` and hash-linked compiler provenance bind the candidate to allowed M0/E1 sources and the contract.
9. **Contract consistency — PASS.** The single licensed match selects reconciliation; stop, complement, and fallback behavior follow the contract.

## Overall disposition

**Auditor A v2: PASS.** All six candidates pass all 15 machine predicates and all nine semantic dimensions in this audit. This sheet alone does not establish full instrument readiness, which requires both independent audits and the contract’s other readiness conditions.
