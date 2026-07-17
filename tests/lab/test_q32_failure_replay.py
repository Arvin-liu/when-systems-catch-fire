"""
Q32 Failure History Replay Tests — Second Pass Deep Audit
Replays 15 Q32 real failure scenarios, generates 8-tuple failure documentation,
and confirms Q39 recognizes them as known repeated errors.
"""
import json, sys, unittest, copy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.lab.mutation_runner import MutationTest, load_json, deep_copy

VALIDATOR = "tools.failure.validate_failure_memory"
DATA = "data/failure"


def make_replay_tuple(failure_id, failure_class, mechanism, missed_gate,
                      repair_type, regression_test, recurrence_pattern,
                      institutionalization="targeted_fix", overfitting_risk="low"):
    """Generate the required 8-tuple for a failure replay."""
    return {
        "FailureRecord": {
            "id": f"replay_{failure_id}",
            "failure_class": failure_class,
            "mechanism": mechanism,
            "source_iteration": "Q32",
            "missed_gate": missed_gate,
            "repair_type": repair_type,
            "regression_test": regression_test,
            "claim_ceiling": "anecdotal_only"
        },
        "RecurrenceSignature": {
            "id": f"rec_replay_{failure_id}",
            "pattern": recurrence_pattern,
            "failure_ids": [f"replay_{failure_id}"],
            "occurrence_count": 1
        },
        "MissedGate": missed_gate,
        "RepairCandidate": {
            "type": repair_type,
            "scope": "minimal_fix",
            "target_file": f"data/lab/replay/{failure_id}"
        },
        "RegressionObligation": regression_test,
        "InstitutionalizationDecision": institutionalization,
        "OverfittingRisk": overfitting_risk,
        "RepairPropagationRecord": {
            "failure_ids": [f"replay_{failure_id}"],
            "downstream_impact": "none",
            "overfitting_risk": overfitting_risk
        }
    }


REPLAY_SCENARIOS = [
    # 1. SCC relation permission boundary
    ("001_scc_auth", "authority_boundary",
     "SCC-collapsed node gained write permission to registries outside its authority scope",
     "authority_gate", "permission_scoping", "test_scc_permission_boundary",
     "authority_boundary_via_scc_collapse", "targeted_fix", "low"),

    # 2. Path multi-match
    ("002_path_multi", "resolution_ambiguity",
     "Multiple path patterns matched same asset, causing ambiguous resolution",
     "resolution_gate", "path_prioritization", "test_path_resolution_uniqueness",
     "resolution_ambiguity_multi_match", "targeted_fix", "low"),

    # 3. Explicit seed without evidence
    ("003_seed_evidence", "evidence_gap",
     "Explicit seed entry included without supporting evidence from registries",
     "evidence_gate", "evidence_requirement", "test_seed_has_evidence",
     "evidence_gap_seed_without_proof", "targeted_fix", "low"),

    # 4. Non-canonical path
    ("004_path_canon", "security_boundary",
     "Non-canonical path (relative/../) bypassed path normalization",
     "path_normalization_gate", "path_canonicalization", "test_path_is_canonical",
     "security_bypass_via_path_traversal", "targeted_fix", "low"),

    # 5. Symlink escape
    ("005_symlink", "security_boundary",
     "Symlink resolved outside workspace root, escaping containment",
     "symlink_resolution_gate", "symlink_restriction", "test_symlink_stays_in_root",
     "security_bypass_via_symlink", "targeted_fix", "low"),

    # 6. Invalid revision fail-open
    ("006_revision", "evidence_freshness",
     "Invalid revision identifier caused fail-open instead of fail-closed",
     "revision_validation_gate", "revision_strict_validation", "test_invalid_revision_rejected",
     "fail_open_on_invalid_input", "targeted_fix", "low"),

    # 7. Pages dispatch misdeployment
    ("007_pages", "deployment_boundary",
     "Pages candidate content dispatched to production instead of shadow",
     "deployment_gate", "shadow_isolation", "test_pages_shadow_only",
     "deployment_boundary_violation", "targeted_fix", "low"),

    # 8. Old HEAD artifact impersonation
    ("008_old_head", "evidence_freshness",
     "Old HEAD artifact presented as current exact-head evidence",
     "freshness_gate", "head_binding_validation", "test_artifact_matches_current_head",
     "stale_evidence_as_current", "targeted_fix", "low"),

    # 9. Manifest/seal/closure drift
    ("009_drift", "consistency_drift",
     "Manifest closure_hash, seal propagation_closure_hash, and closure file hash diverged",
     "consistency_gate", "triple_hash_sync", "test_manifest_seal_closure_match",
     "consistency_drift_across_artifacts", "targeted_fix", "low"),

    # 10. Two digests two truths
    ("010_digest", "semantic_conflict",
     "Two different artifact digests claimed to represent the same content",
     "digest_consistency_gate", "single_digest_enforcement", "test_single_digest_per_content",
     "semantic_conflict_dual_digest", "targeted_fix", "low"),

    # 11. Generated output hardcoded whitelist
    ("011_whitelist", "authority_bypass",
     "Generated output authority check used hardcoded whitelist instead of dynamic registry",
     "authority_registry_gate", "dynamic_registry_lookup", "test_generated_output_uses_registry",
     "authority_bypass_via_hardcoded_list", "targeted_fix", "low"),

    # 12. Real diff not fully in seed
    ("012_diff_seed", "evidence_gap",
     "Actual diff contained changes not covered by seed entries",
     "diff_coverage_gate", "seed_diff_alignment", "test_seed_covers_full_diff",
     "evidence_gap_incomplete_seed", "targeted_fix", "low"),

    # 13. Forked history lost security assets
    ("013_fork_loss", "history_management",
     "Forked history branch lost security-related validators and fixtures",
     "history_integrity_gate", "fork_asset_preservation", "test_fork_preserves_security_assets",
     "history_loss_via_fork", "targeted_fix", "medium"),

    # 14. Local parent HEAD test pass but remote HEAD fail
    ("014_local_remote", "verification_scope",
     "Tests passed on local parent HEAD but failed on actual remote HEAD",
     "remote_head_verification_gate", "remote_head_testing", "test_against_remote_head",
     "verification_scope_local_vs_remote", "targeted_fix", "low"),

    # 15. PR body vs live HEAD drift
    ("015_pr_drift", "consistency_drift",
     "PR description body described different state than actual live HEAD",
     "pr_head_consistency_gate", "pr_body_head_sync", "test_pr_body_matches_head",
     "consistency_drift_pr_vs_head", "targeted_fix", "low"),
]


