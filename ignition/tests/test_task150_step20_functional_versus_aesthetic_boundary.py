import copy
import json
import unittest

from tools.validate_task150_step20_functional_versus_aesthetic_boundary import ARTIFACT_PATH, validate


class Task150Step20FunctionalVersusAestheticBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_boundary_contract_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_functional_criteria_are_pending_step21_not_aesthetic(self):
        boundary = self.document["operation"]["functional_boundary"]
        self.assertEqual(boundary["decision"], "ALLOWED_TO_PROCEED")
        self.assertEqual(boundary["current_status"], "NOT_ADMITTED_PENDING_STEP21")
        self.assertTrue(all(item["class"] == "FUNCTIONAL" for item in boundary["criteria"]))

    def test_aesthetic_endorsement_is_ungranted_and_unclaimed(self):
        boundary = self.document["operation"]["aesthetic_boundary"]
        self.assertEqual(boundary["decision"], "NOT_GRANTED")
        self.assertFalse(boundary["claimed"])
        self.assertFalse(boundary["required_for_current_technical_scope"])
        self.assertTrue(boundary["future_use_requires_separate_gate"])

    def test_functional_pass_without_aesthetic_is_bounded(self):
        cases = {item["case"]: item for item in self.document["boundary_matrix"]}
        self.assertEqual(
            cases["functional_evidence_passes_aesthetic_endorsement_absent"]["permitted_use"],
            "DECLARED_TECHNICAL_BOUNDED_USE_ONLY",
        )

    def test_aesthetic_endorsement_cannot_substitute_for_functional_evidence(self):
        cases = {item["case"]: item for item in self.document["boundary_matrix"]}
        self.assertEqual(
            cases["aesthetic_endorsement_present_without_functional_evidence"]["functional_result"],
            "NOT_ADMITTED",
        )

    def test_forbidden_owner_labels_are_not_decisions(self):
        mutated = copy.deepcopy(self.document)
        mutated["owner_decision"]["owner_visual_accepted"] = True
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["operation"]["aesthetic_boundary"]["decision"] = "OWNER_REJECTED_VISUAL"
        self.assertTrue(validate(mutated))

    def test_future_public_use_requires_separate_gate(self):
        future = next(item for item in self.document["boundary_matrix"] if item["case"] == "future_publication_or_branded_use")
        self.assertEqual(future["aesthetic_result"], "SEPARATE_GATE_REQUIRED")
        self.assertEqual(future["permitted_use"], "NOT_AVAILABLE_IN_STEP20")

    def test_global_boundaries_remain_closed(self):
        scope = self.document["scope_boundaries"]
        self.assertEqual(scope["current_registry_operation_count"], 19)
        self.assertFalse(scope["registry_write"])
        self.assertEqual(scope["default_renderer"], "NOT_SELECTED")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(scope["task151"], "FORBIDDEN")

    def test_functional_and_aesthetic_contract_flags_are_true(self):
        self.assertTrue(all(self.document["validation_contract"].values()))


if __name__ == "__main__":
    unittest.main()
