# D2 repair-r2 — R0 controlled reproduction (RB09-DIRECT-PREDECESSOR-BINDING)

## Scope
Checkpoint 6 of the B09 repair-r2 build train. Inherits the fail-closed shared
engine from `repair-r2/f15-d1-r2-identifiability-semantics` via a `--no-ff` double-parent merge. Closes
**RB09-DIRECT-PREDECESSOR-BINDING** for D2.

## Defect under reproduction (pre-fix)
Before repair, `CONFIG['parent_head']` was bound to the stale prior-repair head
`f0f7d7ff9dda620d59ad1dd1b504bcd503fe5c09` instead of the real predecessor repair-r2 head `95405ae791dc0359c2ab6597bfd7c50224c2c59c`. The shared
engine validates git-object binding and evidence, but the `parent_binding` check only
compared the bundle's `parent_binding.exact_head` against the (wrong) `CONFIG['parent_head']`.
A bundle bound to the wrong predecessor was accepted (exit 0).

## Reproduction fixture
- `data/multihistory/repair-r2-controlled-reproduction.json` — the pilot bundle re-bound to the WRONG
  predecessor head `f0f7d7ff9dda620d59ad1dd1b504bcd503fe5c09`. Pre-fix accepted; post-fix rejected with `PARENT_BINDING_INVALID`.

## Boundary
Repository candidate only. No external action, no truth-layer upgrade, no Main modification,
no repair-r1 head/tag/PR mutation. Every evidence byte resolves against a real Git blob.
