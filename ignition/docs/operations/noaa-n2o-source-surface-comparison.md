# NOAA GML global annual N2O source-surface comparison

`research.compare_noaa_n2o_source_surfaces` compares NOAA Global Monitoring Laboratory's rendered annual nitrous-oxide increase table with its fixed raw table for a caller-bounded inclusive year range. It reports both stated N2O mole-fraction increases and uncertainties in ppb, literal differences, missing years, retrieval metadata, and response digests.

The fixed sources are NOAA's [annual N2O increase page](https://gml.noaa.gov/ccgg/trends_n2o/) and [raw annual-growth table](https://gml.noaa.gov/webdata/ccgg/trends/n2o/n2o_gr_gl.txt). NOAA describes the page's N2O values as globally averaged marine-surface data and notes that annual estimates can change as later samples and quality-control updates enter the analysis. The comparison records each surface as retrieved; it does not resolve which should be preferred.

## Use

```sh
printf '%s\n' '{"schema_version":"toolbox-noaa-n2o-source-surface-comparison-input-r0","start_year":2023,"end_year":2025}' \
  | python3 -B ignition/tools/toolbox_compare_noaa_n2o_surfaces.py --stdin --allow-public-network
```

This isolated integration does not add router eligibility; the candidate remains default-off. Each explicit network invocation still needs the public-network flag.

## Boundaries

- The page and raw table URLs are fixed; caller-supplied URLs, redirects, credentials, secrets, file writes, billing, and external actions are not used.
- The input has only `schema_version`, `start_year`, and `end_year`; years must be integers from 2001 through 2100 and the range may not exceed 50 years.
- Each response is limited to 256 KiB and seven seconds; each request has a five-second timeout. At most two GET requests are attempted.
- Raw response bodies are not retained. SHA-256 values bind the received bytes but do not authenticate NOAA.
- A page/raw difference is arithmetic output only. The tool does not validate measurements, estimate emissions, attribute sources, explain causes, or establish a scientific conclusion.
- N2O (nitrous oxide) is distinct from NO2 (nitrogen dioxide).

## C1 fit and alternatives

The existing fixed CO2 and CH4 comparators remain useful for their own gases and units. Their endpoints and output identities cannot be redirected to N2O, so neither can satisfy this task; no incumbent is retired. Manual inspection of one fixed raw table can serve a raw-only question, while this tool is for a task that needs both surfaces and their contemporaneous comparison. The live 2026-10-26 UTC capture matched for 2023–2025 (1.01, 1.02, 1.23 ppb with stated uncertainties 0.02, 0.01, 0.01 ppb). One matching observation does not establish lasting agreement, comparative accuracy, or measurement validity.

The candidate is optional and default-off. Its machine identity card and evidence are in `ignition/data/operations/toolbox-identity-cards-r0.json` and the adjacent `toolbox-noaa-n2o-*` records.
