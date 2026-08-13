# Pointfire seven-track external cross-domain replay — initial governed pass

Status: ROLE-B_INITIAL_PENDING_ADVERSARIAL_REVIEW

This report records the first governed pass of the preregistered external replay. It is a source-scoped research result and not a declaration of universal external validity, causal identification, or epistemic acceptance.

## Frozen question and scope

Question: 在城市尺度，增加树冠覆盖是否能稳定降低夏季近地面热暴露？在什么条件下这一关系不能被解释为因果？

The scope is urban or urbanized settings during summer or a comparable warm season. Land-surface temperature, near-surface air temperature, and human heat exposure are kept as separate measurement targets. A source family is an original study, cohort, experiment, or independent official dataset; multiple papers or pages describing the same underlying study do not count as independent families.

The preregistered minimum was five source families overall, including at least two air or human-heat families, one land-surface-temperature family, and one null, negative, or boundary family. The causal ceiling was source-scoped conditional support only. No result can be promoted to a universal city-scale claim by this replay.

## Blinded baseline handoff

The baseline was frozen before the governed pass and was written without Pointfire architecture vocabulary. It concluded that canopy is often associated with daytime local cooling, but that the result varies with water availability, climate, urban form, wind, humidity, canopy structure, time of day, and the selected exposure measure. It separately identified the main non-causal explanations: confounding, reverse selection, temporal ambiguity, measurement substitution, spatial mismatch, common-support failure, spillovers, and unvalidated model assumptions.

Baseline artifact: STEP01/BLINDED-BASELINE.md

## Governed pass

The governed pass added an explicit source ledger, source-family identity, measurement-boundary separation, contradiction and boundary recording, causal-ceiling discipline, and typed abstention. It did not treat an association, a lower land-surface temperature, or an internal review result as external truth.

### Evidence ledger summary

Nine source families were recorded:

- three local or regional near-surface air-temperature families (South Tacoma sensors, Portland mobile observations, and Madison mobile observations);
- one European multi-city land-surface-temperature family;
- one local street-level canopy day/night boundary family;
- one mechanistic multi-city model family;
- one national heat-disparity observational family;
- one official urban-climate synthesis family;
- one official causal-inference guidance family.

Retrieval was mixed: four peer-reviewed HTML or repository records were directly readable, four publisher or official records yielded an abstract or authoritative landing-page record with access limits noted, and the official WMO PDF was retrieved but its text extraction was limited in this run. A blocked publisher page was never treated as if full text had been inspected.

### Main findings

1. Local summertime daytime near-surface air-temperature associations with more canopy were supported within the scope of the Tacoma, Portland, and Madison source families. These are local observational results, not a pooled universal effect.
2. The European multi-city satellite family supported lower land-surface temperature in tree-covered areas relative to urban fabric, with climate and water dependence and important remote-sensing limitations.
3. A local temperature-threshold exposure proxy was partially supported in South Tacoma, but the study measured air temperature rather than full human heat stress and remained local.
4. Stable day-and-night cooling was disputed. The boundary family reported daytime cooling with slight nighttime warming or reduced ventilation under dense canopies; the mechanistic family likewise allowed warming in some hours when transpiration was absent or radiation and roughness effects dominated.
5. The relationship was not stable independently of climate, water, species, morphology, ventilation, and timing. These are effect modifiers and plausible pathways, not optional caveats.
6. Heat and tree-cover disparities were supported as a co-location or association in the national observational family. The result did not identify a city-scale causal tree-planting effect.
7. Land-surface temperature, near-surface air temperature, and human heat exposure could not be pooled as one endpoint. The replay therefore rejected endpoint substitution.
8. The available evidence did not identify a universal city-scale causal effect. Observational studies retained confounding, selection, timing, exposure-definition, and spatial-mismatch limits; no randomized or credible city-scale quasi-experimental planting effect was established by this pass.

### Initial claim dispositions

| Claim | Disposition | Boundary |
|---|---|---|
| Local summer daytime canopy is associated with lower near-surface air temperature | SUPPORTED_WITHIN_SOURCE_SCOPE | Tacoma, Portland, and Madison source families; local observational scope |
| Urban trees are associated with lower land-surface temperature than urban fabric | SUPPORTED_WITHIN_SOURCE_SCOPE | European multi-city remote-sensing family; LST only |
| Canopy can lower a local temperature-threshold exposure proxy | PARTIALLY_SUPPORTED | South Tacoma; not a complete human-heat or health endpoint |
| More canopy produces stable cooling in both day and night | DISPUTED | Dense canopy can retain heat or reduce mixing at night |
| The canopy relationship is independent of climate, water, form, and ventilation | CONTRADICTED | Multiple families make these conditions material |
| Tree-cover and heat disparities can co-locate | SUPPORTED_WITHIN_SOURCE_SCOPE | National observational family; association only |
| LST, air temperature, and human heat exposure are interchangeable | CONTRADICTED | Different physical and exposure quantities |
| A universal city-scale causal effect is identified | NOT_IDENTIFIABLE | Confounding, selection, timing, endpoint, and spatial limits remain |
| The replay contains distinct source families | SUPPORTED_WITHIN_SOURCE_SCOPE | Nine family records; duplicate underlying studies were not counted twice |

## Causal boundary

The strongest defensible conclusion from this initial pass is conditional and source-scoped: increasing or preserving canopy is often compatible with lower daytime local heat exposure, especially where shade and evapotranspiration operate, but the direction and size of the relationship depend on endpoint, time, urban form, ventilation, and water. This is not evidence that adding canopy will stably lower summer near-ground heat exposure in every city, nor that the observed associations are causal.

The replay does not establish EPISTEMICALLY_ACCEPTED. The initial governed pass remains pending independent adversarial review, and the source-family census and claims remain revisable if the reviewer identifies duplicate-family, retrieval, measurement, or causal-boundary errors.

## Provenance

- Formal replay base: when-systems-catch-fire/main at e5c6d1d0b75dae41b414474bc22747816cd00c78 at start of this candidate branch.
- Preregistration receipt: 1111 STEP01/REPLAY-PREREGISTRATION.md and JSON, frozen before this pass.
- Blinded baseline: 1111 STEP01/BLINDED-BASELINE.md and JSON, independently prepared before the governed pass.
- Machine-readable ledgers are in the adjacent data directory.
- This branch is a candidate evidence branch only; it is not formal main and is not a release or acceptance tag.
