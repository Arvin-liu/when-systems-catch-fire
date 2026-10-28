# Q43 repair-r2 — R0 controlled reproduction (RB09-DIRECT-PREDECESSOR-BINDING)

## Scope
Checkpoint 8 of the B09 repair-r2 build train. Inherits the fail-closed shared
engine from `repair-r2/q42-r2-counterfactual-semantics` via a `--no-ff` double-parent merge. Closes
**RB09-DIRECT-PREDECESSOR-BINDING** for Q43.

## Defect under reproduction (pre-fix)
Before repair, `CONFIG['parent_head']` was bound to the stale prior-repair head
`2f7777b26e1d52c5e6fff44fbf3d079cb38bdb98` instead of the real predecessor repair-r2 head `3283ef6e76788b30a467467083f0d5ad7086b5a0`. The shared
engine validates git-object binding and evidence, but the `parent_binding` check only
compared the bundle's `parent_binding.exact_head` against the (wrong) `CONFIG['parent_head']`.
A bundle bound to the wrong predecessor was accepted (exit 0).

## Reproduction fixture
- `data/escalation/repair-r2-controlled-reproduction.json` — the pilot bundle re-bound to the WRONG
  predecessor head `2f7777b26e1d52c5e6fff44fbf3d079cb38bdb98`. Pre-fix accepted; post-fix rejected with `PARENT_BINDING_INVALID`.

## Boundary
Repository candidate only. No external action, no truth-layer upgrade, no Main modification,
no repair-r1 head/tag/PR mutation. Every evidence byte resolves against a real Git blob.
