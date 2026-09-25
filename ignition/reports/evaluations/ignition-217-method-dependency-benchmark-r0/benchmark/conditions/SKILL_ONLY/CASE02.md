# Supplemental record CASE02

Source type: local edge-cache operation instruction. Synthetic.

Purpose: perform and record an authorized cache operation after an operator has selected it.

Procedure:
1. [S01] Confirm the incident identifier and operator authorization.
2. [S02] Record the requested content key and the cache control identifier.
3. [S03] Submit the selected operation once and save its returned operation ID.
4. [S04] Fetch the content key from one named region and record the returned revision marker.
5. [S05] Stop if authorization is missing or the operation returns an error; do not report an unobserved region as checked.

Observable fields: incident ID, content key, region, operation ID, revision marker, response status.
