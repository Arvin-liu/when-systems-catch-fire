import copy
import json
import unittest

from tools.validate_task150_step07_architecture_delta_smoke import ARTIFACT_PATH, fixture_results, load_json, validate


class Task150Step07ArchitectureDeltaSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_and_evidence_files_pass(self):
        self.assertEqual(validate(self.document), [])

    def test_lineage_is_formal_and_provenance_only(self):
        lineage = self.document["lineage"]
        self.assertEqual(lineage["relationship"], "FORMAL_TASK149_LINEAGE_PROVENANCE_ONLY_TOPOLOGY_SAME")
        self.assertNotEqual(lineage["before"]["source_revision"], lineage["after"]["source_revision"])
        self.assertEqual(self.document["comparison"]["semantic_classification"]["provenance_changed"], True)
        self.assertEqual(self.document["comparison"]["semantic_classification"]["presentation_changed"], False)

    def test_delta_semantics_are_complete_and_zero_authored_changes(self):
        summary = self.document["comparison"]["semantic_classification"]
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["checks_passed"], 28)
        self.assertEqual(summary["check_count"], 28)
        self.assertEqual(summary["component_changes"], {"added":0,"changed":0,"evidenceChanged":0,"removed":0,"moved":0})
        self.assertEqual(summary["connection_changes"], {"added":0,"changed":0,"removed":0,"rerouted":0})

    def test_fail_closed_fixtures_all_match_expected_results(self):
        base = load_json(ARTIFACT_PATH.parent / "delta-evidence/task150-before.json")
        results = fixture_results(base)
        self.assertEqual([item["expected"] for item in results], [item["observed"] for item in results])
        self.assertEqual(len(results), 4)

    def test_extra_topology_cannot_be_accepted(self):
        mutated = copy.deepcopy(self.document)
        mutated["fixtures"]["results"][0]["expected"] = "PASS"
        self.assertTrue(validate(mutated))

    def test_geometry_or_provenance_movement_is_not_architecture_change(self):
        results = {item["id"]: item for item in fixture_results(load_json(ARTIFACT_PATH.parent / "delta-evidence/task150-before.json"))}
        self.assertEqual(results["geometry-moved"]["observed"], "PASS_TOPOLOGY_UNCHANGED_NOT_ARCHITECTURE_CHANGE")
        self.assertEqual(results["provenance-only"]["observed"], "PASS_PROVENANCE_ONLY")

    def test_delta_visual_blocker_and_current_boundary_remain_closed(self):
        self.assertEqual(self.document["comparison"]["delta_visual"]["status"], "FAIL_UPSTREAM_WRAPPER")
        self.assertEqual(self.document["scope_freeze"]["current_admission"], "NOT_ADMITTED")
        self.assertEqual(self.document["scope_freeze"]["authenticated_channels"], "NO_AUTHENTICATED_ADMISSION")

    def test_live_scope_remains_frozen(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["agent_reach"], "NO_CHANGE")
        self.assertEqual(scope["installation"], "NO_INSTALL_OR_AUTO_UPGRADE")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")


if __name__ == "__main__":
    unittest.main()
