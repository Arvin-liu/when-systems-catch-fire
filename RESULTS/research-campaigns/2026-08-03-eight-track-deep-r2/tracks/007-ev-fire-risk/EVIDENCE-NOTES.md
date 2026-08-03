# 007 EV fire risk — evidence checkpoint

R2 source reading was completed on 2026-08-03. The R1 identity remains `UNVERIFIED_RAPID_EVIDENCE_SCANS`; sources below were read as evidence, not inherited as conclusions.

## Denmark: official fire numerator, stock and age audit

The Danish Emergency Management Agency (Beredskabsstyrelsen, DEMA/BRS) 2023 English report was read in full at pp. 18–19 of the 26-page PDF. It states that registered electric and hybrid vehicles increased from 16,114 at end-2018 to 332,089 at end-2023, while conventional cars decreased to 2,852,167 in 2023. It reports 46 fires involving electric/hybrid vehicles in 2023 versus 20 in 2022, and says the figure’s rate for electric/hybrid vehicles rose from 1.1 to 1.7 per 10,000. The report says the conventional fire-damaged vehicles averaged about 10 years old while electric/hybrid fire-damaged vehicles averaged about 2 years old. It also warns that the report changed after a new standardized assessment and retrospective ODIN adjustments.

The 2025 BRS fact sheet for 2024 reports 50 electric/hybrid fires, approximately 485,000 electric/hybrid vehicles at end-2024, and published frequencies of 1.2 per 10,000 for electric/hybrid and 3.8 for other vehicle types. The 2026 BRS fact sheet for 2025 reports 62 fires, nearly 693,000 electric/hybrid vehicles at end-2025, and published frequencies of 1.0 versus 4.0. The numerator rises while the published rate falls as the fleet expands.

The simple end-of-year denominator recomputation is:

| Denmark year | official fire numerator | public end-year stock | raw `fires/stock×10,000` | BRS published rate | denominator implied by published rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023 | 46 | 332,089 | 1.385 | 1.7 | 270,588 |
| 2024 | 50 | ≈485,000 | 1.031 | 1.2 | 416,667 |
| 2025 | 62 | ≈693,000 | 0.895 | 1.0 | 620,000 |

The discrepancy is not a rounding error in 2024/2025 alone. The implied denominator is lower than the end-year stock, consistent with an annual-average or internally timed exposure denominator, but the public fact sheets do not disclose enough of the BIL54 calculation in the text to identify it exactly. Therefore the official published rates are retained as official rates, while the end-stock calculations are retained as an audit showing that a reader must not silently substitute end-year stock.

## Sweden: official event PM with directly recoverable denominator

The Swedish Civil Defence and Resilience Agency (MCF, formerly MSB) 14-page PM `MSB1647`, dated 2025-04-30, was read in full. It defines the population as cars that are electric or electric/hybrid and excludes intentionally set fires. The source says the data come principally from municipal rescue-service incident reports, supplemented in some cases by accident investigations and media information. Selection used free-text searches because the reports have no predefined drivetrain field. It includes confirmed damage, suspected damage and incidents/near misses where the rescue service was alerted, including charging incidents.

For 2024 the PM reports 40 electric/hybrid passenger-car incidents, 880,958 electric/electric-hybrid cars in traffic, and 4,096,833 cars with other fuels. The resulting arithmetic is 40/880,958×10,000 = 0.45405 per 10,000, matching the separately published 0.45. The PM also reports just over 3,100 passenger cars of all fuels burning in 2024, but that total includes intentional combustion-vehicle fires and is not the same numerator definition; it cannot be used as a clean comparator without qualification. If one mechanically subtracts 40 from 3,100, the other-fuel rate is approximately 7.47 per 10,000, close to the cross-country fact-sheet value 7.50, but this is an audit approximation, not a matched official comparator.

The Swedish PM’s own limits are decisive: 664 electric/electric-hybrid vehicle or other electric-transport fires/near misses were identified across 2018–2024, but the agency explicitly says the result is not systematic statistics for all fires. Free-text search may miss incidents when the reporter did not recognize or mention the electric/hybrid status. The 2024 passenger-car total is 10 in motion, 11 during charging and 19 other/unknown. This prevents a claim that the observed fleet rate is specifically a battery thermal-runaway rate.

## Cross-jurisdiction definitions

The Danish 2025 fact sheet reports 2024 counts of 50 Denmark, 40 Sweden and 84 Norway, but explicitly warns that registration practices differ; in Sweden and Norway, an EV fire spreading to a building may not be registered as an EV fire. The 2026 fact sheet changes the comparison year for Norway to 2025 and uses 75 Norwegian fires, while Sweden remains 2024 because newer data were unavailable. The three-country statement is thus a useful lead, not three independent harmonized datasets.

## Data quality and undercounting

NIST Technical Note 2365 (35 pages) was downloaded and read in full. Its abstract estimates 5,718 EV/PHEV fires since 2011 (95% CI 2,866–10,846), but it is not a matched EV-versus-ICE risk study. For NFIRS it explains that fire departments may report to the department but not NFIRS, reports may be incomplete/inaccurate, and NFIRS has no original dedicated LIB field. Roughly half of vehicle-fire records have a VIN. Its vehicle estimate combines NFIRS and TeslaFires.com using capture–recapture and assumes EV/PHEV fires are reported and identified at the same rate as Teslas. In 2023 it estimates 418 BEV fires (USA) and 800 plugin vehicle fires including hybrids, with wide intervals; excluding Florida gives 596 and 1,311. The note says the Florida overlap rate is likely unrepresentative and that exclusion may be more reliable. It also says the estimate may be substantially underreported. None of this supplies a common ICE denominator.

## Probability versus consequence

The DEMA-hosted RISE full-scale comparison summary was read. It compares two electric vehicles and one conventional vehicle, including one same-model/same-manufacturer powertrain comparison. Peak and total heat release were affected by scenario and vehicle model, not significantly by powertrain in this small experiment. Hydrogen fluoride and certain metals were larger differences in electric-vehicle smoke, while several acute toxic gases occur for either powertrain. This supports a separate consequence/suppression concern; it does not estimate ignition probability.

## Evidence boundary

The evidence establishes lower observed per-vehicle frequencies in the named Nordic official summaries, and the Sweden 2024 arithmetic is directly reproducible. It does not establish a global, lifetime, per-mile or age-adjusted BEV advantage. Denmark’s rate denominator timing is not transparent in the public text; Sweden’s numerator is a free-text incident search including suspected damage and near misses. The correct R2 analysis must preserve these limits.
