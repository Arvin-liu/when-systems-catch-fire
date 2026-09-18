# R0.3 Evaluation-Plane Isolation and Fixed Point

## Reused typed boundary

Task187 reuses the existing Task181/182-R1 repository path-classification
engine and Knowledge admission policy. It creates no parallel candidate or
promotion framework.

- `ignition/evaluation/` and `ignition/reports/evaluations/` are typed as
  `EVALUATION_EVIDENCE` by the current path-classification rule.
- `EVALUATION_EVIDENCE` is in the classifier's non-authoritative category
  set. `AUTHORITATIVE_CLAIM_INPUT` remains restricted to the two existing
  CJK master-table prefixes.
- The Knowledge admission policy maps `evaluation/` and
  `reports/evaluations/` to `EVALUATION_EVIDENCE_ONLY`, with automatic
  discovery disabled and provenance-only retention enabled.
- The live generated classification manifest accounts each new R0.3 packet,
  control, test, and report path. No manual per-file exclusion list is added.

This type boundary prevents Task187 evaluation artifacts from automatic
Foundation function/nonfunction discovery and Knowledge admission. Task187
adds no promotion mapping or source registration for Current or Fire Seeds.
The PR changes no Foundation function or nonfunction candidate rows,
Knowledge canonical files, Fire Seeds, Current facts, or Current projections.
Its only generated Foundation-side update is the
repository-path-classification snapshot required to account for new paths.

## Fixed-point verification

The existing path-classification generator ran twice over the live Git path
set. Pass 1 and pass 2 each generated 4,693 rows with zero unresolved paths.
The second generation left the snapshot byte-identical at SHA256
`7027f511138f1191ea91f7b5064a82db7ccb1276f6c533e1576d3e6f30a9b637`. The
validator then passed all 10 checks: current contract, no unresolved or
duplicate rows, tracked-set parity, no stale paths, stable categories,
authoritative allowlist, schema-valid rows, and anti-backflow constraints.

The existing path-classification suite passed 5 tests. Task187's R0.3
isolation suite passed 4 tests, including typed classification of every new
R0.3 packet, control, test, and report path.

```text
PATHS=4693
UNRESOLVED=0
SECOND_GENERATION_BYTE_FIXED_POINT=PASS
PATH_CLASSIFICATION_CHECKS=10/10
R0.3_ISOLATION_TESTS=4/4
FOUNDATION_CANDIDATE_KNOWLEDGE_CURRENT_FIRE_SEEDS_MUTATIONS=NONE
```
