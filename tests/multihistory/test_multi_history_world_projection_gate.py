#!/usr/bin/env python3
import json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VALIDATOR=ROOT/"tools/multihistory/validate_multi_history_world_projection_gate.py"; FIXTURES=ROOT/"data/multihistory/fixtures"; PILOT=ROOT/"data/multihistory/pilot-d2-i1.json"
def run(p): return subprocess.run([sys.executable,str(VALIDATOR),"--bundle",str(p)],capture_output=True,text=True)
class CapabilityGateTests(unittest.TestCase):
 def test_real_cli_matrix(self):
  paths=sorted(FIXTURES.glob("[0-9][0-9]-*.json")); self.assertEqual(len(paths),24)
  for p in paths:
   expected=int(re.search(r"-exit(\d+)\.json$",p.name).group(1)); r=run(p); self.assertEqual(r.returncode,expected,f"{p.name}: {r.stdout} {r.stderr}")
 def test_pilot_passes(self):
  r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
 def test_typed_record_coverage(self):
  b=json.loads(PILOT.read_text()); self.assertEqual({x["record_type"] for x in b["records"]},set(["TWO_WORLD_EQUIVALENCE_SET", "WEIGHTED_WORLD_WITH_JUSTIFICATION"])); self.assertEqual(set(b["facts"]),set(["every_world_evidence_bound", "no_forced_unique_story", "indistinguishable_not_ranked_fact", "weights_need_justification", "possibility_not_probability", "falsifier_required", "unresolved_paths_preserved", "narrative_ceiling_preserved"]))
 def test_every_field_is_evidence_bound(self):
  b=json.loads(PILOT.read_text());
  for rec in b["records"]:
   for field in ["world_candidates", "divergence_point", "shared_evidence", "branch_specific_assumptions", "indistinguishable_set", "falsifiers", "justified_weights", "unresolved_paths", "narrative_ceiling", "claim_ceiling"]: self.assertTrue(rec[field]["evidence_refs"])
 def test_git_object_binding_is_enforced(self):
  import tempfile,os
  b=json.loads(PILOT.read_text()); ev=b["evidence_registry"][0]
  ev["sha256"]=ev["sha256"][:-1]+("a" if ev["sha256"][-1]!="a" else "b")
  tf=tempfile.NamedTemporaryFile("w",suffix=".json",delete=False); json.dump(b,tf); tf.close()
  r=run(tf.name); os.unlink(tf.name)
  self.assertEqual(r.returncode,4,f"tampered sha256 must fail closed (EVIDENCE_BINDING_INVALID): {r.stdout}")
 def test_f15_d1_predecessor_regression(self):
  f15val=ROOT/"tools/latent/validate_latent_system_identifiability_gate.py"
  f15pilot=ROOT/"data/latent/pilot-f15-d1-i1.json"
  r=subprocess.run([sys.executable,str(f15val),"--bundle",str(f15pilot)],capture_output=True,text=True)
  self.assertEqual(r.returncode,0,f"F15-D1 pilot through F15-D1 validator must pass (shared opt-in Git-object check is non-regressive): {r.stdout} {r.stderr}")
if __name__=="__main__": unittest.main()
