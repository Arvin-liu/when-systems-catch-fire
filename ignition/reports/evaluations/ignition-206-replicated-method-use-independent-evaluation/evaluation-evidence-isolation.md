# Evaluation evidence isolation / fixed point (Step07)

## Typing and path accounting

- 34 Task206 tracked paths, 34 classified `EVALUATION_EVIDENCE`, 0 in any other category (official repository-path-classification generator).
- 4926 tracked paths, 4926 manifest rows, 0 unresolved / duplicate / stale.
- Six frozen bundles copied byte-for-byte; no user absolute path is committed.

## No automatic Foundation candidate

- 0 automatic function-asset candidates, 0 automatic nonfunction-claim candidates.
- Task206 paths appear as `EXCLUDED_EVALUATION_EVIDENCE_ONLY` rows (321 total across the repository); canonical claims remain 18003.
- Task206 emits zero canonical claim IDs; canonical promotion `NONE`.

## Knowledge Experience isolation

Because Task206 Markdown falls under the `reports` human-results source root, human-results may carry it as a navigation projection, and Knowledge Experience isolates it by reusing the existing exact-path `excluded_generated_result_sources` list. Six exact paths were appended; no wide-prefix exclusion was added and only official generators were run:

- `reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/evidence-freeze.md`
- `reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/per-replicate-evaluation.md`
- `reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/replication-analysis.md`
- `reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/replicated-method-use-report.md`
- `reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/negative-control-audit.md`
- `reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/independent-evaluation-report.md`

## No promotion

- Knowledge canonical promotion: none
- Fire Seeds semantic promotion: none
- Current mutation: none
- zero canonical claim IDs

## Deterministic projection chain (full, not only path/nonfunction)

- `tools/foundation/validate_repository_path_classification.py` (generate + 2x --check): REPOSITORY_PATH_CLASSIFICATION_VALID
- `tools/foundation/adjudicate_nonfunction_claims.py` (generate + 2x --check): NONFUNCTION_CLAIM_GENERATION_DETERMINISTIC
- `tools/foundation/adjudicate_core.py --check` (check): ADJUDICATION_CHECK_OK
- `tools/foundation/migrate_legacy.py --check` (check): LEGACY_GENERATOR_RETIRED
- `tools/foundation/build_function_asset_census.py --check` (check): FUNCTION_ASSET_CENSUS_VALID
- `tools/foundation/adjudicate_function_assets.py --check` (check): FUNCTION_ASSET_DEEP_ADJUDICATION_VALID
- `tools/foundation/validate_foundation.py` (validate): ALL_FOUNDATION_VALID
- `tools/foundation/validate_claim_governance.py` (validate): CLAIM_GOVERNANCE_VALID
- `tools/foundation/validate_function_asset_closure.py` (validate): FUNCTION_ASSET_REGISTRY_CLOSURE_VALID
- `tools/foundation/validate_nonfunction_claim_closure.py` (validate): NONFUNCTION_CLAIM_EVIDENCE_LINEAGE_CLOSURE_VALID
- `tools/foundation/run_function_asset_math_checks.py --check` (check): 7/7 PASS
- `tools/foundation/verify_core_claims.py --check` (check): CORE 5/5 ALL_CORE_CLAIMS_REPLAYED
- `tools/governance/build_human_results.py` (generate + --check): HUMAN_RESULTS_OK records=676
- `tools/governance/build_knowledge_experience.py` (generate + --check): KNOWLEDGE_EXPERIENCE_OK cards=724
- `tools/governance/run_self_correction.py --check` (check): SELF_CORRECTION_OK deltas=717
- `tools/governance/validate_knowledge_experience.py` (validate): KNOWLEDGE_EXPERIENCE_AUDIT_OK
- `tools/governance/validate_human_visibility.py` (validate): HUMAN_VISIBILITY_OK
- `tools/governance/gen_source_first_seen.py` (generate): SOURCE_FIRST_SEEN_WRITTEN entries=676
- `tools/governance/check_knowledge_experience_determinism.py` (check): KNOWLEDGE_EXPERIENCE_DETERMINISM_OK two_pass=identical
- `tools/publication/build_fire_seed_census.py` (generate): FIRE_SEEDS_CENSUS_BUILT seeds=64
- `tools/publication/validate_fire_seeds.py --check` (check): FIRE_SEEDS_VALID
- `tools/governance/build_claim_browsers.py --check` (check): HUMAN_ASSETS_CHECK_OK
- `tools/generate_overall_architecture.py --check` (check): SYSTEM_MAP_DERIVED_OK
- `tools/governance/validate_human_surface_contract.py` (validate): HUMAN_SURFACE_CONTRACT_OK
- `tools/governance/refresh_human_surface_materiality.py --check` (check): HUMAN_SURFACE_MATERIALITY_DETERMINISTIC

## Fixed point

Second generator/check pass produces no further diff (Knowledge Experience determinism check reports `two_pass=identical`).

Status: `EVALUATOR_INDEPENDENT_EVALUATION_ONLY`.