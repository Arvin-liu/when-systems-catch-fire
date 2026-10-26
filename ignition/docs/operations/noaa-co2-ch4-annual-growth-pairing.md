# NOAA CO2–CH4 annual-growth year pairing

`research.pair_noaa_co2_ch4_growth_by_year` v0.2.0 joins already captured NOAA GML source-surface comparator outputs by equal integer year. It always accepts CO2 and CH4; input schema r1 may also include N2O. It reads one bounded JSON envelope from stdin and writes a JSON table to stdout. It makes no network requests and reads no caller-selected paths.

The input must contain a complete `research.compare_noaa_co2_source_surfaces` output and a complete `research.compare_noaa_ch4_source_surfaces` output. A schema-r1 envelope may also contain a complete `research.compare_noaa_n2o_source_surfaces` output. Every supplied output must use the same inclusive year range of no more than 50 years; N2O is available only from 2001 onward. The source outputs must keep their fixed NOAA GML URLs, retrieval timestamps, HTTP metadata and response digests. The tool rejects unavailable outputs, mismatched ranges, invented source URLs, incomplete year rows, duplicate years and source/comparison value drift.

Each two-gas output row keeps the CO2 comparator fields in ppm and CH4 fields in ppb in separate objects. With N2O supplied, the row also includes a separate N2O object in ppb. The tool does not convert units or perform arithmetic across gases. The output preserves each comparator's status, four or six source receipts, input digest and time span across the captures. The captured three-gas example spans 19,508 seconds, so the pairer does not describe the inputs as simultaneous.

Example invocation:

```sh
python3 -B ignition/tools/toolbox_pair_noaa_co2_ch4_growth_by_year.py --stdin \
  < ignition/data/operations/toolbox-noaa-co2-ch4-growth-pair-real-task-input-r0.json
```

The optional three-gas example uses schema r1 and the fixed N2O page/raw comparator capture:

```sh
python3 -B ignition/tools/toolbox_pair_noaa_co2_ch4_growth_by_year.py --stdin \
  < ignition/data/operations/toolbox-noaa-co2-ch4-growth-pair-n2o-extension-real-task-input-r1.json
```

An experimental route must explicitly allowlist the exact candidate ID. Route planning does not run this command or grant execution authority. If any supplied gas output is unavailable, retain the independent outputs and report that pairing was not performed. Matching years do not make ppm and ppb values commensurate. This artifact does not authenticate NOAA, validate measurements, estimate emissions, establish causal relationships or provide scientific acceptance.
