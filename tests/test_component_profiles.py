import json, subprocess, sys, unittest
from pathlib import Path
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
