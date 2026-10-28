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
- The four R0.4 Markdown reports are visible in the generated human-results
  ledger as `HUMAN_INDEX_ONLY` and are explicitly listed in
  `excluded_generated_result_sources`; they are not in Knowledge result rows
  or generated canonical source lists.
- Fire Seed census hashes may follow the existing generated nonfunction index
  and chronology hashes, but normalized seed content and source links remain
  unchanged. No R0.4 source is a Fire Seed or Current path.

The Knowledge machine projections were refreshed only because the official
nonfunction generator changed the source hash of its existing generated index;
the Knowledge configuration was also updated with the explicit R0.4 exclusion
list. These are governed provenance/derived projections: they add zero R0.4
sources to Knowledge result rows or canonical source lists. Human
`KNOWLEDGE/` surfaces, Fire Seed content and links, Current facts, and Current
projections remain unchanged.

## Fixed point

The path-classification generator was run twice over the same live path set;
the second output was byte-identical. The official nonfunction generator was
also run twice; its second `--check` pass reported no output drift. The local
isolation suite checks both generated ledgers and the downstream mutation
boundary.

```text
R0_4_ARTIFACTS_PATH_ACCOUNTED=29
R0_4_ARTIFACTS_TYPED=EVALUATION_EVIDENCE
R0_4_ARTIFACTS_PROVENANCE_VISIBLE=PASS
PATH_CLASSIFICATION_CHECKS=10/10
PATH_CLASSIFICATION_PATHS=4725
PATH_CLASSIFICATION_SHA256=fbf422cd3b5bae213d3fc90eb210834a8cb75a7a3647a86a04a8538585384799
R0_4_NONFUNCTION_EXCLUSION_ROWS=29
R0_4_NONFUNCTION_CANDIDATES=0
NONFUNCTION_CLAIM_GENERATION_DETERMINISTIC=PASS
KNOWLEDGE_RESULT_SOURCES_R0_4=0
R0_4_CANONICAL_SOURCE_ADMISSIONS=0
KNOWLEDGE_PROJECTION_REFRESH=DERIVED_INDEX_AND_EXCLUSION_PROVENANCE
FIRE_SEED_CONTENT_LINKS_R0_4=0
R0_4_ISOLATION_TESTS=7/7
SECOND_GENERATION_BYTE_FIXED_POINT=PASS
FOUNDATION_CANDIDATE_KNOWLEDGE_CURRENT_FIRE_SEEDS_MUTATIONS=NONE
NO_AUTOMATIC_PROMOTION
```

The generated records are audit projections only. They do not establish
external truth, evidence maturity, canonical claims, Knowledge objects, Fire
Seeds, Current state, Owner acceptance, or epistemic acceptance.
