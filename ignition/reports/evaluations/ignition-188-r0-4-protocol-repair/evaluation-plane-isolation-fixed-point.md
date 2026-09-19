# R0.4 Evaluation-Plane / Foundation Isolation Closure

R0.4 reuses the existing Task181/186/187 typed evaluation boundary. It does
not create a parallel admission or promotion framework.

- Every R0.4 packet, case, provenance file, control document, validator,
  regression test, and report is path-accounted as `EVALUATION_EVIDENCE`.
- The existing `EVALUATION_EVIDENCE_ONLY` admission rule keeps automatic
  discovery disabled and retains provenance without admitting a Knowledge or
  Foundation claim.
- The existing evaluation-plane contract keeps function discovery excluded,
  nonfunction discovery excluded with an audit row, automatic promotion off,
  and canonicalization off.
- The official nonfunction generator records one
  `EXCLUDED_EVALUATION_EVIDENCE_ONLY` row per R0.4 path with zero candidate
  fragments and zero canonical claim IDs.
- R0.4 report sources are not in the Knowledge result rows or generated
  canonical source lists. No Fire Seed or Current path is registered.

The Knowledge machine projections were refreshed only because the official
nonfunction generator changed the source hash of its existing generated index.
That refresh is a derived hash propagation; it adds zero R0.4 sources to the
Knowledge result rows or canonical source lists. Human `KNOWLEDGE/` surfaces,
the Knowledge admission configuration, Fire Seeds, Current facts, and Current
projections remain unchanged.

## Fixed point

The path-classification generator was run twice over the same live path set;
the second output was byte-identical. The official nonfunction generator was
also run twice; its second `--check` pass reported no output drift. The local
isolation suite checks both generated ledgers and the downstream mutation
boundary.

```text
R0_4_ARTIFACTS_PATH_ACCOUNTED=28
R0_4_ARTIFACTS_TYPED=EVALUATION_EVIDENCE
R0_4_ARTIFACTS_PROVENANCE_VISIBLE=PASS
PATH_CLASSIFICATION_CHECKS=10/10
PATH_CLASSIFICATION_PATHS=4724
PATH_CLASSIFICATION_SHA256=931ea3c331b64117fcec93580ebfeb88649025962efac0ca5b9e73d9a2824d42
R0_4_NONFUNCTION_EXCLUSION_ROWS=28
R0_4_NONFUNCTION_CANDIDATES=0
NONFUNCTION_CLAIM_GENERATION_DETERMINISTIC=PASS
KNOWLEDGE_RESULT_SOURCES_R0_4=0
R0_4_CANONICAL_SOURCE_ADMISSIONS=0
KNOWLEDGE_PROJECTION_REFRESH=DERIVED_NONFUNCTION_INDEX_HASH_ONLY
R0_4_ISOLATION_TESTS=7/7
SECOND_GENERATION_BYTE_FIXED_POINT=PASS
FOUNDATION_CANDIDATE_KNOWLEDGE_CURRENT_FIRE_SEEDS_MUTATIONS=NONE
NO_AUTOMATIC_PROMOTION
```

The generated records are audit projections only. They do not establish
external truth, evidence maturity, canonical claims, Knowledge objects, Fire
Seeds, Current state, Owner acceptance, or epistemic acceptance.
