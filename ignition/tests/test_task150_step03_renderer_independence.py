import copy
import json
import unittest

from tools.validate_task150_step03_renderer_independence import ARTIFACT_PATH, validate


class Task150Step03RendererIndependenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_contract_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_provenance_manifest_covers_all_nodes_and_edges(self):
        manifest = self.document["provenance_manifest"]
        self.assertEqual(len(manifest["node_records"]), 24)
        self.assertEqual(len(manifest["edge_records"]), 24)
        for record in manifest["node_records"] + manifest["edge_records"]:
            self.assertEqual(
                set(record),
                {"source_path", "canonical_or_source_id", "source_revision", "provenance_digest"},
            )

    def test_flow_and_provider_mutation_boundary(self):
        contract = self.document["adapter_contract"]
        self.assertEqual(contract["allowed_flow"], "CANONICAL_SOURCE -> PROVIDER_ADAPTER -> DERIVED_ARTIFACT")
        self.assertTrue(contract["reverse_flow_forbidden"])
        self.assertFalse(contract["repository_scan"])
        self.assertFalse(contract["canonical_write"])
        self.assertEqual(contract["provider_allowed_fields"], ["geometry", "route", "theme", "layout"])

    def test_provenance_digest_drift_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["provenance_manifest"]["node_records"][0]["provenance_digest"] = "0" * 64
        self.assertTrue(any("node provenance manifest" in error for error in validate(mutated)))

    def test_extra_or_missing_topology_id_is_not_allowed(self):
        mutated = copy.deepcopy(self.document)
        mutated["provenance_manifest"]["node_records"].append(copy.deepcopy(mutated["provenance_manifest"]["node_records"][0]))
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["provenance_manifest"]["edge_records"][0]["canonical_or_source_id"] = "invented-edge"
        self.assertTrue(validate(mutated))

    def test_reverse_or_semantic_authority_upgrade_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["adapter_contract"]["canonical_write"] = True
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["boundary"]["provider_can_change_semantic_relationships"] = True
        self.assertTrue(validate(mutated))

    def test_current_auth_and_live_boundaries_remain_closed(self):
        boundary = self.document["boundary"]
        self.assertEqual(boundary["current_integration"], "NOT_CURRENT_INTEGRATION")
        self.assertEqual(boundary["authenticated_channel_admission"], "NO_AUTHENTICATED_CHANNEL_ADMISSION")
        self.assertEqual(boundary["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")


if __name__ == "__main__":
    unittest.main()
