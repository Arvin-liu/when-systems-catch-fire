#!/usr/bin/env python3
import json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VALIDATOR=ROOT/"tools/symbolic/validate_symbolic_power_perspective_gate.py"; FIXTURES=ROOT/"data/symbolic/fixtures"; PILOT=ROOT/"data/symbolic/pilot-symbolic-sphere-i1.json"
def run(p): return subprocess.run([sys.executable,str(VALIDATOR),"--bundle",str(p)],capture_output=True,text=True)
class CapabilityGateTests(unittest.TestCase):
 def test_real_cli_matrix(self):
  paths=sorted(FIXTURES.glob("[0-9][0-9]-*.json")); self.assertEqual(len(paths),24)
  for p in paths:
   expected=int(re.search(r"-exit(\d+)\.json$",p.name).group(1)); r=run(p); self.assertEqual(r.returncode,expected,f"{p.name}: {r.stdout} {r.stderr}")
 def test_pilot_passes(self):
  r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
 def test_typed_record_coverage(self):
  b=json.loads(PILOT.read_text()); self.assertEqual({x["record_type"] for x in b["records"]},set(["COMMUNITY_FOOTBALL_FIELD", "SCHOOL_DATA_POLICY"])); self.assertEqual(set(b["facts"]),set(["material_truth_separate", "ownership_not_truth", "popularity_not_truth", "institution_not_fact", "all_actors_present", "costs_visible", "intent_effect_separate", "interpretive_power_not_legitimacy", "no_causal_totalization", "history_append_only", "evidence_constrained", "claim_ceiling_preserved"]))
 def test_every_field_is_evidence_bound(self):
  b=json.loads(PILOT.read_text());
  for rec in b["records"]:
   for field in ["symbolic_object", "material_fact_base", "actor_positions", "power_forms", "meaning_projections", "intended_use", "actual_use", "front_face", "suppressed_faces", "benefit_cost_distribution", "counter_readings", "institutionalization_mechanism", "symbolic_capture", "counter_appropriation", "transformation_history", "evidence_constraints", "claim_ceiling"]: self.assertTrue(rec[field]["evidence_refs"])
if __name__=="__main__": unittest.main()
