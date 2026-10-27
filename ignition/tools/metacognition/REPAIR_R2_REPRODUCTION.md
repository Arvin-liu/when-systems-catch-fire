# SCIENTIFIC-METACOGNITION repair-r2 — R0 controlled reproduction (RB09-DIRECT-PREDECESSOR-BINDING)

## Scope
Checkpoint 3 of the B09 repair-r2 build train. Inherits the fail-closed shared
engine from `repair-r2/decision-integrity-r2-parent-and-semantics` via a `--no-ff` double-parent merge. Closes
**RB09-DIRECT-PREDECESSOR-BINDING** for SCIENTIFIC-METACOGNITION.

## Defect under reproduction (pre-fix)
Before repair, `CONFIG['parent_head']` was bound to the stale prior-repair head
`b3f27e4c3d614b95af4b112e3564fcf0e3d9f68e` instead of the real predecessor repair-r2 head `1a51d1b3fd1bab4eb1c80a7429e0b629bcae69a9`. The shared
engine validates git-object binding and evidence, but the `parent_binding` check only
compared the bundle's `parent_binding.exact_head` against the (wrong) `CONFIG['parent_head']`.
A bundle bound to the wrong predecessor was accepted (exit 0).

## Reproduction fixture
- `data/metacognition/repair-r2-controlled-reproduction.json` — the pilot bundle re-bound to the WRONG
  predecessor head `b3f27e4c3d614b95af4b112e3564fcf0e3d9f68e`. Pre-fix accepted; post-fix rejected with `PARENT_BINDING_INVALID`.

## Boundary
Repository candidate only. No external action, no truth-layer upgrade, no Main modification,
no repair-r1 head/tag/PR mutation. Every evidence byte resolves against a real Git blob.
