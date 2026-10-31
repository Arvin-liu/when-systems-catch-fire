# Slower methane growth and emissions: bounded source review

**Status:** `PARTIAL`. This is a bounded source review and reproducible calculation for one published inversion. It is not human scientific review, peer review, or scientific acceptance. No result changes `EPISTEMICALLY_ACCEPTED=0`.

**Question:** Does slower atmospheric methane growth, by itself, establish that methane emissions declined?

## Observations and source scope

NOAA's current global annual growth table reports 8.29 ± 0.82 ppb for 2023, 8.04 ± 0.43 ppb for 2024, and 4.77 ± 0.43 ppb for 2025. NOAA describes the reported uncertainty as the quadrature of network-bootstrap and analytical Monte Carlo standard deviations; these values are not presented here as 95% confidence intervals. NOAA also says the latest year can change after recalibration and quality control. [NOAA annual CH4 growth data](https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_gr_gl.txt)

WMO reports a 2025 global mean surface concentration of 1,948 ± 2 ppb and says the 2024–2025 increase was lower than the 2023–2024 increase and the preceding decade's average. These observations describe concentration and growth; alone they do not attribute source or sink changes. [WMO Greenhouse Gas Bulletin No. 22](https://wmo.int/resources/publication-series/greenhouse-gas-bulletin/no-22)

Wang et al. estimate 2019–2024 methane budgets with GONGGA-CH4. The paper reports a stronger atmospheric sink relative to 2019 in 2023 and 2024, a 2024 wetland rebound, and disagreement between the inversion and process-based wetland models in important regions. The calculation below uses one posterior product from that inversion; it is not a second inversion or a multi-model estimate. [Nature Communications paper](https://doi.org/10.1038/s41467-026-72764-3)

## Dataset, coverage, and calculation

The input is the version-pinned Figshare dataset, DOI [10.6084/m9.figshare.31939146.v2](https://doi.org/10.6084/m9.figshare.31939146.v2), published under CC BY 4.0. The three NetCDF files used here are included under `ignition/data/operations/iterations/020/v1-methane-source-bound-real-task-r0/input/data/`; their byte counts, MD5 values, and SHA-256 values are recorded in the evidence package. The captured Figshare API metadata is also retained. NOAA, WMO, and Nature captures are selected web-reader excerpts rather than publisher HTTP response bodies.

Each NetCDF file has 12 monthly posterior means. I parsed daily `HEMCO_diagnostics.YYYYMMDD0000.nc` filenames from its `history` attribute and checked the sequence for internal gaps. The 2019 and 2023 files list 365 daily inputs each. The 2024 file lists 364 inputs, from January 1 through December 29; December 30 and 31 are absent. The primary calculation weights monthly flux × grid-cell area by the number of daily source files present for each month, then converts kg CH4 to Tg CH4. A separate vectorized space-time sum agrees with monthly spatial integration to less than 3e-14 Tg for the reported values.

| Year | Daily coverage | Five-sector sum (Tg CH4) | Reading |
|---:|---:|---:|---|
| 2019 | 365 / 365 days | 578.088 | Complete calendar-year integration |
| 2023 | 365 / 365 days | 580.397 | Complete calendar-year integration |
| 2024 | 364 / 366 days, through Dec 29 | 594.613 | Available-period estimate; two days are missing |

For 2024, sector sums over the 364 represented days are: other natural 59.093, wetlands 147.539, biomass burning 24.143, agriculture and waste 251.807, and fossil fuel 112.032 Tg CH4. The data do not provide daily posterior fields here; these sums apply monthly means over the represented source-file days.

If December 30–31 are imputed at the mean of the 29 available December days, the full-month sensitivity is 597.567 Tg CH4. The earlier +17.170 Tg / +2.96% difference from complete 2023 follows this imputation and is retained only as a sensitivity, not as an observed 2024 annual total.

As a second, matched-calendar-date proxy, January 1–December 29 sums are 577.560 Tg over 363 days for 2023 and 594.613 Tg over 364 days for leap-year 2024. Dividing by represented days gives 1.591074 and 1.633553 Tg CH4/day, respectively, a +2.6698% difference in monthly-mean proxy rate. This is not daily-resolved data; the 2023 December portion uses its 31-day monthly mean to proxy 29 days. Neither comparison propagates inversion uncertainty.

The reproducible script, full sector values, coverage counts, imputation sensitivity, matched-date proxy, and vector cross-check are in the [evidence package](../../data/operations/iterations/020/v1-methane-source-bound-real-task-r0/).

## Judgment and claim limits

The narrow conclusion is supported: slower atmospheric methane growth alone does not prove that emissions declined, because concentration growth reflects the balance of sources and sinks. The single GONGGA inversion's point estimates include a higher agriculture-and-waste sector and little change in fossil-fuel sector in the matched-date proxy; this does not establish an uncertainty-bounded anthropogenic emissions trend. December coverage is incomplete, this calculation does not propagate inversion uncertainty, and no second inversion or multi-model comparison was performed. The dataset ends in 2024 and does not establish 2025 emissions.

## Source-bound workflow and comparison status

The candidate E37 snapshot adapter and retained legacy adapter were run on the same four-source set, normalized text, draft, and claim rows. Both produced four exact text anchors with zero network requests. E37 retained four source captures; the legacy path retained none. The first attempt's shared leading-space anchor miss and both fail-closed receipts remain in `negative-evidence/initial-anchor-miss/`. The matched replay has `CLAIM_REVIEW_INCOMPLETE` / `PARTIAL` status; every claim row is `NOT_REVIEWED`, and pipeline semantic validation remains `NOT_PERFORMED`.

The observed difference is narrow: capture retention improved in this offline replay, while anchor outcomes were equal. Live retrieval quality, source authenticity, semantic accuracy, operator time, and cost were not measured. Overall benefit is `NO_DELTA` / `NOT_ESTABLISHED`; the legacy adapter remains the operational baseline and E37 remains experimental and default-off. These receipts are candidate-stage evidence, not evidence that the component has been released to Formal `main` or used after release.

An independent AI secondary audit identified and checked the 2024 coverage correction recorded here. Human scientific review remains outstanding. Hash agreement establishes byte consistency with the saved inputs; it does not authenticate their origin or validate their scientific interpretation.
