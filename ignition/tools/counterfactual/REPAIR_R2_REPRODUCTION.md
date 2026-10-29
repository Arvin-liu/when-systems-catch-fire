# Q42 repair-r2 — R0 controlled reproduction (RB09-DIRECT-PREDECESSOR-BINDING)

## Scope
Checkpoint 7 of the B09 repair-r2 build train. Inherits the fail-closed shared
engine from `repair-r2/d2-r2-multihistory-semantics` via a `--no-ff` double-parent merge. Closes
**RB09-DIRECT-PREDECESSOR-BINDING** for Q42.

## Defect under reproduction (pre-fix)
Before repair, `CONFIG['parent_head']` was bound to the stale prior-repair head
`1904628103d8c23133107d501a22e3f17d08221d` instead of the real predecessor repair-r2 head `ea447ed7f6331f8ed5e58526f4c2341d3a41d6a6`. The shared
engine validates git-object binding and evidence, but the `parent_binding` check only
compared the bundle's `parent_binding.exact_head` against the (wrong) `CONFIG['parent_head']`.
A bundle bound to the wrong predecessor was accepted (exit 0).

## Reproduction fixture
- `data/counterfactual/repair-r2-controlled-reproduction.json` — the pilot bundle re-bound to the WRONG
  predecessor head `1904628103d8c23133107d501a22e3f17d08221d`. Pre-fix accepted; post-fix rejected with `PARENT_BINDING_INVALID`.

## Boundary
Repository candidate only. No external action, no truth-layer upgrade, no Main modification,
no repair-r1 head/tag/PR mutation. Every evidence byte resolves against a real Git blob.
