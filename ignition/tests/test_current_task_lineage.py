from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import validate_current_task_lineage as validator  # noqa: E402


class CurrentTaskLineageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = validator.load_json(validator.STATUS_PATH)

    def test_canonical_lineage_passes(self) -> None:
        self.assertEqual(validator.validate(self.source), [])

    def test_unexecuted_predecessor_carries_successor_lineage(self) -> None:
        predecessor = self.source["lineages"][0]["predecessor"]
        self.assertEqual(predecessor["task_file_status"], "HISTORICAL_UNEXECUTED")
        self.assertEqual(predecessor["requirement_lineage_status"], "REBASED_INTO_127")
        self.assertEqual(predecessor["canonical_status"], "HISTORICAL_UNEXECUTED_REBASED_INTO_127")

    def test_wrong_predecessor_status_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.source)
        mutated["lineages"][0]["predecessor"]["canonical_status"] = "COMPLETED"
        self.assertTrue(validator.validate(mutated))

    def test_epistemic_boundary_is_unchanged(self) -> None:
        self.assertEqual(self.source["current_state"]["current_state_status"], "CURRENT_WITH_OPEN_OBLIGATIONS")
        self.assertEqual(self.source["current_state"]["epistemically_accepted"], 0)


if __name__ == "__main__":
    unittest.main()
