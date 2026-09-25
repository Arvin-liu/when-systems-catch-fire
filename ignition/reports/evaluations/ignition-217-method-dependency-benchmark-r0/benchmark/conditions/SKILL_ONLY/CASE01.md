# Supplemental record CASE01

Source type: local archive handling instruction. Synthetic.

Purpose: prepare a requested archive package and record what was delivered.

Procedure:
1. [S01] Confirm the requested archive identifier and the caller's access to the source folder.
2. [S02] List the files visible to the caller and record their version labels and signature markers.
3. [S03] Run the export route already selected by the caller; record the route identifier and item count.
4. [S04] Reopen the delivered package and compare its file list with the source list.
5. [S05] Stop if access is denied or the delivered item count differs from the recorded count.

Observable fields: archive ID, route ID, file labels, signature marker, item count, export status.
