from __future__ import annotations

import json
from pathlib import Path
import unittest

from agent_runtime.steering import DependencyEdge, GoalDependencyGraph, GoalDependencyGraphError, GraphNode


class GraphTests(unittest.TestCase):
    def setUp(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data/operations/iterations/129/fixtures/goal-dependency-graph-r1.json"
        self.graph = GoalDependencyGraph.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def test_graph_is_not_supervisor_run_dag(self) -> None:
        self.assertEqual(self.graph.to_dict()["graph_kind"], "LONG_TERM_STEERING")
        self.assertEqual(self.graph.traverse("goal-writing", edge_types=("PREREQUISITE",)), ("goal-research",))

    def test_cycle_is_rejected(self) -> None:
        with self.assertRaises(GoalDependencyGraphError):
            self.graph.add_edge(DependencyEdge("edge-cycle", "goal-research", "goal-writing", "PREREQUISITE", "cycle"))

    def test_dangling_reference_is_rejected(self) -> None:
        with self.assertRaises(GoalDependencyGraphError):
            self.graph.add_edge(DependencyEdge("edge-dangling", "goal-research", "missing", "ENABLES", "missing"))

    def test_cross_namespace_requires_shared_scope(self) -> None:
        graph = GoalDependencyGraph([GraphNode("a", "GOAL", "ns-a"), GraphNode("b", "GOAL", "ns-b")])
        with self.assertRaises(GoalDependencyGraphError):
            graph.add_edge(DependencyEdge("edge-cross", "a", "b", "PREREQUISITE", "deny"))
        graph.add_edge(DependencyEdge("edge-shared", "a", "b", "SHARES_RESOURCE", "explicit shared scope", "shared-fixture"))
        self.assertEqual(len(graph.edges), 1)

    def test_superseded_target_is_hidden_by_default(self) -> None:
        self.assertEqual(self.graph.traverse("goal-old", edge_types=("SUPERSEDES",)), ("goal-research",))


if __name__ == "__main__":
    unittest.main()
