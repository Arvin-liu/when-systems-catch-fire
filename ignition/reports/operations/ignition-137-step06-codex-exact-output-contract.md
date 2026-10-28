# IGNITION-20260824-137 — Step 06 Codex Adapter R2 Exact Output Contract

Strict Task137 envelopes now cause the Codex adapter to pass literal argv with
`--json`, `--ephemeral`, `--ignore-user-config`, `--ignore-rules`,
`--sandbox read-only`, an externally materialized read-only
`--output-schema`, and explicit disposable `--cd`. The adapter does not use
shell interpolation, `--output-last-message`, dangerous bypass flags,
`--add-dir`, remote Git, browser, message, or channel options.

The output schema has `additionalProperties=false` and requires exactly
`nonce`, `selected_ids`, `count`, and `workspace_digest_claim`. The schema is
created in a separate disposable location for the live attempt; it is not
read from the formal repository by the child and is never written to the
fixture workspace.

Adapter, reentrancy, execution, and preflight tests passed: `15 tests / 0
failures / 0 errors / 0 skips`. No live inference was run.

Claim ceiling: this step proves argv and schema-boundary construction only.
Any executor response still enters `RETURNED_UNVALIDATED` before the OS
validator can consider completion.
