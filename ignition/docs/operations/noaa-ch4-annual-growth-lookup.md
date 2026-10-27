# NOAA GML global annual methane growth lookup

This optional tool reads NOAA Global Monitoring Laboratory's fixed public text table at `https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_gr_gl.txt`. Its task contract is narrow: select a caller-bounded inclusive year range (1984–2100, at most 50 years), returning the provider's annual atmospheric methane mole-fraction increment and uncertainty in ppb with retrieval time, HTTP metadata, and a SHA-256 of the received table bytes.

The table's header defines annual CH4 mole-fraction increase from Jan 1 through Dec 31. NOAA's [Trends in Atmospheric Methane page](https://gml.noaa.gov/ccgg/trends_ch4/index.html) explains the global marine-surface basis and says the annual increase sums methane added to and removed from the atmosphere by human and natural processes. Therefore this is a net atmospheric concentration change, not an emissions inventory, source attribution, or causal finding. NOAA says its latest year may change after reference-gas recalibration and quality-control procedures; earlier years can also change. The raw table asks users to credit NOAA GML in publications.

## Boundaries

- The URL, HTTPS hostname, and path are fixed in code. One GET is attempted per explicit CLI invocation; redirects are rejected, only `text/plain` is accepted, response size is capped at 128 KiB, socket timeout is 5 seconds, and body reading has a 7-second budget.
- The JSON input must contain exactly integer `start_year` and `end_year` keys. No caller URL, identifier, title, credential, or other query value is sent.
This isolated integration does not add router eligibility; the candidate remains default-off. Each explicit network invocation still needs the network flag.
No route experiment is carried into this isolated package; ROUTER_ELIGIBLE=false until a separate route review and experiment are completed.
- It writes only JSON to stdout, does not save the provider response, does not modify the repository, and has no package, secret, billing, or external-action dependency.
- `FOUND`, `PARTIAL_DATA`, `NO_MATCH`, and acquisition/parser errors are distinct. A missing row is never filled, extrapolated, or treated as zero.
- The digest binds received bytes. The tool does not authenticate the source, independently validate NOAA's method, interpret the trend, estimate emissions, or establish any scientific conclusion.

## C1 comparison

The existing Crossref and OpenAlex metadata tools resolve DOI-keyed scholarly records; neither accepts a year range or returns NOAA's atmospheric CH4 annual-increment series. The complementary `research.lookup_noaa_global_co2_annual_growth` adapter reads a separate CO2 table and returns ppm; it cannot provide methane values in ppb. The two NOAA tools remain separate by species and task. This establishes distinct input/output purposes, not comparative latency, reliability, quality, or cost; estimated cost remains unknown, and no replacement candidate is identified.

The 2026-10-24 #259 source snapshot recorded the NOAA raw-table SHA-256 `0501e15f5ffea518f8dfb90477ad28a7dbcdb26285c2792118f49b3a71e076eb`, ETag `d6c-65d6d473a0edb`, and Last-Modified `Fri, 09 Oct 2026 19:23:08 GMT`. This prior live source observation is source evidence, not a live execution of this newly implemented adapter. Focused tests use a bounded captured-row fixture with mocked transport; actual public-network use remains per-call opt-in.

A separate explicit invocation of the new adapter completed one bounded public request on 2026-10-25: HTTP 200, `FOUND`, with 2023–2025 values and response digest `0501e15f5ffea518f8dfb90477ad28a7dbcdb26285c2792118f49b3a71e076eb`. The normalized result and invocation boundary are recorded in [`toolbox-noaa-ch4-annual-growth-live-task-evidence-r0.json`](../../data/operations/toolbox-noaa-ch4-annual-growth-live-task-evidence-r0.json). The raw response was not retained; this one task outcome does not establish repeatability, comparative quality, or scientific validity.
