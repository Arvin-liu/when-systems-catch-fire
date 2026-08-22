from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools import validate_residual_ledger as gate


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data/operations/iterations/134/fixtures/residual-delta-negative-fixtures-r1.json"


def base_entry() -> dict:
    objects = [f"object-{index:02d}" for index in range(11)]
    dimensions = ["FAILURE_DIMENSION_A"]
    return {
        "residual_id": "RESIDUAL_TEST",
        "origin_task": "IGNITION-20260821-129",
        "classification": "TEST_INHERITED",
        "status": "OPEN_INHERITED",
        "baseline_fingerprint": gate.fingerprint(count=len(objects), objects=objects, failure_dimensions=dimensions),
        "current_fingerprint": gate.fingerprint(count=len(objects), objects=objects, failure_dimensions=dimensions),
        "baseline_count": len(objects),
        "current_count": len(objects),
        "baseline_objects": objects,
        "current_objects": list(objects),
        "baseline_failure_dimensions": dimensions,
        "current_failure_dimensions": list(dimensions),
        "baseline_source_command": "validator --check",
        "current_source_command": "validator --check",
        "validator": "validator.py",
        "provenance_paths": ["ignition/tests/test_residual_delta_gate.py"],
        "allowed_persistence_rule": "unchanged only",
        "release_impact": "NON_BLOCKING_IF_UNCHANGED",
    }


class ResidualDeltaGateTests(unittest.TestCase):
    def test_fixture_matrix_is_declared(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(fixture["task_id"], "IGNITION-20260822-134")
        self.assertEqual(len(fixture["cases"]), 8)

    def test_inherited_unchanged_is_allowed(self) -> None:
        self.assertEqual(gate.compare_entry(base_entry())["errors"], [])

    def test_growth_in_count_is_not_laundered(self) -> None:
        entry = base_entry()
        entry["current_objects"].append("object-11")
        entry["current_count"] = 12
        entry["current_fingerprint"] = gate.fingerprint(count=12, objects=entry["current_objects"], failure_dimensions=entry["current_failure_dimensions"])
        result = gate.compare_entry(entry)
        self.assertIn("RESIDUAL_GROWTH_UNCLASSIFIED", " ".join(result["errors"]))

    def test_same_count_replacement_is_growth(self) -> None:
        entry = base_entry()
        entry["current_objects"][-1] = "new-object"
        entry["current_fingerprint"] = gate.fingerprint(count=11, objects=entry["current_objects"], failure_dimensions=entry["current_failure_dimensions"])
        result = gate.compare_entry(entry)
        self.assertIn("RESIDUAL_GROWTH_UNCLASSIFIED", " ".join(result["errors"]))

    def test_failure_dimension_change_is_growth(self) -> None:
        entry = base_entry()
        entry["current_failure_dimensions"] = ["FAILURE_DIMENSION_B"]
        entry["current_fingerprint"] = gate.fingerprint(count=11, objects=entry["current_objects"], failure_dimensions=entry["current_failure_dimensions"])
        result = gate.compare_entry(entry)
        self.assertIn("RESIDUAL_GROWTH_UNCLASSIFIED", " ".join(result["errors"]))

    def test_forged_fingerprint_fails(self) -> None:
        entry = base_entry()
        entry["current_fingerprint"] = "0" * 64
        self.assertIn("CURRENT_FINGERPRINT_FORGED", " ".join(gate.compare_entry(entry)["errors"]))

    def test_new_residual_is_release_blocking(self) -> None:
        entry = base_entry()
        entry["baseline_objects"] = []
        entry["baseline_failure_dimensions"] = []
        entry["baseline_count"] = 0
        entry["baseline_fingerprint"] = gate.fingerprint(count=0, objects=[], failure_dimensions=[])
        entry["origin_task"] = "IGNITION-20260822-134"
        entry["status"] = "NEW_REGRESSION"
        self.assertIn("NEW_REGRESSION_RELEASE_BLOCKING", " ".join(gate.compare_entry(entry)["errors"]))

    def test_source_command_change_requires_migration(self) -> None:
        entry = base_entry()
        entry["current_source_command"] = "validator --new-contract"
        self.assertIn("SOURCE_COMMAND_CHANGED_WITHOUT_MIGRATION", " ".join(gate.compare_entry(entry)["errors"]))

    def test_resolved_current_is_allowed(self) -> None:
        entry = base_entry()
        entry["current_objects"] = []
        entry["current_failure_dimensions"] = []
        entry["current_count"] = 0
        entry["current_fingerprint"] = gate.fingerprint(count=0, objects=[], failure_dimensions=[])
        entry["status"] = "RESOLVED_CURRENT"
        self.assertEqual(gate.compare_entry(entry)["errors"], [])

    def test_unchanged_entry_is_not_mutated_by_comparison(self) -> None:
        entry = base_entry()
        original = copy.deepcopy(entry)
        gate.compare_entry(entry)
        self.assertEqual(entry, original)


if __name__ == "__main__":
    unittest.main()
