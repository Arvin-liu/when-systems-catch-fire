# GitHub Actions multi-run interval union

`maintenance.summarize_actions_interval_union` summarizes the wall-clock intervals present in two to twenty caller-supplied GitHub Actions job snapshots. Inputs must share one workflow, event, pull request, and base SHA; the existing repeated-step analyzer validates that binding and normalizes the known skipped-job timestamp anomaly.

Run it only for a task that needs elapsed wall-time coverage across several runs:

```sh
PYTHONPATH=ignition python3 -B ignition/tools/toolbox_actions_interval_union.py --stdin < ignition/tests/fixtures/toolbox-actions-repeated-step-analysis/pr264-four-runs-r0.json
```

The receipt reports the sum of observed job intervals, the union of their time ranges, excess overlap (`sum - union`), peak concurrent observed jobs, per-run values, and missing interval coverage. A partial set remains partial even when the observed intervals can be calculated. The union counts time during which at least one observed job was running; excess overlap counts duplicated job-seconds across overlapping intervals.

The #264 four-run example has 14 supplied job rows, 12 timed rows, 26,972 observed job-seconds, a 26,972-second union, zero observed overlap excess, and a peak of one observed job. Two job rows have no usable interval, so the receipt remains partial; this does not prove the missing intervals were idle.

This is an offline arithmetic tool. It does not authenticate the snapshots, query GitHub, calculate billed minutes or cash cost, infer runner contention or avoidable work, assess required checks, authorize execution, or change a release decision. Interval totals are not runner-billing evidence.

The tool is experimental and excluded from default routing. Explicit candidate allowlisting only creates a route proposal; the planner does not invoke the tool or authorize execution.
