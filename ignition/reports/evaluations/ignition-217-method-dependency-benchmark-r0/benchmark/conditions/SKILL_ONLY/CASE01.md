# Supplemental record CASE01

Source type: local archive export handling instruction. Synthetic.

Purpose: preserve an operator-selected export and record its output.

Procedure:
1. [S01] Record the archive identifier and route identifier selected by the authorized operator.
2. [S02] List visible source files with version labels and signature markers.
3. [S03] Run only the preselected route and save its operation identifier and item count.
4. [S04] Reopen the package and compare its file list with the source list.
5. [S05] Stop on access denial or item-count mismatch; record the response and operation status.

Observable fields: archive ID, route ID, version labels, signature markers, item count, operation status.
