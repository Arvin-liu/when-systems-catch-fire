# Independent AI secondary audit: methane growth versus emissions

**Review status:** independent in-thread AI secondary audit completed; human scientific review not performed. This memo records audit findings as relayed to the Codex coordinator and is not a signed reviewer report, peer review, or scientific acceptance. Overall research status remains `PARTIAL`.

**Question:** Does slower atmospheric methane growth alone establish that methane emissions declined?

## Review scope

The independent reviewer checked the cited NOAA growth table, WMO Bulletin No. 22, the GONGGA paper excerpt, Figshare metadata, the NetCDF file hashes and `history` attributes, and the annual integration arithmetic. The coordinator reran the corrected reproducible script and updated the report and evidence package from those findings. The audit was limited to one GONGGA posterior and the recorded source excerpts; it did not perform another inversion, contact data authors, or obtain human scientific review.

## Material correction: 2024 coverage

The previous calculation multiplied all 12 monthly means by full Gregorian month lengths. The 2024 NetCDF `history` lists 364 daily inputs from 2024-01-01 through 2024-12-29. December 30 and 31 are absent. Thus the previous 597.567 Tg CH4 figure assumed those two days equaled the available December monthly mean. It is a full-month imputation sensitivity, not an observed 2024 total.

The corrected script weights each monthly mean by the count of daily diagnostic files recorded for that month. It also checks that coverage begins on January 1, contains no internal gaps, and does not exceed that month's calendar length. The 2019 and 2023 inputs each contain 365 daily source files; 2024 contains 364.

| Year | Coverage | Available-coverage five-sector sum (Tg CH4) |
|---:|---:|---:|
| 2019 | 365 / 365 days | 578.087804929 |
| 2023 | 365 / 365 days | 580.397362152 |
| 2024 | 364 / 366 days, through Dec 29 | 594.613321542 |

The 2024 full-month imputation sensitivity remains 597.567347888 Tg CH4, with two days imputed. For a matched calendar-date monthly-mean proxy, Jan 1–Dec 29 is 577.560039384 Tg over 363 days in 2023 and 594.613321542 Tg over 364 days in 2024. The corresponding rates are 1.591074489 and 1.633553081 Tg/day, a +2.669805% difference. This proxy is not daily-resolved; the 2023 December value uses the complete 31-day monthly mean to represent 29 days.

## Source and arithmetic findings

The input is Figshare v2, DOI [10.6084/m9.figshare.31939146.v2](https://doi.org/10.6084/m9.figshare.31939146.v2), licensed CC BY 4.0. The three used NetCDF binaries are now included in `input/data/`; recorded byte counts, MD5 values, and SHA-256 values match the captured Figshare metadata for the selected files. The metadata version and DOI are pinned. The two other dataset years were not used.

For each sector, monthly flux (`kg/m2/s`) was multiplied by grid-cell area (`m2`) and represented-day seconds, then converted to Tg. The monthly spatial sum and a separate vectorized time-space reduction agree to below `3e-14 Tg` on the reported values. The available-period 2024 sector totals (Tg CH4) are: other natural 59.092961264; wetlands 147.538841625; biomass burning 24.142853632; agriculture and waste 251.806546792; fossil fuel 112.032118230.

NOAA reports 8.29 ± 0.82 ppb (2023), 8.04 ± 0.43 ppb (2024), and 4.77 ± 0.43 ppb (2025). Its source describes the annual-growth uncertainty as the quadrature of network-bootstrap and analytical Monte Carlo standard deviations; the values should not be restated as 95% confidence intervals. WMO reports 1,948 ± 2 ppb for the 2025 global mean and lower 2025 growth than the preceding year. Neither concentration record alone attributes methane source changes. The GONGGA inversion reports an increased agriculture-and-waste point estimate and little change in fossil-fuel point estimate in the matched-date proxy, but the current calculation does not propagate inversion uncertainty and is not a replicated or multi-model finding.

## Semantic assessment and limits

The narrow proposition is supported: slower atmospheric concentration growth alone does not prove that emissions declined, because growth reflects source and sink balance. The evidence does not establish an uncertainty-bounded anthropogenic emissions trend, a global 2025 emissions estimate, or multi-model consensus. It covers one inversion through 2024 and the last two 2024 days are absent from the source-file list.

The source-bound adapter comparison is separate evidence. On the same offline captured source set, both candidate E37 and legacy produced 4/4 exact text anchors with no network requests; E37 retained four source captures and legacy retained none. This shows a capture-retention difference only. Semantic validation was `NOT_PERFORMED`, claims remain `NOT_REVIEWED`, and both run receipts are `CLAIM_REVIEW_INCOMPLETE` / `PARTIAL`. Overall benefit is `NO_DELTA` / `NOT_ESTABLISHED`; the legacy route remains operational baseline and E37 remains experimental/default-off. This comparison does not prove live retrieval quality, semantic correctness, time savings, or cost savings.

**Final review disposition:** `PARTIAL`; machine pipeline semantic validation `NOT_PERFORMED`; human scientific review `NOT_PERFORMED`; scientific acceptance `NOT_ESTABLISHED`.

## Linked evidence

- [Evidence summary](./evidence-summary.json)
- [Input integrity and attribution](./gongga-input-file-integrity.json)
- [Corrected calculation output](./gongga-recalculation.json)
- [External research report](../../../../../reports/external-research/2026-10-31-methane-growth-emissions-source-bound-review-r0.md)
- [Matched adapter comparison](./matched-adapter-comparison.json)
- [Initial anchor-miss receipts](./negative-evidence/initial-anchor-miss/)
