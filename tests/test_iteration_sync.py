import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.validate_iteration_sync import (
    REGISTRY_PATH,
    ROOT,
    infer_seal_path,
    load_json,
    required_registry_surfaces,
    resolve_era_registry,
    validate_all,
    validate_custom,
    validate_manifest_bindings,
    validate_manifest_schema,
    validate_registry,
)


FRONT_DOORS = [
    "README.md",
    "docs/project-current-state.md",
    "AI-HANDOFF.md",
    "AI-START-HERE.md",
    "llms.txt",
    "SUMMARY.md",
    "CHANGELOG.md",
]


def valid_manifest():
    changed = [
        ".github/workflows/foundation-validation.yml",
        "AI-HANDOFF.md",
        "AI-START-HERE.md",
        "CHANGELOG.md",
        "ITERATION.md",
        "README.md",
        "SUMMARY.md",
        "data/operations/121q24-gap-ledger.json",
        "data/operations/iterations/121Q24.json",
        "docs/VERSIONING.md",
        "docs/project-current-state.md",
        "llms.txt",
        "reports/operations/121Q24-completion-seal.json",
        "reports/operations/121Q24-current-state-reconciliation.md",
        "schemas/operations/iteration-manifest.schema.json",
        "templates/operations/execution-result-template.md",
        "templates/operations/independent-review-template.md",
        "templates/operations/task-command-template.md",
        "tests/test_iteration_sync.py",
        "tools/validate_iteration_sync.py",
    ]
    return {
        "method_version": "1.0.0",
        "task_id": "121Q24",
        "change_classification": ["OPERATIONS_METHOD", "RELEASE_OR_CURRENT_STATE_SYNC", "INTERFACE_CHANGE"],
        "verified_start": {"main_head": "7" * 40, "source": "test", "verified_at": "2026-07-16"},
        "branch_pr": {"branch": "test", "pr_number": 56, "base": "main", "base_head": "7" * 40, "draft": True, "merged": False},
        "head_binding": {
            "mode": "external_exact_head_attestation",
            "pr_number": 56,
            "authority": "pull_request_body_and_1111_receipt",
            "receipt_path": "agent-results/IGNITION-20260716-121Q24C-result.md",
            "embedded_exact_current_head": False,
            "live_refetch_required": True,
            "explanation": "Exact final head and CI are recorded externally after push.",
        },
        "gap": {"summary": "gap", "evidence": ["evidence"], "smallest_material_action": "action"},
        "claim_ceiling": "candidate_only",
        "status": {"candidate": True, "ready_for_gpt_verification": True, "accepted": False, "merged": False, "current": False},
        "impact_matrix": [
            {"surface": path, "decision": "CHANGE", "reason": "changed"}
            for path in changed
        ] + [
            {"surface": "ARCHITECTURE.md", "decision": "NO_CHANGE_WITH_REASON", "reason": "not architectural"},
            {"surface": "FOUNDATION.md", "decision": "NO_CHANGE_WITH_REASON", "reason": "not foundation"},
            {"surface": "LICENSES", "decision": "NO_CHANGE_WITH_REASON", "reason": "no license change"},
        ],
        "changed_surfaces": changed,
        "explicitly_unaffected_surfaces": ["Psi0 source text", "085 architecture freeze assets"],
        "required_synchronization_decisions": ["README links to ITERATION.md."],
        "schema_tools_tests_workflows_reports_changed": [
            "schemas/operations/iteration-manifest.schema.json",
            "tools/validate_iteration_sync.py",
            "tests/test_iteration_sync.py",
            ".github/workflows/foundation-validation.yml",
            "reports/operations/121Q24-current-state-reconciliation.md",
            "reports/operations/121Q24-completion-seal.json",
        ],
        "validation": {
            "local": [{"name": "iteration-sync", "status": "PASS", "evidence": "local pass"}],
            "remote": [
                {"name": "foundation-validation", "status": "SUCCESS", "evidence": "historical", "evidence_scope": "historical_subject_head_only", "subject_head": "5" * 40, "run_id": 1, "conclusion": "success"},
                {"name": "function-os-ci", "status": "SUCCESS", "evidence": "historical", "evidence_scope": "historical_subject_head_only", "subject_head": "5" * 40, "run_id": 2, "conclusion": "success"},
            ],
            "external_exact_head_policy": {
                "required": True,
                "authority": "pull_request_body_and_1111_receipt",
                "required_workflows": ["foundation-validation", "function-os-ci"],
                "live_refetch_before_acceptance_or_merge": True,
            },
        },
        "rollback_strategy": "close PR",
        "remaining_limitations": ["candidate only"],
        "receipt_location": "agent-results/IGNITION-20260716-121Q24C-result.md",
    }


