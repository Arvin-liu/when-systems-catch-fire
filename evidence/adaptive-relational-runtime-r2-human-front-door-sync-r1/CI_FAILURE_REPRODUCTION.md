# CI Failure Reproduction — ARR R2 Human-Front-Door Sync Repair R1

## Trigger
- **Pointer:** `instructions/NEXT-CLUSTER-CURRENT-ARR-R2-HUMAN-FRONT-DOOR-SYNC-REPAIR-R1.md`
- **IGNITION:** `instructions/IGNITION-ARR-R2-HUMAN-FRONT-DOOR-SYNC-REPAIR-R1-2026-07-25.md`
- **Predecessor head:** `5771d6c1174cc5c3ae72d1441c1c26b49951d79b` (`repair/adaptive-relational-runtime-r2-positive-routing-ci-r1`, PR #123)
- **Failed remote run:** `30143814302` (job `89641879479`, `foundation-validation`)
- **Child branch:** `repair/adaptive-relational-runtime-r2-human-front-door-sync-r1` (this branch)
- **Draft PR (target):** #124, base `repair/adaptive-relational-runtime-r2-positive-routing-ci-r1`

## Exact failure (no guessing — from the complete remote job log)
Remote log `REMOTE_CI_JOB_LOG_30143814302.txt` (929 lines):
- Line 719: `{"...interactive_system_map_nodes": 100, ... "status": "PASS"}` — the
  human-front-door validator `validate_all()` itself passes and reports **100** nodes.
- Lines 896–906: the unittest `tests/test_human_front_door.py` raises
  `AssertionError: 100 != 99` at line 101:
  ```python
  self.assertEqual(result["interactive_system_map_nodes"], 99)
  ```

## Local reproduction (detached HEAD on predecessor `5771d6c`)
```
python3 -m unittest tests.test_human_front_door -v
...
test_system_map_has_all_clickable_nodes_and_no_l7_layer ... FAIL
AssertionError: 100 != 99
```
Reproduced byte-for-byte against the remote failure. The validator computes
`interactive_system_map_nodes = len(spec["nodes"])` from `build_projection()`
(the canonical projection), which yields **100** on the unmodified predecessor.

## Root-cause classification
- The discrepancy is **NOT** a data defect. The canonical node set is genuinely 100
  (see `CANONICAL_NODE_IDENTITY_AUDIT.md`).
- The failure is a **stale, hand-maintained count literal** (`99`) in the unittest.
  The inline comment (summing to 63) is already internally inconsistent with the
  asserted 99, proving the literal is drift-prone and was never reconciled when the
  registry grew to 100 visible components.
- The validator's own `required_nodes` set in `tools/validate_human_front_door.py`
  was correctly maintained to 100 and matches the spec exactly, which is why
  `validate_system_map()` passes in CI while only the unittest literal fails.

## Scope boundary
This repair addresses **only** the brittle `== 99` literal. It does not touch the
canonical registries, the generator, Main, PR #109–#123, or any R3/corpus path.
