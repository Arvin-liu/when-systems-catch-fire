## Task228 semantic audit — Auditor A

Read-only audit of the isolated package only. The packaged validator returned `TASK228_POLICY_SCHEMA=PASS` and `TASK228_POLICY_VALID=PASS` for all six candidates. The packaged compiler’s read-only check returned `TASK228_REFERENCE_REBUILD=BYTE_IDENTICAL`.

For **each candidate below**, all 15 machine predicates are **PASS**: `SCHEMA_VALIDITY`, `FAMILY_SOURCE_BINDING`, `UNIQUE_IDENTIFIERS`, `EVIDENCE_REFERENCES`, `TYPED_CONDITIONS`, `SELECTOR_ACTION_BIJECTION`, `LICENSED_REGION_BIJECTION`, `OUT_OF_SCOPE_COMPLEMENT`, `PRESERVATION_SEMANTICS`, `PRESERVED_EVIDENCE_M0_ONLY`, `TYPED_PARAMETER_BINDING`, `FALLBACK_UNIVERSALITY`, `STOP_CONDITION_STRUCTURE`, `SCOPE_REGION_LICENSING`, and `PROVENANCE_COVERAGE`.

### POLICY_F01_A

1. **Evidence support — PASS.** `F01_E1_TRIGGER`, `F01_E1_CONTROLS`, and `F01_E1_LIMITS` support routing the observed silver-film/toward-sun pattern for contact and VWC review, without changing a threshold.
2. **Operational completeness — PASS.** `F01A_MEASUREMENT_VALID`, `F01A_SURFACE_PATTERN`, and `F01A_BEARING_RELATION` select a named category; the action and report fields specify review and records to capture.
3. **Bounded applicability — PASS.** The licensed pattern is explicitly reflective silver film plus toward-sun bearing; `F01_E1_LIMITS` rejects a universal cutoff.
4. **Preservation — PASS.** `F01_M0_ACTIONS` supports the four unconditional, non-retiring preserved actions.
5. **Fallback and edge safety — PASS.** The invalid-measurement stop is `REACQUIRE`; fallback covers missing, excluded, zero-match, and multiple-match cases.
6. **Provenance meaning — PASS.** Candidate references resolve to family M0/E1 evidence; the validator verifies frozen-source hashes and line slices.
7. **No unsupported universalization — PASS.** `F01_E1_LIMITS` and the scope ceiling disclaim universal reflective-surface rules and a global M0 change.
8. **Target-blind lineage — PASS.** `MAP_F01_A` is declared researcher-authored and target-blind; provenance binds the mapping declaration hash. The compiler reads only declared family M0/E1 sources and the declaration.
9. **Contract consistency — PASS.** The single licensed match routes to the linked review action; the empty out-of-scope complement and fallback follow contract routing semantics.

### POLICY_F01_B

1. **Evidence support — PASS.** `F01_E1_PARTIAL` and `F01_E1_LIMITS` support reacquiring the observed incomplete-coverage, variable-reading context without inventing a cutoff.
2. **Operational completeness — PASS.** The coverage boolean and researcher-coded reading pattern select the reacquisition action; required reporting names coverage, bearing, paired readings, mask status, and contact variation.
3. **Bounded applicability — PASS.** `MAP_F01_B` limits the route to the source-observed pattern; `F01_E1_LIMITS` rejects universal thresholds or actions.
4. **Preservation — PASS.** `F01_M0_ACTIONS` supports all four unconditional, non-retiring preserved actions.
5. **Fallback and edge safety — PASS.** The invalid-measurement stop is `REACQUIRE`; all unresolved or unmatched inputs use universal fallback.
6. **Provenance meaning — PASS.** `F01_E1_PARTIAL`, `F01_E1_LIMITS`, `F01_E1_QUALITY`, and M0 references support their assigned elements; frozen locators validate.
7. **No unsupported universalization — PASS.** The claim adds no numeric threshold or global M0 change; limits are explicitly stated.
8. **Target-blind lineage — PASS.** `MAP_F01_B`, declaration-hash provenance, and the allowlisted compiler path support lineage from family M0/E1 and the contract.
9. **Contract consistency — PASS.** One licensed rule, complement exclusion, safe stop, and universal fallback match contract routing.

### POLICY_F02_A

1. **Evidence support — PASS.** `F02_E1_ORGANIC`, `F02_E1_QC`, and `F02_E1_LIMITS` support independent gravimetric review for the named organic-floc observations.
2. **Operational completeness — PASS.** The validity and researcher-coded composition inputs select review; report fields identify the composition assay, turbidity duplicates, M0 estimate, and gravimetric result.
3. **Bounded applicability — PASS.** The claim is limited to the named organic-floc category; `F02_E1_LIMITS` rejects a universal cutoff or new formula.
4. **Preservation — PASS.** `F02_M0_ACTIONS` supports all four unconditional, non-retiring preserved actions.
5. **Fallback and edge safety — PASS.** Invalid measurements stop for reacquisition; unresolved, missing, excluded, and unmatched values use fallback.
6. **Provenance meaning — PASS.** `F02_E1_ORGANIC`, `F02_E1_QC`, `F02_E1_LIMITS`, and M0 references support the policy elements; frozen locators validate.
7. **No unsupported universalization — PASS.** The scope ceiling disclaims a universal composition boundary, single calibration, and global M0 replacement.
8. **Target-blind lineage — PASS.** `MAP_F02_A` and compiler provenance bind the candidate to the declaration and allowlisted M0/E1 inputs.
9. **Contract consistency — PASS.** The single matching rule selects its linked review action; complement and fallback semantics are consistent.

