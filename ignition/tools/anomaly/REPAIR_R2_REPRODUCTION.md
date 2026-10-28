# Q41 repair-r2 — R0 controlled reproduction (RB09-DIRECT-PREDECESSOR-BINDING)

## Scope
Checkpoint 4 of the B09 repair-r2 build train. Inherits the fail-closed shared
engine from `repair-r2/scientific-metacognition-r2-parent-and-semantics` via a `--no-ff` double-parent merge. Closes
**RB09-DIRECT-PREDECESSOR-BINDING** for Q41.

## Defect under reproduction (pre-fix)
Before repair, `CONFIG['parent_head']` was bound to the stale prior-repair head
`183f4343a036d0dbb20ae7df9dd96be97bcd3fc3` instead of the real predecessor repair-r2 head `25f937ea8d53b4b14f31fc9c8779995f3c516bac`. The shared
engine validates git-object binding and evidence, but the `parent_binding` check only
compared the bundle's `parent_binding.exact_head` against the (wrong) `CONFIG['parent_head']`.
A bundle bound to the wrong predecessor was accepted (exit 0).

## Reproduction fixture
- `data/anomaly/repair-r2-controlled-reproduction.json` — the pilot bundle re-bound to the WRONG
  predecessor head `183f4343a036d0dbb20ae7df9dd96be97bcd3fc3`. Pre-fix accepted; post-fix rejected with `PARENT_BINDING_INVALID`.

## Boundary
Repository candidate only. No external action, no truth-layer upgrade, no Main modification,
no repair-r1 head/tag/PR mutation. Every evidence byte resolves against a real Git blob.
