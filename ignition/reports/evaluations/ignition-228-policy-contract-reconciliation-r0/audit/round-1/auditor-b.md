# Task228 auditor-b audit sheet

Audited only the supplied isolated package. The six validator invocations each returned `TASK228_POLICY_SCHEMA=PASS` and `TASK228_POLICY_VALID=PASS`; the packaged rebuild check returned `TASK228_REFERENCE_REBUILD=BYTE_IDENTICAL`.

**Machine predicate results:** the table below follows the contract’s predicate definitions. I mark `PROVENANCE_COVERAGE` **FAIL** for F02_A and F02_B: each report field cites `F02_E1_QC`, but its parent action’s direct evidence references and provenance link omit that ID. The packaged validator reports those policies valid but does not check this nested-evidence coverage requirement. The other 14 predicates pass for all six candidates.

| Predicate ID | F01_A | F01_B | F02_A | F02_B | F03_A | F03_B |
|---|---|---|---|---|---|---|
| `SCHEMA_VALIDITY` | PASS | PASS | PASS | PASS | PASS | PASS |
| `FAMILY_SOURCE_BINDING` | PASS | PASS | PASS | PASS | PASS | PASS |
| `UNIQUE_IDENTIFIERS` | PASS | PASS | PASS | PASS | PASS | PASS |
| `EVIDENCE_REFERENCES` | PASS | PASS | PASS | PASS | PASS | PASS |
| `TYPED_CONDITIONS` | PASS | PASS | PASS | PASS | PASS | PASS |
| `SELECTOR_ACTION_BIJECTION` | PASS | PASS | PASS | PASS | PASS | PASS |
| `LICENSED_REGION_BIJECTION` | PASS | PASS | PASS | PASS | PASS | PASS |
| `OUT_OF_SCOPE_COMPLEMENT` | PASS | PASS | PASS | PASS | PASS | PASS |
| `PRESERVATION_SEMANTICS` | PASS | PASS | PASS | PASS | PASS | PASS |
| `PRESERVED_EVIDENCE_M0_ONLY` | PASS | PASS | PASS | PASS | PASS | PASS |
| `TYPED_PARAMETER_BINDING` | PASS | PASS | PASS | PASS | PASS | PASS |
| `FALLBACK_UNIVERSALITY` | PASS | PASS | PASS | PASS | PASS | PASS |
| `STOP_CONDITION_STRUCTURE` | PASS | PASS | PASS | PASS | PASS | PASS |
| `SCOPE_REGION_LICENSING` | PASS | PASS | PASS | PASS | PASS | PASS |
| `PROVENANCE_COVERAGE` | PASS | PASS | **FAIL** | **FAIL** | PASS | PASS |

## Semantic dimensions

Dimensions: **1** evidence support; **2** operational completeness; **3** bounded applicability; **4** M0 preservation; **5** fallback and stops; **6** provenance meaning; **7** no unsupported universalization; **8** target-blind lineage; **9** exact runtime-contract consistency.

### `POLICY_F01_A`

1. **PASS** — `F01_E1_TRIGGER` records OBS-01/02; `F01_E1_CONTROLS` and `F01_E1_LIMITS` bound interpretation to the observed surface/radiance/view pattern.
2. **PASS** — Declared validity, surface, and bearing inputs route to contact/VWC review; reporting fields name the readings and evidence to record.
3. **PASS** — The licensed category is the coded silver-film/toward-sun pattern; no cutoff or correction is claimed (`F01_E1_LIMITS`).
4. **PASS** — The four M0 actions remain unconditional and cite `F01_M0_ACTIONS`.
5. **PASS** — Missing, excluded, and unmatched cases use universal `RECONCILE` fallback; invalid measurement has a `REACQUIRE` stop (`F01_M0_SELECTION`).
6. **PASS** — Typed elements cite family M0/E1 evidence; source locators bind to the frozen bytes.
7. **PASS** — The claim and limits reject a universal reflective-surface rule or global M0 change (`F01_E1_LIMITS`).
8. **PASS** — `MAP_F01_A`, the build manifest, and compiler use the family’s M0/E1 allowlist; no target inputs are declared.
9. **PASS** — One conjunction is mirrored by its action and licensed region; the complement, stop, and fallback follow the contract.

### `POLICY_F01_B`

1. **PASS** — `F01_E1_PARTIAL` describes OBS-06’s incomplete coverage and variable readings; `F01_E1_LIMITS` says it does not isolate a stable context.
2. **PASS** — The declared incomplete-coverage/variable-pattern inputs route to context reacquisition, with relevant fields specified for reporting.
3. **PASS** — The claim is limited to the observed pattern and does not introduce a numeric threshold (`F01_E1_LIMITS`).
4. **PASS** — All four M0 actions remain unconditional and cite `F01_M0_ACTIONS`.
5. **PASS** — Universal fallback covers missing, excluded, zero-match, and multiple-match cases; invalid measurement stops for reacquisition.
6. **PASS** — Typed policy elements and their locators resolve to the family’s M0/E1 bytes.
7. **PASS** — The claim disclaims universal surface rules and corrected thresholds (`F01_E1_LIMITS`).
8. **PASS** — `MAP_F01_B`, manifest, and compiler provenance are M0/E1-only.
9. **PASS** — Rule/action/region conditions match; the single complement routes to fallback and the stop is checked before routing.

