# NOAA CO2–CH4 annual-growth year pairing

`research.pair_noaa_co2_ch4_growth_by_year` joins two already captured source-surface comparator outputs by equal integer year. It reads one bounded JSON envelope from stdin and writes a JSON table to stdout. It makes no network requests and reads no caller-selected paths.

The input must contain a complete `research.compare_noaa_co2_source_surfaces` output and a complete `research.compare_noaa_ch4_source_surfaces` output. Both must use the same inclusive year range, from 1984 through 2100, at no more than 50 years. The source outputs must keep their fixed NOAA GML URLs, retrieval timestamps, HTTP metadata and response digests. The tool rejects unavailable outputs, mismatched ranges, invented source URLs, incomplete year rows, duplicate years and source/comparison value drift.

Each output row keeps the CO2 comparator fields in ppm and the CH4 comparator fields in ppb in separate objects. The tool does not convert units or perform arithmetic across gases. The output preserves each comparator's status, four source receipts, input digest and the time span across the captures. The example inputs were captured about one hour apart, so the pairer does not describe them as simultaneous.

Example invocation:

```sh
python3 -B ignition/tools/toolbox_pair_noaa_co2_ch4_growth_by_year.py --stdin \
  < ignition/data/operations/toolbox-noaa-co2-ch4-growth-pair-real-task-input-r0.json
```

An experimental route must explicitly allowlist the exact candidate ID. Route planning does not run this command or grant execution authority. If either gas output is unavailable, retain the independent outputs and report that pairing was not performed. This artifact does not authenticate NOAA, validate measurements, estimate emissions, establish causal relationships or provide scientific acceptance.