### POLICY_F02_B

1. **Evidence support — PASS.** `F02_E1_UNREPRODUCIBLE` and `F02_E1_LIMITS` support reconciling OBS-08’s aliquot-dependent composition and disagreeing gravimetric replicates, without a point estimate.
2. **Operational completeness — PASS.** The two observed boolean conditions select reconciliation; reporting requires separate aliquot composition, turbidity, and gravimetric records.
3. **Bounded applicability — PASS.** The licensed claim names the OBS-08 pattern and supplies no point estimate; `F02_E1_LIMITS` rejects extrapolation.
4. **Preservation — PASS.** `F02_M0_ACTIONS` supports all four unconditional, non-retiring preserved actions.
5. **Fallback and edge safety — PASS.** Invalid measurements stop for reacquisition; other unresolved, excluded, missing, or unmatched cases use fallback.
6. **Provenance meaning — PASS.** `F02_E1_UNREPRODUCIBLE`, `F02_E1_LIMITS`, `F02_E1_QC`, and M0 evidence support the corresponding elements; frozen locators validate.
7. **No unsupported universalization — PASS.** The policy disclaims a universal composition boundary, new calibration, and global M0 replacement.
8. **Target-blind lineage — PASS.** `MAP_F02_B`, mapping-hash provenance, and the compiler’s M0/E1 allowlist support target-blind artifact lineage.
9. **Contract consistency — PASS.** The one licensed match selects reconciliation; unmatched or ambiguous routing falls back under the contract.

### POLICY_F03_A

1. **Evidence support — PASS.** `F03_E1_PULSED_P`, `F03_E1_CONTRAST`, and `F03_E1_LIMITS` support review of the observed group-P pulse pattern while preserving the contrasting group-S pulse and group-P continuous case.
2. **Operational completeness — PASS.** The measurement-valid, recorded formulation group, and researcher-coded pulse pattern select review; reporting captures identity, trace, interval record, and assay.
3. **Bounded applicability — PASS.** The claim is limited to the named group-P pattern; no pulse threshold or degradation finding is asserted.
4. **Preservation — PASS.** `F03_M0_ACTIONS` supports all four unconditional, non-retiring M0 actions.
5. **Fallback and edge safety — PASS.** Invalid measurements stop for reacquisition; missing, excluded, zero-match, and multiple-match cases use fallback.
6. **Provenance meaning — PASS.** `F03_E1_PULSED_P`, `F03_E1_CONTRAST`, `F03_E1_LIMITS`, and M0 references support the corresponding elements; frozen locators validate.
7. **No unsupported universalization — PASS.** The scope ceiling disclaims universal pulse thresholds, confirmed degradation rules, and global M0 replacement.
8. **Target-blind lineage — PASS.** `MAP_F03_A` and declaration-hash/compiler provenance bind the candidate to the allowed M0/E1 and contract lineage.
9. **Contract consistency — PASS.** The single matching rule routes to review; stops, complement exclusion, and fallback follow the contract.

### POLICY_F03_B

1. **Evidence support — PASS.** `F03_E1_TRACE_GAP` and `F03_E1_LIMITS` support reconciling OBS-06’s incomplete high-rate trace and assay disagreement without inferring a pulse or degradation.
2. **Operational completeness — PASS.** The trace-completeness and assay-reconciliation inputs select reconciliation; report fields capture trace, assay, clock, and custody context.
3. **Bounded applicability — PASS.** The licensed claim is limited to OBS-06’s pattern; no pulse or degradation conclusion is made.
4. **Preservation — PASS.** `F03_M0_ACTIONS` supports all four unconditional, non-retiring M0 actions.
5. **Fallback and edge safety — PASS.** Invalid measurements stop for reacquisition; missing, excluded, zero-match, and multiple-match cases use fallback.
6. **Provenance meaning — PASS.** `F03_E1_TRACE_GAP`, `F03_E1_LIMITS`, and M0 references support the assigned elements; frozen locators validate.
7. **No unsupported universalization — PASS.** The scope ceiling disclaims universal pulse thresholds, confirmed degradation, and global M0 replacement.
8. **Target-blind lineage — PASS.** `MAP_F03_B`, declaration-hash provenance, and the allowlisted compiler support lineage from the permitted sources and contract.
9. **Contract consistency — PASS.** The single licensed match routes to reconciliation; the stop, out-of-scope complement, and fallback are contract-consistent.
