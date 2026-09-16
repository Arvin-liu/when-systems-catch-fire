"""Regression tests for the fail-closed Task172 Gate R pilot."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from tools.research.validate_task172_gate_r import EXPECTED_PARENT_HEAD, validate
from tools.foundation.knowledge_corpus_admission import admission_for_path


ROOT = Path(__file__).resolve().parents[1]
GATE_R = ROOT / "data/research/task172-gate-r-routing"


class Task172GateRTests(unittest.TestCase):
    def test_gate_r_validator_passes(self):
        validate(ROOT)

    def test_pilot_is_bounded_manual_review_only(self):
        pilot = json.loads((GATE_R / "precision-pilot.json").read_text(encoding="utf-8"))
        audit = json.loads((GATE_R / "precision-audit.json").read_text(encoding="utf-8"))
        self.assertEqual(pilot["source_exact_head"], EXPECTED_PARENT_HEAD)
        self.assertEqual(len(pilot["rows"]), 750)
        self.assertTrue(all(row["review_state"] == "PILOT_MANUAL_REVIEW_REQUIRED" for row in pilot["rows"]))
        self.assertFalse(pilot["live_retrieval"])
        self.assertFalse(pilot["full_routing_promotion"])
        self.assertEqual(audit["manual_review_required"], 750)
        self.assertEqual(sum(audit["hard_checks"].values()), 0)

    def test_receipt_hashes_are_current_and_outputs_are_stable(self):
        receipt = json.loads((GATE_R / "build-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["source_exact_head"], EXPECTED_PARENT_HEAD)
        for key, raw in {
            "routing_schema": "routing-schema.json",
            "controlled_vocabulary": "controlled-vocabulary.json",
            "precision_pilot": "precision-pilot.json",
            "precision_audit": "precision-audit.json",
            "source_freeze": "source-freeze.json",
        }.items():
            digest = hashlib.sha256((GATE_R / raw).read_bytes()).hexdigest()
            self.assertEqual(receipt["outputs"][key], digest, key)

    def test_sidecar_is_excluded_from_foundation_admission(self):
        admission = admission_for_path("data/research/task172-gate-r-routing/precision-pilot.json")
        self.assertEqual(admission.classification, "GENERATED_PROJECTION_EXCLUDED")
        self.assertFalse(admission.auto_discovery)


if __name__ == "__main__":
    unittest.main()
