# CI Failure Reproduction — ARR R2 Q33 Era Resolver Repair R1

## Trigger
- **Predecessor head (locked):**
  `81e6054baf5dd0df0422c0fd42f21854073d75dd`
  (`repair/adaptive-relational-runtime-r2-human-front-door-sync-r1`, PR #124)
- **Failed remote run:** `30145328088` (job `validate`, id `89645933420`,
  workflow `q33-governance-validation`)
- **Child branch:** `repair/adaptive-relational-runtime-r2-q33-era-resolver-repair-r1` (this branch)
- **Draft PR (target):** base `repair/adaptive-relational-runtime-r2-human-front-door-sync-r1`
- **Complete remote log:** `REMOTE_CI_JOB_LOG_30145328088.txt` (636 lines, committed verbatim)

## Exact failure (no guessing — from the complete remote job log)
The `q33-governance-validation` run executed
`tests/test_era_resolver_generalization.py` (log line 419) and reported
**`2 failed, 92 passed, 8 warnings, 24 subtests passed in 3.44s`** (log line 618).

The two failing tests both assert `era_ref is None` for iteration **121Q33**, but the
resolver returns the sealed merge commit `cf321f92014268af40cf9aa9231fe8a4f814b031`:

- **`test_live_iteration_resolves_to_none_era_ref`** (log lines 540–553):
  ```
  self = ...testMethod=test_live_iteration_resolves_to_none_era_ref
      def test_live_iteration_resolves_to_none_era_ref(self):
          for task in LIVE_TASKS:
              era = resolve_era(ROOT, task)
              self.assertIsNotNone(era)
  >           self.assertIsNone(
                  era["era_ref"], f"{task}: live candidate must use base..HEAD (era_ref=None)"
              )
  E   AssertionError: 'cf321f92014268af40cf9aa9231fe8a4f814b031' is not None : 121Q33: live candidate must use base..HEAD (era_ref=None)
  tests/test_era_resolver_generalization.py:110: AssertionError
  ```
- **`test_resolve_for_request_reads_task_id`** (log lines 554–564):
  ```
  self = ...testMethod=test_resolve_for_request_reads_task_id
      def test_resolve_for_request_reads_task_id(self):
  >       req = _load(ROOT / "data/operations/propagation/121Q33-request.json")
          era = resolve_era_for_request(ROOT, req)
  >       self.assertIsNone(era["era_ref"])
  E       AssertionError: 'cf321f92014268af40cf9aa9231fe8a4f814b031' is not None
  tests/test_era_resolver_generalization.py:117: AssertionError
  ```

## Local reproduction (detached HEAD on predecessor `81e6054b`)
Running the same module locally against the unmodified predecessor reproduces both
failures byte-for-byte:
```
python3 -m pytest tests/test_era_resolver_generalization.py -q
... FAILED test_live_iteration_resolves_to_none_era_ref
... FAILED test_resolve_for_request_reads_task_id
2 failed, 9 passed
```

## What is NOT broken
- The **resolver** (`tools/operations/era_resolver.py`) is correct. It returns
  `era_ref = merge_commit if _is_sha(merge_commit) else None`. For a genuinely merged
  iteration this is the sealed merge commit; for a live one it is `None`.
- The **121Q33 manifest** (`data/operations/iterations/121Q33.json`) is correct:
  `branch_pr.merge_commit = cf321f92014268af40cf9aa9231fe8a4f814b031`,
  `status.merged = True`.
- The **generated-output-authority validator** for the Q33 request already passes on
  this head (frozen window `f54577a..cf321f9`), confirming 121Q33 is legitimately frozen.

## Scope boundary
This repair addresses **only** the test-side mis-classification of 121Q33 (merged, but
listed in `LIVE_TASKS`) and the now-incorrect `121Q33-request.json` assumption in
`test_resolve_for_request_reads_task_id`. It does not touch the resolver, the manifests,
Main, PR #109–#124, or any R3/corpus path.
