# Q44 repair-r2 — R0 controlled reproduction (RB09-DIRECT-PREDECESSOR-BINDING)

## Scope
Checkpoint 9 of the B09 repair-r2 build train. Inherits the fail-closed shared
engine from `repair-r2/q43-r2-escalation-semantics` via a `--no-ff` double-parent merge. Closes
**RB09-DIRECT-PREDECESSOR-BINDING** for Q44.

## Defect under reproduction (pre-fix)
Before repair, `CONFIG['parent_head']` was bound to the stale prior-repair head
`5efbce81e96d90d5ebd246891e4762928365d6b8` instead of the real predecessor repair-r2 head `e5181c83efba68f847b55e13c7b5a1ee1fd6888e`. The shared
engine validates git-object binding and evidence, but the `parent_binding` check only
compared the bundle's `parent_binding.exact_head` against the (wrong) `CONFIG['parent_head']`.
A bundle bound to the wrong predecessor was accepted (exit 0).

## Reproduction fixture
- `data/coaching/repair-r2-controlled-reproduction.json` — the pilot bundle re-bound to the WRONG
  predecessor head `5efbce81e96d90d5ebd246891e4762928365d6b8`. Pre-fix accepted; post-fix rejected with `PARENT_BINDING_INVALID`.

## Boundary
Repository candidate only. No external action, no truth-layer upgrade, no Main modification,
no repair-r1 head/tag/PR mutation. Every evidence byte resolves against a real Git blob.
