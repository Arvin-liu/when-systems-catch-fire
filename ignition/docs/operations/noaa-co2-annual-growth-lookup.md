# NOAA GML global annual CO2 growth lookup

This optional tool retrieves a caller-bounded inclusive year range from NOAA Global Monitoring Laboratory's fixed public table at `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_gr_gl.txt`. The input accepts years 1959–2100 and at most 50 years per request. It returns the provider's annual atmospheric CO2 mole-fraction increase and stated uncertainty in ppm, retrieval time, HTTP metadata, and a SHA-256 digest of the response bytes.

NOAA describes this product as global annual carbon dioxide growth based on globally averaged marine-surface data. The raw table states that annual increase is the net CO2 added to and removed from the atmosphere during the year; its recent uncertainty values may be preliminary and the latest data may change after quality-control and reference-gas procedures. The result is not a sector emissions inventory, source attribution, causal analysis, or scientific conclusion. See NOAA's [global CO2 growth page](https://gml.noaa.gov/ccgg/trends/gl_gr.html) and the [fixed raw table](https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_gr_gl.txt).

During the 2026-10-25 source review, the rendered page displayed 2023 growth as 2.70 ppm while the fixed raw table displayed 2.69 ppm; the later raw file header says it was created on 2026-10-09, while the rendered page version is dated 2026-09-08. This difference is preserved as unresolved. The tool returns only the fixed raw table and its digest; it does not reconcile this difference or claim the displayed page and raw file agree. The source review receipt is [`toolbox-noaa-co2-source-review-r0.json`](../../data/operations/toolbox-noaa-co2-source-review-r0.json).

## Boundaries

- The URL, HTTPS hostname, and path are fixed in code. One GET is attempted per explicit CLI invocation; redirects are rejected, only `text/plain` is accepted, response size is capped at 128 KiB, the socket timeout is 5 seconds, and body reading is bounded to 7 seconds.
- The executable requires `--allow-public-network` for that invocation. A route proposal must explicitly allow `gml.noaa.gov`; planning does not grant network permission or authorize execution.
- No credentials, arbitrary query text, user URL, file writes, billing, or external actions are used. The raw response is not retained.
- Missing years remain `PARTIAL_DATA` or `NO_MATCH`; values are never interpolated or filled with zero. A response digest binds the received bytes but does not authenticate NOAA or independently validate the data.

## C1 comparison and fit

`research.lookup_noaa_global_ch4_annual_growth` remains a separate complementary tool. It reads a different fixed NOAA table and returns methane increments in ppb; this tool reads the CO2 table and returns carbon-dioxide increments in ppm. Neither can supply the other's gas-specific observation contract. Keep both default-off and route only for the requested species. This contract comparison does not establish comparative accuracy, service reliability, latency, or cost; cost remains `UNKNOWN`.

The focused tests use a small source-shaped fixture and mocked transport. No live CO2 request has been made through this tool in this integration; its route receipt is proposal-only and keeps `execution_authorized=false`.
