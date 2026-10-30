# Canonical Node-Identity Audit — Is the 100th node legitimate?

## Question
The interactive system map reports **100** nodes, but the unittest asserts **99**.
Is 100 correct, or is there a junk / duplicate / orphan / `l7` node inflating the count?
We do **not** assume either number is correct; we prove it from the canonical sources.

## Canonical sources of truth
- `tools/generate_interactive_system_map.py` → `build_projection()`:
  - `visible = {id for id,item in components if item["map_projection"]["visible"]}`
  - `ordered_ids` from `layout_doc["node_order"]` (top-level dict, keyed by group),
    with `require(set(ordered_ids) == visible)` — the layout MUST declare exactly the
    visible set.
  - `nodes` are built **only** from `ordered_ids`; no node identity is authored in the
    generator.
- `data/operations/project-components.json` (COMPONENT_REGISTRY) — `component_id`,
  `map_projection.visible`, `map_projection.group`, `lifecycle.status`.
- `data/architecture/interactive-system-map-layout.json` (LAYOUT_OVERLAY) — `node_order`.

## Measured facts (machine-checked)
```
registry total components           : 112
registry visible (canonical set)    : 100
layout node_order ids               : 100
build_projection() served node ids  : 100
visible == layout node_order?       : True
visible == served spec?             : True
layout == served spec?              : True
duplicate node ids in spec?         : False
l7 nodes in spec?                   : []
orphan nodes (no backing component)?: []
hidden components lacking rep?      : []
group distribution                  : front_doors:5, layers:7, core:2, models:4,
                                     operations:5, governance:61, writing:9,
                                     feedback:4, boundaries:3
```

## Conclusion
- The three independent views — registry `visible`, layout `node_order`, and the served
  `build_projection()` — are **identical** at exactly **100** node ids.
- There are **no duplicate ids**, **no `l7` layer**, and **no orphan nodes** (every node
  is a real `component_id` in the registry).
- Every hidden component has a visible representative (no malformed hidden entry).
- Therefore the **100th node is legitimate**: it is a real, visible, registered component
  that the layout overlay explicitly declares. The registry, the layout, and the generator
  all agree. **100 is correct; 99 is a stale hand-maintained literal.**

## Why the old test was drift-prone
`tests/test_human_front_door.py` line 101 asserted `== 99` against a comment that itself
sums to 63 — already internally inconsistent. A bare count can pass even if a junk node is
added or a legitimate node is dropped, as long as the total happens to match. The replacement
gate (see commit 2) compares **exact node identities** derived from the registry, so it
fails on any missing / extra / orphan / duplicate / non-clickable / `l7` condition.
