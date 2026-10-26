# Cross-task reusable context preflight

`knowledge.preflight_reusable_context@0.1.0` checks caller-selected derived context cards before a task reuses them. It requires the source identity, declared version, SHA-256 digest, and access-scope identifier to match the caller's current source snapshot. For eligible local files under `ignition/`, it independently hashes the current bytes before returning the derived text.

The tool does not discover sources, create or persist cards, judge semantic relevance, authenticate a permission grant, or establish evidence sufficiency. The `access_state` and `authorized` fields are caller-attested inputs. If a task requires raw, current, freshness-sensitive, or full-text evidence, the tool returns no derived card and lists authorized raw sources to reopen. Returned text is always labelled `DERIVED_CONTEXT_ONLY`.

## Run

```sh
python3 -B ignition/tools/toolbox_reusable_context_preflight.py --stdin < request.json
```

The request schema is `schemas/operations/toolbox-reusable-context-preflight-r0.schema.json`; the result contract is `schemas/operations/toolbox-reusable-context-preflight-result-r0.schema.json`. The input must contain caller-selected cache cards and a current source snapshot. The tool reads only exact source paths under the checked-out `ignition/` tree, rejects symlinks and traversal, caps each source at 1,000,000 bytes and total source reads at 5,000,000 bytes, and caps returned context at the caller's budget (maximum 16,384 UTF-8 bytes).

## Decisions and limits

- `REUSE` means byte digests and caller-declared version/scope fields matched for every source binding. It does not mean the derived summary is correct or relevant.
- `INVALIDATE` means at least one source is missing, changed, inaccessible, or bound to a different scope. Changed accessible sources are listed as refresh candidates; the tool does not refresh or store a card.
- `SKIP` means the caller requires raw sources or the context budget would be exceeded. Raw-source tasks must use a separate source-reading or evidence tool.
- The cache is supplied by the caller on stdin and remains the caller's responsibility to store, update, or delete. The tool has no default route and performs no write, network, credential, billing, or external action.

Focused tests: `python3 -B -m unittest ignition.tests.test_toolbox_reusable_context_preflight` and `python3 -B -m unittest ignition.tests.test_toolbox_routing ignition.tests.test_toolbox_identity_cards`.
