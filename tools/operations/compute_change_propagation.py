#!/usr/bin/env python3
"""Compute a fixpoint over declared project relations, not real-world causality."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator

try:
    from tools.generate_interactive_system_map import build_projection
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.generate_interactive_system_map import build_projection


ROOT = Path(__file__).resolve().parents[2]
COMPONENTS = ROOT / "data/operations/project-components.json"
TOPOLOGY = ROOT / "data/operations/change-propagation-topology.json"
SURFACES = ROOT / "data/operations/synchronization-surfaces.json"
REQUEST_SCHEMA = ROOT / "schemas/operations/change-propagation-request.schema.json"
CLOSURE_SCHEMA = ROOT / "schemas/operations/change-propagation-closure.schema.json"
COMPONENT_SCHEMA = ROOT / "schemas/operations/project-components.schema.json"
TOPOLOGY_SCHEMA = ROOT / "schemas/operations/change-propagation-topology.schema.json"
SURFACE_SCHEMA = ROOT / "schemas/operations/synchronization-surfaces.schema.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_json(document: dict, schema_path: Path, label: str) -> None:
    errors = sorted(Draft202012Validator(load_json(schema_path)).iter_errors(document), key=lambda item: list(item.path))
    require(not errors, f"{label} schema error: {errors[0].message if errors else ''}")


def canonical_hash(document: dict) -> str:
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def matches_pattern(path: str, pattern: str) -> bool:
    return path.startswith(pattern) if pattern.endswith("/") else path == pattern


def resolve_paths(paths: list[str], components: dict[str, dict]) -> tuple[set[str], list[dict]]:
    resolved: set[str] = set()
    residue: list[dict] = []
    for path in paths:
        hits = sorted(component_id for component_id, component in components.items() if any(matches_pattern(path, pattern) for pattern in component["path_patterns"]))
        if hits:
            resolved.update(hits)
        else:
            residue.append({"type": "unmapped_path", "path": path, "message": "Changed path has no canonical component mapping."})
    return resolved, residue


def relation_is_triggered(relation: dict, dimensions: set[str], classifications: set[str]) -> bool:
    dimension_ok = not relation["trigger_dimensions"] or bool(dimensions & set(relation["trigger_dimensions"]))
    classification_ok = not relation["trigger_classifications"] or bool(classifications & set(relation["trigger_classifications"]))
    return dimension_ok and classification_ok


def traverse_fixpoint(seed_components: set[str], topology: dict, dimensions: set[str], classifications: set[str]) -> tuple[set[str], list[dict], int, list[dict]]:
    resolved = set(seed_components)
    traversed: dict[str, dict] = {}
    iterations = 0
    while True:
        iterations += 1
        before = set(resolved)
        for relation in topology["relations"]:
            if relation["source"] not in resolved or not relation_is_triggered(relation, dimensions, classifications):
                continue
            if relation["propagation_mode"] == "informational_only":
                continue
            traversed[relation["relation_id"]] = {
                "relation_id": relation["relation_id"],
                "source": relation["source"],
                "target": relation["target"],
                "relation_class": relation["relation_class"],
                "relation_domain": relation["relation_domain"],
                "propagation_mode": relation["propagation_mode"],
                "creates_sync_obligation": relation["creates_sync_obligation"],
                "claim_ceiling": relation["claim_ceiling"],
            }
            resolved.add(relation["target"])
        if resolved == before:
            break
        require(iterations <= len(topology["relations"]) + 2, "propagation did not reach a bounded fixpoint")

    adjacency: dict[str, list[str]] = defaultdict(list)
    for path in traversed.values():
        adjacency[path["source"]].append(path["target"])
    cycle_residue: list[dict] = []
    visited: set[str] = set()
    active: list[str] = []

    def visit(node: str) -> None:
        if node in active:
            cycle = active[active.index(node):] + [node]
            item = {"type": "propagation_cycle", "path": cycle, "message": "Cycle requires explicit human adjudication; fixpoint reachability alone cannot close it."}
            if item not in cycle_residue:
                cycle_residue.append(item)
            return
        if node in visited:
            return
        active.append(node)
        for target in adjacency.get(node, []):
            visit(target)
        active.pop()
        visited.add(node)

    for seed in sorted(seed_components):
        visit(seed)
    return resolved, [traversed[key] for key in sorted(traversed)], iterations, cycle_residue


def derive_surfaces(surface_doc: dict, dimensions: set[str], classifications: set[str]) -> list[str]:
    surfaces = {item["surface_id"]: item for item in surface_doc["surfaces"]}
    required = {
        surface_id for surface_id, item in surfaces.items()
        if (dimensions & set(item["trigger_dimensions"]) or classifications & set(item["trigger_classifications"]))
    }
    while True:
        before = set(required)
        for surface_id in list(required):
            required.update(surfaces[surface_id]["derived_from"])
        for surface_id, item in surfaces.items():
            if set(item["derived_from"]) & required and (dimensions & set(item["trigger_dimensions"]) or classifications & set(item["trigger_classifications"])):
                required.add(surface_id)
        if required == before:
            return sorted(required)


def edge_key(edge: dict) -> str:
    return f"{edge['source']}->{edge['target']}"


def map_delta(base: dict, current: dict) -> dict:
    base_nodes = {item["id"]: item for item in base.get("nodes", [])}
    current_nodes = {item["id"]: item for item in current.get("nodes", [])}
    base_edges = {edge_key(item): item for item in base.get("edges", [])}
    current_edges = {edge_key(item): item for item in current.get("edges", [])}
    return {
        "base_map_version": base.get("map_version"),
        "candidate_map_version": current.get("map_version"),
        "added_nodes": sorted(set(current_nodes) - set(base_nodes)),
        "removed_nodes": sorted(set(base_nodes) - set(current_nodes)),
        "changed_nodes": sorted(key for key in set(base_nodes) & set(current_nodes) if base_nodes[key] != current_nodes[key]),
        "added_edges": sorted(set(current_edges) - set(base_edges)),
        "removed_edges": sorted(set(base_edges) - set(current_edges)),
        "changed_edges": sorted(key for key in set(base_edges) & set(current_edges) if base_edges[key] != current_edges[key]),
        "unmapped_residue": [],
    }


def git_json(revision: str, path: str) -> dict:
    completed = subprocess.run(["git", "show", f"{revision}:{path}"], cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def decisions_by_id(items: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for item in items:
        require(item["item_id"] not in result, f"duplicate decision: {item['item_id']}")
        require(item["decision"] != "NO_CHANGE_WITH_REASON" or item["reason"].strip(), f"NO_CHANGE lacks reason: {item['item_id']}")
        result[item["item_id"]] = item
    return result


def compute(request: dict, components_doc: dict | None = None, topology_doc: dict | None = None, surfaces_doc: dict | None = None, baseline_map: dict | None = None) -> tuple[dict, dict]:
    validate_json(request, REQUEST_SCHEMA, "propagation request")
    components_doc = components_doc or load_json(COMPONENTS)
    topology_doc = topology_doc or load_json(TOPOLOGY)
    surfaces_doc = surfaces_doc or load_json(SURFACES)
    validate_json(components_doc, COMPONENT_SCHEMA, "project component registry")
    validate_json(topology_doc, TOPOLOGY_SCHEMA, "change propagation topology")
    validate_json(surfaces_doc, SURFACE_SCHEMA, "synchronization surface registry")
    components = {item["component_id"]: item for item in components_doc["components"]}
    require(len(components) == len(components_doc["components"]), "duplicate component id")
    for relation in topology_doc["relations"]:
        require(relation["source"] in components and relation["target"] in components, f"relation references unknown component: {relation['relation_id']}")
        require(not (relation["relation_domain"] == "substantive_causal_candidate" and relation["propagation_mode"] == "automatic"), f"substantive causal candidate cannot auto-propagate: {relation['relation_id']}")

    path_seeds, residue = resolve_paths(request["changed_paths"], components)
    explicit = set(request.get("explicit_seed_components", []))
    unknown_explicit = sorted(explicit - set(components))
    residue.extend({"type": "unknown_seed_component", "component_id": item, "message": "Explicit seed is not registered."} for item in unknown_explicit)
    seed_components = path_seeds | (explicit & set(components))
    dimensions = set(request["changed_dimensions"])
    classifications = set(request["change_classifications"])
    resolved, typed_paths, iterations, cycle_residue = traverse_fixpoint(seed_components, topology_doc, dimensions, classifications)
    residue.extend(cycle_residue)
    required_components = sorted(resolved)
    required_surfaces = derive_surfaces(surfaces_doc, dimensions, classifications)
    component_decisions = decisions_by_id(request["component_decisions"])
    surface_decisions = decisions_by_id(request["surface_decisions"])
    for item in required_components:
        if item not in component_decisions:
            residue.append({"type": "missing_component_decision", "component_id": item, "message": "Resolved component lacks CHANGE/NO_CHANGE/NOT_APPLICABLE decision."})
    for item in required_surfaces:
        if item not in surface_decisions:
            residue.append({"type": "missing_surface_decision", "surface_id": item, "message": "Registry-derived surface lacks decision."})

    current_map = build_projection(components_doc, topology_doc, load_json(ROOT / "data/architecture/interactive-system-map-layout.json"))
    if baseline_map is None:
        try:
            baseline_map = git_json(request["base_identity"], "data/architecture/interactive-system-map.json")
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            baseline_map = {"nodes": [], "edges": []}
            residue.append({"type": "baseline_map_unavailable", "message": str(exc)})
    delta = map_delta(baseline_map, current_map)
    delta_exists = any(delta[key] for key in ("added_nodes", "removed_nodes", "changed_nodes", "added_edges", "removed_edges", "changed_edges", "unmapped_residue"))
    map_decision = request["system_map_decision"]
    if delta_exists and map_decision["decision"] != "CHANGE":
        residue.append({"type": "map_decision_mismatch", "message": "Map projection changed but decision is not CHANGE."})
    if not delta_exists and map_decision["decision"] == "CHANGE":
        residue.append({"type": "map_decision_mismatch", "message": "Map decision says CHANGE but projection has no delta."})
    system_map_impact = {"decision": map_decision["decision"], "reason": map_decision["reason"], **{key: delta[key] for key in ("added_nodes", "removed_nodes", "changed_nodes", "added_edges", "removed_edges", "changed_edges", "unmapped_residue")}}

    closure = {
        "closure_version": "1.0.0",
        "task_id": request["task_id"],
        "base_identity": request["base_identity"],
        "head_identity": request["head_identity"],
        "seed_paths": sorted(request["changed_paths"]),
        "seed_components": sorted(seed_components),
        "resolved_components": sorted(resolved),
        "typed_paths": typed_paths,
        "registry_derived_surfaces": required_surfaces,
        "required_component_decisions": required_components,
        "required_surface_decisions": required_surfaces,
        "actual_component_decisions": [component_decisions[key] for key in sorted(component_decisions)],
        "actual_surface_decisions": [surface_decisions[key] for key in sorted(surface_decisions)],
        "system_map_impact": system_map_impact,
        "residue": residue,
        "fixpoint": {"iterations": iterations, "reached": True},
        "closure_complete": not residue,
        "claim_boundary": "Closure is computed over declared repository and governance relations; reachability is not real-world causal identification.",
    }
    closure["closure_hash"] = canonical_hash(closure)
    validate_json(closure, CLOSURE_SCHEMA, "propagation closure")
    return closure, delta


def impact_report(closure: dict) -> str:
    lines = [
        f"# {closure['task_id']} typed change-propagation impact report",
        "",
        f"- Closure complete: `{str(closure['closure_complete']).lower()}`",
        f"- Closure hash: `{closure['closure_hash']}`",
        f"- Fixpoint iterations: `{closure['fixpoint']['iterations']}`",
        f"- Seeds: `{', '.join(closure['seed_components'])}`",
        f"- Resolved components: `{len(closure['resolved_components'])}`",
        f"- Registry-derived surfaces: `{len(closure['registry_derived_surfaces'])}`",
        f"- System-map decision: `{closure['system_map_impact']['decision']}`",
        "",
        "## Typed paths",
        "",
    ]
    for path in closure["typed_paths"]:
        lines.append(f"- `{path['source']} --{path['relation_class']} / {path['relation_domain']}--> {path['target']}` — {path['claim_ceiling']}")
    lines.extend(["", "## Residue", ""])
    if closure["residue"]:
        lines.extend(f"- `{item['type']}`: {item.get('message', item)}" for item in closure["residue"])
    else:
        lines.append("- None. This means declared closure is complete, not that substantive causality is proved.")
    return "\n".join(lines) + "\n"


def serialized(document: dict) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--map-delta", type=Path, required=True)
    parser.add_argument("--residue", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    closure, delta = compute(load_json(args.request))
    report = impact_report(closure).encode("utf-8")
    residue_doc = {"task_id": closure["task_id"], "closure_hash": closure["closure_hash"], "closure_complete": closure["closure_complete"], "residue": closure["residue"]}
    products = {args.output: serialized(closure), args.report: report, args.map_delta: serialized(delta), args.residue: serialized(residue_doc)}
    if args.check:
        for path, expected in products.items():
            require(path.is_file(), f"missing propagation product: {path}")
            require(path.read_bytes() == expected, f"stale propagation product: {path}")
        require(closure["closure_complete"], "propagation closure has unresolved residue")
        print(json.dumps({"status": "PASS", "closure_hash": closure["closure_hash"], "resolved_components": len(closure["resolved_components"]), "required_surfaces": len(closure["registry_derived_surfaces"]), "fixpoint_iterations": closure["fixpoint"]["iterations"], "claim_scope": "declared_relation_closure_only"}, sort_keys=True))
        return 0
    for path, payload in products.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(json.dumps({"closure_complete": closure["closure_complete"], "closure_hash": closure["closure_hash"], "residue": len(closure["residue"])}, sort_keys=True))
    return 0 if closure["closure_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
