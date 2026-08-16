#!/usr/bin/env python3
"""Build and check the deterministic current-facts projection.

The projection is a bounded derived view.  Canonical registries, manifests,
topology, pack declarations and the federation inventory remain authoritative;
this file records their current, reproducible facts and source fingerprints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import validate_current_state_sync as sync


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
CONTRACT_PATH = ROOT / "data/architecture/current-system-identity.json"
FACTS_PATH = ROOT / "data/architecture/current-facts.json"
FACTS_MARKDOWN_PATH = ROOT / "docs/architecture/current-facts.md"
SCHEMA_PATH = ROOT / "schemas/architecture/current-facts.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_paths(contract: dict[str, Any]) -> list[Path]:
    paths: set[Path] = {
        CONTRACT_PATH,
        HERE,
        SCHEMA_PATH,
        sync.SCHEMA_PATH,
        sync.resolve_repo_path(contract["current_map"]["source_path"]),
        sync.resolve_repo_path(contract["current_method"]["source_path"]),
        sync.resolve_repo_path("ignition/data/operations/project-components.json"),
        sync.resolve_repo_path("ignition/data/operations/change-propagation-topology.json"),
        sync.resolve_repo_path("ignition/data/agent-federation/executor-inventory-r1.json"),
        sync.resolve_repo_path("ignition/data/governance/human-surface/materiality-manifest.json"),
        sync.resolve_repo_path("ignition/data/governance/human-results/config.json"),
        sync.resolve_repo_path("ignition/data/operations/synchronization-surfaces.json"),
    }
    for metric in contract["derived_metrics"]:
        paths.add(sync.resolve_repo_path(metric["source_path"]))
    for pack_path in sorted((ROOT / "packs").glob("*/manifest.json")):
        paths.add(pack_path)
    return sorted(paths, key=relative)


def build_projection(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or load_json(CONTRACT_PATH)
    metrics, errors = sync.derive_metrics(contract)
    if errors:
        raise ValueError("cannot derive current facts: " + "; ".join(errors))

    map_layout = load_json(sync.resolve_repo_path(contract["current_map"]["source_path"]))
    inventory = load_json(sync.resolve_repo_path("ignition/data/agent-federation/executor-inventory-r1.json"))
    pack_paths = sorted((ROOT / "packs").glob("*/manifest.json"))
    packs = [load_json(path) for path in pack_paths]
    materiality = load_json(sync.resolve_repo_path("ignition/data/governance/human-surface/materiality-manifest.json"))
    human_config = load_json(sync.resolve_repo_path("ignition/data/governance/human-results/config.json"))
    sync_registry = load_json(sync.resolve_repo_path("ignition/data/operations/synchronization-surfaces.json"))
    sync_surfaces = sync_registry.get("surfaces", [])
    role_counts = Counter(role for row in sync_surfaces for role in row.get("roles", []))
    executors = inventory.get("executors", [])
    live_statuses = {row["executor_id"]: row.get("live_smoke", {}).get("status", "UNDECLARED") for row in executors}
    residuals = inventory.get("repository_audit", {}).get("residuals", [])
    method_text = sync.resolve_repo_path(contract["current_method"]["source_path"]).read_text(encoding="utf-8")
    method_match = re.search(r"^Current:\s*`([^`]+)`", method_text, re.MULTILINE)
    if not method_match:
        raise ValueError("cannot derive current method version")

    facts = {
        "architecture": {
            "registry_components": metrics["registry_components"],
            "visible_map_nodes": metrics["visible_map_nodes"],
            "hidden_components": metrics["hidden_components"],
            "typed_topology_relations": metrics["typed_topology_relations"],
            "visible_typed_edges": metrics["visible_typed_edges"],
            "current_map_version": map_layout["current_map_version"],
            "historical_map_version": map_layout["historical_map_version"],
            "layout_version": map_layout["layout_version"],
            "semantic_trunk_version": map_layout["semantic_trunk"]["schema_version"],
            "semantic_trunk_route_steps": len(map_layout["semantic_trunk"]["route"]),
        },
        "packs": {
            "count": len(packs),
            "capability_route_count": sum(len(pack.get("capabilities_provided", [])) for pack in packs),
            "pack_ids": sorted(pack["pack_id"] for pack in packs),
        },
        "federation": {
            "adapter_inventory_count": len(executors),
            "adapter_ids": sorted(row["executor_id"] for row in executors),
            "live_status_by_executor": dict(sorted(live_statuses.items())),
            "live_invocation_ceiling": "NOT_RUN_LIVE_EXTERNAL_INVOCATION" if any(status.startswith("NOT_RUN") for status in live_statuses.values()) else "RECORDED_BOUNDED_PROBES_ONLY",
            "reference_executor_identity": "REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR / FALLBACK_MINIMAL",
        },
        "foundation": {
            "function_identity_cards": metrics["function_identity_cards"],
            "function_quarantine_or_pending": metrics["function_quarantine_or_pending"],
            "nonfunction_claims": metrics["nonfunction_claims"],
            "nonfunction_quarantine_or_pending": metrics["nonfunction_quarantine_or_pending"],
        },
        "knowledge_experience": {
            "cards": metrics["knowledge_cards"],
            "changes": metrics["knowledge_changes"],
            "layered_readings": metrics["knowledge_layered_readings"],
            "search_records": metrics["knowledge_search_records"],
            "aliases": metrics["knowledge_aliases"],
        },
        "fire_seeds": {
            "seed_count": metrics["fire_seeds"],
            "source_census_count": metrics["fire_seed_sources"],
        },
        "human_surface": {
            "materiality_entries": len(materiality.get("entries", [])),
            "function_human_entries": materiality.get("counts", {}).get("function_human", 0),
            "nonfunction_human_entries": materiality.get("counts", {}).get("nonfunction_human", 0),
            "registered_synchronization_surfaces": len(sync_surfaces),
            "machine_human_pairs": len(human_config.get("machine_human_pairs", [])),
            "surface_role_counts": dict(sorted(role_counts.items())),
        },
        "iteration": {
            "current_iteration_boundary": contract["current_iteration_boundary"],
            "method_version": method_match.group(1),
            "method_status": contract["current_method"]["status"],
            "current_map_version": map_layout["current_map_version"],
        },
        "environmental_residuals": sorted(str(item) for item in residuals),
    }
    projection = {
        "schema_version": "current-facts-r1",
        "contract_id": contract["contract_id"],
        "identity_epoch": contract["identity_epoch"],
        "current_iteration_boundary": contract["current_iteration_boundary"],
        "facts": facts,
        "source_fingerprints": [{"path": relative(path), "sha256": sha256(path)} for path in source_paths(contract)],
        "claim_ceiling": "Deterministic repository-derived current facts and navigation support only; no external truth, Owner acceptance, production safety or epistemic upgrade.",
    }
    return projection


def render_json(projection: dict[str, Any]) -> bytes:
    return (json.dumps(projection, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def render_markdown(projection: dict[str, Any]) -> bytes:
    facts = projection["facts"]
    architecture = facts["architecture"]
    packs = facts["packs"]
    federation = facts["federation"]
    foundation = facts["foundation"]
    knowledge = facts["knowledge_experience"]
    fire_seeds = facts["fire_seeds"]
    human = facts["human_surface"]
    iteration = facts["iteration"]
    residuals = facts["environmental_residuals"]
    lines = [
        "<!-- BEGIN GENERATED CURRENT-FACTS r1; DO NOT EDIT -->",
        "# Current Facts（机器推导事实）",
        "",
        f"- Identity epoch: `{projection['identity_epoch']}`；current iteration boundary: `{projection['current_iteration_boundary']}`。",
        f"- Architecture registry: `{architecture['registry_components']}` components；`{architecture['visible_map_nodes']}` visible map nodes；`{architecture['hidden_components']}` hidden represented components；`{architecture['typed_topology_relations']}` typed relations；`{architecture['visible_typed_edges']}` visible typed edges。",
        f"- Map/method: map `{architecture['current_map_version']}` Current（historical `{architecture['historical_map_version']}`）；layout `{architecture['layout_version']}`；semantic trunk `{architecture['semantic_trunk_version']}` with `{architecture['semantic_trunk_route_steps']}` bounded route stages；method `{iteration['method_version']}` `{iteration['method_status']}`。",
        f"- Packs: `{packs['count']}` packs；`{packs['capability_route_count']}` declared capability routes。",
        f"- Federation: `{federation['adapter_inventory_count']}` adapter inventory entries；live ceiling `{federation['live_invocation_ceiling']}`；local boundary `{federation['reference_executor_identity']}`。",
        f"- Foundation: function identity cards `{foundation['function_identity_cards']}`；function quarantine/pending `{foundation['function_quarantine_or_pending']}`；non-function claims `{foundation['nonfunction_claims']}`；non-function quarantine/pending `{foundation['nonfunction_quarantine_or_pending']}`。",
        f"- Knowledge Experience: cards `{knowledge['cards']}`；changes `{knowledge['changes']}`；layered readings `{knowledge['layered_readings']}`；search records `{knowledge['search_records']}`；aliases `{knowledge['aliases']}`。",
        f"- Fire Seeds: `{fire_seeds['seed_count']}` seeds/clusters；`{fire_seeds['source_census_count']}` source-census records。",
        f"- Human Surface: `{human['materiality_entries']}` materiality entries（function `{human['function_human_entries']}` + non-function `{human['nonfunction_human_entries']}`）；`{human['registered_synchronization_surfaces']}` registered sync surfaces；`{human['machine_human_pairs']}` machine/human pairs。",
        "- Current environmental residuals: " + ("；".join(residuals) if residuals else "none declared") + "。",
        "",
        "Source authority: the JSON projection records SHA-256 fingerprints for the canonical registries, manifests, topology, pack declarations, federation inventory and generator/schema inputs. Human prose may explain these facts but is not a second numeric authority.",
        "Claim ceiling: " + projection["claim_ceiling"],
        "",
        "Machine source: [`current-facts.json`](../../data/architecture/current-facts.json).",
        "<!-- END GENERATED CURRENT-FACTS r1 -->",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def check() -> list[str]:
    contract = load_json(CONTRACT_PATH)
    expected_json = render_json(build_projection(contract))
    expected_markdown = render_markdown(build_projection(contract))
    errors: list[str] = []
    if not FACTS_PATH.is_file() or FACTS_PATH.read_bytes() != expected_json:
        errors.append(f"stale or missing generated projection: {relative(FACTS_PATH)}")
    if not FACTS_MARKDOWN_PATH.is_file() or FACTS_MARKDOWN_PATH.read_bytes() != expected_markdown:
        errors.append(f"stale or missing generated facts block: {relative(FACTS_MARKDOWN_PATH)}")
    return errors


def write() -> None:
    contract = load_json(CONTRACT_PATH)
    projection = build_projection(contract)
    FACTS_PATH.write_bytes(render_json(projection))
    FACTS_MARKDOWN_PATH.write_bytes(render_markdown(projection))
    print(f"CURRENT_FACTS_WRITTEN json={relative(FACTS_PATH)} markdown={relative(FACTS_MARKDOWN_PATH)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("choose exactly one of --write or --check")
    if args.write:
        write()
        return 0
    errors = check()
    if errors:
        print("CURRENT_FACTS_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("CURRENT_FACTS_DETERMINISTIC_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
