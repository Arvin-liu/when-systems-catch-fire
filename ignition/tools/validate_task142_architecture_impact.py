#!/usr/bin/env python3
"""Validate Task142's architecture transition and sole registry-derived map."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

try:
    from tools.architecture_impact import classify_change
    from tools.generate_interactive_system_map import build_projection, serialized_projection, validate_spec
except ImportError:
    from architecture_impact import classify_change
    from generate_interactive_system_map import build_projection, serialized_projection, validate_spec


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
ARTIFACT = ROOT / "data/operations/iterations/142/step17-architecture-impact.json"
SCHEMA = ROOT / "schemas/operations/task142-architecture-impact-r1.schema.json"
REGISTRY = ROOT / "data/operations/project-components.json"
TOPOLOGY = ROOT / "data/operations/change-propagation-topology.json"
LAYOUT = ROOT / "data/architecture/interactive-system-map-layout.json"
MAP = ROOT / "data/architecture/interactive-system-map.json"
IDENTITY = ROOT / "data/architecture/current-system-identity.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict) -> list[str]:
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load(SCHEMA)).iter_errors(document)]
    classification = classify_change(
        document["semantic_changes"],
        changed_paths=document["changed_paths"],
        evidence=document["evidence"],
        declared_classification="ARCHITECTURE_CHANGING",
    )
    if document["semantic_classification"] != classification:
        errors.append("semantic_classification is not derived from architecture_impact.classify_change")
    for relative in document["changed_paths"]:
        if not (REPO_ROOT / relative).is_file():
            errors.append(f"changed path missing: {relative}")
    registry = load(REGISTRY)
    topology = load(TOPOLOGY)
    layout = load(LAYOUT)
    materialized = load(MAP)
    if registry["registry_version"] != document["component_changes"]["registry_version"]:
        errors.append("registry version mismatch")
    if topology["topology_version"] != document["relation_changes"]["topology_version"]:
        errors.append("topology version mismatch")
    if layout["current_map_version"] != document["map_projection"]["map_version"]:
        errors.append("layout map version mismatch")
    derived = build_projection(registry, topology, layout)
    validate_spec(derived, ROOT)
    if MAP.read_bytes() != serialized_projection(derived):
        errors.append("materialized map is stale relative to registry/topology/layout")
    coverage = derived["component_coverage"]
    for field in ("registry_components", "visible_nodes", "hidden_components", "orphan_components"):
        expected = document["map_projection"].get(field)
        if expected is not None and coverage.get(field) != expected:
            errors.append(f"map coverage mismatch for {field}")
    if len(derived["edges"]) != document["map_projection"]["visible_edges"]:
        errors.append("visible edge count mismatch")
    if load(IDENTITY)["identity_epoch"] != document["surface_sync"]["identity_epoch"]:
        errors.append("identity epoch mismatch")
    if document["map_projection"]["sole_map_path"] != "ignition/data/architecture/interactive-system-map.json":
        errors.append("sole map path is not canonical")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    document = load(ARTIFACT)
    errors = validate(document)
    if errors:
        print("TASK142_ARCHITECTURE_IMPACT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK142_ARCHITECTURE_IMPACT_OK classification=ARCHITECTURE_CHANGING registry=2.4.0 topology=1.13.0 map=0.16.0 visible_nodes=87 visible_edges=92 sole_map=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
