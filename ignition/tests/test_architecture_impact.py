from __future__ import annotations

import copy
import unittest

from tools.architecture_impact import ArchitectureImpactError, classify_change, validate_classification


class ArchitectureImpactTests(unittest.TestCase):
    def test_process_transport_is_behavioral_control_plane_change(self) -> None:
        result = classify_change(
            ["process_transport", "observation_capture"],
            changed_paths=["ignition/agent_federation/live_transport.py"],
            evidence=["step00-baseline-audit.json"],
        )
        self.assertEqual(result["classification"], "BEHAVIORAL_CONTROL_PLANE_CHANGE")
        self.assertEqual(result["legacy_identity_impact"], "ARCHITECTURE_CHANGED")
        self.assertTrue(result["current_identity_sync_required"])

    def test_architecture_component_takes_architecture_changing_class(self) -> None:
        result = classify_change(
            ["architecture_component", "architecture_relation"],
            changed_paths=["ignition/data/operations/project-components.json"],
            evidence=["registry-delta.json"],
        )
        self.assertEqual(result["classification"], "ARCHITECTURE_CHANGING")

    def test_surface_release_and_data_classes_remain_distinct(self) -> None:
        self.assertEqual(classify_change(["current_surface_only"])["classification"], "PRESENTATION_ONLY")
        self.assertEqual(classify_change(["publication_only"])["classification"], "RELEASE_ONLY")
        self.assertEqual(classify_change(["data_refresh_only"])["classification"], "DATA_REFRESH_ONLY")

    def test_control_plane_change_cannot_be_declared_presentation_only(self) -> None:
        with self.assertRaises(ArchitectureImpactError):
            classify_change(
                ["process_transport", "canonical_state_source"],
                changed_paths=["ignition/agent_federation/live_attempt_ledger.py"],
                evidence=["task139-receipt.json"],
                declared_classification="PRESENTATION_ONLY",
            )

    def test_tampered_classification_is_rejected(self) -> None:
        result = classify_change(["process_transport"], evidence=["receipt.json"])
        tampered = copy.deepcopy(result)
        tampered["classification"] = "PRESENTATION_ONLY"
        with self.assertRaises(ArchitectureImpactError):
            validate_classification(tampered)

    def test_behavioral_change_requires_evidence(self) -> None:
        with self.assertRaises(ArchitectureImpactError):
            classify_change(["reconciliation_state_machine"])


if __name__ == "__main__":
    unittest.main()
