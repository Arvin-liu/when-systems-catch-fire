# IGNITION-20260822-135 Step 00 — Fresh baseline and exact failure inventory

Baseline is clean `main@421a41462e26f8323c7b811e61d47f26232d61b5`, obtained from the live formal remote after refreshing `1111/origin/relay/current@43459ecaf9952163d4638c0bf9c76da99ff73b13`. The supplied Codex output directory is non-Git and was not edited.

Task134's exact natural full discovery is retained as evidence, not reinterpreted:

```text
PYTHONPATH=ignition python3 -m unittest discover -s ignition/tests -p 'test*.py'
runtime: 2825.826s
tests: 1010
failures: 12
errors: 3
skips: 0
```

The 15 entries are recorded machine-readably in `ignition/data/operations/iterations/135/step00-failure-inventory.json`. The original three import/path errors are all current runner-boundary defects. The current-main targeted checks show that Task134's post-observation regeneration removed the function/nonfunction projection, path-manifest and durability failures; those are retained as repaired observations and will be protected by Step 02 preflight. The remaining live closure work is:

- make SymPy a declared canonical isolated-environment dependency and fail preflight when it is unavailable;
- represent Task104–106's 18 diagnostics as an exact sealed contract, with fingerprint and non-growth checks rather than a permanent unittest failure;
- split strict Current changelog validation from versioned historical validation without rewriting append-only history;
- derive architecture-map expectations from canonical graph data instead of the stale literal `81`;
- resolve all fixture paths from explicit repository/module roots and make negative fixtures assert rejection in-process;
- run the production-authority validator matrix under the same canonical environment and projection preflight.

No Task134 historical source was rewritten, no residual was expanded, and no skip/xfail/expectedFailure/ignore was added. The current targeted status is therefore mixed by design: some observations are already repaired, while historical and environmental findings remain visible and actionable until their explicit contracts are implemented.

The long-run evidence does not establish a full-suite PASS. Step 01 must define the canonical runner; Step 02 must make generated projections a preflight; Steps 05–08 must close the semantic classes; only then may the two required natural full-suite runs occur.

Claim ceiling: repository-local baseline archaeology and targeted reproduction only. `CURRENT_WITH_OPEN_OBLIGATIONS` and `EPISTEMICALLY_ACCEPTED=0` remain unchanged.
