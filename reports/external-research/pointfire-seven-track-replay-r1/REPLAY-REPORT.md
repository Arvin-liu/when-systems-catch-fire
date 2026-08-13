# Pointfire seven-track external cross-domain replay — initial governed pass

Status: ROLE-C_REPAIRS_APPLIED_PENDING_FRESH_REREVIEW

This report records the first governed pass of the preregistered external replay. It is a source-scoped research result and not a declaration of universal external validity, causal identification, or epistemic acceptance.

## Frozen question and scope

Question: 在城市尺度，增加树冠覆盖是否能稳定降低夏季近地面热暴露？在什么条件下这一关系不能被解释为因果？

The scope is urban or urbanized settings during summer or a comparable warm season. Land-surface temperature, near-surface air temperature, and human heat exposure are kept as separate measurement targets. A source family is an original study, cohort, experiment, or independent official dataset; multiple papers or pages describing the same underlying study do not count as independent families.

The preregistered minimum was five source families overall, including at least two air or human-heat families, one land-surface-temperature family, and one null, negative, or boundary family. The causal ceiling was source-scoped conditional support only. No result can be promoted to a universal city-scale claim by this replay.

## Blinded baseline handoff

The baseline was frozen before the governed pass and was written without Pointfire architecture vocabulary. It concluded that canopy is often associated with daytime local cooling, but that the result varies with water availability, climate, urban form, wind, humidity, canopy structure, time of day, and the selected exposure measure. It separately identified the main non-causal explanations: confounding, reverse selection, temporal ambiguity, measurement substitution, spatial mismatch, common-support failure, spillovers, and unvalidated model assumptions.

Baseline artifact: STEP01/BLINDED-BASELINE.md

## Governed pass

The governed pass added an explicit source ledger, source-family role labels, claim-level measurement boundaries, contradiction and boundary recording, causal-ceiling discipline, and preregistration-aligned SOURCE_NOT_RECOVERED and ABSTAIN handling. The baseline already contained endpoint separation, alternative explanations, and a causal ceiling; those dimensions are therefore recorded as reinforced rather than unique architecture gains. The pass did not treat an association, a lower land-surface temperature, or an internal review result as external truth.

### Evidence ledger summary

Seven substantive source families and two contextual or methodological records were recorded:

- three local or regional near-surface air-temperature families (South Tacoma sensors, Portland mobile observations, and Madison mobile observations);
- one European multi-city land-surface-temperature family;
- one local street-level canopy day/night boundary family;
- one mechanistic multi-city model family;
- one national heat-disparity observational family;
- one official urban-climate contextual record;
- one official causal-inference methodological record.

Retrieval was mixed: five peer-reviewed or official HTML/repository records were directly readable, three publisher or authoritative landing-page records yielded an abstract or landing-page record with access limits noted, and the official WMO PDF was retrieved but its text extraction was limited in this run. A blocked publisher page was never treated as if full text had been inspected.

### Main findings

1. Local summertime near-surface air-temperature associations with measured canopy-cover exposures were supported within the scope of the Tacoma, Portland, and Madison source families. Canopy cover, canopy volume, tree presence, shade, and generic vegetation were not pooled. These are local observational results, not a pooled universal effect.
2. The European multi-city satellite family supported lower land-surface temperature in tree-covered areas relative to urban fabric, with climate and water dependence and important remote-sensing limitations.
3. A local temperature-threshold exposure proxy was partially supported in South Tacoma, but the study measured air temperature rather than full human heat stress and remained local.
4. Stable day-and-night cooling across settings was not established. The Tacoma study reported local canopy cooling without a significant day/night interaction in its setting, while the Madison, Sydney, Portland, and mechanistic records reported different nighttime, ventilation, roughness, or non-transpiration boundaries. The direction is heterogeneous rather than uniformly warming or uniformly cooling.
5. The relationship was not stable independently of climate, water, species, morphology, ventilation, and timing. These are effect modifiers and plausible pathways, not optional caveats.
6. Heat and tree-cover disparities were supported as a co-location or association in the national observational family. The result did not identify a city-scale causal tree-planting effect.
7. Land-surface temperature and near-surface air temperature could not be pooled as one endpoint, and direct human heat-stress exposure was not established by the recovered governed-pass evidence. The replay therefore rejected endpoint substitution.
8. The available evidence did not identify a universal city-scale causal effect. Observational studies retained confounding, selection, timing, exposure-definition, positivity, interference, anthropogenic-heat, and spatial-mismatch limits; no randomized or credible city-scale quasi-experimental planting effect was established by this pass.

