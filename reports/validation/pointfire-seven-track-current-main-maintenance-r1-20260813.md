# Pointfire seven-track current-main maintenance R1

Status: `CURRENT_MAIN_MAINTENANCE_CANDIDATE_WITH_EXPLICIT_RESIDUALS`

Base: fresh formal `main` at
`e5c6d1d0b75dae41b414474bc22747816cd00c78`

Candidate branch: `maintenance/repository-hygiene-and-current-debt-r1-20260813`

This is an engineering maintenance candidate. It does not rerun the seven
track research, change a scientific conclusion, publish formal `main`, create
a Ready or release tag, or set `EPISTEMICALLY_ACCEPTED`.

## Canonical repairs

The following canonical generators were run after each source-bound change:

- `tools/foundation/build_function_asset_census.py`
- `tools/foundation/adjudicate_function_assets.py`
- `tools/foundation/adjudicate_nonfunction_claims.py`
- `tools/governance/build_knowledge_experience.py`
- `tools/foundation/validate_repository_path_classification.py --generate`
- `tools/generate_interactive_system_map.py`
- `tools/foundation/migrate_legacy.py`

The discovery generators now exclude their own repository path-accounting
projection from claim/function discovery while keeping it accountable to the
dedicated path validator. This closes the generated self-ingestion drift
without changing any source claim or disposition.

The current front door was restored with explicit conservative result,
correction, open-question, Foundation, knowledge, system-map, and MCF/PSD/ARN
navigation. The stale human-front-door assertion was updated from the retired
50-node expectation to the canonical 51-node projection.

## Validation evidence

- Foundation integrated validator: `63/63`, `ALL_FOUNDATION_VALID`.
- Claim governance: `39/39`, `CLAIM_GOVERNANCE_VALID`.
- Function-asset closure: `46/46`, `FUNCTION_ASSET_REGISTRY_CLOSURE_VALID`.
- Nonfunction closure: `54/54`, `NONFUNCTION_CLAIM_EVIDENCE_LINEAGE_CLOSURE_VALID`.
- Knowledge-experience generator `--check`: pass.
- Knowledge-experience two-pass determinism: pass; outputs byte-identical.
- Repository path accounting: the baseline `3588` manifest versus `3610`
  tracked paths is closed by the canonical manifest generator; the candidate
  manifest now exactly matches the live tracked inventory, with 9/9 checks
  passing.
- System-map generator: `SYSTEM_MAP_DERIVED_OK nodes=51 edges=57`.
- Human front-door unittest: `8/8` pass.
- Legacy migration `--check`: `MIGRATION_CHECK_OK`.

All generated count changes are deterministic registry accounting. They are
not promotions of evidence, proof, external validity, or scientific truth.

## Residual classification

- `CURRENT_MAIN_DEFECT_REPAIRED`: stale canonical Foundation, function
  deep-adjudication, nonfunction, knowledge-experience, legacy migration, and
  path-accounting outputs.
- `CURRENT_MAIN_DEFECT_REPAIRED`: README front-door contract and stale 50 vs
  canonical 51 test expectation.
- `ENVIRONMENT_LIMITATION`: the earlier `pytest` executable was unavailable;
  the focused standard-library unittest and direct validators were used.
- The repository remains a candidate branch only. No formal-main merge, PR
  closure, release/current tag, or epistemic acceptance is implied.

`EPISTEMICALLY_ACCEPTED=0`
