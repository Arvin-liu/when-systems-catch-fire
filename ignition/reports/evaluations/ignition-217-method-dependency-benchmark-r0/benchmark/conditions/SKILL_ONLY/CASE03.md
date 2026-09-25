# Supplemental record CASE03

Source type: local test-queue status procedure. Synthetic.

Purpose: collect and preserve the status of a queued test request.

Procedure:
1. [S01] Record the immutable request key and the last response stored by the client.
2. [S02] Use the status-lookup control with the same request key.
3. [S03] If a status is pending, wait the local polling interval and query again with that key.
4. [S04] Save each returned status and timestamp without replacing earlier records.
5. [S05] Stop if the lookup returns an error or no response; report status as unavailable.

Observable fields: request key, returned status, query timestamp, receipt identifier, lookup error.
