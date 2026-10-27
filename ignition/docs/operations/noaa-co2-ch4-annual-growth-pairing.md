# NOAA greenhouse gas annual-growth pairing

`research.pair_noaa_co2_ch4_growth_by_year` v0.3.0 aligns already captured NOAA GML source-surface comparison outputs by equal integer year. It always accepts CO2 and CH4. Input schema r1 may also include N2O; schema r2 may include N2O and/or SF6. The tool reads one bounded JSON envelope from stdin and writes a JSON table to stdout. It makes no network requests and reads no caller-selected paths.

Every supplied output must be a complete version-0.1.0 comparator result from its fixed NOAA GML page and raw-table endpoints, with the same inclusive year range, valid UTC retrieval receipts, and response digests. N2O is supported from 2001 onward and SF6 from 1998 onward. The tool rejects unavailable outputs, mismatched ranges, alternate endpoints, incomplete year rows, duplicate years, and disagreement between source receipts and comparison rows.

Each output row keeps a separate object for each supplied gas: CO2 in ppm, CH4 and N2O in ppb, and SF6 in ppt. The output preserves every comparator status, source receipt, retrieval time, response digest, and the capture-time span. No values are converted or combined across gases. The four-gas captured example spans 29,049 seconds, so the tool does not describe those captures as simultaneous.

Example invocation for the backward-compatible two-gas task:

```sh
python3 -B ignition/tools/toolbox_pair_noaa_co2_ch4_growth_by_year.py --stdin \
  < ignition/data/operations/toolbox-noaa-co2-ch4-growth-pair-real-task-input-r0.json
```

The prior three-gas input remains available under schema r1:

```sh
python3 -B ignition/tools/toolbox_pair_noaa_co2_ch4_growth_by_year.py --stdin \
  < ignition/data/operations/toolbox-noaa-co2-ch4-growth-pair-n2o-extension-real-task-input-r1.json
```

The four-gas captured task uses schema r2 and already captured comparator outputs:

```sh
python3 -B ignition/tools/toolbox_pair_noaa_co2_ch4_growth_by_year.py --stdin \
  < ignition/data/operations/toolbox-noaa-co2-ch4-growth-pair-n2o-sf6-extension-real-task-input-r2.json
```

In the captured SF6 results, the page reports uncertainty `0.004 ppt` and the raw table reports `0.00 ppt`; the pairer preserves the resulting literal difference and does not treat the displayed `0.00` as zero uncertainty. An experimental route must explicitly allowlist the exact candidate ID. Route planning neither runs the command nor grants execution authority. If any supplied gas output is unavailable, keep the independent outputs and report that pairing was not performed.

Year-key alignment does not make ppm, ppb, and ppt values commensurate. This artifact does not authenticate NOAA, validate measurements, estimate emissions, establish causal relationships, or provide scientific acceptance.
