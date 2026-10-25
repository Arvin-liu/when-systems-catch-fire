# Actions Validation Attribution R0

`maintenance.attribute_actions_validation_evidence` joins one caller-supplied component-validation plan, one GitHub Actions run/jobs snapshot, an extracted artifact file list and an optional component-validation receipt. It is a local, read-only inspection helper. It does not query GitHub or replace the official validation-evidence verifier.

## Run

```sh
python3 -B ignition/tools/toolbox_actions_validation_attribution.py --stdin < input.json
```

Input and output contracts are in:

- [`toolbox-actions-validation-attribution-input-r0.schema.json`](../../schemas/operations/toolbox-actions-validation-attribution-input-r0.schema.json)
- [`toolbox-actions-validation-attribution-output-r0.schema.json`](../../schemas/operations/toolbox-actions-validation-attribution-output-r0.schema.json)

The input includes a digest-bound validation plan; a workflow-run and jobs response; artifact ID, name and digest; and a caller-declared complete or incomplete list of extracted filenames. A receipt may be supplied only when its filename is in that list. The tool checks the plan and optional receipt digests, run/attempt/head binding, any supplied pull-request base SHA, and each job's run/attempt/head binding.

When the file list is explicitly complete and omits `component-validation-receipt.json`, the output says only `ABSENT_FROM_SUPPLIED_COMPLETE_FILE_LIST`. If the list is incomplete, receipt presence is `UNKNOWN_IN_INCOMPLETE_FILE_LIST`. Neither state says that tests failed or did not run. Receipt target results are emitted as caller-declared data and are never certified by this tool.

## Observed example

The fixture binds Actions run `40064357026`, attempt `1`, head `8230dc6c13ec12c57f9c81f81994ee775ebb2ce8`, and the `FULL` plan digest `0bc5139b39c140cbb995d937276e332984d7ed6755c83acdbf489e8e07e1329f` with 11 selected target IDs. The supplied artifact file list contains the plan and no receipt. The workflow run and both listed jobs concluded `cancelled`; their observed job intervals were 1,949 and 49 seconds. The interval sum is not billable time. With no target receipt, the tool leaves all selected-target outcomes unavailable.

## Limits and C1 comparison

- `maintenance.summarize_actions_step_timeline` already parses one run and reports job/step intervals. This tool adds plan digest, selected target, artifact-list and optional receipt alignment for that same run; the existing timeline result remains useful without a validation plan or artifact inventory.
- `maintenance.compare_actions_repeated_step_sequences` requires 2–20 context-matched runs and groups repeated steps. A one-run plan/receipt attribution task does not meet that input contract. It remains useful for multi-run histories.
- A separate end-to-end route trial replays this same run through the interval-only tool, the attribution tool, and a redundant two-tool counterfactual. Three fresh local subprocess samples measured wall time, child CPU, and input/output bytes; the full job-level plan/artifact/receipt contract was met by attribution alone, while the redundant route added no required fact. These are single-machine, task-local observations, not a general performance or cost benchmark. See [`toolbox-actions-validation-attribution-route-evidence-r0.json`](../../data/operations/toolbox-actions-validation-attribution-route-evidence-r0.json).
- The repeated-step analyzer still requires 2–20 context-matched runs and has a distinct multi-run history contract. Keep the timeline tool for interval-only and detailed-step tasks, the batch tool for multi-run histories, and this tool for plan/artifact/receipt attribution; no existing tool is fully replaced.
- No analyst-time, billed-minute, cash-cost, savings or waste comparison was performed.

Input snapshots and receipts are caller-supplied and unauthenticated. This tool does not certify official CI evidence, check sufficiency, estimate costs or savings, or grant merge/release authority. The candidate stays default-off and requires an explicit route allowlist; route planning does not invoke it.
