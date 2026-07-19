import copy, json, subprocess, sys, unittest
from pathlib import Path
from tools.operations.generate_component_profiles import profile
ROOT=Path(__file__).resolve().parents[1]
def run(*args): return subprocess.run([sys.executable,*args],cwd=ROOT,text=True,capture_output=True)
class ComponentProfilesTest(unittest.TestCase):
    def test_profiles_are_current_and_valid(self):
        self.assertEqual(run("tools/operations/generate_component_profiles.py","--check").returncode, 0)
        self.assertEqual(run("tools/operations/validate_component_profiles.py").returncode, 0)
    def test_profiles_cover_registry_once(self):
        ids=[x["component_id"] for x in json.loads((ROOT/"data/operations/component-execution-profiles.json").read_text())["profiles"]]
        known=[x["component_id"] for x in json.loads((ROOT/"data/operations/project-components.json").read_text())["components"]]
        self.assertEqual(len(ids), len(set(ids))); self.assertEqual(set(ids), set(known))
    def test_generated_profiles_have_safe_structured_producers(self):
        for p in json.loads((ROOT/"data/operations/component-execution-profiles.json").read_text())["profiles"]:
            if p["execution_kind"] == "automatic": self.assertTrue(isinstance(p["producer_argv"],list) and p["producer_argv"])
    def test_generator_fail_closed_validator_contract(self):
        registry=json.loads((ROOT/"data/operations/project-components.json").read_text())
        base=json.loads((ROOT/"data/operations/component-execution-profile-policies.json").read_text())
        topology=json.loads((ROOT/"data/operations/change-propagation-topology.json").read_text())
        component=next(c for c in registry["components"] if c["component_id"]=="no_l7")
        cases=[(["python3","tools/validate_protocol_canonical.py","--check"],None),(["python3","tools/does_not_exist.py"],None),(["python3","-m","unittest"],None),(["python3","tools/validate_human_front_door.py","--invented"],None),(None,"manual_review")]
        for argv,validation in cases:
            policies=copy.deepcopy(base)
            if argv is not None: policies["component_policies"]["no_l7"]["validator_argv"]=argv
            if validation is not None: policies["component_policies"]["no_l7"]["validation_capability"]=validation
            with self.subTest(argv=argv,validation=validation), self.assertRaises(ValueError): profile(component,policies,topology)
    def test_manual_policy_cannot_smuggle_local_validator(self):
        registry=json.loads((ROOT/"data/operations/project-components.json").read_text());policies=json.loads((ROOT/"data/operations/component-execution-profile-policies.json").read_text());topology=json.loads((ROOT/"data/operations/change-propagation-topology.json").read_text())
        component=next(c for c in registry["components"] if c["component_id"]=="accepted_work")
        policies["component_policies"]["accepted_work"]={"validator_argv":["python3","tools/validate_human_front_door.py"]}
        with self.assertRaisesRegex(ValueError,"manual profile"): profile(component,policies,topology)
