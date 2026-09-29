# Target-opening gate R0

No Task225 A/B/C case or sealed target content may be opened before all conditions below are mechanically evidenced:

1. Task229 preregistration manifest and source files are frozen at a committed exact head whose parent is exactly Task228 head `d82a52077df6d4e96e998ace3757f2fb343b4db5`.
2. Task229 PR is OPEN + DRAFT + UNMERGED and its base is the Task228 branch at `d82a52077df6d4e96e998ace3757f2fb343b4db5`.
3. Every required exact-head workflow on that exact Task229 head is completed with conclusion `success`.
4. The Task228 checksum manifest and six candidate policies still match their preregistered hashes; Task227 target/evaluator manifest hashes still match their verified anchors.
5. No experimental output or target-derived file exists in the preregistration subtree.

The coordinator records the live PR/head/workflow evidence in `target-opening-gate-receipt.json` and runs `tools/target_opening_gate.py` before accessing target bytes. A failed or unavailable gate is a hard stop. After a successful gate, read only the frozen Task225 A/B/C case and target assets, record their hashes in the run receipt, then execute sessions in the frozen order. Do not alter this preregistration after opening.
