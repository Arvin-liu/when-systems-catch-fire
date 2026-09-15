# IGNITION-172 Step07 — Knowledge Experience routing index

This logical step is based on exact frozen parent `c2ddfe4f40d943e214984db8dd5e1379f41ab4db` on the existing Task172 branch and Draft PR #218.

- The compact index is a generated, canonical-ID keyed facet projection of the already completed function and nonfunction routing overlays.
- Coverage: 6157 function records + 17981 nonfunction records = 24138 routing records.
- Facets: UNESCO field/discipline when justified, asset role, collision use, topic and classification state. Empty or unresolved facets are retained rather than guessed.
- Operation binding: `knowledge.collide_object` remains `CURRENT_BOUNDED + READ_ONLY_RUN`; the router has no repository, registry or network write permission.
- Candidate policy: bounded facet retrieval → transparent widening/fallback → exact Current authority fingerprint validation. Fallback is never silent.

## Precision-oriented routing pilot

|case|candidate universe|selected|fallback|exact validation|
|---|---:|---:|---|---|
|`gold-structural-analogy`|194|50|NO|ALL_SELECTED_EXACT|
|`xujiu-literary-context`|223|50|NO|ALL_SELECTED_EXACT|
|`rest-evidence-boundary`|800|50|NO|ALL_SELECTED_EXACT|

Hard checks: invalid IDs `0`, all selected exact `True`, explicit fallback reasons `True`.

This is routing evidence, not a claim adjudication or scholarly corpus result. Literary/interpretive, empirical, structural-analogy and source-derived material remain separate at the collision protocol layer.

Decision: `STEP07_ROUTING_INDEX_READY; READ_ONLY; EXACT_VALIDATION_REQUIRED; NO_CANONICAL_MUTATION`.
