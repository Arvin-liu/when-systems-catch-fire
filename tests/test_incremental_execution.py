import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.operations.plan_incremental_execution import plan
from tools.operations.run_incremental_execution import execute_plan, profile_identity
from tools.operations.validate_incremental_execution import (
    canonical,
    canonical_plan_bytes,
    compute_plan_hash,
    digest_bytes,
    validate_incremental_execution,
)


class PhaseD2EndToEndAcceptance(unittest.TestCase):
    def codes(self, result):
        return {item["code"] for item in result["errors"]}

    def assert_valid_live_plan(self, request):
        document = plan(request)
        result = validate_incremental_execution(document)
        self.assertTrue(result["ok"], result)
        return document

    def reseal(self, document):
        document["plan_hash"] = compute_plan_hash(document)
        for item in document["component_decisions"]:
            proof = item.get("non_impact_proof")
            if isinstance(proof, dict):
                proof["plan_hash"] = document["plan_hash"]
        return document

    def authority_snapshot(self):
        temp = tempfile.TemporaryDirectory()
        repo = Path(temp.name)
        (repo / "data/operations").mkdir(parents=True)
        for name in (
            "project-components.json",
            "change-propagation-topology.json",
            "component-execution-profiles.json",
        ):
            shutil.copyfile(ROOT / "data/operations" / name, repo / "data/operations" / name)
        return temp, repo

    def executor_fixture(self, specs):
        temp = tempfile.TemporaryDirectory()
        repo = Path(temp.name)
        (repo / "data/operations").mkdir(parents=True)
        (repo / "input.txt").write_text("input\n", encoding="utf-8")
        components = []
        profiles = []
        for cid, expression, rollback_policy in specs:
            output = f"{cid}.txt"
            (repo / output).write_text(f"before-{cid}\n", encoding="utf-8")
            components.append({"component_id": cid, "path_patterns": ["input.txt", output]})
            profiles.append({
                "component_id": cid,
                "execution_kind": "automatic",
                "execution_capability": "automatic",
                "validation_capability": "local_automatic_validation",
                "authoritative_inputs": ["input.txt"],
                "generated_outputs": [output],
                "input_fingerprint_policy": {"kind": "sha256_sorted_file_set", "paths": ["input.txt"]},
                "output_fingerprint_policy": {"kind": "sha256_single_target", "target": output},
                "producer_argv": [sys.executable, "-c", f"from pathlib import Path\n{expression}"],
                "validator_argv": [sys.executable, "-c", "0"],
                "rollback_policy": rollback_policy,
            })
        registry = {"registry_version": "1.0.0", "components": components}
        topology = {"topology_version": "1.0.0", "relations": []}
        profiles_doc = {"schema_version": "1.0.0", "profiles": profiles}
        for filename, document in (
            ("project-components.json", registry),
            ("change-propagation-topology.json", topology),
            ("component-execution-profiles.json", profiles_doc),
        ):
            (repo / "data/operations" / filename).write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")
        decisions = [{"component_id": cid, "decision": "REBUILD", "non_impact_proof": None} for cid, _, _ in specs]
        execution_plan = {
            "schema_version": "1.0.0",
            "request_identity": "d2-executor-fixture",
            "normalized_change_seeds": ["input.txt"],
            "q32_affected_component_closure": [cid for cid, _, _ in specs],
            "affected_synchronization_surfaces": [],
            "component_decisions": decisions,
            "full_rebuild_reasons": [],
            "unresolved_residue": [],
            "execution_order": [cid for cid, _, _ in specs],
            "claim_ceiling": "repository execution fixture only",
        }
        self.reseal(execution_plan)
        return temp, repo, profiles_doc, execution_plan

    def validate_fixture(self, repo, execution_plan, **kwargs):
        return validate_incremental_execution(execution_plan, root=repo, **kwargs)

    def test_d2_01_system_map_layout_change(self):
        document = self.assert_valid_live_plan({
            "task_id": "D2-01",
            "changed_paths": ["data/architecture/interactive-system-map-layout.json"],
            "changed_dimensions": ["deployment_rendering"],
            "change_classifications": ["INTERFACE_CHANGE"],
        })
        self.assertEqual(document["q32_affected_component_closure"], ["pages_pipeline", "system_map_layout", "system_map_projection"])
        decisions = {item["component_id"]: item for item in document["component_decisions"]}
        self.assertEqual(decisions["system_map_projection"]["decision"], "REBUILD")
        self.assertEqual(decisions["pages_pipeline"]["decision"], "REVALIDATE")
        self.assertEqual(decisions["foundation"]["decision"], "NO_CHANGE_WITH_PROOF")
        self.assertIn("external.pages_homepage", document["affected_synchronization_surfaces"])

    def test_d2_02_rights_publication_rule_change(self):
        document = self.assert_valid_live_plan({
            "task_id": "D2-02",
            "changed_paths": ["docs/governance/licensing-rights-inventory.md"],
            "changed_dimensions": ["governance", "usage"],
            "change_classifications": ["GOVERNANCE_CHANGE"],
        })
        self.assertEqual(document["q32_affected_component_closure"], ["l6", "licensing"])
        decisions = {item["component_id"]: item for item in document["component_decisions"]}
        for cid in ("l1", "l2", "l3", "l4", "mcf", "psd", "arn"):
            self.assertEqual(decisions[cid]["decision"], "NO_CHANGE_WITH_PROOF")

    def test_d2_03_single_case_change(self):
        document = self.assert_valid_live_plan({
            "task_id": "D2-03",
            "changed_paths": ["docs/publication/cases/jin-rise-case-source.md"],
            "changed_dimensions": ["capability"],
            "change_classifications": ["EVIDENCE_UPDATE"],
        })
        self.assertEqual(
            document["q32_affected_component_closure"],
            ["case_source", "external_input", "ignition_increment", "l6", "point_fire_analysis"],
        )
        decisions = {item["component_id"]: item for item in document["component_decisions"]}
        self.assertEqual(decisions["accepted_work"]["decision"], "NO_CHANGE_WITH_PROOF")
        self.assertIn("map_case_analysis", decisions["accepted_work"]["non_impact_proof"]["traversed_declared_relations"])
        self.assertIn("not truth or causal proof", document["claim_ceiling"])

    def test_d2_04_readme_ordinary_text_change(self):
        document = self.assert_valid_live_plan({
            "task_id": "D2-04",
            "changed_paths": ["README.md"],
            "changed_dimensions": ["identity"],
            "change_classifications": ["EVIDENCE_UPDATE"],
        })
        self.assertFalse(document["full_rebuild_reasons"])
        self.assertEqual(document["q32_affected_component_closure"], ["readme"])
        changed = [item for item in document["component_decisions"] if item["decision"] != "NO_CHANGE_WITH_PROOF"]
        self.assertEqual([(item["component_id"], item["decision"]) for item in changed], [("readme", "REVALIDATE")])

    def test_d2_05_registry_and_core_schema_force_full_rebuild(self):
        for changed_path in (
            "data/operations/project-components.json",
            "schemas/operations/project-components.schema.json",
        ):
            with self.subTest(changed_path=changed_path):
                document = self.assert_valid_live_plan({"task_id": "D2-05", "changed_paths": [changed_path]})
                self.assertTrue(all(item["decision"] == "FULL_REBUILD_REQUIRED" for item in document["component_decisions"]))
                forged = copy.deepcopy(document)
                forged["component_decisions"][0]["decision"] = "REVALIDATE"
                self.reseal(forged)
                self.assertIn("E_FULL_REBUILD_DOWNGRADED", self.codes(validate_incremental_execution(forged)))
        temp, repo = self.authority_snapshot()
        try:
            old_plan = plan({"task_id": "D2-05-old", "changed_paths": ["README.md"]})
            profiles_path = repo / "data/operations/component-execution-profiles.json"
            profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
            cache = {"identity": profile_identity(profiles_path, profiles, repo, old_plan), "output_fingerprints": {}, "records": []}
            cache["integrity_digest"] = digest_bytes(canonical(cache).encode())
            registry_path = repo / "data/operations/project-components.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["registry_version"] = "changed"
            registry_path.write_text(json.dumps(registry, sort_keys=True) + "\n", encoding="utf-8")
            self.assertIn("E_CACHE_IDENTITY", self.codes(validate_incremental_execution(old_plan, cache=cache, root=repo)))
        finally:
            temp.cleanup()

    def test_d2_06_topology_change_invalidates_proof_and_cache(self):
        for changed_path in (
            "data/operations/change-propagation-topology.json",
            "schemas/operations/change-propagation-topology.schema.json",
        ):
            with self.subTest(changed_path=changed_path):
                document = self.assert_valid_live_plan({"task_id": "D2-06", "changed_paths": [changed_path]})
                self.assertTrue(all(item["decision"] == "FULL_REBUILD_REQUIRED" for item in document["component_decisions"]))
                forged = copy.deepcopy(document)
                forged["component_decisions"][0]["decision"] = "REVALIDATE"
                self.reseal(forged)
                self.assertIn("E_FULL_REBUILD_DOWNGRADED", self.codes(validate_incremental_execution(forged)))
        temp, repo = self.authority_snapshot()
        try:
            old_plan = plan({"task_id": "D2-06-old", "changed_paths": ["README.md"]})
            profiles_path = repo / "data/operations/component-execution-profiles.json"
            profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
            cache = {"identity": profile_identity(profiles_path, profiles, repo, old_plan), "output_fingerprints": {}, "records": []}
            cache["integrity_digest"] = digest_bytes(canonical(cache).encode())
            topology_path = repo / "data/operations/change-propagation-topology.json"
            topology = json.loads(topology_path.read_text(encoding="utf-8"))
            topology["topology_version"] = "changed"
            topology_path.write_text(json.dumps(topology, sort_keys=True) + "\n", encoding="utf-8")
            result = validate_incremental_execution(old_plan, cache=cache, root=repo)
            self.assertIn("E_PROOF_AUTHORITY_BINDING", self.codes(result))
            self.assertIn("E_CACHE_IDENTITY", self.codes(result))
        finally:
            temp.cleanup()

    def test_d2_07_profile_policy_generator_force_full_and_invalidate_cache(self):
        for changed_path in (
            "data/operations/component-execution-profiles.json",
            "data/operations/component-execution-profile-policies.json",
            "tools/operations/generate_component_profiles.py",
            "schemas/operations/component-execution-profile.schema.json",
        ):
            with self.subTest(changed_path=changed_path):
                document = self.assert_valid_live_plan({"task_id": "D2-07", "changed_paths": [changed_path]})
                self.assertTrue(all(item["decision"] == "FULL_REBUILD_REQUIRED" for item in document["component_decisions"]))
                forged = copy.deepcopy(document)
                forged["component_decisions"][0]["decision"] = "REVALIDATE"
                self.reseal(forged)
                self.assertIn("E_FULL_REBUILD_DOWNGRADED", self.codes(validate_incremental_execution(forged)))
        temp, repo = self.authority_snapshot()
        try:
            old_plan = plan({"task_id": "D2-07-old", "changed_paths": ["README.md"]})
            profiles_path = repo / "data/operations/component-execution-profiles.json"
            profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
            cache = {"identity": profile_identity(profiles_path, profiles, repo, old_plan), "output_fingerprints": {}, "records": []}
            cache["integrity_digest"] = digest_bytes(canonical(cache).encode())
            profiles["profiles"][0]["validator_argv"] = [sys.executable, "-c", "0"]
            profiles_path.write_text(json.dumps(profiles, sort_keys=True) + "\n", encoding="utf-8")
            result = validate_incremental_execution(old_plan, cache=cache, root=repo)
            self.assertIn("E_PROOF_AUTHORITY_BINDING", self.codes(result))
            self.assertIn("E_CACHE_IDENTITY", self.codes(result))
        finally:
            temp.cleanup()

    def test_d2_08_missing_fingerprint_policy_fails_closed(self):
        for field in ("input_fingerprint_policy", "output_fingerprint_policy"):
            with self.subTest(field=field):
                temp, repo = self.authority_snapshot()
                try:
                    profiles_path = repo / "data/operations/component-execution-profiles.json"
                    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
                    del profiles["profiles"][0][field]
                    profiles_path.write_text(json.dumps(profiles, sort_keys=True) + "\n", encoding="utf-8")
                    old_plan = plan({"task_id": "D2-08", "changed_paths": ["README.md"]})
                    result = validate_incremental_execution(old_plan, root=repo)
                    self.assertFalse(result["ok"])
                    self.assertIn("E_PROFILE_FINGERPRINT_POLICY", self.codes(result))
                finally:
                    temp.cleanup()

    def test_d2_09_forged_cache_hit_rejected_by_executor_and_validator(self):
        spec = [("auto1", "Path('auto1.txt').write_text('rebuilt\\n')", "restore_registered_outputs_or_emit_recovery_package")]
        temp, repo, _, execution_plan = self.executor_fixture(spec)
        cache_dir = repo / ".cache/q32i"
        try:
            first = execute_plan(execution_plan, apply=True, isolated_worktree=True, root=repo, cache_dir=cache_dir)
            self.assertTrue(first["ok"])
            manifest_path = cache_dir / "manifest.json"
            forged = json.loads(manifest_path.read_text(encoding="utf-8"))
            forged["identity"]["plan_hash"] = "0" * 64
            result = self.validate_fixture(repo, execution_plan, cache=forged)
            self.assertIn("E_CACHE_INTEGRITY", self.codes(result))
            self.assertIn("E_CACHE_IDENTITY", self.codes(result))
            manifest_path.write_text(json.dumps(forged), encoding="utf-8")
            (repo / "auto1.txt").write_text("stale\n", encoding="utf-8")
            second = execute_plan(execution_plan, apply=True, isolated_worktree=True, root=repo, cache_dir=cache_dir)
            self.assertFalse(second["cache_hit"])
            self.assertEqual((repo / "auto1.txt").read_text(encoding="utf-8"), "rebuilt\n")
        finally:
            temp.cleanup()

    def test_d2_10_stale_generated_output_cannot_hide_behind_cache(self):
        spec = [("auto1", "Path('auto1.txt').write_text('fresh\\n')", "restore_registered_outputs_or_emit_recovery_package")]
        temp, repo, _, execution_plan = self.executor_fixture(spec)
        cache_dir = repo / ".cache/q32i"
        try:
            execute_plan(execution_plan, apply=True, isolated_worktree=True, root=repo, cache_dir=cache_dir)
            old_cache = json.loads((cache_dir / "manifest.json").read_text(encoding="utf-8"))
            for mode in ("modified", "missing"):
                with self.subTest(mode=mode):
                    if mode == "modified":
                        (repo / "auto1.txt").write_text("stale\n", encoding="utf-8")
                    else:
                        (repo / "auto1.txt").unlink()
                    self.assertIn("E_CACHE_IDENTITY", self.codes(self.validate_fixture(repo, execution_plan, cache=old_cache)))
                    result = execute_plan(execution_plan, apply=True, isolated_worktree=True, root=repo, cache_dir=cache_dir)
                    self.assertFalse(result["cache_hit"])
                    self.assertEqual((repo / "auto1.txt").read_text(encoding="utf-8"), "fresh\n")
        finally:
            temp.cleanup()

    def test_d2_11_missing_or_forged_non_impact_proof(self):
        base = plan({"task_id": "D2-11", "changed_paths": ["README.md"]})
        readme_index = next(i for i, item in enumerate(base["component_decisions"]) if item["component_id"] == "readme")
        proof_index = next(i for i, item in enumerate(base["component_decisions"]) if item["decision"] == "NO_CHANGE_WITH_PROOF")
        cases = []
        missing = copy.deepcopy(base)
        missing["component_decisions"][proof_index]["non_impact_proof"] = None
        self.reseal(missing)
        cases.append((missing, "E_PROOF_REQUIRED"))
        component = copy.deepcopy(base)
        component["component_decisions"][proof_index]["non_impact_proof"]["component_id"] = "readme"
        self.reseal(component)
        cases.append((component, "E_PROOF_COMPONENT_BINDING"))
        plan_hash = copy.deepcopy(base)
        plan_hash["component_decisions"][proof_index]["non_impact_proof"]["plan_hash"] = "0" * 64
        cases.append((plan_hash, "E_PROOF_PLAN_HASH_BINDING"))
        authority = copy.deepcopy(base)
        authority["component_decisions"][proof_index]["non_impact_proof"]["authority_fingerprint"] = "0" * 64
        self.reseal(authority)
        cases.append((authority, "E_PROOF_AUTHORITY_BINDING"))
        affected = copy.deepcopy(base)
        forged_proof = copy.deepcopy(affected["component_decisions"][proof_index]["non_impact_proof"])
        forged_proof["component_id"] = "readme"
        affected["component_decisions"][readme_index] = {"component_id": "readme", "decision": "NO_CHANGE_WITH_PROOF", "non_impact_proof": forged_proof}
        self.reseal(affected)
        cases.append((affected, "E_AFFECTED_NO_CHANGE"))
        for document, expected in cases:
            with self.subTest(expected=expected):
                result = validate_incremental_execution(document)
                self.assertFalse(result["ok"])
                self.assertIn(expected, self.codes(result))

    def test_d2_12_unknown_and_escaping_paths_fail_closed(self):
        for raw in ("unknown/path.txt", "/tmp/escape", "C:\\escape", "\\\\server\\share", "../escape"):
            with self.subTest(raw=raw):
                document = plan({"task_id": "D2-12", "changed_paths": [raw]})
                self.assertTrue(document["unresolved_residue"])
                self.assertTrue(all(item["decision"] == "FULL_REBUILD_REQUIRED" for item in document["component_decisions"]))
                self.assertTrue(validate_incremental_execution(document)["ok"])
        spec = [("auto1", "Path('escape').write_text('x')", "restore_registered_outputs_or_emit_recovery_package")]
        temp, repo, _, execution_plan = self.executor_fixture(spec)
        outside = repo.parent / f"{repo.name}-outside"
        outside.write_text("outside", encoding="utf-8")
        try:
            (repo / "auto1.txt").unlink()
            (repo / "auto1.txt").symlink_to(outside)
            result = self.validate_fixture(repo, execution_plan)
            self.assertIn("E_UNSAFE_PATH", self.codes(result))
        finally:
            outside.unlink()
            temp.cleanup()

    def test_d2_13_plan_is_byte_deterministic(self):
        request = {
            "task_id": "D2-13",
            "changed_paths": ["data/architecture/interactive-system-map-layout.json"],
            "changed_dimensions": ["deployment_rendering"],
            "change_classifications": ["INTERFACE_CHANGE"],
        }
        first, second = plan(copy.deepcopy(request)), plan(copy.deepcopy(request))
        self.assertEqual(canonical_plan_bytes(first), canonical_plan_bytes(second))
        self.assertEqual(first["plan_hash"], second["plan_hash"])
        for field in ("component_decisions", "q32_affected_component_closure", "execution_order"):
            self.assertEqual(first[field], second[field])
        self.assertTrue(validate_incremental_execution(first)["ok"])
        self.assertTrue(validate_incremental_execution(second)["ok"])

    def test_d2_14_midstream_failure_rollback_and_recovery(self):
        normal = "restore_registered_outputs_or_emit_recovery_package"
        specs = [
            ("auto1", "Path('auto1.txt').write_text('changed-one\\n')", normal),
            ("auto2", "(Path('auto2.txt').write_text('failed-two\\n'),1/0)", normal),
            ("auto3", "Path('auto3.txt').write_text('must-not-run\\n')", normal),
        ]
        temp, repo, _, execution_plan = self.executor_fixture(specs)
        cache_dir = repo / ".cache/q32i"
        try:
            before = {cid: (repo / f"{cid}.txt").read_bytes() for cid in ("auto1", "auto2", "auto3")}
            execution = execute_plan(execution_plan, apply=True, isolated_worktree=True, root=repo, cache_dir=cache_dir)
            self.assertFalse(execution["ok"])
            self.assertEqual([record["component_id"] for record in execution["records"]], ["auto1", "auto2"])
            self.assertEqual({cid: (repo / f"{cid}.txt").read_bytes() for cid in before}, before)
            package = Path(execution["recovery_package"])
            recovery = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
            result = self.validate_fixture(repo, execution_plan, execution=execution, recovery=recovery, recovery_base=package)
            self.assertTrue(result["ok"], result)
        finally:
            temp.cleanup()
        recovery_only = "recovery_package_only"
        specs[1] = ("auto2", "(Path('auto2.txt').write_text('failed-two\\n'),1/0)", recovery_only)
        temp, repo, _, execution_plan = self.executor_fixture(specs)
        cache_dir = repo / ".cache/q32i"
        try:
            execution = execute_plan(execution_plan, apply=True, isolated_worktree=True, root=repo, cache_dir=cache_dir)
            package = Path(execution["recovery_package"])
            recovery = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(recovery["unrecovered_files"])
            self.assertTrue((package / "backups/auto1.txt").is_file())
            result = self.validate_fixture(repo, execution_plan, execution=execution, recovery=recovery, recovery_base=package)
            self.assertTrue(result["ok"], result)
            forged = copy.deepcopy(recovery)
            forged["component_identity"][0] = "forged-component"
            forged.pop("integrity_digest")
            forged["integrity_digest"] = digest_bytes(canonical(forged).encode())
            result = self.validate_fixture(repo, execution_plan, execution=execution, recovery=forged, recovery_base=package)
            self.assertIn("E_RECOVERY_COMPONENT_IDENTITY", self.codes(result))
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
