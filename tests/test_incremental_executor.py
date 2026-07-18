import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.operations.run_incremental_execution import cache_hit, canonical, execute_plan


class PhaseCExecutorAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "q32i@test.invalid"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Q32I Test"], cwd=self.repo, check=True)
        (self.repo / "data/operations").mkdir(parents=True)
        (self.repo / "input.txt").write_text("input\n")
        (self.repo / "out1.txt").write_text("before-one\n")
        (self.repo / "out2.txt").write_text("before-two\n")
        (self.repo / ".gitignore").write_text(".cache/\n")
        (self.repo / "data/operations/project-components.json").write_text('{"components":[]}\n')
        (self.repo / "data/operations/change-propagation-topology.json").write_text('{"relations":[]}\n')
        self.profiles_path = self.repo / "data/operations/component-execution-profiles.json"
        self.cache = self.repo / ".cache/q32i"
        self.profiles = {"schema_version": "1.0.0", "profiles": [
            self.automatic("auto1", "out1.txt", "Path('out1.txt').write_text('after-one\\n')"),
            self.automatic("auto2", "out2.txt", "(Path('out2.txt').write_text('failed-write\\n'),1/0)"),
            {"component_id":"manual","execution_capability":"manual","execution_kind":"manual","authoritative_inputs":["input.txt"],"generated_outputs":[],"validator_argv":[sys.executable,"-c","0"]},
            {"component_id":"external","execution_capability":"external_attestation","execution_kind":"attestation","authoritative_inputs":[],"generated_outputs":[],"validator_argv":[sys.executable,"-c","0"]},
        ]}
        self.save_profiles()
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=self.repo, check=True)

    def tearDown(self): self.temp.cleanup()

    def automatic(self, cid, output, expression):
        return {"component_id":cid,"execution_capability":"automatic","execution_kind":"automatic","authoritative_inputs":["input.txt"],"generated_outputs":[output],"producer_argv":[sys.executable,"-c",f"from pathlib import Path\n{expression}"],"validator_argv":[sys.executable,"-c","0"],"rollback_policy":"restore_registered_outputs_or_emit_recovery_package"}

    def save_profiles(self): self.profiles_path.write_text(json.dumps(self.profiles, sort_keys=True) + "\n")
    def plan(self, order=None): return {"plan_hash":"a"*64,"execution_order":order or ["auto1"]}
    def execute(self, plan=None, apply=False, isolated=False): return execute_plan(plan or self.plan(), apply=apply, isolated_worktree=isolated, root=self.repo, profiles_path=self.profiles_path, cache_dir=self.cache)

    def test_c01_default_dry_run_zero_write(self):
        before=(self.repo/"out1.txt").read_bytes(); result=self.execute()
        self.assertEqual((self.repo/"out1.txt").read_bytes(),before);self.assertFalse(self.cache.exists());self.assertEqual(result["records"][0]["end_status"],"dry-run")

    def test_c02_apply_clean_and_isolated_gate(self):
        self.assertTrue(self.execute(apply=True)["ok"])
        (self.repo/"input.txt").write_text("dirty\n")
        with self.assertRaisesRegex(ValueError,"clean tree"): self.execute(apply=True)
        self.assertTrue(self.execute(apply=True,isolated=True)["ok"])

    def test_c03_only_registered_profile_argv_executes(self):
        plan=self.plan();plan["producer_argv"]=[sys.executable,"-c","raise SystemExit(99)"]
        result=self.execute(plan,True,True);self.assertEqual(result["records"][0]["return_code"],0);self.assertEqual((self.repo/"out1.txt").read_text(),"after-one\n")

    def test_c04_shell_metacharacters_never_interpreted(self):
        for injected in ["0;bad", "0&&bad", "0|bad", "$(bad)", "`bad`"]:
            self.profiles["profiles"][0]["producer_argv"]=[sys.executable,"-c",injected];self.save_profiles()
            with self.assertRaisesRegex(ValueError,"metacharacter"): self.execute(apply=True,isolated=True)
        self.assertFalse((self.repo/"pwned").exists())

    def test_c05_argv_injection_rejected(self):
        self.profiles["profiles"][0]["producer_argv"]="python -c evil";self.save_profiles()
        with self.assertRaisesRegex(ValueError,"argv array"): self.execute(apply=True,isolated=True)

    def test_c06_path_attacks_rejected(self):
        attacks=["/tmp/x","C:\\x","../x"]
        for raw in attacks:
            self.profiles["profiles"][0]["generated_outputs"]=[raw];self.save_profiles()
            with self.assertRaises(ValueError): self.execute(apply=True,isolated=True)
        outside=Path(self.temp.name).parent/"q32i-outside";outside.write_text("x")
        (self.repo/"escape").symlink_to(outside)
        self.profiles["profiles"][0]["generated_outputs"]=["escape"];self.save_profiles()
        with self.assertRaisesRegex(ValueError,"escapes"): self.execute(apply=True,isolated=True)
        outside.unlink()

    def test_c07_unregistered_output_write_blocked(self):
        self.profiles["profiles"][0]["producer_argv"]=[sys.executable,"-c","from pathlib import Path\nPath('rogue.txt').write_text('x')"] ;self.save_profiles()
        result=self.execute(apply=True,isolated=True);self.assertFalse(result["ok"]);self.assertEqual(result["records"][0]["return_code"],90);self.assertFalse((self.repo/"rogue.txt").exists())

    def test_c08_complete_execution_record(self):
        record=self.execute(apply=True,isolated=True)["records"][0]
        required={"component_id","argv","cwd","start_status","end_status","stdout","stderr","return_code","before_input_fingerprints","before_output_fingerprints","after_output_fingerprints","validator_result","cache_decision","rollback_status"}
        self.assertTrue(required <= set(record));self.assertEqual(record["end_status"],"success")

    def test_c09_legitimate_cache_hit_revalidates_freshness(self):
        self.assertFalse(self.execute(apply=True,isolated=True)["cache_hit"]);result=self.execute(apply=True,isolated=True)
        self.assertTrue(result["cache_hit"]);self.assertEqual(result["records"],[])

    def test_c10_cache_tampering_rejected(self):
        self.execute(apply=True,isolated=True);doc=json.loads((self.cache/"manifest.json").read_text());doc["records"]=[];(self.cache/"manifest.json").write_text(json.dumps(doc))
        self.assertFalse(self.execute(apply=True,isolated=True)["cache_hit"])

    def test_c11_profile_identity_mismatch_rejected(self):
        self.execute(apply=True,isolated=True);self.profiles["schema_version"]="2.0.0";self.save_profiles()
        self.assertFalse(self.execute(apply=True,isolated=True)["cache_hit"])

    def test_c12_registry_and_topology_mismatch_rejected(self):
        self.execute(apply=True,isolated=True)
        for path in [self.repo/"data/operations/project-components.json",self.repo/"data/operations/change-propagation-topology.json"]:
            path.write_text(path.read_text()+" \n");self.assertFalse(self.execute(apply=True,isolated=True)["cache_hit"])

    def test_c13_producer_and_validator_identity_mismatch_rejected(self):
        self.execute(apply=True,isolated=True)
        replacements={"producer_argv":[sys.executable,"-c","0"],"validator_argv":[sys.executable,"-c","print('validator-changed')"]}
        for field, argv in replacements.items():
            self.profiles["profiles"][0][field]=argv;self.save_profiles();self.assertFalse(self.execute(apply=True,isolated=True)["cache_hit"])

    def test_c14_stale_generated_output_is_not_cache_hit(self):
        self.execute(apply=True,isolated=True);(self.repo/"out1.txt").write_text("stale\n");result=self.execute(apply=True,isolated=True)
        self.assertFalse(result["cache_hit"]);self.assertEqual((self.repo/"out1.txt").read_text(),"after-one\n")

    def test_c15_manual_authored_boundary(self):
        result=self.execute(self.plan(["manual"]),True,True);self.assertEqual(result["records"][0]["end_status"],"manual-boundary");self.assertIsNone(result["records"][0]["return_code"])

    def test_c16_external_attestation_boundary(self):
        self.profiles["profiles"][3]["producer_argv"]=[sys.executable,"-c","from pathlib import Path\nPath('forged').write_text('x')"];self.save_profiles()
        result=self.execute(self.plan(["external"]),True,True);self.assertEqual(result["records"][0]["end_status"],"attestation-required");self.assertFalse((self.repo/"forged").exists())

    def test_c17_failure_stops_and_rolls_back(self):
        original=(self.repo/"out1.txt").read_bytes();result=self.execute(self.plan(["auto1","auto2","manual"]),True,True)
        self.assertFalse(result["ok"]);self.assertEqual(len(result["records"]),2);self.assertEqual((self.repo/"out1.txt").read_bytes(),original);self.assertEqual(result["records"][-1]["rollback_status"],"restored")

    def test_c18_failed_rollback_complete_recovery_package(self):
        self.profiles["profiles"][1]["rollback_policy"]="recovery_package_only";self.save_profiles();result=self.execute(self.plan(["auto1","auto2"]),True,True)
        package=Path(result["recovery_package"]);manifest=json.loads((package/"manifest.json").read_text())
        required={"plan_hash","component_identity","failed_action","original_fingerprints","current_fingerprints","sha256","restored_files","unrecovered_files","restore_steps","records","integrity_digest"}
        self.assertTrue(required <= set(manifest));self.assertTrue(manifest["unrecovered_files"]);self.assertTrue((package/"backups/out1.txt").is_file())


if __name__ == "__main__": unittest.main()
