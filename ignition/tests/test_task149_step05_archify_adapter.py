import copy
import json
import unittest

from tools.validate_task149_step05_archify_adapter import ARTIFACT_PATH, IR_PATH, validate


class Task149Step05ArchifyAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
        cls.ir = json.loads(IR_PATH.read_text(encoding="utf-8"))

    def test_adapter_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_external_validation_is_not_claimed_early(self):
        self.assertEqual(self.document["archify_external_validation"]["status"], "PENDING_STEP06")

    def test_non_file_canonical_targets_are_recorded_not_fabricated(self):
        source_evidence = self.document["source_evidence"]
        self.assertEqual(source_evidence["status"], "PARTIAL_BY_CANONICAL_TARGETS")
        self.assertGreater(source_evidence["verified_component_count"], 0)
        self.assertEqual(source_evidence["omitted_non_file_target_count"], len(source_evidence["omitted_non_file_targets"]))

    def test_canonical_data_remains_authoritative(self):
        boundary = self.document["boundary"]
        self.assertEqual(boundary["current_integration"], "NOT_CURRENT_INTEGRATION")
        self.assertFalse(boundary["permission_granted"])

    def test_derived_layout_is_explicit_and_compact(self):
        layout = self.document["derived_layout"]
        self.assertEqual(layout["viewBox"], [1400, 800])
        self.assertEqual(layout["componentSize"], [190, 48])
        self.assertEqual(layout["explicitComponentPositionCount"], len(self.ir["components"]))
        self.assertEqual(layout["explicitConnectionGeometryCount"], len(self.ir["connections"]))
        self.assertTrue(all("pos" in component and "size" in component for component in self.ir["components"]))
        self.assertTrue(all("labelAt" in connection for connection in self.ir["connections"]))
        self.assertTrue(all("sublabel" not in component for component in self.ir["components"]))

    def test_canonical_component_and_connection_counts_remain_complete(self):
        self.assertEqual(len(self.ir["components"]), 24)
        self.assertEqual(len(self.ir["connections"]), 24)
        self.assertEqual(self.document["typed_ir"]["boundary_count"], 8)

    def test_source_hash_drift_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["source_inputs"][0]["sha256"] = "0" * 64
        self.assertTrue(any("source hash mismatch" in error for error in validate(mutated)))

    def test_adapter_network_and_auth_are_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["boundary"]["network_used_by_adapter"] = True
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
