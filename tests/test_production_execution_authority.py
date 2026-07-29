"""Regression probes promoted from the independent Q32I production review."""
from __future__ import annotations

import copy
import json
import os
from collections import Counter
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.operations.plan_incremental_execution import plan as production_plan
from tools.operations.run_incremental_execution import DefensiveBoundaryError, execute_plan, repository_snapshot, snapshot_fingerprint
from tools.operations.validate_incremental_execution import compute_plan_hash


def copy_production_authority(destination: Path) -> None:
    for raw in ("data/operations/project-components.json", "data/operations/change-propagation-topology.json", "data/operations/component-execution-profiles.json"):
        target = destination / raw
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / raw, target)


class ProductionProfileProbe(unittest.TestCase):
    def test_production_capability_contract_and_all_local_validators_run(self):
        """Production-capability contract, derived from the authoritative registries (V17 P4).

        Three universes must stay distinct and consistent:
          1. registry universe        — data/operations/project-components.json (declares every
                                         component AND its schema-declared lifecycle.status)
          2. profile-validation universe — data/operations/component-execution-profiles.json
                                         (one execution profile per registered component)
          3. production-execution authority — derived from each profile's execution_capability /
                                         validation_capability (which components may be auto/validated
                                         produced vs. which require responsible-human manual review)
        The contract is NOT a hardcoded snapshot count (52/59); it is derived from the registry
        and the declared lifecycle states, so it stays valid as components are added.
        """
        profiles_doc = json.loads((ROOT / "data/operations/component-execution-profiles.json").read_text())
        profiles = profiles_doc["profiles"]
        registry_doc = json.loads((ROOT / "data/operations/project-components.json").read_text())

        def iter_components(node):
            for comp in node.get("components", []):
                yield comp
            for grp in node.get("groups", []):
                yield from iter_components(grp)

        registered = list(iter_components(registry_doc))
        registered_ids = {c["component_id"] for c in registered}
        profile_ids = {p["component_id"] for p in profiles}
        # Universe alignment: the profile-validation universe is in 1:1 correspondence with the
        # registry universe. This is the authority-derived replacement for the old hardcoded
        # `len(profiles) == 52` (now 59 components; the count is not the contract — the bijection is).
        self.assertEqual(profile_ids, registered_ids,
                         "execution profiles must be in 1:1 correspondence with registered components")

        exec_counts = Counter(p["execution_capability"] for p in profiles)
        val_counts = Counter(p["validation_capability"] for p in profiles)
        total = len(profiles)

        # Architectural invariants (structural, not a snapshot count):
        # exactly one automatic component — the system map projection — and nothing is executed
        # via external attestation in this architecture.
        self.assertEqual(exec_counts["automatic"], 1)
        self.assertEqual(exec_counts["external_attestation"], 0)
        self.assertEqual(val_counts["external_attestation"], 0)
        # validation_only / automatic components are exactly those carrying a local validator_argv.
        local = [p for p in profiles if "validator_argv" in p]
        self.assertEqual(len(local), exec_counts["automatic"] + exec_counts["validation_only"])
        self.assertEqual(exec_counts["validation_only"], val_counts["local_validation_only"])
        self.assertEqual(exec_counts["automatic"], val_counts["local_automatic_validation"])
        self.assertEqual(exec_counts["manual"], val_counts["manual_review"])
        self.assertEqual(exec_counts["manual"], total - len(local))

        # Lifecycle contract: a draft_candidate component is NOT production-capable. It must remain
        # manual / manual_review and carry no automatic validator_argv until it is promoted. This
        # keeps the draft universe out of the production-execution authority count (the old test
        # conflated everything into a single hardcoded number).
        draft_ids = {
            c["component_id"] for c in registered
            if isinstance(c.get("lifecycle"), dict) and c["lifecycle"].get("status") == "draft_candidate"
        }
        for p in profiles:
            if p["component_id"] in draft_ids:
                self.assertEqual(p["execution_capability"], "manual",
                                 f"draft_candidate component {p['component_id']} must be manual, not production-capable")
                self.assertEqual(p["validation_capability"], "manual_review",
                                 f"draft_candidate component {p['component_id']} must be manual_review")
                self.assertNotIn("validator_argv", p,
                                 f"draft_candidate component {p['component_id']} must not carry an automatic validator_argv")

        # No profile may declare the forbidden validator argv.
        self.assertFalse(any(p.get("validator_argv") == ["python3", "tools/validate_protocol_canonical.py", "--check"] for p in profiles))
        # manual_review / external_attestation profiles must not carry an automatic validator_argv.
        self.assertTrue(all("validator_argv" not in p for p in profiles if p["validation_capability"] in {"manual_review", "external_attestation"}))

        with tempfile.TemporaryDirectory() as tmp:
            checkout = Path(tmp) / "checkout"
            subprocess.run(["git", "worktree", "add", "--detach", str(checkout), "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True)
            try:
                shutil.copytree(ROOT, checkout, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git", ".cache", "__pycache__", "*.pyc"), symlinks=True)
                for p in local:
                    with self.subTest(component=p["component_id"]):
                        completed = subprocess.run(p["validator_argv"], cwd=checkout, text=True, capture_output=True)
                        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(checkout)], cwd=ROOT, check=True, capture_output=True, text=True)

    def test_production_profiles_materialize_only_declared_outputs(self):
        profiles = json.loads((ROOT / "data/operations/component-execution-profiles.json").read_text())
        automatic = [p for p in profiles["profiles"] if p["execution_capability"] == "automatic"]
        self.assertEqual([p["component_id"] for p in automatic], ["system_map_projection"])
        self.assertTrue(all(not p.get("producer_argv") for p in profiles["profiles"] if p["execution_capability"] != "automatic"))
        with tempfile.TemporaryDirectory() as tmp:
            checkout = Path(tmp) / "checkout"
            shutil.copytree(ROOT, checkout, ignore=shutil.ignore_patterns(".git", ".cache", "__pycache__", "*.pyc"), symlinks=True)
            subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
            subprocess.run(["git", "config", "user.email", "q32i@test.invalid"], cwd=checkout, check=True)
            subprocess.run(["git", "config", "user.name", "Q32I Test"], cwd=checkout, check=True)
            subprocess.run(["git", "add", "."], cwd=checkout, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=checkout, check=True)
            declared = set(automatic[0]["generated_outputs"])
            for raw in declared:
                path = checkout / raw
                if path.exists() or path.is_symlink(): path.unlink()
            baseline = repository_snapshot(checkout)
            completed = subprocess.run(automatic[0]["producer_argv"], cwd=checkout, text=True, capture_output=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            subprocess.run(automatic[0]["validator_argv"], cwd=checkout, check=True, capture_output=True, text=True)
            after = repository_snapshot(checkout)
            changed = {p for p in set(baseline) | set(after) if snapshot_fingerprint(baseline.get(p)) != snapshot_fingerprint(after.get(p))}
            self.assertEqual(changed, declared)
            self.assertTrue(all((checkout / raw).is_file() for raw in declared))


class CompleteRollbackProbe(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        (self.repo / "data/operations").mkdir(parents=True)
        (self.repo / "input.txt").write_text("input\n")
        (self.repo / "out.txt").write_text("before\n")
        (self.repo / "ordinary.txt").write_text("ordinary-before\n")
        (self.repo / "deleted.txt").write_text("deleted-before\n")
        (self.repo / "target-a").write_text("a\n")
        (self.repo / "target-b").write_text("b\n")
        (self.repo / "ordinary-dir").mkdir()
        (self.repo / "ordinary-dir/nested.txt").write_text("nested-before\n")
        (self.repo / "link").symlink_to("target-a")
        os.chmod(self.repo / "ordinary.txt", 0o640)
        self.registry = {"components":[{"component_id":"alpha","path_patterns":["input.txt","out.txt"]}]}
        self.topology = {"relations":[]}
        self.profile = {"schema_version":"1.0.0","profiles":[{"component_id":"alpha","execution_capability":"automatic","validation_capability":"local_automatic_validation","execution_kind":"automatic","execution_cwd":".","authoritative_inputs":["input.txt"],"generated_outputs":["out.txt"],"input_fingerprint_policy":{"kind":"sha256_sorted_file_set","paths":["input.txt"]},"output_fingerprint_policy":{"kind":"sha256_declared_outputs","target":"out.txt"},"producer_argv":[sys.executable,"-c","raise SystemExit(7)"],"validator_argv":[sys.executable,"-c","raise SystemExit(0)"],"rollback_policy":"restore_registered_outputs_or_emit_recovery_package"}]}
        for name, value in (("project-components.json",self.registry),("change-propagation-topology.json",self.topology),("component-execution-profiles.json",self.profile)):
            (self.repo / "data/operations" / name).write_text(json.dumps(value)+"\n")
        self.plan = {"schema_version":"1.0.0","request_identity":"rollback","normalized_change_seeds":["input.txt"],"q32_affected_component_closure":["alpha"],"affected_synchronization_surfaces":[],"component_decisions":[{"component_id":"alpha","decision":"REBUILD","non_impact_proof":None}],"full_rebuild_reasons":[],"unresolved_residue":[],"execution_order":["alpha"],"claim_ceiling":"fixture"}
        self.plan["plan_hash"] = compute_plan_hash(self.plan)
        self.cache = self.repo / ".cache/q32i"

    def tearDown(self): self.temp.cleanup()

    def run_mutation(self, code: str, recovery_only: bool = False):
        self.profile["profiles"][0]["producer_argv"]=[sys.executable,"-c",code]
        if recovery_only: self.profile["profiles"][0]["rollback_policy"]="recovery_package_only"
        (self.repo / "data/operations/component-execution-profiles.json").write_text(json.dumps(self.profile)+"\n")
        before = repository_snapshot(self.repo, (self.cache,))
        result = execute_plan(self.plan, apply=True, isolated_worktree=True, root=self.repo, profiles_path=self.repo/"data/operations/component-execution-profiles.json", cache_dir=self.cache)
        return before, result

    def assert_restored(self, before, result):
        after = repository_snapshot(self.repo, (self.cache,))
        self.assertEqual({k:snapshot_fingerprint(v) for k,v in before.items()}, {k:snapshot_fingerprint(v) for k,v in after.items()})
        self.assertEqual(result["records"][-1]["rollback_status"], "restored")

    def test_rollback_restores_modified_preexisting_unregistered_file(self):
        before,result=self.run_mutation("from pathlib import Path\nPath('ordinary.txt').write_text('changed')\nraise SystemExit(7)");self.assert_restored(before,result)
    def test_rollback_restores_deleted_preexisting_unregistered_file(self):
        before,result=self.run_mutation("from pathlib import Path\nPath('deleted.txt').unlink()\nraise SystemExit(7)");self.assert_restored(before,result)
    def test_rollback_removes_new_unregistered_file(self):
        before,result=self.run_mutation("from pathlib import Path\nPath('new.txt').write_text('new')\nraise SystemExit(7)");self.assert_restored(before,result)
    def test_rollback_restores_symlink_type_and_target(self):
        before,result=self.run_mutation("from pathlib import Path\np=Path('link')\np.unlink()\np.symlink_to('target-b')\nraise SystemExit(7)");self.assert_restored(before,result);self.assertEqual(os.readlink(self.repo/'link'),'target-a')
    def test_rollback_restores_directory_type_and_contents(self):
        before,result=self.run_mutation("import shutil\nfrom pathlib import Path\nshutil.rmtree('ordinary-dir')\nPath('ordinary-dir').write_text('replacement')\nraise SystemExit(7)");self.assert_restored(before,result);self.assertEqual((self.repo/'ordinary-dir/nested.txt').read_text(),'nested-before\n')
    def test_rollback_restores_mode(self):
        before,result=self.run_mutation("import os\nos.chmod('ordinary.txt',0o777)\nraise SystemExit(7)");self.assert_restored(before,result);self.assertEqual(stat.S_IMODE((self.repo/'ordinary.txt').stat().st_mode),0o640)
    def test_unrecoverable_policy_never_reports_restored(self):
        _,result=self.run_mutation("from pathlib import Path\nPath('ordinary.txt').write_text('changed')\nraise SystemExit(7)",True);self.assertEqual(result['records'][-1]['rollback_status'],'recovery-package-required');self.assertTrue(json.loads((Path(result['recovery_package'])/'manifest.json').read_text())['unrecovered_files'])


class ApplyAuthorityPreflightProbe(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.repo = Path(self.temp.name)
        copy_production_authority(self.repo)
        self.profiles_path=self.repo/'data/operations/component-execution-profiles.json';self.cache=self.repo/'.cache/q32i'
        self.plan=production_plan({'task_id':'preflight-probe','changed_paths':['data/architecture/interactive-system-map.json']})
        self.output=self.repo/'data/architecture/interactive-system-map.json'

    def tearDown(self): self.temp.cleanup()
    def reseal(self,p): p['plan_hash']=compute_plan_hash(p);[d['non_impact_proof'].__setitem__('plan_hash',p['plan_hash']) for d in p.get('component_decisions',[]) if isinstance(d.get('non_impact_proof'),dict)];return p
    def reject_zero(self, mutate):
        p=copy.deepcopy(self.plan);mutate(p)
        before=repository_snapshot(self.repo,(self.cache,))
        with mock.patch('tools.operations.run_incremental_execution.subprocess.run') as runner:
            with self.assertRaises(DefensiveBoundaryError): execute_plan(p,apply=True,isolated_worktree=True,root=self.repo,profiles_path=self.profiles_path,cache_dir=self.cache)
            runner.assert_not_called()
        self.assertEqual({k:snapshot_fingerprint(v) for k,v in before.items()},{k:snapshot_fingerprint(v) for k,v in repository_snapshot(self.repo,(self.cache,)).items()});self.assertFalse(self.cache.exists())
    def test_preflight_rejects_bad_plan_hash_zero_side_effects(self): self.reject_zero(lambda p:p.__setitem__('plan_hash','0'*64))
    def test_preflight_rejects_duplicate_decision_zero_side_effects(self): self.reject_zero(lambda p:(p['component_decisions'].append(copy.deepcopy(p['component_decisions'][0])),self.reseal(p)))
    def test_preflight_rejects_missing_decision_zero_side_effects(self): self.reject_zero(lambda p:(p['component_decisions'].pop(),self.reseal(p)))
    def test_preflight_rejects_affected_no_change_zero_side_effects(self): self.reject_zero(lambda p:([d.update(decision='NO_CHANGE_WITH_PROOF',non_impact_proof=None) for d in p['component_decisions'] if d['component_id']==p['q32_affected_component_closure'][0]],self.reseal(p)))
    def test_preflight_rejects_nonautomatic_order_zero_side_effects(self): self.reject_zero(lambda p:(p['execution_order'].__setitem__(0,'human_knowledge_surfaces'),[d.update(decision='REBUILD') for d in p['component_decisions'] if d['component_id']=='human_knowledge_surfaces'],self.reseal(p)))
    def test_preflight_rejects_nonrebuild_decision_zero_side_effects(self): self.reject_zero(lambda p:([d.update(decision='REVALIDATE') for d in p['component_decisions'] if d['component_id']==p['execution_order'][0]],self.reseal(p)))
    def test_preflight_rejects_authority_identity_zero_side_effects(self): self.reject_zero(lambda p:p.__setitem__('authority_fingerprint','0'*64))
    def test_preflight_rejects_closure_order_mismatch_zero_side_effects(self): self.reject_zero(lambda p:(p['q32_affected_component_closure'].remove(p['execution_order'][0]),self.reseal(p)))
    def test_preflight_rejects_replaced_profile_argv_zero_side_effects(self):
        profiles=json.loads(self.profiles_path.read_text());[x.update(producer_argv=[sys.executable,'-c','raise SystemExit(99)']) for x in profiles['profiles'] if x['execution_capability']=='automatic'];self.profiles_path.write_text(json.dumps(profiles)+'\n');self.reject_zero(lambda p:None)


if __name__ == '__main__': unittest.main()
