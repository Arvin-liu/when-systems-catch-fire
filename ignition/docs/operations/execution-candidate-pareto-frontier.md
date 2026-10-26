# Paired execution candidate Pareto frontier

`maintenance.summarize_execution_candidate_pareto_frontier` analyzes caller-supplied observations for candidate implementations evaluated on the same case/trial set, evaluator digest, task-set digest, and environment reference. It reports each candidate's empirical pass fraction and exact mean of one caller-declared resource metric. It marks candidates below the baseline pass-rate floor, dominated candidates, and the observed nondominated frontier.

## Run

```sh
python3 -B ignition/tools/toolbox_execution_pareto_frontier.py --stdin < comparison.json
```

The command reads at most 512 KiB of UTF-8 JSON from stdin and emits one JSON receipt. It uses only the Python standard library, makes no network request, reads no secrets, writes no files, and changes no tool, route, permission, or repository state.

The input schema is `ignition/schemas/operations/execution-candidate-pareto-input-r0.schema.json`; the output schema is `ignition/schemas/operations/execution-candidate-pareto-output-r0.schema.json`. Each candidate must have exactly one row for every shared `(case_id, trial_id)` pair. The caller declares one resource metric and unit for the whole evaluation. A `null` cost means it was not measured; null is never converted to zero. If any cost is missing, the tool returns `COMPARISON_UNDETERMINED_COST_MISSING` and no frontier.

## Reading the result

- `quality_floor_pass_rate_fraction` is the baseline candidate's observed pass fraction. It is a descriptive floor for this input set, not a statistical guarantee.
- `mean_resource_cost_fraction` is an exact rational string such as `31/2`, in the caller-declared unit.
- `ON_FRONTIER` means no other above-floor candidate is at least as good on pass fraction and no more costly with one strict improvement. `DOMINATED` names the observed dominators. `BELOW_BASELINE_PASS_RATE` candidates are excluded from the frontier.
- Equal observed profiles can both remain on the frontier. The tool does not break ties or choose a lite/medium/heavy profile.
- `execution_authorized` is always false. The receipt does not establish source authenticity, measurement validity, statistical significance, generalization, causality, route eligibility, or permission to edit a harness.

## Scope and comparison

This is a small deterministic analysis primitive inspired by Workbench #85's separate HarnessPro candidate-selection item. It implements only matched-input outcome/resource aggregation and Pareto-dominance reporting. It does not implement HarnessPro's agents, trajectory diagnosis, generated tests, candidate editing, recursion, benchmark claims, or deployment choices. The paper treats task success and cost as joint objectives, requires a performance floor, and keeps latency auxiliary; this tool follows only the bounded aggregate/frontier portion and does not reproduce the paper's experiments.

The existing GitHub Actions tools analyze per-run checks, CI target attribution, or repeated job/step intervals. `maintenance.compare_context_packet_variants` compares packet structure and declared obligations. Those tools do not accept paired task outcome/resource rows or compute a candidate frontier. Their distinct functions remain available. No real paired task comparison with this candidate tool has yet been recorded, so replacement value remains `COMPARISON_UNKNOWN` and no existing tool is retired.

## Source and license

- Workbench #85, exact indexed head `77d308ea132a4952d151cab1d81f9f9c9f44f55c`, item `AB-19-HARNESS-PARETO-R0`.
- Pan et al., *HarnessPro: Recursive Harness Self-Improvement with Pareto Optimization for Performance-Cost Trade-offs*, arXiv `2610.26770v2`, 2026-10-20: <https://arxiv.org/abs/2610.26770>.
- This implementation was written for Ignition and does not copy external repository code. The paper's benchmark metrics are not evidence for this tool.
- Tool code uses Ignition repository license `BUSL-1.1`; runtime dependency is Python 3.9+ standard library.
