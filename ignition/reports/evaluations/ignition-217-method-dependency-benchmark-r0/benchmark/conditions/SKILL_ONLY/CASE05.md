# Supplemental record CASE05

Source type: local archive packaging instruction. Synthetic.

Purpose: prepare a requested bundle while preserving source labels and a delivery record.

Procedure:
1. [S01] Confirm the archive identifier, destination group, and operator authorization.
2. [S02] List each source file with its supplied label and file digest.
3. [S03] Run the selected packaging operation and save the package identifier.
4. [S04] Reopen the output and verify the file list, labels, and digests against the source list.
5. [S05] Stop on a missing label, digest mismatch, or authorization error.

Observable fields: archive ID, destination group, file label, digest, package ID, verification result.
