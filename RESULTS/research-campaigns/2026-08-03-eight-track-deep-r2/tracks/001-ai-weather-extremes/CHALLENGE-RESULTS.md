# 001 AI weather extremes — challenge checkpoint

## Adversarial review

### Does the primary paper measure “unprecedented weather” or “unprecedented in ERA5”?

Only the latter is established. A strict maximum over 1979–2017 ERA5 is a reproducible benchmark rule, but it is not a station-observed atmospheric bound. Reanalysis smoothing, grid resolution, and the use of one gridded truth define which events count. This challenge narrows the claim from physical novelty to model behavior outside a selected gridded training support.

### Does the common truth make the comparison fair?

It makes the score reproducible but does not remove all comparability questions. Zhang uses ERA5 as the main truth and also reports an HRES-fc0 operational-style alternative. HRES source resolution, initialization, model generation, interpolation and the AI models’ training data are not identical. The paper’s method pages do not permit a causal attribution to “physics” alone. The primary ordering can survive as an empirical benchmark result without being a clean architecture effect.

### Is the result robust to event dependence?

No universal independence claim is available. One large heatwave or cold outbreak creates many spatially adjacent grid-cell records. The paper acknowledges spatial duplication and reports bootstrap sensitivity, but a cell-level event count is not the same as an independent-event count. The conclusion is therefore “record-gridpoint scores in the published domain,” not “number of independent disasters.”

### Does the independent literature overturn the primary result?

It overturns only the universal extension. Olivetti & Messori use percentile tails and find data-driven models competitive or better in many settings; Pasche’s events are mixed; the coarse WeatherBench2 audit finds Pangu better on this record score at 24/48 hours. None is a direct reanalysis of the same Zhang model releases, grid, period, and code. The appropriate synthesis is competing estimands and context dependence, not a pooled vote.

### Does FastNet solve the extrapolation problem?

Not yet. Its physical/spectral loss is a plausible mechanism and its technical paper reports selected cases and holdout tests, but it is proof-of-principle, deterministic, and not an operational prospective warning evaluation. The institutional release is not counted as independent confirmation.

### Can the result support replacement of NWP?

No. A replacement claim needs the same operational inputs, station/observation truth, prospective cases, uncertainty calibration, lead-time decisions, missed-event costs, and independent evaluation. The sources instead identify the reanalysis/real-world and in-distribution/out-of-distribution gap.

## Surviving claim

After challenge, the primary result remains supported only as a specified record-exceedance benchmark finding. The universal R1 extension, a causal “physics beats AI” explanation, and any operational replacement claim do not survive.
