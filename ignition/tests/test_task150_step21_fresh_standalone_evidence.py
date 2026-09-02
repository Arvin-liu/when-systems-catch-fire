import copy
import json
import unittest

from tools.validate_task150_step21_fresh_standalone_evidence import (
    ARTIFACT_PATH,
    CANONICAL_PATH,
    FIXTURE_PATH,
    IR_PATH,
    apply_fixture,
    exact_topology_errors,
    load_json,
    validate,
)


class Task150Step21FreshStandaloneEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
        cls.architecture = load_json(CANONICAL_PATH)
        cls.ir = load_json(IR_PATH)
        cls.fixture = load_json(FIXTURE_PATH)

    def test_fresh_evidence_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_source_provider_ir_and_artifact_are_bound(self):
        self.assertEqual(self.document["canonical_source"]["formal_source_revision"], "68d5d30bda0d8eb9c715ac346ce6476a55c0e288")
        self.assertEqual(self.document["provider"]["immutable_revision"], "06dd052602dd9a369e4d034e24faef0917b5a60c")
        self.assertEqual(self.document["typed_ir"]["components"], 24)
        self.assertEqual(self.document["typed_ir"]["connections"], 24)
        self.assertEqual(self.document["delivery"]["artifact_sha256"], "da7947e408af2839e51fddc90871de30f84b1846ae1d14809a076a40d55daf45")

    def test_exact_node_and_edge_equality_passes(self):
        self.assertEqual(exact_topology_errors(self.architecture, self.ir), [])
        self.assertTrue(self.document["node_edge_equality"]["semantic_relationships_unchanged"])

    def test_extra_node_fixture_is_rejected(self):
        mutated = apply_fixture(self.ir, self.fixture, "extra_node")
        self.assertTrue(exact_topology_errors(self.architecture, mutated))
        case = next(item for item in self.document["adversarial_fixtures"]["cases"] if item["id"] == "extra_node")
        self.assertEqual(case["observed"], "REJECTED")

    def test_deleted_node_fixture_is_rejected(self):
        mutated = apply_fixture(self.ir, self.fixture, "deleted_node")
        self.assertTrue(exact_topology_errors(self.architecture, mutated))
        case = next(item for item in self.document["adversarial_fixtures"]["cases"] if item["id"] == "deleted_node")
        self.assertEqual(case["observed"], "REJECTED")

    def test_visual_check_has_zero_required_failures(self):
        visual = self.document["standalone_visual_check"]
        self.assertEqual(visual["status"], "PASS")
        self.assertEqual(visual["containment_failures"], 0)
        self.assertEqual(visual["readability_failures"], 0)
        self.assertEqual(visual["viewer_chrome_failures"], 0)
        self.assertEqual(len(visual["required_viewport_observations"]), 6)
        self.assertTrue(all(item["ok"] for item in visual["required_viewport_observations"]))

    def test_repeatability_is_exact(self):
        repeatability = self.document["repeatability"]
        self.assertTrue(repeatability["ir_identical"])
        self.assertTrue(repeatability["artifact_identical"])
        self.assertEqual(repeatability["adapter_ir_first_sha256"], repeatability["adapter_ir_second_sha256"])
        self.assertEqual(repeatability["delivery_artifact_first_sha256"], repeatability["delivery_artifact_second_sha256"])

    def test_compatibility_and_current_boundaries_remain_pending(self):
        self.assertEqual(self.document["status"], "STANDALONE_EVIDENCE_PASS_COMPATIBILITY_PENDING")
        self.assertEqual(self.document["base_gate_results"]["immutable_tested_compatibility_envelope"], "PENDING_STEP22")
        admission = self.document["admission_decision"]
        self.assertFalse(admission["current_capability"])
        self.assertFalse(admission["registry_write"])
        self.assertEqual(admission["delta_extension"], "EXPERIMENTAL_EXTENSION_DEFERRED")

    def test_mutating_provenance_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["provenance"]["artifact_sha_bound"] = False
        self.assertTrue(validate(mutated))

    def test_mutating_zero_failure_census_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["standalone_visual_check"]["containment_failures"] = 1
        self.assertTrue(validate(mutated))

    def test_side_effect_and_successor_boundaries_are_closed(self):
        fixture = self.document["adversarial_fixtures"]
        self.assertFalse(fixture["provider_process_started"])
        self.assertFalse(fixture["credentials_or_sessions_accessed"])
        self.assertFalse(fixture["system_or_repository_mutation"])
        self.assertEqual(self.document["scope_freeze"]["task151"], "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
