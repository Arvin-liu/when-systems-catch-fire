# NOAA CO2 Source-Surface Comparator

research.compare_noaa_co2_source_surfaces compares the annual-growth values
and stated uncertainties on NOAA GML's rendered CO2 page and its fixed raw
table for a bounded year range.

The comparator makes exactly two HTTPS requests to fixed gml.noaa.gov URLs.
It accepts only start_year and end_year; the range is limited to 50 years
from 1959 through 2100. Invocation requires the per-call
--allow-public-network flag. The routing planner can propose this tool only
after an explicit experimental-tool allowlist and never authorizes invocation.

The output preserves each surface's selected values, retrieval time, HTTP
metadata when supplied, and response SHA-256. It reports exact numeric matches,
literal numeric differences, or missing years. It does not judge rounding or
statistical significance, decide which surface is correct, retain raw response
bodies, or authenticate NOAA. It cannot establish emissions, attribution,
causation, measurement validity, or scientific acceptance.

Example:

    printf '%s\n' '{"schema_version":"toolbox-noaa-co2-source-surface-comparison-input-r0","start_year":2023,"end_year":2025}' \
      | python3 -B ignition/tools/toolbox_compare_noaa_co2_surfaces.py \
          --stdin --allow-public-network

If either source is unavailable or its table shape changes, the tool reports
the source or parse status and does not fabricate missing values. For a
raw-table-only request, use the existing
research.lookup_noaa_global_co2_annual_growth adapter; this comparator adds
the page-to-raw-table cross-check.
