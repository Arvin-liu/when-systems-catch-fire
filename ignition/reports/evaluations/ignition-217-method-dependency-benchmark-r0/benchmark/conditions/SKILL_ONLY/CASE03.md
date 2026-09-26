# Supplemental record CASE03

Source type: local test-queue event recorder. Synthetic.

Purpose: preserve request identifiers, a selected control, and its returned status.

Procedure:
1. [S01] Record the immutable request key and last response stored by the client.
2. [S02] Record the queue control chosen by the authorized operator.
3. [S03] Save the control response and timestamp under the original event record.
4. [S04] Preserve earlier status entries when a later response arrives.
5. [S05] Stop if the service returns an error or no response; record the response code and timestamp.

Observable fields: request key, selected control, returned status, timestamp, receipt identifier, lookup error.
