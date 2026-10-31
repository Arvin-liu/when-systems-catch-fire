# NOAA GML global annual N2O growth lookup

`research.lookup_noaa_global_n2o_annual_growth` retrieves a caller-bounded year range from NOAA Global Monitoring Laboratory's fixed raw annual nitrous-oxide mole-fraction increase table. It returns provider-reported annual increases and uncertainties in ppb, explicit missing-year status, retrieval metadata, and a digest of the received bytes.

The endpoint is fixed at <https://gml.noaa.gov/webdata/ccgg/trends/n2o/n2o_gr_gl.txt>. The tool makes one request per explicitly opted-in invocation; it does not fetch the rendered page.

## Use

```sh
printf '%s\n' '{"schema_version":"toolbox-noaa-n2o-annual-growth-lookup-input-r0","start_year":2023,"end_year":2025}' \
  | python3 -B ignition/tools/toolbox_noaa_n2o_annual_growth_lookup.py --stdin --allow-public-network
```

`--allow-public-network` is required for every invocation. Without it the CLI exits before making a request. The candidate remains excluded from default routing; a route proposal must explicitly include the exact candidate ID and the `gml.noaa.gov` host, and still does not authorize execution.

## Boundaries

- Caller-supplied URLs, redirects, credentials, secrets, file writes, billing, and external actions are not used.
- Input accepts only the declared schema version and integer years from 2001 through 2100, with at most 50 inclusive years.
- The fixed host, path, HTTPS scheme, `text/plain` response, five-second request timeout, seven-second response limit, and 256 KiB response ceiling are checked.
- The raw response is parsed in memory and not retained. Its SHA-256 binds received bytes but does not authenticate NOAA.
- Annual atmospheric mole-fraction growth is not an emissions inventory, source attribution, causal explanation, or scientific conclusion. Missing years are not zero.

## C1 fit and alternatives

This narrow lookup is for a task that needs only provider values from the raw N2O table. In a matched 2023–2025 run, it returned 1.01, 1.02, and 1.23 ppb with stated uncertainties 0.02, 0.01, and 0.01 ppb from one request. The existing N2O page/raw comparator used two requests for the same range, returned the same raw values, and found an exact page/raw match in that observation. The comparator remains useful when both current surfaces and their differences are required; the tools coexist by task scope. Existing CO2 and CH4 raw-table lookups remain useful for their different fixed species and units. No incumbent is retired. Request count is observable here; this does not establish a reliability, accuracy, latency, monetary-cost, long-run agreement, or scientific-validity ranking. See the machine records in `ignition/data/operations/toolbox-noaa-n2o-annual-growth-lookup-c1-evidence-r0.json` and `ignition/data/operations/toolbox-noaa-n2o-annual-growth-lookup-real-task-evidence-r0.json`.