### `POLICY_F02_A`

1. **PASS** — `F02_E1_ORGANIC` records OBS-04–06 and their gravimetric results; `F02_E1_QC` records measurement checks.
2. **PASS** — The coded composition input routes to independent gravimetric review, with report fields for composition, duplicates, and mass.
3. **PASS** — It covers only the researcher-coded observed organic-floc category and claims no composition cutoff or new formula (`F02_E1_LIMITS`).
4. **PASS** — All four M0 actions remain unconditional and cite `F02_M0_ACTIONS`.
5. **PASS** — Universal fallback and the invalid-measurement reacquisition stop are explicit.
6. **FAIL** — The report field `F02A_COMPOSITION_AND_MASS` cites `F02_E1_QC`, while action `F02A_GRAVIMETRIC_REVIEW` and its provenance link omit it. This conflicts with the contract’s nested-report coverage requirement.
7. **PASS** — No universal composition boundary, new calibration, or global M0 replacement is claimed (`F02_E1_LIMITS`).
8. **PASS** — `MAP_F02_A`, manifest, and compiler provenance use only the family’s M0/E1 inputs.
9. **PASS** — Selector, action, and region agree; out-of-scope, missing-value fallback, and stop behavior match the contract.

### `POLICY_F02_B`

1. **PASS** — `F02_E1_UNREPRODUCIBLE` records OBS-08’s aliquot-dependent composition and gravimetric spread; `F02_E1_LIMITS` supports no point mapping.
2. **PASS** — The joint boolean pattern routes to reconciliation, and the report field requires separate recording of aliquot, turbidity, and gravimetric results.
3. **PASS** — The claim is limited to OBS-08’s pattern and supplies no point estimate (`F02_E1_LIMITS`).
4. **PASS** — All four M0 actions remain unconditional and cite `F02_M0_ACTIONS`.
5. **PASS** — Universal fallback and the invalid-measurement reacquisition stop are explicit.
6. **FAIL** — Report field `F02B_ALIQUOT_RECONCILIATION` cites `F02_E1_QC`, but action `F02B_RECONCILE_ALIQUOTS` and its provenance link omit it.
7. **PASS** — No universal composition boundary, new calibration, or global M0 replacement is claimed (`F02_E1_LIMITS`).
8. **PASS** — `MAP_F02_B`, manifest, and compiler provenance use only the family’s M0/E1 inputs.
9. **PASS** — The single selector/action/region conjunction and the fallback/stop paths match the contract.

### `POLICY_F03_A`

1. **PASS** — `F03_E1_PULSED_P` records group-P pulse cases; `F03_E1_CONTRAST` and `F03_E1_LIMITS` bound them against group-S and continuous-profile cases.
2. **PASS** — Declared group/pulse-pattern inputs route to stability review; reporting fields specify trace, interval record, and assay.
3. **PASS** — The claim is limited to the researcher-coded group-P pattern; it asserts no pulse threshold or degradation finding (`F03_E1_LIMITS`).
4. **PASS** — All four M0 actions remain unconditional and cite `F03_M0_ACTIONS`.
5. **PASS** — Universal fallback and invalid-measurement reacquisition stop are explicit.
6. **PASS** — Typed elements cite the family’s M0/E1 evidence; locators bind to the frozen bytes.
7. **PASS** — No universal pulse threshold, confirmed degradation rule, or global M0 replacement is claimed (`F03_E1_LIMITS`).
8. **PASS** — `MAP_F03_A`, manifest, and compiler provenance are M0/E1-only.
9. **PASS** — Conditions are identical across selector, action, and region; fallback and stop semantics match the contract.

### `POLICY_F03_B`

1. **PASS** — `F03_E1_TRACE_GAP` records OBS-06’s missing trace and assay disagreement; `F03_E1_LIMITS` says the pulse is unknown.
2. **PASS** — The declared trace-completeness and replicate inputs route to record reconciliation, with reporting fields for trace, assay, and custody context.
3. **PASS** — The claim is limited to OBS-06’s pattern and does not infer a pulse or degradation (`F03_E1_LIMITS`).
4. **PASS** — All four M0 actions remain unconditional and cite `F03_M0_ACTIONS`.
5. **PASS** — Universal fallback and invalid-measurement reacquisition stop are explicit.
6. **PASS** — Typed elements cite family M0/E1 evidence; locators bind to the frozen bytes.
7. **PASS** — The claim rejects universal pulse thresholds and confirmed degradation from an isolated reading (`F03_E1_LIMITS`).
8. **PASS** — `MAP_F03_B`, manifest, and compiler provenance are M0/E1-only.
9. **PASS** — Selector/action/region conditions match, and complement, fallback, and stop behavior align with the contract.

**Audit disposition:** F01_A, F01_B, F03_A, and F03_B pass all listed machine predicates and semantic dimensions. F02_A and F02_B have the nested-evidence coverage failures described above and fail semantic provenance meaning.

References inspected: [reviewer rubric](/tmp/ignition-228-semantic-audits/auditor-b/repo/ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/reference/reviewer-rubric.md), [validator](/tmp/ignition-228-semantic-audits/auditor-b/repo/ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/tools/validate_policy.py), [build manifest](/tmp/ignition-228-semantic-audits/auditor-b/repo/ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/build/candidate-build-manifest.json).
