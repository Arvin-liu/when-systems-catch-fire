# Supplemental record CASE05

Source type: local archive packaging recorder. Synthetic.

Purpose: prepare and verify an archive using a grouping key selected outside this instruction.

Procedure:
1. [S01] Record archive identifier, recipient group, and operator authorization.
2. [S02] List each source file with its supplied label and digest.
3. [S03] Record the grouping key supplied by the authorized operator.
4. [S04] Reopen the output and compare each file, label, and digest with the source list.
5. [S05] Stop on a missing label, digest mismatch, or authorization error; preserve the discrepancy without changing the grouping key.

Observable fields: archive ID, recipient group, grouping key, file label, digest, package ID, verification result.
