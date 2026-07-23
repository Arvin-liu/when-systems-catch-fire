# SCIENTIFIC-CONTEXT-PROTOCOL repair-r2 — R0 controlled reproduction (RB09-DIRECT-PREDECESSOR-BINDING)

## Scope
Checkpoint 10 of the B09 repair-r2 build train. Inherits the fail-closed shared
engine from `repair-r2/q44-r2-consent-semantics` via a `--no-ff` double-parent merge. Closes
**RB09-DIRECT-PREDECESSOR-BINDING** for SCIENTIFIC-CONTEXT-PROTOCOL.

## Defect under reproduction (pre-fix)
Before repair, `CONFIG['parent_head']` was bound to the stale prior-repair head
`4d15ccaf2e574248c0e224c05716c3af46203a39` instead of the real predecessor repair-r2 head `7532b4b34cf841c09faab8c835c5fc7f896d30d8`. The shared
engine validates git-object binding and evidence, but the `parent_binding` check only
compared the bundle's `parent_binding.exact_head` against the (wrong) `CONFIG['parent_head']`.
A bundle bound to the wrong predecessor was accepted (exit 0).

## Reproduction fixture
- `data/context_protocol/repair-r2-controlled-reproduction.json` — the pilot bundle re-bound to the WRONG
  predecessor head `4d15ccaf2e574248c0e224c05716c3af46203a39`. Pre-fix accepted; post-fix rejected with `PARENT_BINDING_INVALID`.

## Boundary
Repository candidate only. No external action, no truth-layer upgrade, no Main modification,
no repair-r1 head/tag/PR mutation. Every evidence byte resolves against a real Git blob.
