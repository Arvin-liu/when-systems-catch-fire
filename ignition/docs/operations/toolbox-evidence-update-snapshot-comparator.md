# Evidence Update Snapshot Comparator

`research.compare_evidence_update_snapshots` makes one bounded, read-only structural comparison between two caller-supplied snapshots for the same task and claim. It reports added and absent evidence IDs, exact record-field changes, source-family count changes, declared scope/applicability/state deltas, predecessor/as-of references, change-reason codes, and evaluator/update/stopping/acquisition-dependence drift.

The result is a derived comparison record that a separately authorized workflow may preserve in an append-only update history. This tool does not maintain a ledger, modify claim state, retrieve evidence, or decide whether an update is scientifically warranted.

## Use it when

- A task has two versioned evidence snapshots for the same claim and the caller needs a structural update trace.
- A reviewer needs to see whether evidence identifiers, caller-declared source families, record states, scope, applicability, or update policies changed.
- A negative or unchanged update must remain explicit rather than being silently turned into a new synthesis.

## Do not use it when

- The sources or their digests must be authenticated, retrieved, or semantically evaluated.
- The task requires ranking evidence, deciding a claim's truth, inferring that a status change is a downgrade, measuring accumulation bias, or approving scientific acceptance.
- The snapshots concern different task IDs or claim IDs, or their temporal ordering is unknown.

## Input and output

Run `python3 -B ignition/tools/toolbox_compare_evidence_update_snapshots.py --stdin` and provide one UTF-8 JSON object matching `ignition/schemas/operations/toolbox-evidence-update-snapshot-comparison-input-r0.schema.json`. Input is capped at 256 KiB and 200 evidence rows per snapshot. Each snapshot binds a task revision, claim, as-of reference and UTC observation time, scope and applicability digests, caller-declared state/reason, evaluation instrument, update policy, stopping policy, acquisition-dependence mode, and evidence rows.

The output matches `ignition/schemas/operations/toolbox-evidence-update-snapshot-comparison-output-r0.schema.json`. `COMPARABLE_AS_DECLARED` means the declared comparison controls match and are present; it does not mean the evidence is comparable in a scientific sense. Any missing or changed scope, applicability, evaluator, policy, acquisition-dependence, task revision, or record-version metadata yields `COMPARISON_UNKNOWN` while preserving the structural deltas. A missing item from the successor snapshot is reported as absent, not as withdrawn. Only an explicit caller-declared transition to `WITHDRAWN` or `RETRACTED` appears in the withdrawal list.

If evidence is acquired while prior synthesis is visible, the output records that dependency and requests a separate accumulation-bias review. The comparator itself does not estimate bias. Claim-state labels, record states, source families, hashes, and change reasons remain caller-declared. It reports exact label changes and never ranks them.

## Permissions, cost and fallback

- Local stdin/stdout only. No filesystem reads/writes, network, secrets, billing, or external actions.
- Python 3.9+ standard library at runtime. Cost is `UNKNOWN`; no latency or memory benchmark has been calibrated.
- Default off. It is not selected by the route planner unless the experimental tool ID is explicitly allowlisted for a matching evidence-update task. Route selection is a proposal and does not authorize invocation.
- If a snapshot is incomplete or incomparable, preserve `NO_CHANGE_NOT_ESTABLISHED` or `COMPARISON_UNKNOWN`, retain the original snapshots, and have a human review the discrepancy. Manual side-by-side review is the fallback.

## Current evidence and limits

The local synthetic fixture exercises additions, absence, a declared withdrawal, a claim-state label change, source-family counts, and acquisition dependence. It does not prove source authenticity, scientific utility, independent review, or lower task cost. No existing comparator is retired: this candidate's same-task outcome and cost comparison remains `COMPARISON_UNKNOWN`.
