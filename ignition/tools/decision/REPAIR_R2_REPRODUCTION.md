# DECISION-INTEGRITY repair-r2 — R0 controlled reproduction (RB09-DIRECT-PREDECESSOR-BINDING)

## Scope
Checkpoint 2 of the B09 repair-r2 build train. Inherits the fail-closed shared
engine from `repair-r2/symbolic-sphere-r2-shared-engine-hardening` via a
`--no-ff` double-parent merge. This checkpoint closes
**RB09-DIRECT-PREDECESSOR-BINDING** for DECISION-INTEGRITY.

## Defect under reproduction (pre-fix)
Before repair, the wrapper `CONFIG['parent_head']` was bound to the stale
pre-repair predecessor head `213dced90f1e9b1f1992a148ee10fc0844917490`
(agent/symbolic-sphere-i1) instead of the real SYMBOLIC-SPHERE repair-r2 head.
The shared engine (now fail-closed) correctly validates git-object binding and
evidence, but the `parent_binding` check only compared the bundle's
`parent_binding.exact_head` against the (wrong) `CONFIG['parent_head']`. So a
bundle bound to the wrong i1 head was accepted (exit 0) — the direct-predecessor
binding was not enforced against the real repair-r2 head.

## Reproduction fixture
- `data/decision/repair-r2-controlled-reproduction.json` — the pilot bundle
  re-bound to the WRONG predecessor head `213dced90f…` (i1). Pre-fix this is
  accepted; post-fix it is rejected with `PARENT_BINDING_INVALID` (exit 3).

## Controlled negative classes (shared engine, inherited)
Absolute path, `..` traversal, backslash, symlink escape, fabricated exact head,
omitted mandatory git-object field, tampered commit/path/blob/sha256, and
caller-asserted `facts=true` / `status=PASS` are all rejected by the inherited
engine. These are covered by `tests/test_structured_capability_gate.py` (10/10)
and the per-checkpoint repair-r2 contract test.

## Boundary
Repository candidate only. No external action, no truth-layer upgrade, no Main
modification, no repair-r1 head/tag/PR mutation. Every evidence byte is resolved
against a real Git blob; the working tree is never authoritative.
