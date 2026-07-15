#!/usr/bin/env python3
"""Validate 121Q14 Ignition Atlas projections."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> object:
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: str) -> list[dict]:
    rows: list[dict] = []
    with (ROOT / path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
    return rows


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_baseline() -> None:
    baseline = load_json("data/atlas/121q14-baseline.json")
    require(baseline["stacked_on"]["head"] == "5297fe6c4c3aa36519b2e0a4d751be43dee09441", "unexpected Q13 base")
    scope = baseline["atlas_scope"]
    require(scope["adds_truth_layer"] is False, "atlas must not add a truth layer")
    require(scope["creates_second_canonical_truth"] is False, "atlas must not create second canonical truth")
    require(scope["replaces_matrices_or_registries"] is False, "atlas must not replace matrices or registries")
    require(scope["creates_permanent_total_map"] is False, "atlas must not be a permanent total map")
    guard = baseline["guard"]
    for key in ("map_position_is_proof", "visual_proximity_is_isomorphism", "evolution_stage_is_natural_law", "dependency_is_causality", "sourcing_decision_transfers_charter_duty"):
        require(guard[key] is False, f"guard violated: {key}")


def validate_atlas() -> None:
    atlas = load_json("data/atlas/generated/ignition-atlas-121q14.json")
    spec = atlas["atlas_spec"]
    require(spec["permanent_total_map"] is False, "atlas spec cannot be permanent total map")
    require("remain authoritative" in spec["canonical_truth_source"], "atlas must point back to canonical sources")
    maps = atlas["maps"]
    require(len(maps) == 3, "expected exactly three first atlas maps")
    map_ids = {m["id"] for m in maps}
    require(map_ids == {"map-maintainer-sustainability-economics", "map-epistemic-architecture", "map-agent-delivery-operations"}, "unexpected map set")
    for m in maps:
        require(m["as_of_commit"] == spec["as_of_commit"], f"{m['id']}: commit mismatch")
        require(m["observer_or_decision_owner"], f"{m['id']}: observer missing")
        require(m["decision_question"], f"{m['id']}: decision question missing")
        require(m["value_recipient_or_affected_subject"], f"{m['id']}: value recipient missing")
        require(m["layout_semantics"]["visual_boundary"], f"{m['id']}: visual boundary missing")
        require(m["data_sources"], f"{m['id']}: data sources missing")
        require(m["projections"], f"{m['id']}: projection rules missing")
        require(m["unmapped_residue"], f"{m['id']}: unmapped residue missing")
        nodes = {n["id"]: n for n in m["nodes"]}
        require(nodes, f"{m['id']}: nodes missing")
        connected = set()
        for e in m["edges"]:
            require(e["from"] in nodes, f"{m['id']}: edge from missing node {e['from']}")
            require(e["to"] in nodes, f"{m['id']}: edge to missing node {e['to']}")
            require(e["edge_type"] in {"dependency", "information_flow", "control_flow", "evidence_flow", "value_flow"}, f"{m['id']}: invalid edge type")
            require(e["not_causality"] is True, f"{m['id']}: edge missing not_causality")
            require(e["source_refs"], f"{m['id']}: edge source missing")
            connected.add(e["from"])
            connected.add(e["to"])
        isolated = set(nodes) - connected
        require(not isolated, f"{m['id']}: isolated nodes {sorted(isolated)}")
        for n in nodes.values():
            require(n["source_refs"], f"{m['id']}:{n['id']}: source refs missing")
            require(n["uncertainty"], f"{m['id']}:{n['id']}: uncertainty missing")
            require(n["evolution_record"]["basis"], f"{m['id']}:{n['id']}: stage basis missing")
            require(n["evolution_record"]["not_natural_law"] is True, f"{m['id']}:{n['id']}: stage treated as natural law")
            require(n["sourcing_decision"]["responsibility_retained"] is True, f"{m['id']}:{n['id']}: sourcing transfers responsibility")
            require(n["sourcing_decision"]["charter_constraint"], f"{m['id']}:{n['id']}: Charter constraint missing")


def validate_decisions_and_diff() -> None:
    decisions = load_json("data/atlas/generated/121q14-map-decisions.json")["decisions"]
    require(len(decisions) == 3, "expected one decision summary per map")
    for decision in decisions:
        require(decision["new_decision_revealed"], "map decision cannot be empty")
        require(decision["max_uncertainty"], "max uncertainty missing")
        require(decision["unmapped_residue"], "decision residue missing")
    diff = load_json("data/atlas/generated/121q14-mapdiff-q13-to-q14.json")
    require(diff["from_commit"] == "5297fe6c4c3aa36519b2e0a4d751be43dee09441", "MapDiff from commit mismatch")
    require(diff["to_commit"], "MapDiff to commit missing")
    require(diff["node_changes"], "MapDiff node changes missing")
    require("not proof" in diff["claim_boundary"], "MapDiff claim boundary must reject proof")


def validate_run_state() -> None:
    state = load_json("data/atlas/121q14-run-state.json")
    require(state["draft_pr"] == 49, "run-state must point to Draft PR #49")
    require(len(state["steps"]) == 4, "run-state must contain four steps")
    require(all(step["status"] == "complete" for step in state["steps"]), "all macro steps must be complete")
    ledger = load_jsonl("data/atlas/121q14-ledger.jsonl")
    require([row["step"] for row in ledger] == ["000", "001", "002", "003"], "ledger must contain steps 000-003")


def main() -> int:
    try:
        validate_baseline()
        validate_atlas()
        validate_decisions_and_diff()
        validate_run_state()
    except AssertionError as exc:
        print(f"121Q14 atlas validation failed: {exc}", file=sys.stderr)
        return 1
    print("121Q14 ignition atlas validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