def valid_current_manifest():
    manifest = valid_manifest()
    manifest["branch_pr"]["draft"] = False
    manifest["branch_pr"]["merged"] = True
    manifest["branch_pr"]["merge_commit"] = "b" * 40
    manifest["head_binding"]["receipt_path"] = "agent-results/IGNITION-20260716-121Q24D-result.md"
    manifest["claim_ceiling"] = "current_operation_method_capability_only"
    manifest["status"] = {
        "candidate": True,
        "ready_for_gpt_verification": True,
        "accepted": True,
        "merged": True,
        "current": True,
    }
    manifest["receipt_location"] = "agent-results/IGNITION-20260716-121Q24D-result.md"
    return manifest


def valid_seal():
    m = valid_manifest()
    return {
        "task_id": "121Q24",
        "status": "READY_FOR_GPT_VERIFICATION_CANDIDATE_ONLY",
        "method_version": m["method_version"],
        "phase_a": {"merged_pr": 55, "accepted_head": "1" * 40, "merge_commit": m["branch_pr"]["base_head"]},
        "phase_b": {
            "draft_pr": 56,
            "branch": m["branch_pr"]["branch"],
            "base_head": m["branch_pr"]["base_head"],
            "head_binding": {
                "mode": m["head_binding"]["mode"],
                "authority": m["head_binding"]["authority"],
                "receipt_path": m["head_binding"]["receipt_path"],
                "embedded_exact_current_head": False,
                "live_refetch_required": True,
            },
            "claim_ceiling": m["claim_ceiling"],
        },
        "lifecycle": m["status"],
    }


def valid_current_seal():
    m = valid_current_manifest()
    seal = valid_seal()
    seal["status"] = "MERGED_AND_CURRENT_REPOSITORY_OPERATION_CAPABILITY"
    seal["phase_b"]["merged_pr"] = m["branch_pr"]["pr_number"]
    seal["phase_b"]["merge_commit"] = m["branch_pr"]["merge_commit"]
    seal["phase_b"]["head_binding"]["receipt_path"] = m["head_binding"]["receipt_path"]
    seal["phase_b"]["claim_ceiling"] = m["claim_ceiling"]
    seal["lifecycle"] = m["status"]
    return seal


