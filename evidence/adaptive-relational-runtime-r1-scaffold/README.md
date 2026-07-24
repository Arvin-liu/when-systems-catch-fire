# Adaptive Relational Runtime R1 Scaffold — Publication Evidence

This directory is an **evidence branch** artifact set. It does **not** add to the
6-commit ARR-R1 scaffold history (the 6-commit rule applies only to the scaffold
branch `architecture/adaptive-relational-runtime-r1-scaffold`). The evidence branch
`agent/adaptive-relational-runtime-r1-scaffold-20260724` only carries documentation
and the raw attack-matrix execution logs produced by the Release Engineer (Agent L).

## Publish identity note

- `publisher`: Agent L (Release Engineer) — narrow, safe publish operations only.
- `self_final_sha_claimed`: **false** — this evidence branch does **not** assert a
  separate final-verification SHA. The authoritative frozen head is recorded by the
  annotated tag `archive/adaptive-relational-runtime-r1-scaffold-frozen-head` and must
  be confirmed by live refetch.
- `live_refetch_required`: **true** — all "remote verified" claims in this repository
  must be confirmed by `git fetch origin` / `gh` queries against the live remote, not
  by local assumptions.
- Git identity (every commit by Agent L): `49422864+Arvin-liu@users.noreply.github.com`
  / `Arvin Liu`.

## Blocker → Repair narrative (record accurately)

1. **Original 5-commit scaffold** (HEAD `7e32cd84`, 5 commits above production base
   `6723cdfaf52873516c564c324066361b257cdf52`) was **BLOCKED** by the independent
   integration / propagation audit (Agent K) on `compute_change_propagation` reporting
   `unmapped_path residue = 24`:
   - 22 files under `tests/adaptive_relational_runtime/**` from commit 4, plus
   - 2 commit-1 architecture docs:
     `docs/architecture/object-relation-mechanism-model.md` and
     `docs/architecture/self-growth-control-plane.md`.
2. The task owner (之元) **upheld** K's BLOCKED verdict and **did not** allow
   downgrading it to a known limitation. Instead, a **separately-authorized repair task**
   added exactly **ONE ordinary commit 6** (total 6 commits above base `6723cdfa`),
   on the **same branch** and the **same PR #120**, with **no new branch / new PR** and
   **no amend / rebase / squash / reset** of the original 5 commits.
3. **Commit 6** (`a0d6c46cd55ef2dde49d13f958b230f71f619e73`) mapped
   `tests/adaptive_relational_runtime/` to component `arr_runtime` and the 2 architecture
   docs to component `arr` (SINGLE ownership, no overlap → no `ambiguous_path`), fixed the
   evidence / manifest "9 object primitives" → "10", and bumped `registry_version`
   `1.1.14` → `1.1.15`.
4. A **fresh** Agent K re-audit of `a0d6c46` returned **ACCEPT_AS_IS**: over the full
   60-path ARR set `unmapped_path=[]` and `ambiguous_path_mapping=[]`,
   `closure_complete=True`, `residue=0`.

The scaffold remains a **Draft** PR (#120), awaiting external review. This evidence
branch is published alongside it; it does **not** mark the PR ready and does **not**
claim `EXTERNAL_ACCEPTED`.

## Counters

| Counter | Value |
|---|---|
| commits (scaffold branch, above base) | 6 |
| schemas | 14 |
| registries | 10 |
| object primitives | 10 |
| fixtures | 12 (3 text / 3 Git / 2 structured / 2 runtime-receipt / 2 event-sequence) |
| attack-matrix items | 40 (8 REJECT codes, B1–B6, 3 engine guards, 13 projection rules) |
| lifecycle | 10 states – 26 edges – 11 reject_reason_codes |
| failure classes | 8 |
| growth gates | 6 (G1–G6 + G5g) |
| sub-agents | 12 (A–L) |

(Also provided machine-readably in `COUNTERS.json`.)

## Attack-matrix raw logs

`attack_matrix_raw_logs/` contains:
- `attack_matrix.json` — the source matrix (copied from the scaffold).
- `fixtures/` — the 12 fixture files (copied from the scaffold).
- `<id>.log` for each of the 40 items (`ATT-01` … `ATT-40`): produced by executing the
  item's attack against the real runtime (same execution path as the repo's pytest
  harness). Each log captures the `command` (the item's `original_command` descriptive
  form), the `actual_exit_code`, the `decisive_artifact` and its `validity`, and the
  `observed_result`. All 40 executed; all recorded exit codes match the actual process
  exit codes (0 = attack reproduced / decisive outcome valid).

## Audit trail

- **A** — predecessor-auditor
- **B** — cartographer
- **C** — object-model
- **D** — projection
- **E** — mechanism / runtime
- **F** — evidence / lifecycle
- **G** — growth / governance
- **H** — sole-builder
- **I** — red-team
- **J** — replay-auditor
- **K** — integration / propagation audit. **First** audit = BLOCKED on `unmapped_path`
  residue = 24. After authorized repair commit 6, a **fresh** K re-audit =
  **ACCEPT_AS_IS** (`unmapped_path=[]` / `ambiguous_path_mapping=[]` /
  `closure_complete=True` / `residue=0`).
- **L** — release (this evidence branch; the publish operations).
