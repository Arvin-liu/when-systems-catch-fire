# Receiver Handoff Preflight

This optional read-only tool checks an incoming serialized `FederatedHandoffBundle` against its `FederatedResultReceipt` before a receiver separately considers a takeover. It validates the receipt's canonical self-digest, rebuilds the handoff projection through the existing Federation API, compares every projected field, and then checks the receiver's declared capabilities and observed artifact references.

Run the checked-in controlled example from the repository root:

```sh
python3 -B ignition/tools/toolbox_receiver_handoff_preflight.py --stdin < ignition/tests/fixtures/toolbox-receiver-handoff-preflight/valid-input-r0.json
```

The bounded UTF-8 JSON input has a strict top-level key set shown in the fixture. `source_receipt` and `handoff_bundle` must use the strict shapes emitted by the existing Federation contract objects. A mismatch returns `SOURCE_RECEIPT_BUNDLE_MISMATCH` before receiver capability checks. A matching receipt and bundle can return `PREFLIGHT_READY_NO_AUTHORITY`; that result is not an acceptance, execution authorization, or claim that the target actually observed the workspace.

## Scope and limits

- Checks source task/executor binding, validated completed work, artifact references, external-session pointers, and propagation of unresolved items by rebuilding the bundle with `build_handoff_bundle`.
- Checks the existing `accept_handoff` capability, workspace-reobservation declaration, and observed-artifact preconditions after the receipt-to-bundle comparison passes.
- Rejects a receipt whose canonical self-digest is inconsistent, but cannot authenticate who created it or whether its contents are true. The digest is unkeyed.
- Does not independently observe a workspace, authenticate target identity or capability claims, authorize actions, dispatch or resume an executor, enforce isolation, or establish task correctness.
- Reads only stdin and the local Federation implementation; writes one bounded JSON result to stdout. It makes no network requests and writes no files.

The candidate is `EXPERIMENTAL_AVAILABLE`, default-off, and `READ_ONLY_RUN`. Use only as an explicit preflight for a serialized public receipt and handoff bundle. Existing direct Federation APIs remain available; this tool does not replace them.
