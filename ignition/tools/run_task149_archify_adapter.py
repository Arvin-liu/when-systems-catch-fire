#!/usr/bin/env python3
"""Build a derived Archify architecture IR from Ignition canonical projections.

This adapter intentionally owns no architecture semantics.  It copies only the
canonical nodes/edges as typed derived data, records both input fingerprints,
and leaves Archify validation/delivery to the pinned external checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ITERATION_DIR = ROOT / "data/operations/iterations/149"
DEFAULT_ARCHITECTURE = ROOT / "data/architecture/overall-architecture.json"
DEFAULT_SYSTEM_MAP = ROOT / "data/architecture/interactive-system-map.json"
DEFAULT_IR = ITERATION_DIR / "archify-typed-ir-r0.json"
DEFAULT_RECEIPT = ITERATION_DIR / "step05-archify-adapter-ir-receipt.json"

FORMAL_BASELINE = "14c2595d796494286caf31378173fd9dd027edcf"
FORMAL_PREVIOUS_COMMIT = "a051ad31b72d5cbb8deeaf2007b0e09431f8a4ba"
ARCHIFY_REVISION = "2bfb47132c057195d8dddb3e25ae966dd7c7a72e"
ARCHIFY_SCHEMA_SHA = "8c96140b6af8d93fb825a3c63e46b74176c9485185c978074ffe89e0f614576c"

GROUP_TYPES = {
    "sources": "external",
    "claims": "backend",
    "governance": "security",
    "execution": "backend",
    "validation": "backend",
    "human": "frontend",
    "publication": "external",
    "navigation": "frontend",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_ir(architecture: dict[str, Any], system_map: dict[str, Any], formal_revision: str) -> dict[str, Any]:
    groups = {group["id"]: group for group in architecture["groups"]}
    components = []
    group_indices: dict[str, int] = {}
    for node in architecture["nodes"]:
        group_id = node["group"]
        group = groups[group_id]
        index = group_indices.get(group_id, 0)
        group_indices[group_id] = index + 1
        components.append(
            {
                "id": node["id"],
                "type": GROUP_TYPES[group_id],
                "label": node["label"],
                "sublabel": group["label"],
                "tag": "CANONICAL_DERIVED_PROJECTION",
                "sources": [{"path": node["target"], "label": "canonical target"}],
                "row": int(group["row"]) * 4 + index,
                "col": int(group["column"]),
            }
        )

    valid_ids = {component["id"] for component in components}
    connections = []
    for index, edge in enumerate(architecture["edges"], start=1):
        if edge["source"] not in valid_ids or edge["target"] not in valid_ids:
            raise ValueError(f"canonical edge endpoint is not a component: {edge}")
        connections.append(
            {
                "id": f"canonical-edge-{index:02d}",
                "from": edge["source"],
                "to": edge["target"],
                "label": edge["label"],
                "variant": "default",
                "route": "auto",
            }
        )

    boundaries = []
    for group_id, group in groups.items():
        boundaries.append(
            {
                "kind": "region",
                "label": group["label"],
                "wraps": [node["id"] for node in architecture["nodes"] if node["group"] == group_id],
                "pad": 24,
            }
        )

    return {
        "schema_version": 1,
        "diagram_type": "architecture",
        "meta": {
            "title": architecture["title"],
            "locale": "zh-CN",
            "subtitle": "Derived visualization from Ignition canonical architecture and current interactive map; not architecture truth.",
            "output": "task149-archify-derived",
            "quality_profile": "showcase",
            "repository": {"url": architecture["repository_url"], "revision": formal_revision},
            "viewBox": [1440, 1040],
        },
        "layout": {
            "mode": "grid",
            "origin": [56, 56],
            "cols": 4,
            "gapX": 72,
            "gapY": 24,
            "cellW": 252,
            "cellH": 72,
        },
        "boundaries": boundaries,
        "components": components,
        "connections": connections,
    }


def build_receipt(
    architecture_path: Path,
    system_map_path: Path,
    ir_path: Path,
    ir: dict[str, Any],
    formal_revision: str,
) -> dict[str, Any]:
    system_map = read_json(system_map_path)
    return {
        "schema_version": "ignition-149-step05-archify-adapter-ir-r0",
        "task_id": "IGNITION-20260831-149",
        "step": "05",
        "status": "IR_GENERATED",
        "provider_id": "archify",
        "provider_class": "DERIVED_VISUALIZATION_PROVIDER",
        "formal_previous_commit": FORMAL_PREVIOUS_COMMIT,
        "formal_baseline_sha": formal_revision,
        "upstream_revision": ARCHIFY_REVISION,
        "upstream_schema_surface": {
            "path": "archify/schemas/architecture.schema.json",
            "sha256": ARCHIFY_SCHEMA_SHA,
            "source_remains_external": True,
        },
        "upstream_update_awareness": {
            "command": "node scripts/check-update.mjs",
            "status": "CURRENT_SILENT",
            "output": "{\"status\":\"silent\",\"reason\":\"current\"}",
            "recorded_separately_from_adapter_network": True,
        },
        "source_inputs": [
            {
                "path": "ignition/data/architecture/overall-architecture.json",
                "role": "canonical_architecture_input",
                "sha256": sha256(architecture_path),
                "status": "CURRENT_CANONICAL_SOURCE",
            },
            {
                "path": "ignition/data/architecture/interactive-system-map.json",
                "role": "current_system_map_context_and_cross_check",
                "sha256": sha256(system_map_path),
                "status": "CURRENT_CANONICAL_SOURCE",
                "map_version": system_map["map_version"],
            },
        ],
        "adapter": {
            "script": "ignition/tools/run_task149_archify_adapter.py",
            "algorithm": "CANONICAL_GROUPS_NODES_EDGES_TO_ARCHIFY_COMPONENTS_CONNECTIONS",
            "source_copy_or_vendor": False,
            "provider_output_can_update_canonical_truth": False,
        },
        "typed_ir": {
            "path": "ignition/data/operations/iterations/149/archify-typed-ir-r0.json",
            "sha256": sha256(ir_path),
            "schema_version": ir["schema_version"],
            "diagram_type": ir["diagram_type"],
            "component_count": len(ir["components"]),
            "connection_count": len(ir["connections"]),
            "boundary_count": len(ir["boundaries"]),
        },
        "adapter_structural_validation": {
            "status": "PASS",
            "checks": [
                "all canonical architecture nodes became typed components",
                "all canonical architecture edges became typed connections",
                "all connection endpoints resolve to typed components",
                "all group boundaries wrap only typed components",
                "canonical source paths and formal revision are retained in IR metadata",
            ],
        },
        "archify_external_validation": {
            "status": "PENDING_STEP06",
            "validation_receipt": "NOT_YET_CREATED",
            "delivery_receipt": "NOT_YET_CREATED",
            "visual_check": "NOT_YET_RUN",
        },
        "boundary": {
            "flow": "IGNITION_CANONICAL_DATA -> ADAPTER -> ARCHIFY_TYPED_IR",
            "provider_role": "DERIVED_VISUALIZATION_PROVIDER",
            "side_effect_class": "DERIVED_ARTIFACT_ONLY",
            "network_used_by_adapter": False,
            "authentication_used": False,
            "permission_granted": False,
            "current_integration": "NOT_CURRENT_INTEGRATION",
            "live_external_invocation": "UNCHANGED_OPEN_OWNER_DEFERRED",
        },
        "claim_ceiling": "The adapter deterministically generated a typed Archify-shaped IR from the recorded Ignition canonical inputs in this repository revision. It does not establish Archify validation/delivery success, visual usefulness, architecture truth, Current integration, production readiness, authenticated-channel admission or external truth.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--architecture", type=Path, default=DEFAULT_ARCHITECTURE)
    parser.add_argument("--system-map", type=Path, default=DEFAULT_SYSTEM_MAP)
    parser.add_argument("--ir", type=Path, default=DEFAULT_IR)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--formal-revision", default=FORMAL_BASELINE)
    args = parser.parse_args()
    if not args.write:
        parser.error("--write is required")
    architecture = read_json(args.architecture)
    system_map = read_json(args.system_map)
    ir = build_ir(architecture, system_map, args.formal_revision)
    args.ir.parent.mkdir(parents=True, exist_ok=True)
    args.ir.write_text(json.dumps(ir, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = build_receipt(args.architecture, args.system_map, args.ir, ir, args.formal_revision)
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"TASK149_STEP05_ARCHIFY_IR_WRITTEN components={len(ir['components'])} connections={len(ir['connections'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
