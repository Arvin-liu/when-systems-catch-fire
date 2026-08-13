# STEP14 — Current-main validation, debt census, and limited repair

Baseline fetched from live formal `main`:
`e5c6d1d0b75dae41b414474bc22747816cd00c78`

Candidate repair branch: `repair/current-main-validation-r1-20260813`

## Direct validator results

| Check | Result | Evidence |
|---|---|---|
| Epistemic-governance relationships | `PASS` | strict schema, authority profiles, typed effects, obligations and closed public routes |
| Foundation integrated validator | `FAIL_WITH_RUN_EVIDENCE` | `60/63`; claim-governance census generator is stale |
| Function-asset closure | `FAIL_WITH_RUN_EVIDENCE` | `45/46`; `DEEP_ADJUDICATION_OUT_OF_DATE` generated products |
| Nonfunction-claim closure | `FAIL_WITH_RUN_EVIDENCE` | `52/54`; repository-path accounting `3588` listed vs `3610` tracked and generated-output drift |
| Knowledge-experience validator | `FAIL_WITH_RUN_EVIDENCE` | stale source projection `NFC-2f6931fff5a6554c`; deterministic drift in `asset-cards.jsonl`, `search-index.jsonl`, and `manifest.json` |
| Human front door after bounded repair | `PASS` | human visibility `21` surfaces / `14` pairs / `16` two-click destinations; system map `51` nodes; `external_truth_verified=false` |
| System-map audit | `PASS` | `NO_IMPACT_JUSTIFIED`; governed map sources unchanged; `51` nodes / `57` edges in the system-map projection |

The failing generated-output and path checks are recorded as current-main
engineering debt. No scientific conclusion was changed to make them pass.

## Limited repair applied

`README.md` received one bounded front-door repair:

- restored the explicit headings required by the repository-native human
  visibility validator;
- stated the physics correction with the required conservative wording;
- added direct links to Function/Nonfunction closure summaries and the MCF,
  PSD, ARN, and iteration-method entry points.

The repair does not regenerate Foundation, nonfunction, or knowledge-experience
outputs; it does not change a claim, status, source, proof, or scientific
result. The standalone front-door validator passes after this repair.

## Targeted test run

Command:

`PYTHONPATH=. uv run --no-project --with pytest --with jsonschema pytest -q tests/test_human_front_door.py tests/test_knowledge_experience.py tests/foundation/test_foundation.py tests/foundation/test_claim_governance.py tests/foundation/test_function_asset_closure.py tests/foundation/test_nonfunction_claim_closure.py`

Observed: `25 passed, 11 failed, 4 subtests passed`.

Classification of the failures:

- one physics-visibility wording assertion was corrected by the bounded README
  repair;
- one test expects `50` system-map nodes while the live validator and map
  produce `51`; this is a stale test expectation, not a reason to alter the
  map output;
- knowledge-experience failures reproduce the stale source projection and
  deterministic output drift above;
- Foundation closure/generator failures reproduce the direct validator debt;
- core-claim test failures also report missing optional `z3`/`sympy` modules in
  this temporary test environment and are not upgraded into repository truth.

Post-repair command `python3 tools/validate_human_front_door.py` returns
`status=PASS`. The focused `test_human_front_door.py` run is `7 passed, 1
failed, 4 subtests passed`; the only remaining failure is the stale `50` versus
live `51` system-map node assertion.

## Residual classification

- `CURRENT_MAIN_DEFECT_REPAIRED`: README human front-door contract.
- `CURRENT_MAIN_DEFECT_REMAINS`: generated Foundation/nonfunction/knowledge
  projections and nonfunction path accounting.
- `HISTORICAL_OR_STALE_TEST`: expected system-map node count `50` vs live `51`.
- `ENVIRONMENT_LIMITATION`: missing optional proof-test modules in the
  temporary pytest environment.

This branch is a candidate repair only. It is not formal-main publication,
Ready, a release tag, or `EPISTEMICALLY_ACCEPTED`.
