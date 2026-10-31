# Toolbox Component Coverage Comparison

`maintenance.compare_toolbox_component_coverage` compares one incumbent toolbox component with one proposed successor. It checks caller-declared valuable use-case inventories, exact input and output contract digests, paired outcomes, a shared evaluator and environment, one resource metric, permission rank, and declared adverse effects.

## Run

```sh
python3 -B ignition/tools/toolbox_component_comparison.py --stdin < comparison.json
```

The command reads at most 512 KiB of UTF-8 JSON and writes one JSON result to stdout. It uses the Python standard library, makes no network requests, reads only its own source file to report a source digest, writes no files, and changes no route, permission, identity card, or registry.

The schemas are `ignition/schemas/operations/toolbox-component-comparison-input-r0.schema.json` and `ignition/schemas/operations/toolbox-component-comparison-output-r0.schema.json`. Quality scores use the caller's shared 0–1000 rubric, with higher scores better. Permission ranks must use one shared scale where a higher number means broader permission exposure. Adverse-effect IDs must come from one shared checklist. These are caller-declared scales, not independently checked policies.

A replacement recommendation requires that every declared incumbent use case has an identical successor contract, every shared case has a complete matched pair under the same evaluator and environment, the successor is no worse on outcomes, quality, resource cost, permission rank, and declared adverse effects, and it is strictly better on at least one measured dimension.

When either tool has a distinct declared use case, the output preserves both task ranges as `COEXIST_DISTINCT_SCOPE`; the performance comparison can still remain `COMPARISON_UNKNOWN`. Missing pairs, mismatched contracts, unknown outcomes, missing cost, or unpinned evaluator/environment do not become zeroes. The tool reports a bounded low-cost next comparison when evidence is incomplete.

## Limits

All use-case value, result, cost, permission, risk, and evidence-reference fields are caller supplied. The tool does not authenticate them, prove that the inventories cover every valuable task, independently score output quality, delete runtime code, deprecate a card, change routing, or authorize a replacement. Any lifecycle change remains a separate governed edit. Preserve the input, result, and referenced evidence as historical records if a component is later retired.

The current PR #264 task comparison is recorded in `ignition/data/operations/toolbox-component-comparison-real-task-r0.json`. It identifies the standalone timeline's per-step task and the attribution tool's plan/run/artifact task as distinct scopes. The shared interval summary is recorded as a matched output observation, while evaluator, environment, and comparable-cost evidence remain unknown; the tool therefore keeps both task ranges without claiming that one is globally superior.
