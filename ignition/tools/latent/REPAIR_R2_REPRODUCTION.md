# F15-D1 repair-r2 — R0 controlled reproduction (RB09-DIRECT-PREDECESSOR-BINDING)

## Scope
Checkpoint 5 of the B09 repair-r2 build train. Inherits the fail-closed shared
engine from `repair-r2/q41-r2-anomaly-semantics` via a `--no-ff` double-parent merge. Closes
**RB09-DIRECT-PREDECESSOR-BINDING** for F15-D1.

## Defect under reproduction (pre-fix)
Before repair, `CONFIG['parent_head']` was bound to the stale prior-repair head
`da9c4e2a6b8c0f757aa676814fda7c86d4ac2558` instead of the real predecessor repair-r2 head `e92e7d3eadbb67da288077052f635e3c052bd3a1`. The shared
engine validates git-object binding and evidence, but the `parent_binding` check only
compared the bundle's `parent_binding.exact_head` against the (wrong) `CONFIG['parent_head']`.
A bundle bound to the wrong predecessor was accepted (exit 0).

## Reproduction fixture
- `data/latent/repair-r2-controlled-reproduction.json` — the pilot bundle re-bound to the WRONG
  predecessor head `da9c4e2a6b8c0f757aa676814fda7c86d4ac2558`. Pre-fix accepted; post-fix rejected with `PARENT_BINDING_INVALID`.

## Boundary
Repository candidate only. No external action, no truth-layer upgrade, no Main modification,
no repair-r1 head/tag/PR mutation. Every evidence byte resolves against a real Git blob.
