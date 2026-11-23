import base64
import copy
import gzip
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from tools.operations import validate_responsibility_domain_registry as registry_validator
from tools.operations.validate_responsibility_domain_registry import (
    FORMAL_MAIN,
    MAIN_COMPONENTS_PATH,
    OWNER_ACCEPTANCE_SOURCE,
    OWNER_RELATION_ACCEPTANCE_SOURCE,
    REGISTRY_PATH,
    SOURCE_SNAPSHOT_PATH,
    derive_domain_views,
    validate,
)


class ResponsibilityDomainRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_candidate_registry_and_source_evidence_resolve(self):
        self.assertEqual(validate(self.registry), [])

    def test_q14_maturity_claims_are_bound_to_the_exact_owner_source(self):
        q14 = lambda registry: next(
            row for row in registry["domains"] if row["domain_id"] == "decision_support_mapping"
        )
        constraint = lambda registry: registry["owner_claim_constraints"][0]["maturity_claims"]
        self.assertEqual(validate(self.registry), [])

        mutations = []
        mature_engine = copy.deepcopy(self.registry)
        q14(mature_engine)["maturity"] = "A mature automated decision engine."
        mutations.append(("mature-engine-description", mature_engine))

        freshness_removed = copy.deepcopy(self.registry)
        del constraint(freshness_removed)["snapshot_freshness"]
        mutations.append(("freshness-removed", freshness_removed))

        freshness_reversed = copy.deepcopy(self.registry)
        constraint(freshness_reversed)["snapshot_freshness"] = "verified"
        mutations.append(("freshness-reversed", freshness_reversed))

        benefit_removed = copy.deepcopy(self.registry)
        del constraint(benefit_removed)["external_actual_decision_benefit"]
        mutations.append(("benefit-removed", benefit_removed))

        benefit_reversed = copy.deepcopy(self.registry)
        constraint(benefit_reversed)["external_actual_decision_benefit"] = "verified"
        mutations.append(("benefit-reversed", benefit_reversed))

        mature_claim = copy.deepcopy(self.registry)
        constraint(mature_claim)["mature_automated_decision_engine"] = True
        mutations.append(("mature-engine-claim", mature_claim))

        source_rebound = copy.deepcopy(self.registry)
        source_rebound["owner_claim_constraints"][0]["source_content_sha256"] = "0" * 64
        mutations.append(("source-hash-rebound", source_rebound))

        for label, mutated in mutations:
            with self.subTest(label=label):
                errors = validate(mutated, verify_sources=False)
                self.assertTrue(
                    any("Q14 maturity" in error for error in errors),
                    errors,
                )

    def test_global_claim_ceiling_is_a_pinned_candidate_boundary(self):
        self.assertEqual(validate(self.registry), [])
        fields = (
            "formal_main_current",
            "formal_merge_authorized",
            "other_component_relationships_owner_accepted",
            "validation_map_routes_authorized",
            "execution_authorized",
            "review_authorized",
            "publication_authorized",
            "external_action_authorized",
        )
        for field in fields:
            with self.subTest(field=field):
                mutated = copy.deepcopy(self.registry)
                mutated["claim_ceiling"][field] = True
                errors = validate(mutated, verify_sources=False)
                self.assertTrue(any("claim_ceiling differs" in error for error in errors), errors)

        rewritten = copy.deepcopy(self.registry)
        rewritten["claim_ceiling"] = "Validation Map routes and execution are authorized."
        errors = validate(rewritten, verify_sources=False)
        self.assertTrue(any("claim_ceiling differs" in error for error in errors), errors)

    def test_q14_shared_interface_requires_the_exact_two_endpoints(self):
        endpoint_mutations = (
            ["G"],
            ["G", "R"],
            ["G", "G", "decision_support_mapping"],
            ["G", "agent_execution_coordination"],
        )
        for endpoints in endpoint_mutations:
            with self.subTest(endpoints=endpoints):
                mutated = copy.deepcopy(self.registry)
                relation = next(
                    row
                    for row in mutated["component_relationship_decisions"]
                    if row["decision_id"] == "q14::G::shared_interface"
                )
                relation["interface_domain_ids"] = endpoints
                errors = validate(mutated, verify_sources=False)
                self.assertTrue(
                    any("endpoints must be exactly {G, decision_support_mapping}" in error for error in errors),
                    errors,
                )

    def test_q14_governance_interaction_is_proposed_without_full_tuple_acceptance(self):
        interaction = next(
            row
            for row in self.registry["inter_domain_interactions"]
            if row["from_domain_id"] == "G" and row["to_domain_id"] == "decision_support_mapping"
        )
        self.assertEqual(interaction["interaction_status"], "proposed")
        self.assertIsNone(interaction["owner_acceptance_record_id"])
        self.assertEqual(validate(self.registry), [])

    def test_inter_domain_interaction_cannot_inherit_q14_owner_acceptance(self):
        mutations = (
            ("exact-proposal", lambda row: None),
            ("unaccepted-component", lambda row: row["component_ids"].append("function_os")),
            ("interaction-type", lambda row: row.update(interaction_type="permission_grant")),
            ("from-domain", lambda row: row.update(from_domain_id="decision_support_mapping")),
            ("to-domain", lambda row: row.update(to_domain_id="O")),
            ("component-set", lambda row: row.update(component_ids=["q14"])),
            ("interaction-content", lambda row: row.update(interaction="Q14 is authorized to execute and publish.")),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                candidate = copy.deepcopy(self.registry)
                interaction = next(
                    row
                    for row in candidate["inter_domain_interactions"]
                    if row["from_domain_id"] == "G" and row["to_domain_id"] == "decision_support_mapping"
                )
                interaction["interaction_status"] = "owner_accepted"
                interaction["owner_acceptance_record_id"] = OWNER_ACCEPTANCE_SOURCE
                mutate(interaction)
                errors = validate(candidate, verify_sources=False)
                self.assertTrue(
                    any("full-tuple Owner acceptance" in error for error in errors),
                    errors,
                )

    def test_pinned_source_snapshot_validates_without_git_source_objects(self):
        registry_validator._pinned_source_blob.cache_clear()
        try:
            with patch.object(registry_validator, "_git_blob_if_available", return_value=None):
                for source_id, (_, _, expected_blob_sha1) in registry_validator.FIXED_SOURCE_ANCHORS.items():
                    if source_id not in {"identity_audit_r0_1", "previous_registry_candidate_a30"}:
                        continue
                    content = registry_validator._pinned_source_blob(source_id, str(SOURCE_SNAPSHOT_PATH))
                    self.assertEqual(registry_validator._git_blob_oid(content), expected_blob_sha1)
                self.assertEqual(validate(self.registry), [])
        finally:
            registry_validator._pinned_source_blob.cache_clear()

    def test_pinned_source_snapshot_tampering_fails_closed(self):
        snapshot = json.loads(gzip.decompress(SOURCE_SNAPSHOT_PATH.read_bytes()).decode("utf-8"))
        entry = snapshot["sources"]["previous_registry_candidate_a30"]
        content = bytearray(base64.b64decode(entry["content_base64"], validate=True))
        content[0] ^= 1
        entry["content_base64"] = base64.b64encode(content).decode("ascii")
        with tempfile.TemporaryDirectory() as directory:
            snapshot_path = Path(directory) / "tampered-source-snapshot.json.gz"
            snapshot_bytes = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            snapshot_path.write_bytes(gzip.compress(snapshot_bytes, mtime=0))
            registry_validator._pinned_source_blob.cache_clear()
            try:
                with patch.object(registry_validator, "SOURCE_SNAPSHOT_PATH", snapshot_path), patch.object(
                    registry_validator, "_git_blob_if_available", return_value=None
                ):
                    errors = validate(self.registry)
                self.assertTrue(any("source snapshot Git blob SHA-1 mismatch" in error for error in errors), errors)
            finally:
                registry_validator._pinned_source_blob.cache_clear()

    def test_accepted_domain_definitions_and_boundaries_are_content_pinned(self):
        accepted_new_domains = [
            "agent_execution_coordination",
            "formal_repository_change_coordination",
            "bounded_function_execution",
            "decision_support_mapping",
        ]
        for domain_id in accepted_new_domains:
            for field, boundary_key in (
                ("definition", None),
                ("responsibility_boundary", "included"),
                ("responsibility_boundary", "excluded"),
            ):
                with self.subTest(domain_id=domain_id, field=field, boundary_key=boundary_key):
                    mutated = copy.deepcopy(self.registry)
                    domain = next(row for row in mutated["domains"] if row["domain_id"] == domain_id)
                    if field == "definition":
                        domain[field] += " Tampered."
                    else:
                        domain[field][boundary_key][0] += " Tampered."
                    errors = validate(mutated, verify_sources=False)
                    self.assertTrue(any("fingerprint mismatch" in error for error in errors), errors)

    def test_acceptance_record_cannot_expand_or_forge_the_accepted_domain_set(self):
        expanded_list_only = copy.deepcopy(self.registry)
        expanded_list_only["owner_acceptance_records"][0]["accepted_domain_ids"].append("unaccepted_domain")
        self.assertTrue(
            any(
                "exact pinned accepted set" in error
                for error in validate(expanded_list_only, verify_sources=False)
            )
        )

        expanded = copy.deepcopy(self.registry)
        extra = copy.deepcopy(expanded["domains"][0])
        extra.update(
            domain_id="forged_owner_domain",
            name_zh="伪造接受领域",
            aliases=[],
            definition="A forged accepted domain.",
            responsibility_boundary={
                "included": ["A forged responsibility."],
                "excluded": ["Validation routes."],
            },
            domain_status="owner_accepted",
            owner_acceptance_record_id=OWNER_ACCEPTANCE_SOURCE,
        )
        expanded["domains"].append(extra)
        expanded["owner_acceptance_records"][0]["accepted_domain_ids"].append("forged_owner_domain")
        self.assertTrue(
            any("exact pinned accepted set" in error for error in validate(expanded, verify_sources=False))
        )

        disguised = copy.deepcopy(self.registry)
        disguised["domains"].append(extra)
        errors = validate(disguised, verify_sources=False)
        self.assertTrue(any("owner-accepted domain lacks its matching acceptance record" in error for error in errors))

    def test_owner_accepted_new_domain_cannot_be_demoted(self):
        mutated = copy.deepcopy(self.registry)
        domain = next(row for row in mutated["domains"] if row["domain_id"] == "bounded_function_execution")
        domain["domain_status"] = "proposed"
        domain["owner_acceptance_record_id"] = None
        errors = validate(mutated, verify_sources=False)
        self.assertTrue(any("pinned Owner-accepted domain was demoted" in error for error in errors), errors)

    def test_owner_decision_source_and_fingerprint_bindings_cannot_be_rewritten(self):
        mutations = []

        changed_source_hash = copy.deepcopy(self.registry)
        changed_source_hash["sources"][-1]["body_sha256"] = "0" * 64
        mutations.append(changed_source_hash)

        changed_both_summaries = copy.deepcopy(self.registry)
        changed_both_summaries["sources"][-1]["decision_content_summary"] = "A forged summary."
        changed_both_summaries["owner_acceptance_records"][0]["decision_content_summary"] = "A forged summary."
        mutations.append(changed_both_summaries)

        changed_fingerprint = copy.deepcopy(self.registry)
        changed_fingerprint["owner_acceptance_records"][0]["accepted_domain_fingerprints"][0][
            "fingerprint_sha256"
        ] = "0" * 64
        mutations.append(changed_fingerprint)

        changed_pointer = copy.deepcopy(self.registry)
        changed_pointer["owner_acceptance_records"][0]["accepted_domain_fingerprints"][0]["source_ref"][
            "json_pointer"
        ] = "/domains/2"
        mutations.append(changed_pointer)

        for mutated in mutations:
            with self.subTest(mutation=mutated["owner_acceptance_records"][0]["accepted_domain_fingerprints"][0]):
                self.assertNotEqual(validate(mutated, verify_sources=False), [])

    def test_component_evidence_pointer_cannot_be_swapped_to_another_component(self):
        mutated = copy.deepcopy(self.registry)
        identity = mutated["component_identity_snapshot"][0]
        identity["source_ref"]["json_pointer"] = "/components/1"
        errors = validate(mutated)
        self.assertTrue(
            any("identifies components" in error or "exact main registry row" in error for error in errors),
            errors,
        )

    def test_prior_candidate_pointer_must_resolve_to_the_same_component_relation(self):
        mutated = copy.deepcopy(self.registry)
        function_os = next(
            row for row in mutated["component_relationship_decisions"]
            if row["component_id"] == "function_os" and row["domain_id"] == "bounded_function_execution"
        )
        prior_ref = next(
            ref for ref in function_os["evidence_refs"]
            if ref.get("source_id") == "previous_registry_candidate_a30"
        )
        prior_ref["json_pointer"] = "/component_mappings/10/domain_relations/0"
        errors = validate(mutated)
        self.assertTrue(
            any("identifies components" in error or "different component" in error or "does not match component/domain/type" in error for error in errors),
            errors,
        )

    def test_identity_audit_evidence_key_must_name_the_same_component_row(self):
        mutated = copy.deepcopy(self.registry)
        q14 = next(
            row for row in mutated["component_relationship_decisions"]
            if row["component_id"] == "q14" and row["domain_id"] == "decision_support_mapping"
        )
        audit_ref = next(ref for ref in q14["evidence_refs"] if ref.get("source_id") == "identity_audit_r0_1")
        audit_ref["location"] = "§逐项身份记录 item 40 (line 207)"
        errors = validate(mutated)
        self.assertTrue(any("does not identify any expected component" in error for error in errors), errors)

    def test_external_consumer_is_explicit_and_remains_proposed(self):
        interface = self.registry["external_consumer_interfaces"][0]
        domain_ids = {row["domain_id"] for row in self.registry["domains"]}
        self.assertEqual(interface["target_type"], "external_consumer")
        self.assertEqual(interface["direction"], "external_consumer_invokes_source_domain")
        self.assertNotIn(interface["external_consumer_id"], domain_ids)
        self.assertEqual(interface["interface_status"], "proposed")
        self.assertIsNone(interface["owner_acceptance_record_id"])
        self.assertEqual(validate(self.registry), [])

        forged_domain_target = copy.deepcopy(self.registry)
        forged_domain_target["external_consumer_interfaces"][0]["external_consumer_id"] = "decision_support_mapping"
        errors = validate(forged_domain_target, verify_sources=False)
        self.assertTrue(any("must use an external identity" in error for error in errors), errors)

    def test_external_interface_cannot_be_owner_accepted_without_a_record(self):
        mutated = copy.deepcopy(self.registry)
        mutated["external_consumer_interfaces"][0]["interface_status"] = "owner_accepted"
        errors = validate(mutated, verify_sources=False)
        self.assertTrue(any("owner_acceptance_record_id" in error for error in errors), errors)

    def test_external_acceptance_must_match_component_type_and_target(self):
        original = self.registry["external_consumer_interfaces"][0]
        binding = {
            "source_domain_id": original["source_domain_id"],
            "target_type": original["target_type"],
            "external_consumer_id": original["external_consumer_id"],
            "direction": original["direction"],
            "interface_type": original["interface_type"],
            "component_ids": copy.deepcopy(original["component_ids"]),
            "interaction": original["interaction"],
        }
        for field, changed_value in (
            ("component_ids", ["function_os"]),
            ("interface_type", "forged_interface_type"),
            ("external_consumer_id", "decision_support_mapping"),
        ):
            with self.subTest(field=field):
                mutated = copy.deepcopy(self.registry)
                accepted_binding = copy.deepcopy(binding)
                accepted_binding[field] = changed_value
                mutated["owner_acceptance_records"][0]["accepted_external_interfaces"] = [accepted_binding]
                interface = mutated["external_consumer_interfaces"][0]
                interface["interface_status"] = "owner_accepted"
                interface["owner_acceptance_record_id"] = OWNER_ACCEPTANCE_SOURCE
                interface["evidence_refs"].append(
                    {
                        "source_id": OWNER_ACCEPTANCE_SOURCE,
                        "comment_id": 7093080490,
                        "url": "https://github.com/Arvin-liu/1111/issues/164#issuecomment-7093080490",
                        "evidence_key": "accepted responsibility-domain set and boundaries; Q14 primary/shared-interface principle",
                    }
                )
                errors = validate(mutated, verify_sources=False)
                self.assertTrue(
                    any("does not match the accepted target/direction/type/components" in error for error in errors),
                    errors,
                )

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
        for row in decisions:
            if row["decision_status"] == "owner_accepted":
                self.assertEqual(row["owner_acceptance_record_id"], OWNER_RELATION_ACCEPTANCE_SOURCE)
        for domain in self.registry["domains"]:
            self.assertEqual(domain["owner_acceptance_record_id"], OWNER_ACCEPTANCE_SOURCE)

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
