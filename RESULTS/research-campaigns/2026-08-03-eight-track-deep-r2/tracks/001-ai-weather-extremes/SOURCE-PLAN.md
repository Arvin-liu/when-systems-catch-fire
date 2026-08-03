# 001 source plan

## Source roles

| Role | Minimum source | What must be extracted |
| --- | --- | --- |
|承重 primary benchmark|Zhang et al. full article and supplement|training/test years, ERA5 fields, model versions, HRES setup, lead times, grid, record definition, event count, RMSE/bias/recall, limitations|
|independent primary or critique|separate benchmark, replication, or peer-reviewed critique|whether the reversal survives another model/region/period/truth and which estimand is comparable|
|pure AI comparator documentation|original GraphCast/Pangu/FuXi or official technical paper|training corpus, forecast variables, resolution, inference design, known extremes limits|
|physics comparator|ECMWF/NWP technical documentation or paper|HRES version, initialization, resolution, truth and score comparability|
|physical-guided/hybrid|FastNet technical paper or auditable report; official release only as lead|loss/constraint, cases versus systematic benchmark, independence, operational status|
|truth/data|ERA5 documentation and any independent observation source|reanalysis status, grid, records, station versus gridded truth, availability and hash|

## Reading and reproduction plan

Read the承重 paper and supplement before interpreting any release. Build a model/metric crosswalk and a claim matrix. Download any public tables, code, or event data; hash them; reproduce at least one reported error contrast, event count, or figure/table statistic. If raw data/checkpoints are not available, execute and record the access test and downgrade to benchmark audit rather than pretending to reanalyze.

## Competition plan

The challenge stage will seek: an independent benchmark with a different truth or test period; a result showing a pure AI advantage on extremes; a failure mode in the primary event construction; and evidence that FastNet's physical consistency claim is only a case-study or institution-selected result. It will also test whether “record” means record over the training history, record in the test period, or a threshold chosen after looking at forecasts.

## Stop conditions

Stop only after the primary method is fully located, at least one independent competing source is read, all reported headline metrics have a denominator/definition, and the reproducibility outcome is either completed or blocked with verifiable evidence. A press release plus the original paper is not sufficient competition.

