# Exact-head GitHub check-run observations

`maintenance.inspect_exact_head_check_observations` compares a caller-supplied GitHub `check-runs` JSON snapshot with an expected commit SHA and a caller-supplied list of check names and GitHub App IDs. It reports exact matches, stale-SHA observations, provider mismatches, pending/non-success results, missing contexts, incomplete snapshots, and duplicate exact matches.

## Input and output

Input is one UTF-8 JSON request on stdin, validated against [`toolbox-actions-check-observations-input-r0.schema.json`](../../schemas/operations/toolbox-actions-check-observations-input-r0.schema.json). `check_runs_complete` is a caller assertion that all pages were collected. The request names the expected SHA and the context/App pairs to inspect; it does not import branch protection automatically.

Output is a deterministic JSON receipt validated against [`toolbox-actions-check-observations-output-r0.schema.json`](../../schemas/operations/toolbox-actions-check-observations-output-r0.schema.json). A unique exact-SHA, exact-name, exact-App check with `completed`/`success` is labeled `OBSERVED_SUCCESS`. A missing App identity stays `UNKNOWN_PROVIDER_STATE`. The tool never chooses the latest among duplicate matches. Incomplete snapshots report `SNAPSHOT_INCOMPLETE` so absence is not treated as proof.

```sh
python3 -B ignition/tools/toolbox_actions_check_observations.py --stdin < request.json
```

## Boundaries

- The input snapshot and requested context/App pairs are caller supplied and unauthenticated by this tool.
- It does not read repository branch protection, establish that a context is required, authenticate the API response, or evaluate check sufficiency.
- A result is not permission to reuse CI, skip a run, merge, release, or claim scientific validity.
- It makes no network request, creates no files, and uses only the Python standard library.
- The existing timeline analyzer remains useful for job/step intervals. The plan/artifact attribution tool remains useful for linking one run to a component validation plan, targets, and artifacts. This tool answers only the exact check name/SHA/App observation question.
- Local latency, analyst-time savings, CI-minute savings, and cost are unknown; no optimization claim is made.

## Failure and rollback

Malformed or oversized input, duplicate JSON keys, invalid SHAs, duplicate check-run IDs, or a claimed complete snapshot whose count does not match its rows exits nonzero without partial JSON output. To roll back, remove this optional tool, schemas, fixture, focused tests, route/C1 evidence, and this document; regenerate the candidate identity cards and `TOOLBOX.md`. Existing Actions tools and current operations remain usable.
