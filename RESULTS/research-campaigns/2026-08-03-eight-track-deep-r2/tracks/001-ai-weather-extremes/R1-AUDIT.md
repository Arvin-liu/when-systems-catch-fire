# 001 audit of R1

R1 source packet: `research/overnight-public-evidence-20260803-r1`, exact tip `232299483f701e8304265c1484b5b50e5dcf2799`.

R1 report: `RESULTS/research-campaigns/2026-08-03-overnight-r1/round-001-ai-weather-extremes/REPORT.md`; report SHA-256 `86f1630b1728833dfd5e375d3a6e52d28ae9dd0a4bc00ee08e687ab1103478e1`.

## Claims retained as leads

- The承重 paper was identified as Zhang et al., *Science Advances*, comparing GraphCast, Pangu-Weather, FuXi and ECMWF HRES using ERA5, with a 1979–2017 training period and 2018/2020 test years.
- R1 reported lower average RMSE for several AI models but an apparent reversal on record-breaking heat, cold, and wind.
- R1 attributed the reversal to distributional interpolation, peak smoothing, and possible physics-based extrapolation.
- R1 used a Met Office FastNet release as a competing physically guided design and an IT Pro article about NOAA cloud modernization as context.

## Items not accepted without R2 verification

R1's four-source count is not a depth certificate. The exact paper version, supplement, table values, event-count construction, record threshold, gridded truth, model checkpoints, and whether all models used comparable truth and resolution remain to be read directly. The FastNet press release is not an independent validation or a substitute for its technical paper. The NOAA article is contextual only.

## Required repair

R2 must recover exact page/figure/table/field locators, distinguish pure AI from physical-guided AI, audit the benchmark's test distribution and event duplication, and record whether a reproducible numerical subset can be reconstructed. R1's `PARTIALLY_SUPPORTED` label remains provisional until those repairs are complete.

