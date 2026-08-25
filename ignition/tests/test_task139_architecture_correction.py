from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from tools.architecture_impact import classify_change


class Task139ArchitectureCorrectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.correction = json.loads(
            (self.root / "data/operations/iterations/140/step02-task139-architecture-impact-correction.json").read_text(encoding="utf-8")
        )

    def test_correction_is_provenance_and_classifies_task139_behavior(self) -> None:
        result = classify_change(
            self.correction["audit"]["changed_semantics"],
            evidence=self.correction["audit"]["evidence"],
        )
        self.assertEqual(result["classification"], "BEHAVIORAL_CONTROL_PLANE_CHANGE")
        self.assertTrue(self.correction["subject_task"]["historical_records_unchanged"])
        self.assertTrue(self.correction["current_lineage_correction"]["task140_registration_is_architecture_changing"])

    def test_immutable_task139_sources_match_recorded_digests(self) -> None:
        for relative, expected in self.correction["subject_task"]["source_digests"].items():
            observed = hashlib.sha256((self.root.parent / relative).read_bytes()).hexdigest()
            self.assertEqual(observed, expected, relative)


if __name__ == "__main__":
    unittest.main()
