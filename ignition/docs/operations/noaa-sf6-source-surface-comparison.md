# NOAA GML global annual SF6 source-surface comparison

`research.compare_noaa_sf6_source_surfaces` compares NOAA GML's rendered annual SF6 growth page with its fixed raw table for a bounded inclusive year range. It returns both provider-reported increments and uncertainties in ppt, literal differences, missing years, retrieval metadata, and a digest for each received response.

The fixed sources are NOAA's [annual SF6 increase page](https://gml.noaa.gov/ccgg/trends_sf6/) and [raw annual-growth table](https://gml.noaa.gov/webdata/ccgg/trends/sf6/sf6_gr_gl.txt). The page reports globally averaged marine-surface values and notes that annual estimates can change as observations and quality-control updates enter the analysis. The tool records the two surfaces at retrieval time; it does not determine which is correct.

## Use

```sh
printf '%s\n' '{"schema_version":"toolbox-noaa-sf6-source-surface-comparison-input-r0","start_year":2023,"end_year":2025}' \
  | python3 -B ignition/tools/toolbox_compare_noaa_sf6_surfaces.py --stdin --allow-public-network
```

The `--allow-public-network` flag is required on every invocation. Without it, the program exits before any request. A route proposal must separately include the experimental candidate and `gml.noaa.gov`; route planning does not authorize network access or execution.

## Boundaries

- The page and raw-table URLs are fixed. Caller-supplied URLs, redirects, credentials, secrets, billing, file writes, and external actions are not used.
- Input contains only `schema_version`, `start_year`, and `end_year`; years range from 1998 through 2100 and the inclusive range is at most 50 years.
- Exactly two fixed HTTPS GET requests are attempted. Each response is bounded by the shared NOAA comparison engine's byte, duration, and timeout limits.
- Raw response bodies are not retained. SHA-256 values bind received bytes but do not authenticate NOAA.
- A literal page/raw difference is arithmetic output, not a judgment about measurement quality or which source is preferable. This is not an emissions inventory, attribution, causal explanation, or scientific conclusion.

## C1 fit and alternatives

The companion `research.lookup_noaa_global_sf6_annual_growth` is sufficient for a raw-table-only task with one GET; it does not fetch the page or reveal page/raw differences. This comparator is useful when both contemporaneous surfaces and their stated precision are required, at the cost of a second fixed request. A raw-only lookup after this comparator duplicates the raw request unless a separate task needs that receipt. Existing CO2, CH4, and N2O comparators remain specialized to their fixed species and units. No incumbent is retired.

The candidate is optional and default-off. Its machine card and source/route/task receipts are recorded beside the `toolbox-noaa-sf6-source-surface-comparison-*` files in `ignition/data/operations/`.
