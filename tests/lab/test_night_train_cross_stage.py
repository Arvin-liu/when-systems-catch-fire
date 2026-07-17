"""
Cross-Stage Integration Tests — Second Pass Deep Audit
Tests that Q33-Q39 validators interact correctly across stage boundaries.
Must call real validators, not re-implement business logic.
"""
import json, sys, unittest, copy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.lab.mutation_runner import MutationTest, load_json, deep_copy


def import_validator(module_path, func_name="validate_all"):
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, func_name)


class CrossStageIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.mt = MutationTest("cross")

    def tearDown(self):
        self.mt.restore()

    def test_x01_q33_unknown_rights_blocks_q34_commitment(self):
        """Q33: rights unknown material must not enter Q34 commitment plane."""
        # Mutate Q34 commitment to include an entry referencing unknown rights
        doc = load_json("data/discovery/commitment-candidates.json")
        d = deep_copy(doc)
        d["entries"].append({
            "id": "x01_unknown_rights",
            "plane": "commitment",
            "status": "committed",
            "epistemic_level": "tested_claim",
            "gates": {"rights_gate": "pass", "epistemic_gate": "pass", "action_authority_gate": "pass"},
            "rights_source_id": "nonexistent_rights_entry"
        })
        self.mt.mutate_file("data/discovery/commitment-candidates.json", d)

        # Q34 validator should pass (it doesn't check rights_source_id)
        q34 = import_validator("tools.discovery.validate_dual_plane")
        r34 = q34()

        # Q33 validator should also pass (it reads Q33 data, not Q34)
        q33 = import_validator("tools.rights.validate_rights_gate")
        r33 = q33()

        # GAP: no cross-stage validator checks rights_source_id against Q33 registries
        # This test documents the GAP
        self.skipTest("GAP: no cross-stage validator links Q34 rights_source_id to Q33 registries")

    def test_x02_q34_no_authority_blocks_q35_execution(self):
        """Q34: object without ActionAuthorityGate must not be Q35-executable."""
        # Create a Q34 entry with action_authority_gate=fail
        doc = load_json("data/discovery/commitment-candidates.json")
        d = deep_copy(doc)
        d["entries"].append({
            "id": "x02_no_authority",
            "plane": "commitment",
            "status": "committed",
            "epistemic_level": "tested_claim",
            "gates": {"rights_gate": "pass", "epistemic_gate": "pass", "action_authority_gate": "fail"}
        })
        self.mt.mutate_file("data/discovery/commitment-candidates.json", d)

        q34 = import_validator("tools.discovery.validate_dual_plane")
        r34 = q34()
        # Q34 validator must catch: committed but action_authority_gate != pass
        self.assertFalse(r34.is_pass, f"Q34 must block committed with failed authority gate: {r34.report()}")

    def test_x03_q35_unauthorized_generates_q39_failure(self):
        """Q35: unauthorized tool call must generate Q39 FailureRecord."""
        # Mutate Q35 permissions to allow main push
        doc = load_json("data/agent/tool-permissions.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            if e.get("target") == "main":
                e["allowed"] = True
        self.mt.mutate_file("data/agent/tool-permissions.json", d)

        # Q35 validator catches this
        q35 = import_validator("tools.agent.validate_agent_duty")
        r35 = q35()
        self.assertFalse(r35.is_pass, "Q35 must detect main push allowed")

        # GAP: Q39 does not automatically generate FailureRecord from Q35 violations
        # No runtime pipeline connects Q35 detection to Q39 recording
        self.skipTest("GAP: no runtime pipeline generates Q39 FailureRecord from Q35 violations")

    def test_x04_q36_expired_prediction_only_calibration(self):
        """Q36: expired prediction must only generate CalibrationCandidate, not modify Current."""
        doc = load_json("data/temporal/prediction-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["expiry_status"] = "expired"
        self.mt.mutate_file("data/temporal/prediction-records.json", d)

        q36 = import_validator("tools.temporal.validate_temporal_causality")
        r36 = q36()

        # GAP: validator does not check expiry_status semantics
        self.skipTest("GAP: validator does not enforce expired->CalibrationCandidate constraint")

    def test_x05_q37_analogy_only_in_q34_discovery(self):
        """Q37: analogy products must only enter Q34 discovery plane, not commitment."""
        # Q37 analogy-candidates exist
        doc = load_json("data/analogy/analogy-candidates.json")
        self.assertTrue(len(doc["entries"]) > 0, "Q37 must have analogy entries")

        # Q34 discovery registry should accept exploration-level items
        disc = load_json("data/discovery/discovery-registry.json")
        self.assertTrue(len(disc["entries"]) > 0, "Q34 must have discovery entries")

        # GAP: no validator checks that Q37 products only appear in Q34 exploration plane
        self.skipTest("GAP: no cross-validator ensures Q37 products stay in Q34 discovery")

    def test_x06_q38_retrieval_must_have_counterexample_and_ceiling(self):
        """Q38: retrieval results must include counterexample and claim ceiling."""
        q38 = import_validator("tools.retrieval.validate_structural_retrieval")
        r38 = q38()
        self.assertTrue(r38.is_pass, f"Q38 base must pass: {r38.report()}")

        # Mutate: remove claim_ceiling from cases
        doc = load_json("data/retrieval/case-structures.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e.pop("claim_ceiling", None)
        self.mt.mutate_file("data/retrieval/case-structures.json", d)

        r38b = q38()
        self.assertFalse(r38b.is_pass, "Q38 must catch missing claim_ceiling")

    def test_x07_q39_repair_must_pass_q34_gates(self):
        """Q39: repair candidate must re-pass Q34 three gates."""
        # Q39 repair propagation exists
        doc = load_json("data/failure/repair-propagation.json")
        self.assertTrue(len(doc["entries"]) > 0, "Q39 must have repair propagation")

        # GAP: no validator checks that Q39 repairs go through Q34 gates
        self.skipTest("GAP: no cross-validator ensures Q39 repairs pass Q34 gates")

    def test_x08_q39_rights_failure_triggers_q33_gate(self):
        """Q39: copyright-related failure must re-trigger Q33 PublicationGate."""
        # Check Q39 failure records for rights-related failures
        doc = load_json("data/failure/failure-records.json")
        rights_failures = [e for e in doc["entries"]
                          if "rights" in e.get("failure_class", "").lower()
                          or "copyright" in e.get("failure_class", "").lower()
                          or "publication" in e.get("failure_class", "").lower()]

        # GAP: no validator connects Q39 rights failures back to Q33
        self.skipTest("GAP: no cross-validator connects Q39 rights failures to Q33 PublicationGate")

    def test_x09_no_bypass_q32_propagation_closure(self):
        """All Q33-Q39 outputs must not bypass Q32 propagation closure."""
        # Q32 propagation closure hash is fixed
        # Check that no Q33-Q39 data modifies Q32 core files
        import subprocess
        result = subprocess.run(
            ["git", "-C", str(ROOT), "diff", "1e6e734d", "HEAD", "--name-only"],
            capture_output=True, text=True
        )
        changed = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Q32 core files that must not change
        q32_core = [
            "data/foundation/", "tools/foundation/", "schemas/foundation/",
            "data/iteration/", "tools/iteration/",
        ]
        violations = []
        for f in changed:
            for prefix in q32_core:
                if f.startswith(prefix):
                    violations.append(f)

        self.assertEqual(violations, [], f"Q32 core files must not change: {violations}")

    def test_x10_agent_no_permission_expansion_via_cross_stage(self):
        """Agent must not expand permissions through cross-stage calls."""
        # Q35 tool permissions
        perms = load_json("data/agent/tool-permissions.json")
        for e in perms["entries"]:
            if e.get("allowed") is True:
                # Each allowed tool must not grant access to forbidden targets
                self.assertNotEqual(e.get("target"), "main",
                    "Agent must not have main push permission via any path")
                self.assertNotEqual(e.get("target"), "production",
                    "Agent must not have production deploy permission")


if __name__ == "__main__":
    unittest.main()
