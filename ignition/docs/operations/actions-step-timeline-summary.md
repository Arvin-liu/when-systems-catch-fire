# GitHub Actions job/step timeline summarizer

## Provenance and purpose

This optional offline tool implements the low-risk measurement portion of Workbench PR #85, “HarnessPro Pareto RSI lessons and P0 Foundation CI verification economics.” Source: `Arvin-liu/ignition-architecture-workbench` PR #85 head `77d308ea132a4952d151cab1d81f9f9c9f44f55c`; blueprint `governance/IGNITION-FOUNDATION-VALIDATION-ECONOMICS-AND-CAUSAL-TRIGGERS-R0.md`, blob `bf952c00c50fa356b72d2260e4d5197017089b47`. The blueprint calls for separating observed wall intervals, hosted-runner time, billable minutes, tokens, and user wait. This tool reports only timestamps present in a caller-supplied snapshot. It does not infer billing or change CI gates.

## Invocation and limits

`python3 -B ignition/tools/toolbox_actions_step_timeline.py --stdin` reads one UTF-8 JSON envelope from stdin and writes one deterministic JSON receipt to stdout. It accepts a `workflow_run` object and a `jobs_response` object projected from the GitHub Actions workflow-run and jobs APIs. Every supplied job must match the envelope's run ID, attempt, and head SHA. Duplicate JSON keys, repeated job IDs or step numbers, malformed timestamps, mismatched bindings, reversed intervals, and inputs over 2 MiB fail with a nonzero exit and no partial stdout. Limits are 500 jobs and 1,000 steps per job.

The CLI makes no network requests and accepts no file paths. It reads only stdin plus its own source file for the source digest; it writes only stdout/stderr. The card remains optional and excluded from routing unless explicitly allowlisted. A route proposal does not authorize invocation.

## Claim ceiling

The receipt summarizes caller-supplied timestamps and binds the exact input bytes and tool source digest. A supplied snapshot is unauthenticated. Parallel job intervals may overlap, so their sum is not elapsed workflow time, hosted-runner minutes, billable time, cash cost, or user wait. The tool does not interpret required checks, test equivalence, CI sufficiency, merge permission, release permission, or scientific evidence.

## Reference smoke fixture

`ignition/tests/fixtures/toolbox-actions-step-timeline/actions-run-40064357026.json` is a minimized field projection of the GitHub API response for run `40064357026`, attempt 1, head `8230dc6c13ec12c57f9c81f81994ee775ebb2ce8`, event `pull_request`. The workflow conclusion is `cancelled`; one job completed as cancelled and the other was cancelled. The fixture preserves 2 jobs and 65 steps with the timestamps returned by the API. `COMPLETE_SNAPSHOT` describes job-list and interval coverage only; it does not mean the workflow succeeded or completed its intended checks. Observed job intervals are 1,949 and 49 seconds; the route job's `Run selected component and consumer tests` interval is 1,894 seconds. These are timestamp differences only and do not imply a completed Foundation run or a cost estimate. A separate negative control removes a timestamp and confirms that the receipt is marked `PARTIAL_OR_UNVERIFIED_SNAPSHOT`.

No same-task usability, accuracy, or cost comparison against manual API inspection has been completed. C1 comparison status remains `COMPARISON_UNKNOWN`; no replacement, retirement, or unique-use conclusion is made.
