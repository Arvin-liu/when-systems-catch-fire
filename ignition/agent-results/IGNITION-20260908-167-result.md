# IGNITION-20260908-167 result

## Verdict

`MAINLINE_INTEGRATION_STILL_BLOCKED`

This result records a bounded execution of the controlling command
`Arvin-liu/1111@3fafaeec7d928309d51f18c3fb0483218706c8a1`,
`agent-commands/IGNITION-20260908-167.md` (command blob
`a5d27d6b72d9f20507b08bf741084c403112b5f3`). No new material run was
started.

## Exact baseline and current remote state

- Formal repository: `Arvin-liu/when-systems-catch-fire`
- Old formal `main`: `212322d41db79bce2dbd116166d3f1ad226291f3`
- PR #216 head: `62c7fc1f3055e887d95299cdb4411cb4b133c664`
- PR #216 branch: `work/IGNITION-20260908-166-mainline-integration`
- PR #216 state at pre-edit observation: `OPEN`, `DRAFT`, base `main`, mergeable
- Candidate ancestry: old `main` is an ancestor; candidate is 22 commits ahead
- Remote `main` remained `212322d41db79bce2dbd116166d3f1ad226291f3`

The exact candidate was checked out in a fresh clone with an initially clean
worktree. The branch itself was not force-updated and `main` was not changed.

## Reproduction and root-cause finding

The three Method 1.4 workflow requests were run with the exact workflow
arguments, including the sealed era/head reference
`f59b9f359ea16a346e07e9621049468417b66423`.

- Phase-D closeout: PASS.
- Q32I propagation check: PASS; closure hash
  `be079995b291e41dcb4c9b8ffdd1997e05f9eef5763da91c9584f4ef8169f705`.
- Method 1.4 A: PASS; closure hash
  `3332a4e7b8ed9e69b9c2ecfcbd6984d75ee4a8bae2aa77da2ddead4ba4d550d0`.
- Method 1.4 B: PASS; closure hash
  `77da4171b1cc289f1d706e56263813431faceb8f410ee764bbb5a3034edba65f`.
- Method 1.4 C: PASS; closure hash
  `d193ddeda5ff2fc1e447657cc18bd85b88572f0ac97f9093a9dc6c19c5787a65`.

The required A→B→C, C→B→A and B→A→C permutations all passed. Each request
also passed three consecutive checks. Product bytes and `git status --porcelain`
remained unchanged. A temporary tampered closure failed with
`stale propagation product`; binding B to A's report also failed closed with
the same diagnostic.

Therefore the previously described “third Method 1.4 check becomes stale”
failure was not reproducible at the exact current head. No root cause was
proven, so no speculative change was made to the checker, historical products,
or workflow binding.

## Current hard blocker

The current remote Foundation run is blocked before the Method 1.4 step:

- Workflow run: `34193681824`
- Job: `101956794159`
- `validate_foundation.py`: `CHECKS_TOTAL=63 CHECKS_PASSED=62 CHECKS_FAILED=1`
- Underlying failures include `discovery:every-repository-path-accounted`
  (`listed=5788`, `tracked=5786`) and
  `generator:deterministic NONFUNCTION_CLAIM_OUTPUT_DRIFT` for four generated
  non-function-claim outputs.

The non-function-claim output drift reproduces locally. The initial local path
accounting miss was caused by this newly added result file; the official path
classification generator was run and the resulting path check is now
`PASS`, with no unresolved paths. The remote job skipped the propagation step
because the Foundation gate failed first. This is a delta from Task166's
recorded propagation-only blocker and is not repaired here because the command
authorizes only the propagation checker/binding/workflow defect.

After the official path-manifest generation, the final local Foundation run
was `CHECKS_TOTAL=63 CHECKS_PASSED=61 CHECKS_FAILED=2`. Its two blocking
families were `claim-governance:integrated` with
`generator:deterministic CENSUS_OUT_OF_DATE census-summary.json`, and
`nonfunction-claim-closure:integrated` with the stale discovery/output
products (`listed=5788`, `tracked=5787` plus
`NONFUNCTION_CLAIM_OUTPUT_DRIFT`). These generated products were not rewritten
because the controlling command does not authorize unrelated Foundation
product repair.

## Regression and validation evidence

Changed files in this Task167 candidate:

- `tests/test_change_propagation.py`: adds reentrancy, permutation, isolation,
  read-only and negative-fixture coverage for the three Method 1.4 requests.
- `data/foundation/repository-path-classification/classification-manifest.jsonl`:
  official generated accounting entry for this result.
- `agent-results/IGNITION-20260908-167-result.md`: this result.

Passed locally:

- Task167 regression: 1 test, `OK`.
- Existing propagation suite: 58 tests, `OK`.
- Exact Method 1.4 original, permutation and repeated-check runs.
- Phase-D closeout, Q32I propagation and the required stale negative cases.

Blocked or not eligible for promotion:

- Full Foundation validation: failed on the generated-output/path-accounting
  blocker above; final local result was 61/63, and the remote exact-head result
  was 62/63 before this candidate was published.
- Remote required checks: not all green.
- PR #216: remains `OPEN` + `DRAFT`; it was not marked Ready and was not merged.
- Formal `main`: unchanged.

## Lifecycle and epistemic boundary

Tasks 158–165 retain their prior ceilings, including
`DETECTOR_NOT_VALIDATED / UNDERDETERMINED`,
`MIXED_LOCK_IN_SUPPORTED_AS_RESEARCH_FINDING`,
`BASIS_LEARNING_OPERATOR_NOT_VALIDATED`,
`BASIS_PRESSURE_SENSOR_NOT_VALIDATED`, and
`NO_VALIDATED_CREATIVE_DISCONTINUITY_FOUND` with Stage B
`GENERATIVE_LEAD_ONLY / NOT_VALIDATED`. This engineering investigation does
not create a canonical layer, raise any research claim, establish external
truth, grant Owner acceptance, or authorize a material run.
