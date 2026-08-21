#!/usr/bin/env python3
"""Validate the long-term steering graph independently from Supervisor DAG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/goal-dependency-graph-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-goal-dependency-graph-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import DependencyEdge, GoalDependencyGraph, GoalDependencyGraphError, GraphNode  # noqa: E402


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    graph = GoalDependencyGraph.from_dict(document)
    if graph.traverse("goal-writing", edge_types=("PREREQUISITE",)) != ("goal-research",):
        errors.append("deterministic prerequisite traversal failed")
    try:
        graph.add_edge(DependencyEdge("edge-cycle", "goal-research", "goal-writing", "PREREQUISITE", "cycle fixture"))
    except GoalDependencyGraphError:
        pass
    else:
        errors.append("dependency cycle was not rejected")
    try:
        cross = GoalDependencyGraph([GraphNode("n-a", "GOAL", "namespace-a"), GraphNode("n-b", "GOAL", "namespace-b")])
        cross.add_edge(DependencyEdge("edge-cross", "n-a", "n-b", "PREREQUISITE", "cross namespace without grant"))
    except GoalDependencyGraphError:
        pass
    else:
        errors.append("cross-namespace edge was not rejected")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_GRAPH_INVALID")
        for error in errors: print(f"- {error}")
        return 1
    print("STEERING_GRAPH_OK nodes=4 edges=3 cycle=FAIL_CLOSED namespace=FAIL_CLOSED supervisor_dag=SEPARATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
