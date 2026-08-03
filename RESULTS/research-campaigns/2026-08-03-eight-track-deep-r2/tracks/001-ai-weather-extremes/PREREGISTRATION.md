# 001 preregistration

## Research identity

`BENCHMARK_AND_METHOD_AUDIT`

## Frozen question

For AI weather forecasts compared with numerical weather prediction (NWP), what evidence supports or contradicts the claim that a pure data-driven model can replace a physics-based model for warnings of record-breaking heat, cold, wind, or other high-impact extremes?

The unit of judgment is not “AI versus physics” in the abstract. The audit separates model family, variable, forecast lead, spatial/temporal aggregation, training and test distribution, truth construction, extreme-event definition, metric, and operational decision threshold.

## Candidate claims

1. Pure data-driven models can have lower average-field RMSE and much lower computational cost than a reference NWP model.
2. Average-field skill does not by itself establish skill on record-level extremes; a model may regress toward the training distribution and underpredict unseen peaks.
3. Physical NWP may retain an advantage for the specific out-of-distribution record benchmark used by the承重 study, but the result may be sensitive to event definition, truth, lead time, and model version.
4. Physically guided or hybrid models are a genuine competing class, not evidence that all pure AI models are safe for extremes. Their evidence must be graded separately from press-release claims and case studies.
5. No reviewed benchmark can by itself establish operational replacement, which requires independent observations, probabilistic calibration, threshold-based recall/precision, reliability, regional and seasonal transfer, and failure-cost evaluation.

## Conclusion ceiling

The strongest permitted conclusion is a bounded benchmark/method judgment. The audit may support, contest, or block the R1 claim for specified models, variables, years, and metrics. It may not claim that all AI weather models fail or that all physics-based models win. It may not convert speed or average RMSE into safety or replacement qualification.

## Falsifiers and stopping conditions

The R1 direction would be weakened if an independent full-text benchmark using the same or broader extreme definition found pure AI matching or exceeding NWP on record intensity, event recall, and calibration; if the primary result disappeared after harmonizing truth or model versions; or if the apparent reversal came from an invalid split or duplicate-event construction. The replacement claim would remain blocked if only average metrics, two case studies, or institution-authored summaries were available.

## Required evidence and data work

- Full承重 paper and supplement, including training/test split, preprocessing, model checkpoints/versions, variables, resolution, lead times, and event selection.
- At least one independent benchmark or peer-reviewed critique, plus original or official documentation for the NWP comparator.
- A primary paper or fully auditable technical report for physically guided/hybrid models; official news is a lead only.
- Independent observation or reanalysis truth description and any code/data used to reconstruct one reported table, event count, or error contrast.
- A model-family crosswalk: pure data-driven, physics-based NWP, and physical-guided/hybrid.

If exact numerical reproduction is blocked by unavailable data or checkpoints, the block must identify the missing artifact, the failed retrieval or access evidence, and the strongest result that can still be audited. No text summary will be called a reanalysis.

