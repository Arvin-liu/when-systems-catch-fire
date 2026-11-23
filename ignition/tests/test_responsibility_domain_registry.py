import copy
import json
import unittest
from collections import Counter
from pathlib import Path

from tools.operations.validate_responsibility_domain_registry import (
    FORMAL_MAIN,
    MAIN_COMPONENTS_PATH,
    OWNER_ACCEPTANCE_SOURCE,
    REGISTRY_PATH,
    derive_domain_views,
    validate,
)


class ResponsibilityDomainRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_candidate_registry_and_source_evidence_resolve(self):
        self.assertEqual(validate(self.registry), [])

    def test_source_matrix_facts_remain_separate_from_relationship_decisions(self):
        rows = self.registry["source_matrix_snapshot"]["document"]["components"]
        source_counts = Counter(row["classification_status"] for row in rows)
        self.assertEqual(
            source_counts,
            Counter({"UNRESOLVED": 86, "SINGLE_DOMAIN_PRIMARY": 18, "SHARED_CROSS_DOMAIN": 2}),
        )

        decisions = self.registry["component_relationship_decisions"]
        states = Counter(row["decision_status"] for row in decisions)
        self.assertEqual(states["source_declared"], 28)
        self.assertEqual(states["proposed"], 107)
        self.assertEqual(states["owner_accepted"], 2)
        self.assertEqual(states["unresolved"], 2)
        q14 = next(row for row in rows if row["component_id"] == "q14")
        self.assertEqual(q14["classification_status"], "UNRESOLVED")
        self.assertIsNone(q14["primary_responsibility_domain"])

        accepted = {
            (row["component_id"], row["domain_id"], row["relationship_type"])
            for row in decisions
            if row["decision_status"] == "owner_accepted"
        }
        self.assertEqual(
            accepted,
            {
                ("q14", "decision_support_mapping", "primary"),
                ("q14", "G", "shared_interface"),
            },
        )

    def test_rg_definitions_match_the_exact_matrix_text(self):
        matrix = self.registry["source_matrix_snapshot"]["document"]
        domains = {row["domain_id"]: row for row in self.registry["domains"]}
        for domain_id in ("R", "O", "G"):
            self.assertEqual(domains[domain_id]["definition"], matrix["domain_definitions"][domain_id])

    def test_embedded_source_matrix_cannot_drift_from_its_pinned_commit(self):
        mutated = copy.deepcopy(self.registry)
        mutated["source_matrix_snapshot"]["document"]["components"][0]["canonical_target"] += "#tampered"
        self.assertTrue(
            any("differs from its exact source commit" in error for error in validate(mutated))
        )

    def test_new_domains_are_dynamic_and_have_no_fixed_count_ceiling(self):
        mutated = copy.deepcopy(self.registry)
        source_ref = {
            "source_id": "formal_main_component_registry",
            "commit": FORMAL_MAIN,
            "path": MAIN_COMPONENTS_PATH,
            "json_pointer": "/components/0",
            "blob_sha1": "a008b89b05efea82967c0fb0bb0ba70574bcff8f",
        }
        for index in range(40):
            mutated["domains"].append(
                {
                    "domain_id": f"open_extension_{index}",
                    "name_zh": f"开放扩展域 {index}",
                    "aliases": [],
                    "definition": f"A test-only extension domain {index}.",
                    "responsibility_boundary": {
                        "included": ["A uniquely named responsibility used by this validator test."],
                        "excluded": ["Validation routes and execution permissions."],
                    },
                    "inputs": ["Source-backed inputs."],
                    "outputs": ["Bounded outputs."],
                    "consumers": ["Declared consumers."],
                    "inter_domain_dependencies": [],
                    "lifecycle": "TEST_ONLY_NOT_REGISTERED",
                    "maturity": "Synthetic test fixture; no product claim.",
                    "prior_candidate_status": "NOT_IN_PRIOR_CANDIDATE",
                    "domain_status": "proposed",
                    "owner_acceptance_record_id": None,
                    "evidence_refs": [copy.deepcopy(source_ref)],
                }
            )
        self.assertEqual(validate(mutated), [])
        self.assertEqual(mutated["validation_domain_associations"], [])

        schema = json.loads(
            (REGISTRY_PATH.parents[2] / "schemas/operations/responsibility-domain-registry-r1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("enum", schema["$defs"]["domainId"])
        self.assertNotIn("maxItems", schema["properties"]["domains"])

    def test_duplicate_ids_and_casefold_name_or_alias_collisions_fail(self):
        duplicate_id = copy.deepcopy(self.registry)
        duplicate_id["domains"].append(copy.deepcopy(duplicate_id["domains"][0]))
        self.assertTrue(any("duplicate domain_id" in error for error in validate(duplicate_id, verify_sources=False)))

        name_collision = copy.deepcopy(self.registry)
        extra = copy.deepcopy(name_collision["domains"][0])
        extra.update(
            domain_id="new_open_domain",
            name_zh="新领域",
            aliases=["r"],
            domain_status="proposed",
            owner_acceptance_record_id=None,
            evidence_refs=[copy.deepcopy(name_collision["component_identity_snapshot"][0]["source_ref"])],
        )
        name_collision["domains"].append(extra)
        self.assertTrue(any("case-folding" in error for error in validate(name_collision, verify_sources=False)))

    def test_unknown_component_or_domain_fails_closed(self):
        unknown_component = copy.deepcopy(self.registry)
        unknown_component["component_relationship_decisions"][0]["component_id"] = "not_a_component"
        self.assertTrue(any("unknown component" in error for error in validate(unknown_component, verify_sources=False)))

        unknown_domain = copy.deepcopy(self.registry)
        unknown_domain["component_relationship_decisions"][0]["domain_id"] = "not_a_domain"
        self.assertTrue(any("unknown domain" in error for error in validate(unknown_domain, verify_sources=False)))

    def test_unknown_source_and_dangling_evidence_pointer_fail_closed(self):
        missing_source = copy.deepcopy(self.registry)
        missing_source["domains"][0]["evidence_refs"][0]["source_id"] = "source_not_registered"
        self.assertTrue(any("unknown source_id" in error for error in validate(missing_source, verify_sources=False)))

        dangling_pointer = copy.deepcopy(self.registry)
        ref = next(
            ref
            for ref in dangling_pointer["domains"][0]["evidence_refs"]
            if ref.get("path") and ref.get("json_pointer")
        )
        ref["json_pointer"] = "/definitely/not/a/real/pointer"
        self.assertTrue(any("dangling JSON Pointer" in error for error in validate(dangling_pointer)))

    def test_duplicate_relationship_fails_closed(self):
        mutated = copy.deepcopy(self.registry)
        mutated["component_relationship_decisions"].append(
            copy.deepcopy(mutated["component_relationship_decisions"][0])
        )
        errors = validate(mutated, verify_sources=False)
        self.assertTrue(any("duplicate decision_id" in error for error in errors))
        self.assertTrue(any("duplicate logical" in error for error in errors))

    def test_shared_interface_view_can_overlap_primary_membership(self):
        views = derive_domain_views(self.registry)
        component_id = "epistemic_governance_kernel"
        self.assertIn(component_id, views["G"]["core_components"])
        self.assertIn(component_id, views["G"]["interfaces"])

        accepted_views = derive_domain_views(self.registry, {"owner_accepted"})
        self.assertEqual(accepted_views["decision_support_mapping"]["core_components"], ["q14"])
        self.assertIn("q14", accepted_views["G"]["interfaces"])

    def test_responsibility_domain_does_not_create_validation_route_or_target(self):
        self.assertEqual(self.registry["validation_domain_associations"], [])
        validation_schema = json.loads(
            (REGISTRY_PATH.parents[2] / "schemas/operations/component-validation-map-r1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(validation_schema["$defs"]["domain"]["enum"], ["R", "O", "G"])
        self.assertNotIn(
            "decision_support_mapping",
            validation_schema["$defs"]["domain"]["enum"],
        )

    def test_route_crosswalk_needs_an_existing_target_and_separate_authorization(self):
        mutated = copy.deepcopy(self.registry)
        mutated["validation_domain_associations"].append(
            {
                "component_id": "ai_guide",
                "responsibility_domain_id": "decision_support_mapping",
                "validation_domain_id": "O",
                "validation_target_id": "not_an_existing_target",
                "evidence_refs": [
                    copy.deepcopy(
                        next(
                            row["source_ref"]
                            for row in self.registry["component_identity_snapshot"]
                            if row["component_id"] == "ai_guide"
                        )
                    )
                ],
                "migration_authorization_ref": {
                    "source_id": OWNER_ACCEPTANCE_SOURCE,
                    "comment_id": 7093080490,
                    "url": "https://github.com/Arvin-liu/1111/issues/164#issuecomment-7093080490",
                },
            }
        )
        errors = validate(mutated, verify_sources=False)
        self.assertTrue(any("target is not declared" in error for error in errors))
        self.assertTrue(any("separate explicit Owner migration-authorization" in error for error in errors))

    def test_independent_closed_enums_remain_closed(self):
        ignition_root = REGISTRY_PATH.parents[2]
        component_schema = json.loads(
            (ignition_root / "schemas/operations/project-components.schema.json").read_text(encoding="utf-8")
        )
        topology_schema = json.loads(
            (ignition_root / "schemas/operations/change-propagation-topology.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            component_schema["$defs"]["component"]["properties"]["component_type"]["enum"],
            [
                "front_door", "architecture_layer", "cross_layer_control_plane", "foundation_core",
                "model_projection", "operation_control", "governance_constraint", "publication_chain",
                "feedback_interface", "interpretation_boundary", "repository_infrastructure", "historical_asset",
            ],
        )
        self.assertEqual(
            topology_schema["$defs"]["relation"]["properties"]["relation_domain"]["enum"],
            ["substantive_causal_candidate", "repository_dependency", "synchronization_obligation"],
        )


if __name__ == "__main__":
    unittest.main()
