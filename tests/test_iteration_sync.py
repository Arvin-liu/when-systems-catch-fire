import copy
import unittest

from tools.validate_iteration_sync import validate_all, validate_custom


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

    def test_draft_cannot_be_current(self):
        manifest = valid_manifest()
        manifest["status"]["current"] = True
        with self.assertRaisesRegex(AssertionError, "current cannot be true|Draft cannot"):
            validate_custom(manifest, __file__, valid_seal())


if __name__ == "__main__":
    unittest.main()
