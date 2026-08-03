# 001 AI weather extremes — analysis checkpoint

## Estimand separation

The apparently conflicting evidence is not one clean head-to-head estimate. Zhang et al. ask a deliberately high-threshold question: for each grid cell and calendar month, did the 2018/2020 ERA5 value exceed the maximum seen in the 1979–2017 training history? Their primary event score is therefore an out-of-distribution record-exceedance score, with event counts, tail bias, and recall in addition to RMSE. The data-generating question is close to “can a model extrapolate beyond the historical support it was trained on?”

Olivetti & Messori ask a different question: for a common 1.5° field and shared ERA5 truth, how do models behave in the top 1% or 5% of the realized variable distribution? A top-quantile tail can contain very severe events while still remaining inside the training distribution. A model can therefore be strong on quantile extremes but weak on unprecedented records without logical inconsistency. Their regional and lead dependence also prevents the result from being summarized as “AI wins extremes.”

Pasche et al. use three named events with event-specific variables and compound structure. Their humid-heat case exposes a variable-set problem: a model that does not predict the relevant humidity field cannot be ranked on the same physical phenomenon as a model that does. The winter-storm result exposes another problem: aggregate pointwise RMSE and event-relevant structure are different estimands.

## Model and truth crosswalk

The primary comparison is not only an architecture contest. HRES, GraphCast, Pangu, FuXi, operational variants, initialization, target resolution, model version, and truth construction differ. Zhang partially addresses this by evaluating a common HRES-fc0 operational-style truth and a forecast-conditioned extreme benchmark, but the design still does not identify which component causes the reversal. The strict record threshold is based on ERA5, so “unprecedented” means unprecedented in that gridded reanalysis history, not unprecedented in station observations or the physical atmosphere.

The primary and Olivetti studies also use different common grids (0.25°/0.1° source fields versus 1.5° comparison), different extreme definitions, and different regional aggregation. The comparison is therefore a cross-benchmark consistency test, not a pooled effect estimate. ECMWF’s review and RealBench’s design challenge independently identify the unresolved reanalysis-to-operation and in-distribution-to-out-of-distribution boundaries.

## Public-data calculation

The WeatherBench2 access audit loaded the official public ERA5, HRES, and Pangu Zarr metadata and values. The threshold reproduction returned 349 land/latitude-masked record exceedances on the 64×32 grid in 2020. Applying the same threshold to the available forecast data produced:

| lead | HRES record RMSE | Pangu record RMSE | HRES bias | Pangu bias |
| --- | ---: | ---: | ---: | ---: |
| 24 h | 1.438 K | 0.676 K | −1.003 K | −0.358 K |
| 48 h | 1.564 K | 1.060 K | −1.093 K | −0.666 K |
| 120 h | 2.626 K | 2.635 K | −1.711 K | −1.823 K |

The counts are 349 at 24 h and 348 at 48/120 h because valid forecast times are restricted to 2020. The public slice thus does not reproduce the primary paper’s model/version/resolution or event table; it demonstrates that the threshold is executable and that a public benchmark can produce a different ranking. The result is not evidence that Pangu universally beats HRES, because the field, lead alignment, model release, aggregation and event definition remain specific to this audit.

## Bounded inference

The strongest defensible inference is:

> Pure AI models in Zhang et al.’s named model/version set underperformed HRES on their strict reanalysis-record benchmark, while independent quantile and case-study benchmarks show that extreme-event skill is estimand-, region-, lead-, variable-, truth- and model-version-dependent.

This supports a scoped primary result and rejects the universal R1-style ranking. It does not establish that AI cannot extrapolate, because the public coarse Pangu result and FastNet’s physical-guided work show that model design and benchmark construction matter. It also does not establish operational readiness: no source supplies a harmonized station-verified, decision-threshold, independent prospective comparison.

## Pre-challenge verdict

`CONTEXT_DEPENDENT_COMPETING_BENCHMARKS`. The primary benchmark survives as a bounded record-extrapolation result; its proposed general explanation and any replacement claim remain open to challenge.
