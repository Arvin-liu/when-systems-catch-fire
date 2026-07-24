# Known Limitations — ARR-R1 Scaffold (evidence branch)

These are recorded, **not fixed**, on the evidence branch. Fixing any of them would
require a 7th commit on the scaffold branch, which is **unauthorized** under the
repair scenario (exactly ONE repair commit 6 was authorized; the original 5 were not
amended/rebased/squashed/reset).

## KL-1 — Propagation residue (RESOLVED by commit 6, not a limitation)

The original Agent K BLOCKER: `compute_change_propagation` reported
`unmapped_path residue = 24` (22 files under `tests/adaptive_relational_runtime/**`
from commit 4 + 2 commit-1 architecture docs:
`docs/architecture/object-relation-mechanism-model.md` and
`docs/architecture/self-growth-control-plane.md`).

**Resolution:** commit 6 (`a0d6c46`) mapped `tests/adaptive_relational_runtime/` to the
`arr_runtime` component and the 2 architecture docs to the `arr` component under
**single ownership** (no overlap → no `ambiguous_path`). A fresh K re-audit of
`a0d6c46` confirms `unmapped_path=[]` / `ambiguous_path_mapping=[]` /
`closure_complete=True` / `residue=0`.

**Status: RESOLVED.** Recorded here only for traceability; it is **not** an open
limitation.

## KL-2 — Commit-2 non-blocking items (left as documentation)

The following commit-2 non-blocking review items were **not** applied at the time
(bound by the then-active exactly-5-commit rule); they remain as documentation only:

- (a) a `$id` form inconsistency;
- (b) `signal_scope` marked required;
- (c) G2 `machine_rule` text;
- (d) `source.tier` ↔ `evidence.tier` bridge.

These are non-blocking and were intentionally left unaddressed to preserve the
5-commit boundary; they are not blockers.

## KL-3 — NB-1 (`_apply_anti_overstep` bindings param unused)

In `_apply_anti_overstep`, the `bindings` parameter is currently unused. The B1–B6
anti-overstep guards are enforced via a hardcoded path. The **security outcome is
correct** (the guards fire as intended); only the unused parameter is noted.

## KL-4 — NB-2 (`eng.run()` mutates caller input in place)

`eng.run()` mutates the caller-supplied input in place. Functionally acceptable within
the scaffold's usage, but callers should not rely on input immutability.

## KL-5 — Stale "5 commits" on the scaffold-branch evidence doc

The scaffold-branch evidence document
`docs/architecture/adaptive-relational-runtime-r1-scaffold-evidence.md` (line ~66) still
says "5 commits". This is **stale** after the authorized commit 6. It is a **cosmetic
narrative** item, **NOT** a forbidden item, and is **left unmodified** on the scaffold
branch to avoid introducing a 7th commit. The **authoritative count (6)** is recorded
here on the evidence branch (see `README.md` Counters and `COUNTERS.json`).
