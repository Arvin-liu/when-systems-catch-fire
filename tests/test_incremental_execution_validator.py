import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.operations.run_incremental_execution import profile_identity
from tools.operations.validate_incremental_execution import (
    authority_fingerprint,
    canonical,
    compute_plan_hash,
    digest_bytes,
    validate_incremental_execution,
)


class UnifiedIncrementalValidatorAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        (self.repo / "data/operations").mkdir(parents=True)
        (self.repo / "input.txt").write_text("input\n", encoding="utf-8")
        (self.repo / "out.txt").write_text("output\n", encoding="utf-8")
        self.registry_path = self.repo / "data/operations/project-components.json"
        self.topology_path = self.repo / "data/operations/change-propagation-topology.json"
        self.profiles_path = self.repo / "data/operations/component-execution-profiles.json"
        self.registry = {
            "registry_version": "1.0.0",
            "components": [
                {"component_id": "alpha", "path_patterns": ["input.txt", "out.txt"]},
                {"component_id": "beta", "path_patterns": ["input.txt"]},
                {"component_id": "gamma", "path_patterns": ["input.txt"]},
            ],
        }
        self.topology = {"topology_version": "1.0.0", "relations": []}
        self.profiles = {
            "schema_version": "1.0.0",
            "profiles": [
                {
                    "component_id": "alpha", "execution_kind": "automatic", "execution_capability": "automatic",
                    "authoritative_inputs": ["input.txt"], "generated_outputs": ["out.txt"],
                    "input_fingerprint_policy": {"kind": "sha256_sorted_file_set", "paths": ["input.txt"]},
                    "output_fingerprint_policy": {"kind": "sha256_single_target", "target": "out.txt"},
                    "producer_argv": [sys.executable, "-c", "0"], "validator_argv": [sys.executable, "-c", "0"],
                },
                {
                    "component_id": "beta", "execution_kind": "manual", "execution_capability": "manual",
                    "authoritative_inputs": ["input.txt"], "generated_outputs": [],
                    "input_fingerprint_policy": {"kind": "sha256_sorted_file_set", "paths": ["input.txt"]},
                    "output_fingerprint_policy": {"kind": "sha256_single_target", "target": "input.txt"},
                    "validator_argv": [sys.executable, "-c", "0"],
                },
                {
                    "component_id": "gamma", "execution_kind": "attestation", "execution_capability": "external_attestation",
                    "authoritative_inputs": ["input.txt"], "generated_outputs": [],
                    "input_fingerprint_policy": {"kind": "sha256_sorted_file_set", "paths": ["input.txt"]},
                    "output_fingerprint_policy": {"kind": "sha256_single_target", "target": "input.txt"},
                    "validator_argv": [sys.executable, "-c", "0"],
                },
            ],
        }
        self.save_authorities()
        self.plan = self.make_plan()

    def tearDown(self):
        self.temp.cleanup()

    def save_authorities(self):
        self.registry_path.write_text(json.dumps(self.registry, sort_keys=True) + "\n", encoding="utf-8")
        self.topology_path.write_text(json.dumps(self.topology, sort_keys=True) + "\n", encoding="utf-8")
        self.profiles_path.write_text(json.dumps(self.profiles, sort_keys=True) + "\n", encoding="utf-8")

    def proof(self, cid):
        return {
            "component_id": cid,
            "basis": "outside declared closure",
            "unchanged_authoritative_input_fingerprints": [],
            "unchanged_dependency_fingerprints": [],
            "traversed_declared_relations": [],
            "excluded_declared_relations": [],
            "excluded_trigger_dimensions": ["identity"],
            "proof_method": "fixture authority exclusion",
            "plan_hash": "<bound-to-canonical-plan-hash>",
            "authority_fingerprint": authority_fingerprint(self.registry_path, self.topology_path, self.profiles_path),
            "expiry_or_recheck_condition": "any authority or input change",
            "claim_ceiling": "repository dependency only",
        }

    def make_plan(self):
        plan = {
            "schema_version": "1.0.0",
            "request_identity": "validator-test",
            "normalized_change_seeds": ["input.txt"],
            "q32_affected_component_closure": ["alpha"],
            "affected_synchronization_surfaces": [],
            "component_decisions": [
                {"component_id": "alpha", "decision": "REBUILD", "non_impact_proof": None},
                {"component_id": "beta", "decision": "NO_CHANGE_WITH_PROOF", "non_impact_proof": self.proof("beta")},
                {"component_id": "gamma", "decision": "NO_CHANGE_WITH_PROOF", "non_impact_proof": self.proof("gamma")},
            ],
            "full_rebuild_reasons": [],
            "unresolved_residue": [],
            "execution_order": ["alpha"],
            "claim_ceiling": "declared repository dependency only",
        }
        return self.reseal(plan)

    def reseal(self, plan):
        plan["plan_hash"] = compute_plan_hash(plan)
        for item in plan["component_decisions"]:
            if isinstance(item.get("non_impact_proof"), dict):
                item["non_impact_proof"]["plan_hash"] = plan["plan_hash"]
        return plan

    def validate(self, plan=None, **kwargs):
        return validate_incremental_execution(
            plan or self.plan,
            root=self.repo,
            registry_path=self.registry_path,
            topology_path=self.topology_path,
            profiles_path=self.profiles_path,
            **kwargs,
        )

    def codes(self, result):
        return {error["code"] for error in result["errors"]}

    def record(self, cid="alpha", status="success"):
        return {
            "component_id": cid, "argv": [sys.executable, "-c", "0"], "cwd": ".",
            "start_status": "running", "end_status": status, "stdout": "", "stderr": "",
            "return_code": 0 if status == "success" else 1,
            "before_input_fingerprints": {"input.txt": None},
            "before_output_fingerprints": {"out.txt": None} if cid == "alpha" else {},
            "after_output_fingerprints": {"out.txt": None} if cid == "alpha" else {},
            "validator_result": {"return_code": 0}, "cache_decision": "MISS",
            "rollback_status": "not-required",
        }

    def valid_cache(self):
        identity = profile_identity(self.profiles_path, self.profiles, self.repo, self.plan)
        cache = {"identity": identity, "output_fingerprints": {"out.txt": identity["output_fingerprints"]["out.txt"]}, "records": []}
        cache["integrity_digest"] = digest_bytes(canonical(cache).encode())
        return cache

    def test_d01_complete_valid_plan_passes(self):
        result = self.validate()
        self.assertTrue(result["ok"], result)

    def test_d02_profile_missing_component_fails(self):
        self.profiles["profiles"].pop()
        self.save_authorities()
        self.assertIn("E_PROFILE_MISSING_COMPONENT", self.codes(self.validate()))

    def test_d03_duplicate_component_decision_fails(self):
        plan = copy.deepcopy(self.plan)
        plan["component_decisions"].append(copy.deepcopy(plan["component_decisions"][0]))
        self.reseal(plan)
        self.assertIn("E_PLAN_DUPLICATE_DECISION", self.codes(self.validate(plan)))

    def test_d04_affected_component_forged_no_change_fails(self):
        plan = copy.deepcopy(self.plan)
        plan["component_decisions"][0] = {"component_id": "alpha", "decision": "NO_CHANGE_WITH_PROOF", "non_impact_proof": self.proof("alpha")}
        plan["execution_order"] = []
        self.reseal(plan)
        self.assertIn("E_AFFECTED_NO_CHANGE", self.codes(self.validate(plan)))

    def test_d05_no_change_without_proof_fails(self):
        plan = copy.deepcopy(self.plan)
        plan["component_decisions"][1]["non_impact_proof"] = None
        self.reseal(plan)
        self.assertIn("E_PROOF_REQUIRED", self.codes(self.validate(plan)))

    def test_d06_proof_plan_hash_binding_mismatch_fails(self):
        plan = copy.deepcopy(self.plan)
        plan["component_decisions"][1]["non_impact_proof"]["plan_hash"] = "0" * 64
        self.assertIn("E_PROOF_PLAN_HASH_BINDING", self.codes(self.validate(plan)))

    def test_d07_canonical_plan_hash_tampering_fails(self):
        plan = copy.deepcopy(self.plan)
        plan["claim_ceiling"] = "tampered"
        self.assertIn("E_PLAN_HASH_MISMATCH", self.codes(self.validate(plan)))

    def test_d08_unknown_or_unresolved_path_must_fail_closed(self):
        plan = copy.deepcopy(self.plan)
        plan["unresolved_residue"] = [{"path": "unknown.txt"}]
        self.reseal(plan)
        codes = self.codes(self.validate(plan))
        self.assertIn("E_UNRESOLVED_NOT_FAIL_CLOSED", codes)
        self.assertIn("E_FULL_REBUILD_DOWNGRADED", codes)
        plan = copy.deepcopy(self.plan)
        plan["normalized_change_seeds"] = ["unknown/file.txt"]
        self.reseal(plan)
        codes = self.codes(self.validate(plan))
        self.assertIn("E_UNKNOWN_PATH_NOT_FAIL_CLOSED", codes)
        self.assertIn("E_FULL_REBUILD_DOWNGRADED", codes)

    def test_d09_meta_structure_change_cannot_be_local(self):
        plan = copy.deepcopy(self.plan)
        plan["normalized_change_seeds"] = ["tools/operations/run_incremental_execution.py"]
        self.reseal(plan)
        codes = self.codes(self.validate(plan))
        self.assertIn("E_META_CHANGE_NOT_FAIL_CLOSED", codes)
        self.assertIn("E_FULL_REBUILD_DOWNGRADED", codes)

    def test_d10_cache_integrity_tampering_fails(self):
        cache = self.valid_cache()
        cache["records"] = [{"forged": True}]
        self.assertIn("E_CACHE_INTEGRITY", self.codes(self.validate(cache=cache)))

    def test_d11_registry_or_topology_cache_identity_mismatch_fails(self):
        cache = self.valid_cache()
        self.topology["relations"].append({"relation_id": "changed"})
        self.save_authorities()
        self.assertIn("E_CACHE_IDENTITY", self.codes(self.validate(cache=cache)))

    def test_d12_execution_order_duplicate_missing_or_unauthorized_fails(self):
        cases = [
            [self.record(), self.record()],
            [],
            [self.record("beta")],
        ]
        for records in cases:
            with self.subTest(records=[r["component_id"] for r in records]):
                result = self.validate(execution={"ok": True, "records": records})
                self.assertIn("E_EXECUTION_ORDER", self.codes(result))

    def test_d13_failure_requires_rollback_and_recovery_material(self):
        failed = self.record(status="failed")
        result = self.validate(execution={"ok": False, "records": [failed]})
        codes = self.codes(result)
        self.assertIn("E_ROLLBACK_INCOMPLETE", codes)
        self.assertIn("E_RECOVERY_REFERENCE_MISSING", codes)

    def test_d14_manual_and_external_boundaries_cannot_be_crossed(self):
        plan = copy.deepcopy(self.plan)
        for item in plan["component_decisions"][1:]:
            item["decision"] = "REBUILD"
            item["non_impact_proof"] = None
        plan["execution_order"] = ["alpha", "beta", "gamma"]
        self.reseal(plan)
        records = [self.record(), self.record("beta"), self.record("gamma")]
        result = self.validate(plan, execution={"ok": True, "records": records})
        self.assertEqual(sum(e["code"] == "E_EXECUTION_BOUNDARY" for e in result["errors"]), 2)

    def test_d15_absolute_windows_traversal_symlink_and_unregistered_outputs_fail(self):
        outside = self.repo.parent / f"{self.repo.name}-outside"
        outside.write_text("outside", encoding="utf-8")
        (self.repo / "escape").symlink_to(outside)
        try:
            for raw in ["/tmp/x", "C:\\x", "../x", "escape", "rogue.txt"]:
                with self.subTest(raw=raw):
                    self.profiles["profiles"][0]["generated_outputs"] = [raw]
                    self.save_authorities()
                    codes = self.codes(self.validate())
                    expected = "E_UNSAFE_PATH" if raw != "rogue.txt" else "E_UNREGISTERED_OUTPUT"
                    self.assertIn(expected, codes)
        finally:
            outside.unlink()

    def test_d16_cli_success_emits_json_and_human_summary(self):
        plan_path = self.repo / "plan.json"
        plan_path.write_text(json.dumps(self.plan), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(ROOT / "tools/operations/validate_incremental_execution.py"), "--plan", str(plan_path), "--root", str(self.repo), "--check"],
            text=True, capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["ok"])
        self.assertIn("PASS:", completed.stderr)

    def test_d17_cli_failure_is_nonzero_with_stable_error_code(self):
        plan = copy.deepcopy(self.plan)
        plan["claim_ceiling"] = "tampered"
        plan_path = self.repo / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(ROOT / "tools/operations/validate_incremental_execution.py"), "--plan", str(plan_path), "--root", str(self.repo), "--check"],
            text=True, capture_output=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("E_PLAN_HASH_MISMATCH", self.codes(json.loads(completed.stdout)))

    def test_d18_exception_never_silently_passes(self):
        plan_path = self.repo / "broken.json"
        plan_path.write_text("{", encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(ROOT / "tools/operations/validate_incremental_execution.py"), "--plan", str(plan_path), "--root", str(self.repo), "--check"],
            text=True, capture_output=True,
        )
        result = json.loads(completed.stdout)
        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(result["ok"])
        self.assertIn("E_VALIDATOR_EXCEPTION", self.codes(result))


if __name__ == "__main__":
    unittest.main()
