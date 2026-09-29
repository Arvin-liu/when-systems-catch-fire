# Task228 v2 — Auditor B Raw Audit Sheet

**Scope:** Isolated v2 package only. No target material or other audit sheets inspected.

**Checks run:** All six packaged validator invocations returned schema and contract `PASS`. `build_reference_instruments.py --check` returned `TASK228_REFERENCE_REBUILD=BYTE_IDENTICAL`.

## Machine predicates

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
| `PROVENANCE_COVERAGE` | PASS | PASS | PASS | PASS | PASS | PASS |

## Semantic dimensions

For each candidate: **1** evidence support; **2** operational completeness; **3** bounded applicability; **4** M0 preservation; **5** fallback and stops; **6** provenance meaning; **7** no unsupported universalization; **8** target-blind lineage; **9** contract consistency.

### `POLICY_F01_A`

1. **PASS** — `F01_E1_TRIGGER`, `F01_E1_CONTROLS`, and `F01_E1_LIMITS` support the coded silver-film/toward-sun review pattern; `F01_M0_SELECTION` preserves the distinction between thermal triage and independent VWC review.
2. **PASS** — Validity, surface, and bearing inputs select a review route; required fields specify the readings and evidence to record.
3. **PASS** — The claim is limited to the coded observed pattern and introduces no correction or cutoff.
4. **PASS** — The four M0 actions remain unconditional; `F01_M0_ACTIONS`.
5. **PASS** — Missing, excluded, or unmatched inputs use universal fallback; invalid measurement stops for reacquisition.
6. **PASS** — Provenance points to the family’s M0/E1 evidence; nested parameter and report references are covered by the parent action.
7. **PASS** — `F01_E1_LIMITS` and the claim disclaim universal reflective-surface rules and global M0 changes.
8. **PASS** — `MAP_F01_A`, compiler, and manifest bind only family M0/E1 sources; manifest records no target, transfer, or revision access.
9. **PASS** — Selector, action, and licensed-region conditions match; complement, fallback, and stop behavior follow the contract.

### `POLICY_F01_B`

1. **PASS** — `F01_E1_PARTIAL` describes OBS-06’s partial coverage and variable readings; `F01_E1_LIMITS` bounds its interpretation.
2. **PASS** — The incomplete-coverage and observed-variable inputs route to reacquisition; the action and reporting fields specify what context to collect.
3. **PASS** — The claim is confined to the observed pattern and adds no numeric cutoff.
4. **PASS** — The four M0 actions remain unconditional; `F01_M0_ACTIONS`.
5. **PASS** — Universal fallback handles missing, excluded, and unmatched cases; invalid measurement stops for reacquisition.
6. **PASS** — The typed provenance links and nested references resolve to family M0/E1 evidence.
7. **PASS** — `F01_E1_LIMITS` and the claim reject universal thresholds or actions.
8. **PASS** — `MAP_F01_B`, compiler, and manifest use the family M0/E1 allowlist only.
9. **PASS** — One selector conjunction is mirrored by its action and licensed region; complement, fallback, and stop semantics match the contract.

### `POLICY_F02_A`

1. **PASS** — `F02_E1_ORGANIC` records OBS-04–06 and their gravimetric results; `F02_E1_QC` supports the measurement checks.
2. **PASS** — The researcher-coded category routes to independent gravimetric review with specified composition, turbidity, estimate, and mass reporting.
3. **PASS** — The claim is limited to the named organic-floc observation category and creates no formula or composition cutoff.
4. **PASS** — The four M0 actions remain unconditional; `F02_M0_ACTIONS`.
5. **PASS** — Universal fallback and invalid-measurement reacquisition stop are explicit.
6. **PASS** — `F02_E1_QC` is included in the action evidence and provenance, covering the nested report field.
7. **PASS** — `F02_E1_LIMITS` and the claim reject a universal composition boundary or global M0 replacement.
8. **PASS** — `MAP_F02_A`, compiler, and manifest bind only family M0/E1 inputs.
9. **PASS** — Selector/action/region match; exclusions, fallback, and stop behavior conform.

### `POLICY_F02_B`

1. **PASS** — `F02_E1_UNREPRODUCIBLE` records OBS-08’s aliquot-dependent composition and gravimetric spread; `F02_E1_LIMITS` supports no point mapping.
2. **PASS** — The two boolean conditions route the observed pattern to reconciliation; the report field requires separate aliquot and replicate records.
3. **PASS** — The claim is limited to OBS-08’s pattern and supplies no point estimate.
4. **PASS** — The four M0 actions remain unconditional; `F02_M0_ACTIONS`.
5. **PASS** — Universal fallback and invalid-measurement reacquisition stop are explicit.
6. **PASS** — `F02_E1_QC` is included in the action evidence and provenance, covering the nested report field.
7. **PASS** — `F02_E1_LIMITS` and the claim reject universal composition boundaries and new calibrations.
8. **PASS** — `MAP_F02_B`, compiler, and manifest use only family M0/E1 inputs.
9. **PASS** — Selector/action/region match; complement, fallback, and stop behavior conform.

### `POLICY_F03_A`

1. **PASS** — `F03_E1_PULSED_P` records the group-P pulse cases; `F03_E1_CONTRAST` and `F03_E1_LIMITS` bound the interpretation.
2. **PASS** — The declared group and coded pulse-pattern inputs route to stability review, with trace, interval, and assay reporting specified.
3. **PASS** — The claim is limited to the named group-P pattern and asserts no pulse threshold or degradation finding.
4. **PASS** — The four M0 actions remain unconditional; `F03_M0_ACTIONS`.
5. **PASS** — Universal fallback and invalid-measurement reacquisition stop are explicit.
6. **PASS** — Typed provenance and nested references resolve to family M0/E1 evidence.
7. **PASS** — `F03_E1_LIMITS` and the claim reject universal thresholds and confirmed degradation claims.
8. **PASS** — `MAP_F03_A`, compiler, and manifest use only family M0/E1 inputs.
9. **PASS** — Selector/action/region conditions match; fallback and stop semantics conform.

### `POLICY_F03_B`

1. **PASS** — `F03_E1_TRACE_GAP` records OBS-06’s trace gap and assay disagreement; `F03_E1_LIMITS` says the pulse is unknown.
2. **PASS** — The declared trace and assay inputs route to reconciliation; the report field specifies trace, assay, clock, and custody records.
3. **PASS** — The claim is limited to OBS-06 and does not infer a pulse or degradation.
4. **PASS** — The four M0 actions remain unconditional; `F03_M0_ACTIONS`.
5. **PASS** — Universal fallback and invalid-measurement reacquisition stop are explicit.
6. **PASS** — Typed provenance and nested references resolve to family M0/E1 evidence.
7. **PASS** — `F03_E1_LIMITS` and the claim reject universal pulse thresholds and confirmed-failure claims.
8. **PASS** — `MAP_F03_B`, compiler, and manifest use only family M0/E1 inputs.
9. **PASS** — Selector/action/region conditions match; complement, fallback, and stop behavior conform.

## Overall disposition

**Auditor B v2 result:** all six candidates pass all 15 machine predicates and all nine semantic dimensions. The packaged validator and byte-identical compiler check pass.

**Formal overall instrument readiness: NOT_ESTABLISHED by this sheet alone.** The rubric requires both independent audits for an overall readiness decision.
