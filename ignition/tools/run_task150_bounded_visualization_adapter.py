#!/usr/bin/env python3
"""Build the Task150 bounded Archify architecture candidate.

The adapter is deliberately a projection of the authored overall-architecture
source.  Its only Task150-specific change is a documented, deterministic
geometry repair: horizontal spacing is widened, vertical coordinates are
compressed, and the authored viewBox is widened/shortened so the Delta review
surface can fit its required desktop viewports.  Node/edge identity, labels,
boundaries and semantics remain copied from the canonical source.

Archify remains an external derived-artifact provider.  This script does not
scan the repository for topology, write canonical data, install dependencies
or perform any external action.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.run_task149_archify_adapter import build_ir, read_json


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ITERATION_DIR = ROOT / "data/operations/iterations/150"
DEFAULT_ARCHITECTURE = ROOT / "data/architecture/overall-architecture.json"
DEFAULT_SYSTEM_MAP = ROOT / "data/architecture/interactive-system-map.json"
DEFAULT_IR = ITERATION_DIR / "task150-archify-typed-ir-r1.json"

X_SCALE = 1.0
Y_SCALE = 0.54
Y_OFFSET = 12
REPAIRED_VIEWBOX = [1650, 420]
REPAIRED_COMPONENT_SIZE = [190, 28]


def project_point(point: list[int | float]) -> list[int]:
    return [round(float(point[0]) * X_SCALE), round(float(point[1]) * Y_SCALE + Y_OFFSET)]


def repair_geometry(ir: dict[str, Any]) -> dict[str, Any]:
    repaired = json.loads(json.dumps(ir))
    for component in repaired["components"]:
        component["pos"] = project_point(component["pos"])
        component["size"] = list(REPAIRED_COMPONENT_SIZE)
        position_overrides = {
            "source-history": 218,
            "source-evidence": 145,
            "claim-foundation": 80,
            "governance-charter": 102,
            "governance-k13": 60,
            "execution-iteration": 60,
            "execution-obligations": 36,
            "execution-reos": 93,
            "governance-state": 328,
            "navigation-machine": 282,
            "navigation-map": 366,
        }
        if component["id"] in position_overrides:
            component["pos"][1] = position_overrides[component["id"]]
        if component["id"] in {"governance-state", "navigation-machine"}:
            component["pos"][0] = 740
        if component["id"] == "navigation-map":
            component["pos"][0] = 1050
    route_via_overrides = {
        "canonical-edge-03": [[395, 198], [520, 198], [520, 237]],
        "canonical-edge-02": [[706, 159], [706, 131]],
        "canonical-edge-06": [[655, 275], [720, 275], [720, 130], [1100, 130], [1100, 91]],
        "canonical-edge-07": [[395, 78], [355, 78], [355, 104]],
        "canonical-edge-14": [[710, 131], [710, 207], [655, 207]],
        "canonical-edge-17": [[945, 292], [945, 400], [1340, 400], [1340, 194]],
        "canonical-edge-20": [[1145, 230], [800, 230], [800, 166]],
        "canonical-edge-24": [[1340, 300], [1340, 194]],
        "canonical-edge-12": [[1095, 50], [1095, 91]],
    }
    for connection in repaired["connections"]:
        if connection["id"] in route_via_overrides:
            connection["via"] = route_via_overrides[connection["id"]]
        elif "via" in connection:
            connection["via"] = [project_point(point) for point in connection["via"]]
        route_overrides = {
            "canonical-edge-02": "orthogonal-h",
            "canonical-edge-08": "straight",
            "canonical-edge-10": "auto",
        }
        if connection["id"] in route_overrides:
            connection["route"] = route_overrides[connection["id"]]
        if connection["id"] == "canonical-edge-02":
            connection["fromSide"] = "right"
            connection["toSide"] = "right"
        if connection["id"] == "canonical-edge-14":
            connection["labelAt"] = [620, 180]
        if "labelAt" in connection:
            connection["labelAt"] = project_point(connection["labelAt"])
        label_overrides = {
            "canonical-edge-01": [320, 312],
            "canonical-edge-02": [475, 190],
            "canonical-edge-09": [680, 320],
            "canonical-edge-07": [430, 52],
            "canonical-edge-11": [1040, 145],
            "canonical-edge-12": [1160, 118],
            "canonical-edge-23": [740, 324],
        }
        if connection["id"] in label_overrides:
            connection["labelAt"] = label_overrides[connection["id"]]
    repaired["meta"]["output"] = "task150-archify-bounded-derived-r1"
    repaired["meta"]["subtitle"] = (
        "Bounded derived visualization of Ignition authored topology; "
        "not architecture truth or a Current provider capability."
    )
    repaired["meta"]["viewBox"] = list(REPAIRED_VIEWBOX)
    return repaired


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--architecture", type=Path, default=DEFAULT_ARCHITECTURE)
    parser.add_argument("--system-map", type=Path, default=DEFAULT_SYSTEM_MAP)
    parser.add_argument("--ir", type=Path, default=DEFAULT_IR)
    parser.add_argument("--formal-revision", required=True)
    args = parser.parse_args()
    if not args.write:
        parser.error("--write is required")
    architecture = read_json(args.architecture)
    system_map = read_json(args.system_map)
    baseline = build_ir(architecture, system_map, args.formal_revision)
    ir = repair_geometry(baseline)
    args.ir.parent.mkdir(parents=True, exist_ok=True)
    args.ir.write_text(json.dumps(ir, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "TASK150_BOUNDED_VISUALIZATION_IR_WRITTEN "
        f"components={len(ir['components'])} connections={len(ir['connections'])} "
        f"viewBox={ir['meta']['viewBox']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