### Initial claim dispositions

| Claim | Disposition | Boundary |
|---|---|---|
| Local summer near-surface air temperature is associated with measured canopy-cover exposure | SUPPORTED_WITHIN_SOURCE_SCOPE | Tacoma, Portland, and Madison source families; canopy cover only; local observational scope |
| Canopy volume, tree presence, shade, and generic vegetation can be substituted for canopy cover | ABSTAIN | Exposure definitions and estimands are not interchangeable under the preregistration |
| Urban trees are associated with lower land-surface temperature than urban fabric | SUPPORTED_WITHIN_SOURCE_SCOPE | European multi-city remote-sensing family; LST only |
| Canopy can lower a local temperature-threshold exposure proxy | PARTIALLY_SUPPORTED | South Tacoma; not a complete human-heat or health endpoint |
| More canopy produces stable cooling in both day and night across settings | DISPUTED | Tacoma did not show a significant day/night interaction in its local setting; other records show heterogeneous nighttime and mechanism-specific effects |
| The canopy relationship is independent of climate, water, form, and ventilation | CONTRADICTED | Multiple families make these conditions material |
| Tree-cover and heat disparities can co-locate | SUPPORTED_WITHIN_SOURCE_SCOPE | National observational family; association only |
| LST, air temperature, and human heat exposure are interchangeable | CONTRADICTED | Different physical and exposure quantities; direct human heat-stress endpoint not established here |
| A universal city-scale causal effect is identified | NOT_IDENTIFIABLE | Confounding, selection, timing, endpoint, and spatial limits remain |
| The replay contains seven substantive source families plus two contextual records | SUPPORTED_WITHIN_SOURCE_SCOPE | Contextual records are not counted toward substantive source-family support |
| Direct human heat-stress exposure is established by the governed pass | SOURCE_NOT_RECOVERED | Air temperature and a temperature-threshold proxy were recovered; a complete human heat-stress metric was not |

## Causal boundary

The strongest defensible conclusion from this repaired pass is conditional and measurement-specific: in the Tacoma, Portland, and Madison settings, measured canopy-cover exposures were associated with lower local summertime near-surface air temperature under the reported observational designs, while the size and direction depend on endpoint, time, urban form, ventilation, water, and the exact exposure definition. A local temperature-threshold proxy was observed in Tacoma, but direct human heat-stress exposure was not established. This is not evidence that adding or preserving canopy will stably lower summer near-ground heat exposure in every city, nor that the observed associations are causal.

The replay does not establish EPISTEMICALLY_ACCEPTED. ROLE-C identified repairs to source metadata, exposure pooling, outcome typing, source-family roles, and causal audit fields. Those repairs are applied in this candidate commit and require a fresh independent ROLE-C recheck.

## Provenance

- Formal replay base: when-systems-catch-fire/main at e5c6d1d0b75dae41b414474bc22747816cd00c78 at start of this candidate branch.
- Preregistration receipt: 1111 STEP01/REPLAY-PREREGISTRATION.md and JSON, frozen before this pass.
- Blinded baseline: 1111 STEP01/BLINDED-BASELINE.md and JSON, independently prepared before the governed pass.
- Machine-readable ledgers are in the adjacent data directory.
- This branch is a candidate evidence branch only; it is not formal main and is not a release or acceptance tag.
