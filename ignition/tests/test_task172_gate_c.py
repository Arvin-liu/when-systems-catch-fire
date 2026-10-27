"""Regression tests for the policy-only Task172 Gate C lock."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.foundation.knowledge_corpus_admission import admission_for_path
from tools.research.validate_task172_gate_c import EXPECTED_SOURCE_HEAD, validate


ROOT = Path(__file__).resolve().parents[1]
GATE_C = ROOT / "data/research/task172-gate-c-scholarly-admission"


class Task172GateCTests(unittest.TestCase):
    def test_gate_c_validator_passes(self):
        validate(ROOT)

    def test_policy_is_metadata_only_and_has_four_domains(self):
        policy = json.loads((GATE_C / "admission-policy.json").read_text(encoding="utf-8"))
        pilot = json.loads((GATE_C / "cross-domain-pilot.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["mode"], "METADATA_ONLY")
        self.assertEqual(policy["admission_ceiling"]["metadata_rows_admitted_in_gate_c"], 0)
        self.assertFalse(policy["admission_ceiling"]["mass_formal_ingestion_authorized_in_gate_c"])
        self.assertEqual(len(pilot["domains"]), 4)
        self.assertFalse(pilot["live_retrieval"])
        self.assertFalse(pilot["corpus_admission"])
        self.assertEqual(pilot["metadata_rows_admitted"], 0)

    def test_sidecar_operation_and_report_are_excluded(self):
        for path in [
            "data/research/task172-gate-c-scholarly-admission/admission-policy.json",
            "data/operations/iterations/172/step05-scholarly-gate.json",
            "reports/operations/ignition-172-20260913-step05-gate-c-scholarly.md",
        ]:
            admission = admission_for_path(path)
            self.assertEqual(admission.classification, "GENERATED_PROJECTION_EXCLUDED", path)
            self.assertFalse(admission.auto_discovery, path)

    def test_source_head_and_no_content(self):
        receipt = json.loads((GATE_C / "build-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["source_exact_head"], EXPECTED_SOURCE_HEAD)
        self.assertFalse(receipt["corpus_admission"])
        self.assertFalse(receipt["abstract_fulltext_persisted"])
        self.assertEqual([p.suffix for p in GATE_C.iterdir() if p.is_file() and p.suffix in {".pdf", ".txt", ".html"}], [])


if __name__ == "__main__":
    unittest.main()
