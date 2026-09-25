# Supplemental record CASE02

Source type: local edge-cache operation recorder. Synthetic.

Purpose: record the result of an operator-selected cache control.

Procedure:
1. [S01] Record incident ID and operator authorization.
2. [S02] Record the content key and cache control chosen outside this procedure.
3. [S03] Submit the selected control once and save its operation ID and response.
4. [S04] Record each requested region and the revision marker returned for it.
5. [S05] Stop on an operation error or unavailable region response; record the returned error or marker verbatim.

Observable fields: incident ID, content key, control ID, operation ID, region, revision marker, response status.
