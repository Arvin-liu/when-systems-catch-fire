# NOAA GML global annual CH4 source-surface comparison

This optional tool compares NOAA Global Monitoring Laboratory's rendered annual methane-growth table with its fixed raw table for a caller-bounded inclusive year range. It returns both reported increments and uncertainties in ppb, their exact arithmetic differences, request timestamps, HTTP metadata, and response digests.

The page describes globally averaged methane based on marine surface data. NOAA notes that recent values can change after additional observations, calibration, and quality-control work; the tool reports the two surfaces as retrieved and does not resolve which is authoritative. See NOAA's [annual methane-growth page](https://gml.noaa.gov/ccgg/trends_ch4/) and the [fixed raw table](https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_gr_gl.txt).

## Boundaries

- Both HTTPS URLs, the `gml.noaa.gov` host, response types, and paths are fixed in the shared implementation. One explicit invocation attempts two GET requests; redirects are rejected, bodies are size- and time-bounded, and only HTML/text responses are accepted.
- The request accepts exactly `schema_version`, `start_year`, and `end_year`; the selected range must be within 1984–2100 and contain at most 50 years.
This isolated integration does not add router eligibility; the candidate remains default-off. Each explicit network invocation still needs the public-network flag.
- No credentials, caller URL, file writes, billing, or external actions are used. Raw bodies are not retained.
- Missing years are reported explicitly. A digest binds the received bytes but does not authenticate NOAA, validate measurements, establish emissions, attribute sources, or explain a disagreement.

## C1 fit and alternatives

`research.lookup_noaa_global_ch4_annual_growth` remains useful for a one-request raw-table-only lookup, including when a rendered-page comparison is unnecessary or unavailable. This comparator adds the distinct two-surface task: it preserves both page and raw values and reports literal differences or missing years. The existing CO2 comparator covers a different gas and units (ppm); it cannot satisfy a methane/ppb task. These tools can coexist by task scope. This does not establish comparative accuracy, service reliability, latency, or monetary cost.

For reproducibility, use a pinned NOAA source snapshot rather than treating a later live response as the same observation. If either live surface cannot be read or parsed, report its explicit acquisition or parse status and do not claim agreement.
