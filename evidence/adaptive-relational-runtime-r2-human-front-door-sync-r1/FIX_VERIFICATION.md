# Fix Verification — ARR R2 Human-Front-Door Sync Repair R1

## Repair applied (commit 2)
- `tests/test_human_front_door.py::test_system_map_has_all_clickable_nodes_and_no_l7_layer`
  replaced the brittle `assertEqual(result["interactive_system_map_nodes"], 99)` with a
  **drift-resistant canonical node-set gate**:
  - Derives `expected_ids` INDEPENDENTLY from `data/operations/project-components.json`
    (`map_projection.visible`) and cross-checks `data/architecture/interactive-system-map-layout.json`
    (`node_order`). This is an independent path from the validator's hardcoded `required_nodes`.
  - Asserts **exact node identity** (`actual_ids == expected_ids`), not a bare count.
  - Retains the explicit **no-`l7`** assertion.
  - Fails on **missing / extra / orphan / duplicate / non-clickable / `l7`**.
  - Binds `result["interactive_system_map_nodes"]` to `len(expected_ids)`.
- `tests/adaptive_relational_runtime/test_r2_positive_routing_repair.py`: generalized the
  branch-family assertion from the strict `positive-routing` sub-family to the R2 repair
  family prefix `repair/adaptive-relational-runtime-r2-` (two sites). This repair runs on the
  sibling R2 child branch `human-front-door-sync-r1`, so the suite must be portable across R2
  repair sub-branches. Still rejects main / feature / PR merge refs. Test-only; no ARR runtime
  change, so the 48/48 positive semantics digest is preserved.

## Why not a blind 99 → 100
The 100th node was proven legitimate (see `CANONICAL_NODE_IDENTITY_AUDIT.md`): registry,
layout, and generator agree on exactly 100 real, visible, registered components — no
duplicate, orphan, hidden-without-representative, or `l7` node. The gate therefore derives the
count from the registry rather than pinning a number, so it cannot silently drift.

## Artifact regeneration
Canonical data did **not** change (registry already declared 100 visible components; layout
already declared the same 100; materialized spec already 100). `generate_interactive_system_map.py
--check` reports `SYSTEM_MAP_DERIVED_OK nodes=100 edges=45`, so no artifact regeneration was
required.

## Local verification (all green)
- `python3 -m unittest tests.test_human_front_door` → 15 tests OK (incl. the new gate).
- `python3 -m pytest tests/adaptive_relational_runtime/ -q` → 183 passed.
- `python3 tools/generate_interactive_system_map.py --check` → SYSTEM_MAP_DERIVED_OK nodes=100.
- `python3 tools/validate_human_front_door.py` → status PASS, interactive_system_map_nodes=100.
- `python3 tools/validate_iteration_sync.py` → status PASS (closure PASS).
- `python3 -m unittest tests.test_pages_deploy_gate` → 6 tests OK.

## Guardrail ledger (all 0)
`WAIC_FULL_CORPUS_RUNS=0`, `R3_STARTED=0`, `REAL_WORLD_ACTIONS=0`, `FORMAL_ASSETS_PROMOTED=0`,
`AUTO_EVOLVE_STARTED=0`, `FORMAL_READY_PRS=0`, `FORMAL_MERGES=0`, `MAIN_CHANGES=0`,
`FORCE_PUSHES=0`, `HISTORY_REWRITES=0`, `EXTERNAL_ACCEPTANCE_CLAIMED=0`. No R3 / Ready / merge /
Main change / force push / PROMOTE / EVOLVE.