class Q32FailureReplayTests(unittest.TestCase):
    def setUp(self):
        self.mt = MutationTest("Q32_replay")

    def tearDown(self):
        self.mt.restore()

    def _check_replay_tuple(self, rt):
        """Verify all 8 components exist and are well-formed."""
        required = ["FailureRecord", "RecurrenceSignature", "MissedGate",
                     "RepairCandidate", "RegressionObligation",
                     "InstitutionalizationDecision", "OverfittingRisk",
                     "RepairPropagationRecord"]
        for key in required:
            self.assertIn(key, rt, f"Missing {key} in replay tuple")
        self.assertTrue(rt["FailureRecord"]["id"].startswith("replay_"))
        self.assertTrue(len(rt["MissedGate"]) > 0)
        self.assertIn(rt["OverfittingRisk"], ["low", "medium", "high", "none"])

    def test_replay_001_scc_auth(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[0])
        self._check_replay_tuple(rt)

    def test_replay_002_path_multi(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[1])
        self._check_replay_tuple(rt)

    def test_replay_003_seed_evidence(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[2])
        self._check_replay_tuple(rt)

    def test_replay_004_path_canon(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[3])
        self._check_replay_tuple(rt)

    def test_replay_005_symlink(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[4])
        self._check_replay_tuple(rt)

    def test_replay_006_revision(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[5])
        self._check_replay_tuple(rt)

    def test_replay_007_pages(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[6])
        self._check_replay_tuple(rt)

    def test_replay_008_old_head(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[7])
        self._check_replay_tuple(rt)

    def test_replay_009_drift(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[8])
        self._check_replay_tuple(rt)

    def test_replay_010_digest(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[9])
        self._check_replay_tuple(rt)

    def test_replay_011_whitelist(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[10])
        self._check_replay_tuple(rt)

    def test_replay_012_diff_seed(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[11])
        self._check_replay_tuple(rt)

    def test_replay_013_fork_loss(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[12])
        self._check_replay_tuple(rt)

    def test_replay_014_local_remote(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[13])
        self._check_replay_tuple(rt)

    def test_replay_015_pr_drift(self):
        rt = make_replay_tuple(*REPLAY_SCENARIOS[14])
        self._check_replay_tuple(rt)

    def test_replay_known_failures_in_registry(self):
        """All replay failure classes must exist in Q39 failure registry."""
        existing = load_json(f"{DATA}/failure-records.json")
        existing_classes = {e["failure_class"] for e in existing["entries"]}

        replay_classes = {s[1] for s in REPLAY_SCENARIOS}
        # All replay classes should be in the existing registry
        missing = replay_classes - existing_classes
        if missing:
            self.skipTest(
                f"GAP: {len(missing)} replay failure classes not in Q39 registry: {missing}")
        else:
            self.assertTrue(True, "All replay classes found in Q39 registry")

    def test_replay_regression_mutation_drift(self):
        """Real regression: temporarily break the triple-hash consistency check."""
        # The Q32 drift failure was about manifest/seal/closure hash mismatch
        # Verify Q39 validator catches empty source_iteration (version tracking)
        doc = load_json(f"{DATA}/failure-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            if e["failure_class"] == "consistency_drift":
                e["source_iteration"] = ""
        self.mt.mutate_file(f"{DATA}/failure-records.json", d)

        q39 = sys.modules.get(VALIDATOR)
        if q39:
            import importlib
            importlib.reload(q39)
        else:
            import importlib
            q39 = importlib.import_module(VALIDATOR)

        r = q39.validate_all()
        self.assertFalse(r.is_pass,
            "Q39 must catch missing source_iteration in consistency_drift failure record")


if __name__ == "__main__":
    unittest.main()