class IterationSyncTests(unittest.TestCase):
    def test_iteration_sync_manifest_validates(self):
        result = validate_all()
        self.assertEqual(result["status"], "PASS")
        self.assertGreaterEqual(result["checked"], 1)

    def test_ready_candidate_requires_pr_number(self):
        manifest = valid_manifest()
        manifest["branch_pr"]["pr_number"] = None
        with self.assertRaisesRegex(AssertionError, "requires PR number"):
            validate_custom(manifest, __file__, valid_seal())

    def test_valid_cumulative_current_lifecycle(self):
        validate_custom(valid_current_manifest(), __file__, valid_current_seal())

    def test_pending_validation_is_rejected(self):
        manifest = valid_manifest()
        manifest["validation"]["remote"][0]["status"] = "PENDING"
        with self.assertRaisesRegex(AssertionError, "unresolved validation"):
            validate_custom(manifest, __file__, valid_seal())

    def test_stale_ci_mislabeled_as_current_final_is_rejected(self):
        manifest = valid_manifest()
        manifest["validation"]["remote"][0]["evidence_scope"] = "current_final"
        with self.assertRaisesRegex(AssertionError, "mislabeled as current-final"):
            validate_custom(manifest, __file__, valid_seal())

    def test_old_candidate_head_contract_is_rejected_by_schema(self):
        manifest = valid_manifest()
        manifest["candidate_head"] = "5" * 40
        manifest["candidate_head_note"] = "claimed current final head"
        with self.assertRaisesRegex(AssertionError, "schema error"):
            from tools.validate_iteration_sync import validate_manifest_schema
            validate_manifest_schema(manifest, __file__)

    def test_embedded_current_head_claim_is_rejected(self):
        manifest = valid_manifest()
        manifest["head_binding"]["embedded_exact_current_head"] = True
        with self.assertRaisesRegex(AssertionError, "cannot claim embedded exact current self HEAD"):
            validate_custom(manifest, __file__, valid_seal())

    def test_missing_external_attestation_authority_is_rejected(self):
        manifest = valid_manifest()
        manifest["head_binding"]["authority"] = ""
        with self.assertRaisesRegex(AssertionError, "externally resolvable attestation authority"):
            validate_custom(manifest, __file__, valid_seal())

    def test_ready_candidate_requires_external_exact_head_policy(self):
        manifest = valid_manifest()
        manifest["validation"]["external_exact_head_policy"]["required"] = False
        with self.assertRaisesRegex(AssertionError, "requires external exact-head attestation policy"):
            validate_custom(manifest, __file__, valid_seal())

    def test_seal_head_binding_mode_mismatch_is_rejected(self):
        seal = valid_seal()
        seal["phase_b"]["head_binding"]["mode"] = "embedded"
        with self.assertRaisesRegex(AssertionError, "seal head-binding mode mismatch"):
            validate_custom(valid_manifest(), __file__, seal)

    def test_seal_attestation_authority_mismatch_is_rejected(self):
        seal = valid_seal()
        seal["phase_b"]["head_binding"]["authority"] = "other"
        with self.assertRaisesRegex(AssertionError, "seal attestation authority mismatch"):
            validate_custom(valid_manifest(), __file__, seal)

    def test_duplicate_impact_surface_is_rejected(self):
        manifest = valid_manifest()
        manifest["impact_matrix"].append(copy.deepcopy(manifest["impact_matrix"][0]))
        with self.assertRaisesRegex(AssertionError, "duplicate impact_matrix"):
            validate_custom(manifest, __file__, valid_seal())

    def test_change_decision_must_be_declared_changed(self):
        manifest = valid_manifest()
        manifest["changed_surfaces"].remove("README.md")
        with self.assertRaisesRegex(AssertionError, "CHANGE decision"):
            validate_custom(manifest, __file__, valid_seal())

    def test_declared_changed_path_must_exist(self):
        manifest = valid_manifest()
        manifest["changed_surfaces"].append("missing/path.md")
        manifest["impact_matrix"].append({"surface": "missing/path.md", "decision": "CHANGE", "reason": "test"})
        with self.assertRaisesRegex(AssertionError, "does not exist"):
            validate_custom(manifest, __file__, valid_seal())

    def test_completion_seal_mismatch_is_rejected(self):
        seal = valid_seal()
        seal["phase_b"]["draft_pr"] = 57
        with self.assertRaisesRegex(AssertionError, "seal PR mismatch"):
            validate_custom(valid_manifest(), __file__, seal)

    def test_unaccepted_ready_non_draft_is_rejected(self):
        manifest = valid_manifest()
        manifest["branch_pr"]["draft"] = False
        with self.assertRaisesRegex(AssertionError, "unaccepted ready candidate must remain Draft"):
            validate_custom(manifest, __file__, valid_seal())

    def test_accepted_merged_current_draft_is_rejected(self):
        manifest = valid_current_manifest()
        manifest["branch_pr"]["draft"] = True
        with self.assertRaisesRegex(AssertionError, "Draft cannot be accepted|must not remain Draft"):
            validate_custom(manifest, __file__, valid_current_seal())

    def test_merged_without_accepted_is_rejected(self):
        manifest = valid_current_manifest()
        manifest["status"]["accepted"] = False
        with self.assertRaisesRegex(AssertionError, "merged cannot be true unless accepted"):
            validate_custom(manifest, __file__, valid_current_seal())

    def test_current_without_merged_is_rejected(self):
        manifest = valid_current_manifest()
        manifest["status"]["merged"] = False
        manifest["branch_pr"]["merged"] = False
        with self.assertRaisesRegex(AssertionError, "current cannot be true unless merged"):
            validate_custom(manifest, __file__, valid_current_seal())

    def test_merged_requires_merge_commit(self):
        manifest = valid_current_manifest()
        del manifest["branch_pr"]["merge_commit"]
        with self.assertRaisesRegex(AssertionError, "requires valid merge commit"):
            validate_custom(manifest, __file__, valid_current_seal())

    def test_malformed_merge_commit_is_rejected(self):
        manifest = valid_current_manifest()
        manifest["branch_pr"]["merge_commit"] = "not-a-sha"
        with self.assertRaisesRegex(AssertionError, "requires valid merge commit"):
            validate_custom(manifest, __file__, valid_current_seal())

    def test_manifest_seal_merge_commit_disagreement_is_rejected(self):
        seal = valid_current_seal()
        seal["phase_b"]["merge_commit"] = "c" * 40
        with self.assertRaisesRegex(AssertionError, "seal merge commit mismatch"):
            validate_custom(valid_current_manifest(), __file__, seal)

    def test_candidate_only_seal_after_merge_is_rejected(self):
        seal = valid_current_seal()
        seal["status"] = "READY_FOR_GPT_VERIFICATION_CANDIDATE_ONLY"
        with self.assertRaisesRegex(AssertionError, "seal remains candidate-only after merge"):
            validate_custom(valid_current_manifest(), __file__, seal)

    def test_candidate_only_claim_ceiling_after_merge_is_rejected(self):
        manifest = valid_current_manifest()
        manifest["claim_ceiling"] = "validated_operation_method_candidate_only"
        with self.assertRaisesRegex(AssertionError, "candidate-only claim ceiling"):
            validate_custom(manifest, __file__, valid_current_seal())

    def test_false_current_final_ci_claim_after_merge_is_rejected(self):
        manifest = valid_current_manifest()
        manifest["validation"]["remote"][0]["evidence_scope"] = "current_final"
        with self.assertRaisesRegex(AssertionError, "mislabeled as current-final"):
            validate_custom(manifest, __file__, valid_current_seal())

    def test_draft_cannot_be_current(self):
        manifest = valid_manifest()
        manifest["status"]["current"] = True
        with self.assertRaisesRegex(AssertionError, "current cannot be true|Draft cannot"):
            validate_custom(manifest, __file__, valid_seal())

    def q25_documents(self):
        registry = validate_registry(load_json(REGISTRY_PATH))
        q25_path = ROOT / "data/operations/iterations/121Q25.json"
        q25b_path = ROOT / "data/operations/iterations/121Q25B.json"
        q25 = load_json(q25_path)
        q25b = load_json(q25b_path)
        q25_seal = load_json(infer_seal_path(q25))
        q25b_seal = load_json(infer_seal_path(q25b))
        return registry, q25_path, q25, q25_seal, q25b_path, q25b, q25b_seal

    def q25c_document(self, *, current=False):
        registry = validate_registry(load_json(REGISTRY_PATH))
        path = ROOT / "data/operations/iterations/121Q25C.json"
        manifest = load_json(path)
        seal = load_json(infer_seal_path(manifest))
        if not current:
            manifest["branch_pr"].update({"draft": True, "merged": False})
            manifest["branch_pr"].pop("merge_commit", None)
            manifest["head_binding"]["receipt_path"] = "agent-results/IGNITION-20260716-121Q25C-result.md"
            manifest["receipt_location"] = "agent-results/IGNITION-20260716-121Q25C-result.md"
            manifest["claim_ceiling"] = "validated_lifecycle_gated_whole_project_synchronization_candidate_only"
            manifest["status"].update({"accepted": False, "merged": False, "current": False})
            manifest["completion_state"].update({"external_synchronization_attested": False, "project_synchronization_complete": False})
            manifest["synchronization_closure"]["external_attestations"][0].update({"status": "pending", "evidence_refs": ["external:pr_body:57", "external:1111_receipt:IGNITION-20260716-121Q25C-result.md"]})
            seal["status"] = "READY_FOR_GPT_VERIFICATION_CANDIDATE_ONLY"
            seal["phase_b"].pop("merge_commit", None)
            seal["phase_b"]["head_binding"]["receipt_path"] = manifest["head_binding"]["receipt_path"]
            seal["phase_b"]["claim_ceiling"] = manifest["claim_ceiling"]
            seal["lifecycle"] = copy.deepcopy(manifest["status"])
            seal["completion_state"] = copy.deepcopy(manifest["completion_state"])
            seal["external_attestations"] = copy.deepcopy(manifest["synchronization_closure"]["external_attestations"])
        return registry, path, manifest, seal

    def q32_document(self):
        registry = validate_registry(load_json(REGISTRY_PATH))
        path = ROOT / "data/operations/iterations/121Q32.json"
        manifest = load_json(path)
        seal = load_json(infer_seal_path(manifest))
        return registry, path, manifest, seal

    def set_lifecycle(self, manifest, seal, *, accepted=False, merged=False, current=False):
        manifest["status"].update({"ready_for_gpt_verification": True, "accepted": accepted, "merged": merged, "current": current})
        manifest["branch_pr"]["draft"] = not accepted
        manifest["branch_pr"]["merged"] = merged
        if merged:
            manifest["branch_pr"]["merge_commit"] = "d" * 40
            manifest["claim_ceiling"] = "validated_lifecycle_gate"
            seal["phase_b"]["merge_commit"] = "d" * 40
            seal["phase_b"]["claim_ceiling"] = manifest["claim_ceiling"]
            seal["status"] = "MERGED_TEST_STATE"
        seal["lifecycle"] = copy.deepcopy(manifest["status"])

    def test_actual_q25_method_100_binds_its_own_seal(self):
        registry, path, manifest, seal, *_ = self.q25_documents()
        validate_manifest_schema(manifest, path)
        validate_custom(manifest, path, seal, registry)

    def test_actual_q25b_method_110_self_hosted_closure(self):
        registry, *_, path, manifest, seal = self.q25_documents()
        validate_manifest_schema(manifest, path)
        validate_custom(manifest, path, seal, registry)

    def test_actual_q25c_binds_own_seal_and_is_current_method_increment(self):
        registry, path, manifest, seal = self.q25c_document(current=True)
        validate_manifest_schema(manifest, path)
        validate_custom(manifest, path, seal, registry)
        q25b = load_json(ROOT / "data/operations/iterations/121Q25B.json")
        self.assertFalse(q25b["status"]["ready_for_gpt_verification"])
        self.assertTrue(manifest["status"]["current"])

    def test_actual_q32_method_120_recomputes_typed_closure(self):
        registry, path, manifest, seal = self.q32_document()
        validate_manifest_schema(manifest, path)
        validate_custom(manifest, path, seal, registry)
        self.assertEqual(manifest["method_version"], "1.2.0")
        self.assertTrue(manifest["propagation_closure"]["closure_complete"])
        self.assertTrue(manifest["status"]["current"])
        self.assertTrue(manifest["status"]["merged"])
        self.assertTrue(manifest["status"]["accepted"])
        self.assertFalse(manifest["status"]["candidate"])
        closure = manifest["propagation_closure"]
        self.assertTrue(closure["closure_hash"])
        self.assertGreater(len(closure["typed_path_ids"]), 0)
        self.assertEqual(closure["unresolved_residue"], [])

    def test_q32_missing_propagation_binding_is_schema_rejected(self):
        _, path, manifest, _ = self.q32_document()
        del manifest["propagation_closure"]
        with self.assertRaisesRegex(AssertionError, "schema error"):
            validate_manifest_schema(manifest, path)

    def test_q32_closure_hash_drift_is_rejected(self):
        registry, path, manifest, seal = self.q32_document()
        manifest["propagation_closure"]["closure_hash"] = "0" * 64
        with self.assertRaisesRegex(AssertionError, "closure hash mismatch"):
            validate_custom(manifest, path, seal, registry)

    def test_q32_typed_path_drift_is_rejected(self):
        registry, path, manifest, seal = self.q32_document()
        manifest["propagation_closure"]["typed_path_ids"] = []
        with self.assertRaisesRegex(AssertionError, "typed propagation paths mismatch"):
            validate_custom(manifest, path, seal, registry)

    def test_q32_sync_and_component_surface_decisions_cannot_diverge(self):
        registry, path, manifest, seal = self.q32_document()
        manifest["synchronization_closure"]["surface_decisions"][0]["decision"] = "NO_CHANGE_WITH_REASON"
        with self.assertRaisesRegex(AssertionError, "propagation and synchronization decisions disagree|changed registry surface"):
            validate_custom(manifest, path, seal, registry)

    def test_q32_seal_must_bind_propagation_hash(self):
        registry, path, manifest, seal = self.q32_document()
        seal["propagation_closure"]["closure_hash"] = "0" * 64
        with self.assertRaisesRegex(AssertionError, "seal propagation closure hash mismatch"):
            validate_custom(manifest, path, seal, registry)

    def test_missing_q25_seal_is_rejected(self):
        registry, q25_path, q25, *_ = self.q25_documents()
        missing = ROOT / "reports/operations/missing-Q25-seal.json"
        with patch("tools.validate_iteration_sync.infer_seal_path", return_value=missing):
            with self.assertRaisesRegex(AssertionError, "missing completion seal"):
                validate_manifest_bindings([(q25_path, q25)])

    def test_q25_seal_claim_mismatch_is_rejected(self):
        registry, path, manifest, seal, *_ = self.q25_documents()
        seal["phase_b"]["claim_ceiling"] = "legacy-q24-cannot-satisfy-q25"
        with self.assertRaisesRegex(AssertionError, "seal claim ceiling mismatch"):
            validate_custom(manifest, path, seal, registry)

    def test_q25_seal_lifecycle_mismatch_is_rejected(self):
        registry, path, manifest, seal, *_ = self.q25_documents()
        seal["lifecycle"]["ready_for_gpt_verification"] = False
        with self.assertRaisesRegex(AssertionError, "seal lifecycle mismatch"):
            validate_custom(manifest, path, seal, registry)

    def test_duplicate_task_binding_is_rejected(self):
        _, path, manifest, *_ = self.q25_documents()
        with self.assertRaisesRegex(AssertionError, "duplicate task binding"):
            validate_manifest_bindings([(path, manifest), (Path("duplicate.json"), copy.deepcopy(manifest))])

    def test_duplicate_seal_binding_is_rejected(self):
        _, q25_path, q25, _, q25b_path, q25b, _ = self.q25_documents()
        q25b["completion_seal_path"] = q25["completion_seal_path"]
        with self.assertRaisesRegex(AssertionError, "duplicate completion seal binding"):
            validate_manifest_bindings([(q25_path, q25), (q25b_path, q25b)])

    def assert_missing_surface_rejected(self, surface_id):
        registry, path, manifest, seal = self.q25c_document()
        manifest["synchronization_closure"]["surface_decisions"] = [
            item for item in manifest["synchronization_closure"]["surface_decisions"]
            if item["surface_id"] != surface_id
        ]
        with self.assertRaisesRegex(AssertionError, "missing registry-derived surface decisions"):
            validate_custom(manifest, path, seal, registry)

    def test_capability_or_method_change_requires_human_front_doors(self):
        for surface_id in ("human.readme", "human.current_state", "human.ai_guide"):
            with self.subTest(surface_id=surface_id):
                self.assert_missing_surface_rejected(surface_id)

    def test_change_requires_ai_and_agent_machine_assessments(self):
        for surface_id in ("ai.start", "agent.handoff", "machine.llms"):
            with self.subTest(surface_id=surface_id):
                self.assert_missing_surface_rejected(surface_id)

    def test_pages_source_change_requires_rendered_pages_obligation(self):
        self.assert_missing_surface_rejected("external.pages_homepage")

    def test_no_change_without_evidence_is_rejected(self):
        registry, path, manifest, seal = self.q25c_document()
        decision = next(item for item in manifest["synchronization_closure"]["surface_decisions"] if item["decision"] == "NO_CHANGE_WITH_REASON")
        decision["evidence_refs"] = []
        with self.assertRaisesRegex(AssertionError, "lacks evidence references"):
            validate_custom(manifest, path, seal, registry)

    def test_implementation_complete_but_repository_incomplete_cannot_be_ready(self):
        registry, path, manifest, seal = self.q25c_document()
        manifest["synchronization_closure"]["unresolved_residue"] = ["stale human projection"]
        manifest["completion_state"]["repository_synchronization_complete"] = False
        with self.assertRaisesRegex(AssertionError, "repository synchronization incomplete candidate cannot be ready"):
            validate_custom(manifest, path, seal, registry)

    def test_ready_with_post_merge_pages_pending_passes(self):
        registry, path, manifest, seal = self.q25c_document()
        validate_custom(manifest, path, seal, registry)

    def test_accepted_with_post_merge_only_pages_pending_passes(self):
        registry, path, manifest, seal = self.q25c_document()
        self.set_lifecycle(manifest, seal, accepted=True)
        validate_custom(manifest, path, seal, registry)

    def test_merged_with_post_merge_pages_pending_and_not_current_passes(self):
        registry, path, manifest, seal = self.q25c_document()
        self.set_lifecycle(manifest, seal, accepted=True, merged=True)
        validate_custom(manifest, path, seal, registry)

    def test_current_with_post_merge_pages_pending_is_rejected(self):
        registry, path, manifest, seal = self.q25c_document()
        self.set_lifecycle(manifest, seal, accepted=True, merged=True, current=True)
        with self.assertRaisesRegex(AssertionError, "pending external surfaces block current"):
            validate_custom(manifest, path, seal, registry)

    def test_current_with_individually_attested_pages_passes(self):
        registry, path, manifest, seal = self.q25c_document()
        self.set_lifecycle(manifest, seal, accepted=True, merged=True, current=True)
        manifest["synchronization_closure"]["external_attestations"][0]["status"] = "attested"
        manifest["completion_state"]["external_synchronization_attested"] = True
        manifest["completion_state"]["project_synchronization_complete"] = True
        seal["external_attestations"] = copy.deepcopy(manifest["synchronization_closure"]["external_attestations"])
        seal["completion_state"] = copy.deepcopy(manifest["completion_state"])
        validate_custom(manifest, path, seal, registry)

    def test_external_surface_that_blocks_accepted_rejects_pending(self):
        registry, path, manifest, seal = self.q25c_document()
        registry["external.pages_homepage"]["blocks"].append("accepted")
        self.set_lifecycle(manifest, seal, accepted=True)
        with self.assertRaisesRegex(AssertionError, "pending external surfaces block accepted"):
            validate_custom(manifest, path, seal, registry)

    def test_global_attested_true_with_pending_surface_is_rejected(self):
        registry, path, manifest, seal = self.q25c_document()
        manifest["completion_state"]["external_synchronization_attested"] = True
        with self.assertRaisesRegex(AssertionError, "global external synchronization flag disagrees"):
            validate_custom(manifest, path, seal, registry)

    def test_two_external_surfaces_require_both_attested_for_current(self):
        registry, path, manifest, seal = self.q25c_document()
        second = copy.deepcopy(registry["external.pages_homepage"])
        second["surface_id"] = "external.second"
        second["locator"] = "https://example.invalid/second"
        registry[second["surface_id"]] = second
        decision = copy.deepcopy(next(item for item in manifest["synchronization_closure"]["surface_decisions"] if item["surface_id"] == "external.pages_homepage"))
        decision["surface_id"] = "external.second"
        manifest["synchronization_closure"]["surface_decisions"].append(decision)
        attestation = copy.deepcopy(manifest["synchronization_closure"]["external_attestations"][0])
        attestation["surface_id"] = "external.second"
        manifest["synchronization_closure"]["external_attestations"].append(attestation)
        self.set_lifecycle(manifest, seal, accepted=True, merged=True, current=True)
        manifest["synchronization_closure"]["external_attestations"][0]["status"] = "attested"
        seal["external_attestations"] = copy.deepcopy(manifest["synchronization_closure"]["external_attestations"])
        with self.assertRaisesRegex(AssertionError, "pending external surfaces block current"):
            validate_custom(manifest, path, seal, registry)

    def test_duplicate_unknown_and_wrong_authority_attestations_are_rejected(self):
        for mutation, pattern in (
            ("duplicate", "duplicate external attestation"),
            ("unknown", "external attestation coverage mismatch"),
            ("authority", "wrong external attestation authority"),
        ):
            with self.subTest(mutation=mutation):
                registry, path, manifest, seal = self.q25c_document()
                if mutation == "duplicate":
                    manifest["synchronization_closure"]["external_attestations"].append(copy.deepcopy(manifest["synchronization_closure"]["external_attestations"][0]))
                elif mutation == "unknown":
                    manifest["synchronization_closure"]["external_attestations"][0]["surface_id"] = "external.unknown"
                else:
                    manifest["synchronization_closure"]["external_attestations"][0]["authority"] = "self_asserted"
                with self.assertRaisesRegex(AssertionError, pattern):
                    validate_custom(manifest, path, seal, registry)

    def test_draft_cannot_claim_post_merge_production_attestation(self):
        registry, path, manifest, seal = self.q25c_document()
        manifest["synchronization_closure"]["external_attestations"][0]["status"] = "attested"
        manifest["completion_state"]["external_synchronization_attested"] = True
        manifest["completion_state"]["project_synchronization_complete"] = True
        with self.assertRaisesRegex(AssertionError, "Draft/unmerged candidate cannot claim post-merge"):
            validate_custom(manifest, path, seal, registry)

    def test_fake_repository_evidence_reference_is_rejected(self):
        registry, path, manifest, seal = self.q25c_document()
        manifest["synchronization_closure"]["surface_decisions"][0]["evidence_refs"] = ["missing/fake-proof.md"]
        with self.assertRaisesRegex(AssertionError, "nonexistent repository evidence"):
            validate_custom(manifest, path, seal, registry)

    def test_declared_external_evidence_reference_passes_without_local_live_claim(self):
        registry, path, manifest, seal = self.q25c_document()
        validate_custom(manifest, path, seal, registry)
        self.assertFalse(manifest["synchronization_closure"]["live_external_surfaces_verified"])

    def test_local_validator_cannot_claim_live_rendered_verification(self):
        registry, path, manifest, seal = self.q25c_document()
        manifest["synchronization_closure"]["live_external_surfaces_verified"] = True
        with self.assertRaisesRegex(AssertionError, "local validator cannot claim live rendered verification"):
            validate_custom(manifest, path, seal, registry)

    def test_stale_projection_residue_blocks_ready(self):
        registry, path, manifest, seal = self.q25c_document()
        manifest["synchronization_closure"]["unresolved_residue"] = ["superseded capability wording remains"]
        manifest["completion_state"]["repository_synchronization_complete"] = False
        with self.assertRaisesRegex(AssertionError, "repository synchronization incomplete"):
            validate_custom(manifest, path, seal, registry)

    def test_external_surface_cannot_be_repository_changed_path(self):
        registry, path, manifest, seal = self.q25c_document()
        manifest["changed_surfaces"].append("https://arvin-liu.github.io/when-systems-catch-fire/")
        with self.assertRaisesRegex(AssertionError, "external surface incorrectly listed"):
            validate_custom(manifest, path, seal, registry)

    def test_seal_task_mismatch_is_rejected(self):
        registry, path, manifest, seal, *_ = self.q25_documents()
        seal["task_id"] = "121Q24"
        with self.assertRaisesRegex(AssertionError, "seal task mismatch"):
            validate_custom(manifest, path, seal, registry)

    def test_temporally_version_aware_validation_preserves_sealed_early_iterations_and_current_candidate(self):
        """P4 Conclusion B regression.

        A synchronization surface introduced after an early iteration was sealed
        (``copyright_governance``, added in the Q33 era) must NOT be
        retroactively required of that early iteration. Historical manifests are
        validated against the committed registry snapshot of the era their
        ``registry_version`` declares; the current candidate is validated against
        the live registry and must still satisfy the current contract.

        No manifest is special-cased: the validator resolves the era registry from
        the git history of the registry file, never from a per-task exception list.
        """
        reg_doc = load_json(REGISTRY_PATH)
        live_registry = validate_registry(reg_doc)
        live_version = reg_doc["registry_version"]
        self.assertIn("copyright_governance", live_registry,
                      "precondition: later-added surface exists in the live registry")

        # Representative sealed early iteration that predates copyright_governance.
        early_path = ROOT / "data/operations/iterations/121Q25B.json"
        early = load_json(early_path)
        early_seal = load_json(infer_seal_path(early))
        self.assertNotEqual(early["synchronization_closure"]["registry_version"], live_version,
                            "precondition: early iteration declares an older registry_version")

        # Demonstrate the retrospective defect: under the LIVE registry the early
        # manifest would be required to cover the later-added surface.
        required_under_live = required_registry_surfaces(early, live_registry)
        self.assertIn("copyright_governance", required_under_live,
                      "the bug: live registry would retroactively require copyright_governance")

        # The era-aware resolver maps the declared version to a snapshot that
        # predates the later-added surface.
        era_registry = resolve_era_registry(early["synchronization_closure"]["registry_version"], live_registry)
        self.assertNotIn("copyright_governance", era_registry,
                         "era registry must not contain the later-added surface")

        # Historical early iteration validates against the era registry (no
        # retrospective failure) and also via the live validator, which internally
        # selects the era registry for non-current declarations.
        validate_manifest_schema(early, early_path)
        validate_custom(early, early_path, early_seal, era_registry)
        validate_custom(early, early_path, early_seal, live_registry)

        # The current candidate (Q33) declares the live version and MUST still
        # satisfy the current contract against the live registry.
        q33_path = ROOT / "data/operations/iterations/121Q33.json"
        q33 = load_json(q33_path)
        q33_seal = load_json(infer_seal_path(q33))
        self.assertEqual(q33["synchronization_closure"]["registry_version"], live_version)
        self.assertIn("copyright_governance", required_registry_surfaces(q33, live_registry),
                      "current candidate must still be governed by the current contract")
        validate_manifest_schema(q33, q33_path)
        validate_custom(q33, q33_path, q33_seal, live_registry)


if __name__ == "__main__":
    unittest.main()
