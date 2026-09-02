import copy
import json
import unittest

from tools.validate_task150_step11_capability_registry_candidate_gate import ARTIFACT_PATH, validate


class Task150Step11CapabilityRegistryCandidateGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_candidate_gate_is_fail_closed(self):
        self.assertEqual(validate(self.document), [])
        candidate = self.document["candidate"]
        self.assertFalse(candidate["registry_write_performed"])
        self.assertFalse(candidate["operation_present_after"])
        self.assertEqual(self.document["admission_decision"]["decision"], "NOT_REGISTERED")

    def test_registry_census_is_unchanged(self):
        candidate = self.document["candidate"]
        self.assertEqual(candidate["registry_sha256_before"], candidate["registry_sha256_after"])
        self.assertEqual(candidate["operation_count_before"], 19)
        self.assertEqual(candidate["operation_count_after"], 19)

    def test_failed_delta_gate_cannot_be_promoted(self):
        mutated = copy.deepcopy(self.document)
        next(gate for gate in mutated["gates"] if gate["id"] == "delta_viewport_containment_zero_failure")["result"] = "PASS"
        self.assertTrue(validate(mutated))

    def test_pending_owner_acceptance_cannot_be_promoted(self):
        mutated = copy.deepcopy(self.document)
        next(gate for gate in mutated["gates"] if gate["id"] == "owner_visual_acceptance")["result"] = "PASS"
        self.assertTrue(validate(mutated))

    def test_current_or_default_renderer_remains_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["current_admission"], "NOT_ADMITTED")
        self.assertEqual(scope["default_renderer"], "NOT_SELECTED")
        mutated = copy.deepcopy(self.document)
        mutated["scope_freeze"]["current_admission"] = "CURRENT_BOUNDED"
        self.assertTrue(validate(mutated))

    def test_registry_write_is_rejected(self):
        mutated = copy.deepcopy(self.document)
        mutated["candidate"]["registry_write_performed"] = True
        self.assertTrue(validate(mutated))

    def test_auth_and_live_invocation_boundaries_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["authenticated_channels"], "NO_AUTHENTICATED_ADMISSION")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")


if __name__ == "__main__":
    unittest.main()
