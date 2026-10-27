# Validation Invocation Deduplication Planner

`maintenance.plan_validation_invocation_deduplication@0.1.0` groups caller-supplied validation profile records that have an exactly matching argument vector, working directory, source tree, runtime fingerprint, environment fingerprint, and result contract. It reports a potential read-only reuse group only when every profile also declares a source-reviewed read-only effect boundary.

The tool reads one bounded JSON document from stdin and prints deterministic JSON. It does not read the checkout, launch a validator, change a workflow, share a result, or authorize a check to be skipped. Source tree, runtime/environment fingerprints, result contracts, and review references are caller-supplied and unauthenticated. A group is a reuse candidate for human/executor review; it is not proof that two validations have identical semantics.

Use it when a concrete task compares several validation profiles on one pinned tree and needs to find exact repeated invocations. Do not use it to infer billing, wall-time savings, required-check sufficiency, or gate changes. Any later execution plan must preserve each profile's required assertion and independently authorize reuse.

```sh
python3 -B ignition/tools/toolbox_validation_invocation_deduplication.py --stdin < profiles.json
```

The planner is experimental and excluded from routing by default. Its route test shows that the default route leaves the task incomplete; an explicit allowlist proposes only this planner and still sets `execution_authorized=false`.
