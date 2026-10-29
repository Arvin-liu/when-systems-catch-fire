# Handoff Action Binding Preflight (experimental)

`collaboration.preflight_handoff_action_binding@0.1.0` checks whether one caller-supplied Federation handoff, local action packet, approval request/decision, execution lease, and receiver descriptor agree on the action being proposed. It extends the receipt-to-bundle and receiver-precondition checks in `collaboration.preflight_receiver_handoff`; it does not accept the handoff or call an executor.

## Use

Pass one UTF-8 JSON object on stdin:

```sh
python3 -B ignition/tools/toolbox_handoff_action_binding_preflight.py --stdin < input.json
```

The object follows `schemas/operations/toolbox-handoff-action-binding-input-r0.schema.json`. Its `expected` object records the source revision, artifact path and SHA-256, task-state revision as observed by the receiver, approval-decision ID, receiver ID/interface version, and whether native resume is required. The matching action packet must carry these public `payload` keys so its digest binds the same context:

- `handoff_action_id`
- `handoff_source_revision`
- `handoff_task_state_revision`
- `handoff_authorization_ref`
- `handoff_target_artifact_ref`
- `handoff_target_artifact_sha256`
- `handoff_receiver_executor_id`
- `handoff_receiver_adapter_version`

The artifact reference and digest must match the source receipt, handoff bundle, action packet, and caller's expected values. The approval request and decision must point to the action packet's exact digest and IDs; the lease must match its run, action, idempotency key, approval lease, receiver and digest, and its declared active time window must include the local preflight clock. This time check does not authenticate the lease. The receiver descriptor is compared with the caller's expected adapter version and declared session-reference kinds.

## What the result means

`DECLARED_BINDINGS_MATCH_NO_AUTHORITY` means the supplied records are internally consistent under the declared checks. It does not mean those records or actors are authentic, that an observation is current, that an approval is legitimate, or that any action is authorized. Every result fixes `handoff_accepted`, `execution_authorized`, and `runtime_invoked` to `false`; the receipt digest is unkeyed and caller supplied.

This is a read-only, default-off experimental tool. It reads one bounded stdin object and the local input schema, then writes JSON to stdout. It makes no network request and writes no files. The receiver descriptor, workspace re-observation, source revision, task-state revision and authority records are caller declarations, not independently observed state. Lease expiry uses the local clock only as a freshness comparison.

## Limits and fallback

Use `collaboration.preflight_receiver_handoff` when only source-receipt projection and receiver preconditions need checking. Use `maintenance.preflight_execution_effect_receipt` for its distinct generic post-run, tool/version/input/output and bounded local-file observation contract. These tools remain useful for their own scopes; the current evidence does not support replacing or retiring either.

Do not use this tool to resume a native executor, authenticate an external actor, observe a live workspace, grant permission, dispatch an action, or establish task/scientific correctness. If any required binding is missing, stale or mismatched, stop and reconcile the source records. If authenticated or live state is required, use an independently authorized process and record its evidence separately.

The checked-in fixture and negative controls are synthetic contract tests only. They include stale/expired lease, mismatched packet digest, malformed/duplicate/non-finite/oversized input, and unsupported receiver resume/session cases. No real-task benefit, comparative reliability, latency, or monetary cost has been established; cost remains `UNKNOWN`.
