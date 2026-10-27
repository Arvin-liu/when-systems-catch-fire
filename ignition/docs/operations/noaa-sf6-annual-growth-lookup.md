# NOAA GML global annual SF6 growth lookup

`research.lookup_noaa_global_sf6_annual_growth` v0.1.0 reads one bounded inclusive year range from NOAA GML's fixed [global annual SF6 raw table](https://gml.noaa.gov/webdata/ccgg/trends/sf6/sf6_gr_gl.txt). The matching [NOAA trend page](https://gml.noaa.gov/ccgg/trends_sf6/) describes the values as globally averaged marine-surface data and explains that annual increase is measured from January 1 through December 31 after seasonal-cycle removal.

The tool accepts exactly `schema_version`, `start_year`, and `end_year`; years are integers from 1998 through 2100 and the inclusive range is at most 50 years. It makes one HTTPS GET to `gml.noaa.gov` only when called with `--allow-public-network`. It rejects redirects, unexpected content types, oversized or slow responses, wrong-species markers, malformed or duplicate rows, and invalid uncertainties. Missing years are explicit; values are not interpolated or zero-filled.

`0.00` in the raw uncertainty column is rounded to two decimal places. It does not mean exact zero uncertainty. In a live matched 2025 observation, the page reported 0.004 ppt while the raw table reported 0.00 ppt; both surfaces reported 0.48 ppt growth. This is a precision limitation in the raw table, not evidence that one surface is superior. For tasks requiring higher uncertainty precision or a current page/raw comparison, this raw-only tool is counterindicated.

## Example

```sh
printf '%s\n' '{"schema_version":"toolbox-noaa-sf6-annual-growth-lookup-input-r0","start_year":2023,"end_year":2025}' |
  python3 -B ignition/tools/toolbox_noaa_sf6_annual_growth_lookup.py --stdin --allow-public-network
```

The query is read-only and returns the selected records, retrieval time, HTTP metadata when supplied, response byte count and digest. It does not retain the raw response, write repository files, estimate emissions, attribute sources, or establish a scientific conclusion. A digest binds received bytes; it does not authenticate the provider.

The existing CO2, CH4, and N2O tools remain useful for their distinct species and units. No replacement is established. The SF6 reader is optional and default-off; explicit routing still does not grant execution permission. See the machine-readable identity card and route evidence in `ignition/data/operations/`.
