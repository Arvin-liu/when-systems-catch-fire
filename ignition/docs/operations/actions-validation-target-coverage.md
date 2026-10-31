# Actions validation target coverage comparison

`maintenance.compare_actions_validation_target_coverage` compares validation plans and caller-declared target results across 2–20 GitHub Actions runs from the same workflow, event, pull request, and base commit.

The tool accepts a bounded JSON envelope on standard input. Each `runs` item is one complete input accepted by `maintenance.attribute_actions_validation_evidence`, including its plan, run/jobs snapshot, artifact inventory, and optional receipt. The existing single-run validator remains responsible for plan digests, run/head/attempt bindings, receipt digests, target ordering, artifact file-list shape, and timeline validation. The new tool compares only after every row passes that contract.

```sh
python3 -B ignition/tools/toolbox_actions_validation_target_coverage.py --stdin < input.json
```

The input limit is 2 MiB and the run limit is 2–20. Rows must share one workflow ID/path, event, pull-request number, and base SHA. Repeated workflow run/attempt pairs are rejected. Input order defines adjacent-run comparisons; the tool does not infer chronology from names or sort commits.

## Output

The output reports, per run:

- run ID, attempt, head SHA, status, and conclusion;
- plan mode/digests and selected target IDs;
- the supplied artifact ID, name, SHA-256, file list, and run-attempt binding;
- receipt presence, binding status, and caller-declared target values.

It then reports the selected-target union/intersection, additions/removals/retained targets between adjacent rows, per-target plan and receipt-claim counts, and repeated target-set signatures. A repeated signature means only that the same set of targets appeared in multiple supplied plans; it does not establish duplicate plans, redundant CI, avoidable work, or waste.

When no receipt content is supplied, the selected targets receive `NO_TARGET_RESULT_CLAIM`. This is unknown evidence, not a failure. If a receipt is supplied, its booleans remain caller declarations; matching hashes and IDs do not make the receipt official CI evidence.

For a completed skipped job whose supplied timestamps run backward, the tool drops only that interval from timeline parsing and records the original timestamps and handling. Reversed intervals for executed jobs remain rejected by the reused single-run contract.

## Boundaries and alternatives

The tool is default-off and has no filesystem writes, network access, secrets, billing access, or external actions. A route proposal does not run the tool, authenticate source data, satisfy a required check, or authorize merge or release. It does not estimate billed minutes or cost savings.

Use `maintenance.attribute_actions_validation_evidence` for one run’s plan/artifact/receipt attribution. Use `maintenance.compare_actions_repeated_step_sequences` for repeated job/step names, outcomes, and observed intervals across runs. Use the current Actions timeline operation for a single run’s job/step interval summary. Their scopes differ, so this addition does not replace them.

The tool can be removed by deleting its candidate card and implementation/evidence bundle, then regenerating identity projections. Existing attribution and repeated-step tools do not depend on it. Historical evidence should remain available if it is retired.

Focused checks:

```sh
python3 -B -m unittest ignition.tests.test_toolbox_actions_validation_target_coverage
```
