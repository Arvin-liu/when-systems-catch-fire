# Era Resolver Finding — ARR R2 Q33 Era Resolver Repair R1

## Verdict
**The `era_ref` resolution is NOT defective.** The failure is a **test-side
mis-classification**: iteration `121Q33` is genuinely merged, but the test fixtures
list it in `LIVE_TASKS` (and one test loads the 121Q33 request while asserting a live
`era_ref=None`). The resolver and manifest are both correct.

## Evidence the resolver is correct
`tools/operations/era_resolver.py::resolve_era`:
```python
era_ref = branch_pr.merge_commit if _is_sha(branch_pr.merge_commit) else None
```
This is the canonical frozen-vs-live rule:
- **Merged** iteration (manifest `status.merged=True` + `branch_pr.merge_commit` present)
  → `era_ref` = the sealed merge commit (frozen diff window `base..merge_commit`).
- **Live/unmerged** candidate → `era_ref=None` (diff window `base..HEAD`).

The guards `test_no_hardcoded_sha_in_resolver` and `test_no_hardcoded_task_id_in_resolver`
still pass — the resolver contains no task-id/SHA special-casing, so this is not a
resolver generalization regression.

## Evidence 121Q33 is genuinely merged (frozen)
From `data/operations/iterations/121Q33.json`:
- `branch_pr.merge_commit = cf321f92014268af40cf9aa9231fe8a4f814b031`
- `status.merged = True`

Git-side confirmation (fresh, this branch):
```
$ git merge-base --is-ancestor cf321f92014268af40cf9aa9231fe8a4f814b031 origin/main
  -> rc=0  (True: cf321f9 is an ancestor of origin/main)
$ git log -1 --format=%s cf321f92014268af40cf9aa9231fe8a4f814b031
  -> "Merge Q33 candidate after exact-head review"
```
A commit that is an ancestor of `origin/main` and carries a `Merge ...` subject is, by
definition, the sealed result of a merged iteration. Therefore `era_ref=cf321f9` is the
**correct** frozen value — not a bug.

## Evidence 121Q25B is genuinely live
From `data/operations/iterations/121Q25B.json`:
- `branch_pr.merge_commit = None`
- `status.merged = False`

Resolver output (live):
```
121Q25B era_ref: None
121Q25B base:    7fc4b309720ea1b4e9c4b47477c2f423860d53df
```
So `121Q25B` is the right fixture for the "live candidate uses base..HEAD (era_ref=None)"
assertion.

## Why the tests failed
The original `test_era_resolver_generalization.py` classified 121Q33 as **live**:
```python
FROZEN_TASKS = ["121Q25", "121Q25C", "121Q25D", "121Q32", "121Q32I"]
LIVE_TASKS   = ["121Q25B", "121Q33"]
```
But 121Q33 had since been merged (its merge commit is in `origin/main`), so:
- `test_live_iteration_resolves_to_none_era_ref` iterated `LIVE_TASKS`, hit 121Q33, and
  the resolver returned the frozen `cf321f9` instead of `None` → assertion error.
- `test_resolve_for_request_reads_task_id` loaded `121Q33-request.json` and asserted
  `era_ref is None`, but 121Q33 now resolves to the frozen `cf321f9` → assertion error.

Supporting cross-check: `test_q33_changed_paths_uniquely_covered` already **passes** with
the frozen window `f54577a..cf321f9`, which is only consistent if 121Q33 is treated as
frozen — confirming the FROZEN classification is correct and the LIVE classification was
stale.

## The fix (narrow, test-only)
1. Move `121Q33` from `LIVE_TASKS` to `FROZEN_TASKS` (it is genuinely merged).
2. Rewrite `test_resolve_for_request_reads_task_id` to use an inline **live** request
   `{"task_id": "121Q25B"}`, asserting `era_ref is None` and
   `base == 7fc4b309720ea1b4e9c4b47477c2f423860d53df`. The frozen 121Q33 era_ref is
   still covered by `test_frozen_iterations_resolve_to_era_ref`.

Result after fix (this branch): `python3 -m pytest tests/test_era_resolver_generalization.py -q`
→ **11 passed**.

## Impact on the two required gates
- **`q33-governance-validation`:** runs this module + 12 other modules + the
  `validate_generated_output_authority.py --request 121Q33-request.json` step. Only the
  2 era-resolver tests failed on `81e6054b`; all others were green. With the fix, this
  workflow is expected `success`.
- **`foundation-validation`:** does **NOT** run `test_era_resolver_generalization.py`
  (it references the era concept only at the Q32I frozen ref `0a13c246...`). The change
  is confined to a test file, so `foundation-validation` stays green (it was already
  `success` on the predecessor `81e6054b`).
