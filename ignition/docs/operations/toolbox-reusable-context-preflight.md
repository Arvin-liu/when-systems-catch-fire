# Cross-task reusable context preflight

`knowledge.preflight_reusable_context@0.2.0` checks caller-selected derived context cards before a task reuses them. It requires the source identity, declared version, SHA-256 digest, and access-scope identifier to match the caller's current source snapshot. For eligible local files under `ignition/`, it independently hashes the current bytes before returning the derived text.

The legacy R0 request remains supported and has no expiry field or time-freshness check. R1 requires a caller-supplied canonical UTC `expires_at_utc` on every cache card. At the start of an R1 run, the tool records the local system clock in UTC; an expiry at or before that instant invalidates the card before any source file is read. A future expiry permits the existing byte, version, and access-scope checks to run. The tool reports the observed time and expiry with the decision. It does not define a default TTL: the caller supplies the expiry policy for each task.

The tool does not discover sources, create or persist cards, judge semantic relevance, authenticate a permission grant, or establish evidence sufficiency. The `access_state`, `authorized`, and expiry policy are caller-attested inputs; the system clock is observed but not authenticated. If a task requires raw, current, freshness-sensitive, or full-text evidence, the tool returns no derived card and lists authorized raw sources to reopen. Returned text is always labelled `DERIVED_CONTEXT_ONLY`. R0 must not be used to satisfy a task that requires time-based invalidation.

## Run

```sh
python3 -B ignition/tools/toolbox_reusable_context_preflight.py --stdin < request.json
```

R0 uses `schemas/operations/toolbox-reusable-context-preflight-r0.schema.json` and `schemas/operations/toolbox-reusable-context-preflight-result-r0.schema.json`. R1 uses `schemas/operations/toolbox-reusable-context-preflight-r1.schema.json` and `schemas/operations/toolbox-reusable-context-preflight-result-r1.schema.json`. Both accept caller-selected cache cards and a current source snapshot. The tool reads only exact source paths under the checked-out `ignition/` tree, rejects symlinks and traversal, caps each source at 1,000,000 bytes and total source reads at 5,000,000 bytes, and caps returned context at the caller's budget (maximum 16,384 UTF-8 bytes).

## Decisions and limits

- `REUSE` means byte digests and caller-declared version/scope fields matched for every source binding. It does not mean the derived summary is correct or relevant.
- R1 `INVALIDATE` with reason `MEMORY_CARD_EXPIRED` means the caller-declared expiry was at or before the observed local system clock. No source bytes are read for that card; the time, expiry, and any caller-attested active/authorized refresh candidates are returned. This is not a claim that the clock or expiry policy is correct.
- `INVALIDATE` means at least one source is missing, changed, inaccessible, or bound to a different scope. Changed accessible sources are listed as refresh candidates; the tool does not refresh or store a card.
- `SKIP` means the caller requires raw sources or the context budget would be exceeded. Raw-source tasks must use a separate source-reading or evidence tool.
- The cache is supplied by the caller on stdin and remains the caller's responsibility to store, update, or delete. The tool has no default route and performs no write, network, credential, billing, or external action.

Focused tests: `python3 -B -m unittest ignition.tests.test_toolbox_reusable_context_preflight` and `python3 -B -m unittest ignition.tests.test_toolbox_routing ignition.tests.test_toolbox_identity_cards`. The task-specific expiry comparison is recorded in `data/operations/toolbox-reusable-context-expiry-c1-evidence-r0.json`; its overall replacement/portfolio status remains `COMPARISON_UNKNOWN`.
