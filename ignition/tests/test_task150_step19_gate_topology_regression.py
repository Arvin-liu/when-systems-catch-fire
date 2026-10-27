import copy
import json
import unittest

from tools.validate_task150_step19_gate_topology_regression import ARTIFACT_PATH, validate


class Task150Step19GateTopologyRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_split_topology_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_standalone_pass_delta_fail_admits_only_base_candidate(self):
        case = next(item for item in self.document["regression_cases"] if item["id"] == "standalone_pass_delta_fail")
        self.assertEqual(case["expected_base_admission"], "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE")
        self.assertEqual(case["expected_delta_admission"], "DEFER")

    def test_standalone_fail_delta_pass_keeps_base_deferred(self):
        case = next(item for item in self.document["regression_cases"] if item["id"] == "standalone_fail_delta_pass")
        self.assertEqual(case["expected_base_admission"], "DEFER")
        self.assertEqual(case["expected_delta_admission"], "SEPARATE_ADMISSION_REQUIRED")
        mutated = copy.deepcopy(self.document)
        next(item for item in mutated["regression_cases"] if item["id"] == "standalone_fail_delta_pass")["expected_base_admission"] = "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE"
        self.assertTrue(validate(mutated))

    def test_delta_repair_does_not_auto_promote_extension(self):
        case = next(item for item in self.document["regression_cases"] if item["id"] == "delta_repaired_base_pass")
        self.assertEqual(case["delta_gate_result"], "PASS")
        self.assertEqual(case["expected_delta_admission"], "SEPARATE_ADMISSION_REQUIRED")
        self.assertFalse(self.document["gate_topology"]["delta_extension"]["base_pass_promotes_delta"])

    def test_aesthetic_absence_does_not_block_functional_candidate(self):
        case = next(item for item in self.document["regression_cases"] if item["id"] == "aesthetic_endorsement_absent")
        self.assertEqual(case["expected_base_admission"], "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE")
        self.assertEqual(case["expected_aesthetic_claim"], "NOT_CLAIMED")

    def test_historical_step11_combined_failure_is_retained(self):
        historical = self.document["historical_step11"]
        self.assertTrue(historical["retained_as_historical"])
        self.assertFalse(historical["rewritten"])
        self.assertEqual(historical["combined_model_result"], "NOT_REGISTERED")

    def test_delta_gate_is_not_in_base_gate_family(self):
        base = self.document["gate_topology"]["base_operation"]
        self.assertNotIn("delta_viewport_containment_zero_failure", base["gate_ids"])
        self.assertNotIn("owner_aesthetic_endorsement", base["gate_ids"])
        self.assertEqual(base["gate_ids"][3], "standalone_viewport_containment_zero_failure")

    def test_registry_and_global_boundaries_remain_closed(self):
        current = self.document["current_state"]
        self.assertEqual(current["registry_operation_count"], 19)
        self.assertFalse(current["registry_write_in_step19"])
        self.assertFalse(current["base_operation_current"])
        self.assertFalse(current["delta_current"])
        self.assertEqual(current["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(current["task151"], "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
