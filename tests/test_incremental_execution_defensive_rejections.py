import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.operations.plan_incremental_execution import plan as production_plan
from tools.operations.run_incremental_execution import (
    DefensiveBoundaryError,
    cache_hit,
    canonical,
    digest_bytes,
    execute_plan,
    profile_identity,
)
from tools.operations.validate_incremental_execution import (
    authority_fingerprint,
    compute_plan_hash,
    validate_incremental_execution,
)


class PhaseD3DefensiveRejections(unittest.TestCase):
    """Local-only single-variable rejection cases through production entry points."""

    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, "tools/operations/generate_component_profiles.py", "--check"], cwd=ROOT, check=True)
        subprocess.run([sys.executable, "tools/operations/validate_component_profiles.py"], cwd=ROOT, check=True, capture_output=True, text=True)

    def setUp(self):
        self.network_guards = [
            mock.patch("socket.create_connection", side_effect=AssertionError("D3 network access forbidden")),
            mock.patch("socket.socket.connect", side_effect=AssertionError("D3 network access forbidden")),
            mock.patch("socket.socket.connect_ex", side_effect=AssertionError("D3 network access forbidden")),
        ]
        for guard in self.network_guards:
            guard.start()
            self.addCleanup(guard.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        (self.repo / "data/operations").mkdir(parents=True)
        (self.repo / "input.txt").write_text("input\n", encoding="utf-8")
        (self.repo / "out.txt").write_text("before\n", encoding="utf-8")
        self.registry_path = self.repo / "data/operations/project-components.json"
        self.topology_path = self.repo / "data/operations/change-propagation-topology.json"
        self.profiles_path = self.repo / "data/operations/component-execution-profiles.json"
        self.cache_dir = self.repo / ".cache/q32i"
        self.registry = {"registry_version": "1.0.0", "components": [{"component_id": "alpha", "path_patterns": ["input.txt", "out.txt"]}]}
        self.topology = {"topology_version": "1.0.0", "relations": []}
        self.profiles = {"schema_version": "1.0.0", "profiles": [self.automatic_profile()]}
        self.save_authorities()
        self.plan = self.make_plan()

        # Every case starts from a live planner baseline and an independent valid
        # fixture baseline accepted by the production executor and unified validator.
        self.live_plan = production_plan({"task_id": self.id(), "changed_paths": ["README.md"]})
        self.assertTrue(validate_incremental_execution(self.live_plan)["ok"])
        dry_run = execute_plan(self.plan, root=self.repo, profiles_path=self.profiles_path, cache_dir=self.cache_dir)
        self.assertTrue(self.validate(execution=dry_run)["ok"])
        self.before_outside = sorted(Path(self.temp.name).glob("outside-*"))

    def tearDown(self):
        self.assertEqual(self.before_outside, sorted(Path(self.temp.name).glob("outside-*")))
        self.temp.cleanup()

    def automatic_profile(self):
        return {
            "component_id": "alpha",
            "execution_kind": "automatic",
            "execution_capability": "automatic",
            "authoritative_inputs": ["input.txt"],
            "generated_outputs": ["out.txt"],
            "input_fingerprint_policy": {"kind": "sha256_sorted_file_set", "paths": ["input.txt"]},
            "output_fingerprint_policy": {"kind": "sha256_single_target", "target": "out.txt"},
            "producer_argv": [sys.executable, "-c", "from pathlib import Path\nPath('out.txt').write_text('after\\n')"],
            "validator_argv": [sys.executable, "-c", "raise SystemExit(0)"],
            "rollback_policy": "restore_registered_outputs_or_emit_recovery_package",
        }

    def save_authorities(self):
        for path, value in ((self.registry_path, self.registry), (self.topology_path, self.topology), (self.profiles_path, self.profiles)):
            path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")

    def make_plan(self):
        value = {
            "schema_version": "1.0.0",
            "request_identity": "D3-local-fixture",
            "normalized_change_seeds": ["input.txt"],
            "q32_affected_component_closure": ["alpha"],
            "affected_synchronization_surfaces": [],
            "component_decisions": [{"component_id": "alpha", "decision": "REBUILD", "non_impact_proof": None}],
            "full_rebuild_reasons": [],
            "unresolved_residue": [],
            "execution_order": ["alpha"],
            "claim_ceiling": "local repository fixture only",
        }
        return self.reseal(value)

    def reseal(self, value):
        value["plan_hash"] = compute_plan_hash(value)
        for decision in value.get("component_decisions", []):
            proof = decision.get("non_impact_proof")
            if isinstance(proof, dict):
                proof["plan_hash"] = value["plan_hash"]
        return value

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
        return {item["code"] for item in result["errors"]}

    def valid_cache(self, plan=None):
        plan = plan or self.plan
        identity = profile_identity(self.profiles_path, self.profiles, self.repo, plan)
        value = {"identity": identity, "output_fingerprints": identity["output_fingerprints"], "records": []}
        value["integrity_digest"] = digest_bytes(canonical(value).encode())
        return value

    def seal_artifact(self, value):
        value.pop("integrity_digest", None)
        value["integrity_digest"] = digest_bytes(canonical(value).encode())
        return value

    def assert_boundary_error(self, code, callback):
        with self.assertRaises(DefensiveBoundaryError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code)

    def failed_execution(self):
        self.profiles["profiles"][0]["producer_argv"] = [sys.executable, "-c", "from pathlib import Path\nPath('out.txt').write_text('failed\\n')\nraise SystemExit(7)"]
        self.save_authorities()
        return execute_plan(self.plan, apply=True, isolated_worktree=True, root=self.repo, profiles_path=self.profiles_path, cache_dir=self.cache_dir)

    # G1 command input contract
    def test_d3_g1_01_caller_command_is_ignored(self):
        forged = copy.deepcopy(self.plan)
        forged["producer_argv"] = [sys.executable, "-c", "raise SystemExit(99)"]
        self.assert_boundary_error("E_PLAN_HASH_MISMATCH", lambda: execute_plan(forged, apply=True, isolated_worktree=True, root=self.repo, profiles_path=self.profiles_path, cache_dir=self.cache_dir))
        self.assertEqual((self.repo / "out.txt").read_text(), "before\n")

    def test_d3_g1_02_shell_string_is_rejected(self):
        self.profiles["profiles"][0]["producer_argv"] = "python -c invalid"
        self.save_authorities()
        self.assert_boundary_error("E_COMMAND_ARGV", lambda: execute_plan(self.plan, apply=True, isolated_worktree=True, root=self.repo, profiles_path=self.profiles_path, cache_dir=self.cache_dir))
        self.assertEqual((self.repo / "out.txt").read_text(), "before\n")

    def test_d3_g1_03_execution_command_identity_mismatch(self):
        execution = execute_plan(self.plan, root=self.repo, profiles_path=self.profiles_path, cache_dir=self.cache_dir)
        execution["records"][0]["argv"] = [sys.executable, "-c", "raise SystemExit(99)"]
        self.assertIn("E_EXECUTION_COMMAND_IDENTITY", self.codes(self.validate(execution=execution)))

    def test_d3_g1_04_cache_command_identity_mismatch(self):
        cache = self.valid_cache()
        cache["records"] = [{"component_id": "alpha", "argv": [sys.executable, "-c", "raise SystemExit(99)"]}]
        self.seal_artifact(cache)
        self.assertIn("E_CACHE_COMMAND_IDENTITY", self.codes(self.validate(cache=cache)))

    # G2 repository path and write contract
    def test_d3_g2_01_authoritative_input_escape(self):
        self.profiles["profiles"][0]["authoritative_inputs"] = ["../outside-input"]
        self.save_authorities()
        self.assertIn("E_UNSAFE_PATH", self.codes(self.validate()))
        self.assert_boundary_error("E_UNSAFE_PATH", lambda: execute_plan(self.plan, root=self.repo, profiles_path=self.profiles_path, cache_dir=self.cache_dir))

    def test_d3_g2_02_generated_output_symlink_escape(self):
        outside = Path(self.temp.name) / "outside-target"
        outside.write_text("outside\n", encoding="utf-8")
        (self.repo / "escape.txt").symlink_to(outside)
        self.registry["components"][0]["path_patterns"].append("escape.txt")
        self.profiles["profiles"][0]["generated_outputs"] = ["escape.txt"]
        self.save_authorities()
        self.assert_boundary_error("E_UNSAFE_PATH", lambda: execute_plan(self.plan, apply=True, isolated_worktree=True, root=self.repo, profiles_path=self.profiles_path, cache_dir=self.cache_dir))
        self.assertEqual(outside.read_text(), "outside\n")
        outside.unlink()

    def test_d3_g2_03_cache_directory_escape(self):
        outside = Path(self.temp.name) / "outside-cache"
        self.assert_boundary_error("E_UNSAFE_PATH", lambda: execute_plan(self.plan, apply=True, isolated_worktree=True, root=self.repo, profiles_path=self.profiles_path, cache_dir=outside))
        self.assertFalse(outside.exists())

    def test_d3_g2_04_unregistered_write_is_removed(self):
        self.profiles["profiles"][0]["producer_argv"] = [sys.executable, "-c", "from pathlib import Path\nPath('rogue.txt').write_text('rogue')"]
        self.save_authorities()
        result = execute_plan(self.plan, apply=True, isolated_worktree=True, root=self.repo, profiles_path=self.profiles_path, cache_dir=self.cache_dir)
        self.assertFalse(result["ok"])
        self.assertEqual(result["records"][0]["error_code"], "E_UNREGISTERED_WRITE")
        self.assertFalse((self.repo / "rogue.txt").exists())

    def test_d3_g2_05_recovery_target_escape(self):
        execution = self.failed_execution()
        package = Path(execution["recovery_package"])
        recovery = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
        recovery["restored_files"] = ["../outside-restore"]
        self.seal_artifact(recovery)
        self.assertIn("E_UNSAFE_PATH", self.codes(self.validate(execution=execution, recovery=recovery, recovery_base=package)))

    # G3 cache and authority identity contract
    def test_d3_g3_01_cache_integrity_mismatch(self):
        cache = self.valid_cache()
        cache["records"] = [{"forged": True}]
        self.assertIn("E_CACHE_INTEGRITY", self.codes(self.validate(cache=cache)))

    def test_d3_g3_02_profile_digest_mismatch(self):
        cache = self.valid_cache()
        self.profiles["schema_version"] = "changed"
        self.save_authorities()
        self.assertIn("E_CACHE_IDENTITY", self.codes(self.validate(cache=cache)))

    def test_d3_g3_03_registry_digest_mismatch(self):
        cache = self.valid_cache()
        self.registry["registry_version"] = "changed"
        self.save_authorities()
        self.assertIn("E_CACHE_IDENTITY", self.codes(self.validate(cache=cache)))

    def test_d3_g3_04_topology_digest_mismatch(self):
        cache = self.valid_cache()
        self.topology["topology_version"] = "changed"
        self.save_authorities()
        self.assertIn("E_CACHE_IDENTITY", self.codes(self.validate(cache=cache)))

    def test_d3_g3_05_producer_identity_mismatch(self):
        cache = self.valid_cache()
        self.profiles["profiles"][0]["producer_argv"] = [sys.executable, "-c", "raise SystemExit(0)"]
        self.save_authorities()
        self.assertFalse(cache_hit(self.cache_dir, self.plan, self.profiles_path, self.profiles, self.repo))
        self.assertIn("E_CACHE_IDENTITY", self.codes(self.validate(cache=cache)))

    def test_d3_g3_06_validator_identity_mismatch(self):
        cache = self.valid_cache()
        self.profiles["profiles"][0]["validator_argv"] = [sys.executable, "-c", "print('changed')"]
        self.save_authorities()
        self.assertIn("E_CACHE_IDENTITY", self.codes(self.validate(cache=cache)))

    def test_d3_g3_07_plan_identity_mismatch(self):
        cache = self.valid_cache()
        changed_plan = copy.deepcopy(self.plan)
        changed_plan["request_identity"] = "different-plan"
        self.reseal(changed_plan)
        self.assertIn("E_CACHE_IDENTITY", self.codes(self.validate(changed_plan, cache=cache)))

    def test_d3_g3_08_input_fingerprint_mismatch(self):
        cache = self.valid_cache()
        (self.repo / "input.txt").write_text("changed\n", encoding="utf-8")
        self.assertIn("E_CACHE_IDENTITY", self.codes(self.validate(cache=cache)))

    def test_d3_g3_09_output_fingerprint_mismatch(self):
        cache = self.valid_cache()
        (self.repo / "out.txt").write_text("stale\n", encoding="utf-8")
        self.assertIn("E_CACHE_IDENTITY", self.codes(self.validate(cache=cache)))

    # G4 plan, proof, execution, and recovery consistency contract
    def test_d3_g4_01_duplicate_decision(self):
        forged = copy.deepcopy(self.plan)
        forged["component_decisions"].append(copy.deepcopy(forged["component_decisions"][0]))
        self.reseal(forged)
        self.assertIn("E_PLAN_DUPLICATE_DECISION", self.codes(self.validate(forged)))

    def test_d3_g4_02_affected_cannot_claim_no_change(self):
        forged = copy.deepcopy(self.plan)
        forged["component_decisions"][0] = {"component_id": "alpha", "decision": "NO_CHANGE_WITH_PROOF", "non_impact_proof": self.proof("alpha")}
        forged["execution_order"] = []
        self.reseal(forged)
        self.assertIn("E_AFFECTED_NO_CHANGE", self.codes(self.validate(forged)))

    def proof(self, cid):
        return {
            "component_id": cid, "basis": "fixture exclusion", "unchanged_authoritative_input_fingerprints": [],
            "unchanged_dependency_fingerprints": [], "traversed_declared_relations": [], "excluded_declared_relations": [],
            "excluded_trigger_dimensions": ["identity"], "proof_method": "registered fixture closure", "plan_hash": "pending",
            "authority_fingerprint": authority_fingerprint(self.registry_path, self.topology_path, self.profiles_path),
            "expiry_or_recheck_condition": "any authority or input change", "claim_ceiling": "repository dependency only",
        }

    def test_d3_g4_03_proof_component_binding(self):
        forged = copy.deepcopy(self.live_plan)
        decision = next(item for item in forged["component_decisions"] if item["decision"] == "NO_CHANGE_WITH_PROOF")
        decision["non_impact_proof"]["component_id"] = "wrong-component"
        self.reseal(forged)
        result = validate_incremental_execution(forged)
        self.assertIn("E_PROOF_COMPONENT_BINDING", self.codes(result))

    def test_d3_g4_04_execution_continues_after_failure(self):
        failed = self.failed_execution()
        failed["records"].append(copy.deepcopy(failed["records"][0]))
        self.assertIn("E_EXECUTION_CONTINUED_AFTER_FAILURE", self.codes(self.validate(execution=failed)))

    def test_d3_g4_05_recovery_component_identity(self):
        execution = self.failed_execution()
        package = Path(execution["recovery_package"])
        recovery = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
        recovery["component_identity"] = ["wrong-component"]
        self.seal_artifact(recovery)
        self.assertIn("E_RECOVERY_COMPONENT_IDENTITY", self.codes(self.validate(execution=execution, recovery=recovery, recovery_base=package)))

    # G5 lifecycle, self-reference, and scope contract
    def test_d3_g5_01_lifecycle_escalation(self):
        forged = copy.deepcopy(self.plan)
        forged["lifecycle_status"] = "Current"
        self.reseal(forged)
        self.assertIn("E_LIFECYCLE_ESCALATION", self.codes(self.validate(forged)))

    def test_d3_g5_02_self_referential_head_authority(self):
        forged = copy.deepcopy(self.plan)
        forged["candidate_basis"] = "current HEAD is the candidate's own authority"
        self.reseal(forged)
        self.assertIn("E_SELF_REFERENTIAL_AUTHORITY", self.codes(self.validate(forged)))

    def test_d3_g5_03_unauthorized_scope_asset(self):
        forged = copy.deepcopy(self.plan)
        forged["scope_assets"] = ["experiments/shadow/phase-d4.json"]
        self.reseal(forged)
        self.assertIn("E_SCOPE_CONTAMINATION", self.codes(self.validate(forged)))


if __name__ == "__main__":
    unittest.main()
