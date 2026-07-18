import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.operations.plan_incremental_execution import plan
class PlannerTest(unittest.TestCase):
 def test_readme_is_limited_and_complete(self):
  p=plan({'changed_paths':['README.md']});self.assertFalse(p['full_rebuild_reasons']);self.assertEqual(len(p['component_decisions']),len(json.loads((ROOT/'data/operations/project-components.json').read_text())['components']));self.assertIn('readme',p['q32_affected_component_closure']);self.assertTrue(any(x['decision']=='NO_CHANGE_WITH_PROOF' and x['non_impact_proof'] for x in p['component_decisions']))
 def test_registry_requires_full_rebuild(self):
  p=plan({'changed_paths':['data/operations/project-components.json']});self.assertTrue(p['full_rebuild_reasons']);self.assertTrue(all(x['decision']=='FULL_REBUILD_REQUIRED' for x in p['component_decisions']))
 def test_unknown_path_fails_closed(self):
  p=plan({'changed_paths':['unknown/file.md']});self.assertTrue(p['unresolved_residue'])
