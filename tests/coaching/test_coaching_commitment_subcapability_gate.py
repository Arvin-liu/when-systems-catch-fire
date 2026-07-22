#!/usr/bin/env python3
import json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VALIDATOR=ROOT/"tools/coaching/validate_coaching_commitment_subcapability_gate.py"; FIXTURES=ROOT/"data/coaching/fixtures"; PILOT=ROOT/"data/coaching/pilot-q44-i1.json"
def run(p): return subprocess.run([sys.executable,str(VALIDATOR),"--bundle",str(p)],capture_output=True,text=True)
class CapabilityGateTests(unittest.TestCase):
 def test_real_cli_matrix(self):
  paths=sorted(FIXTURES.glob("[0-9][0-9]-*.json")); self.assertEqual(len(paths),24)
  for p in paths:
   expected=int(re.search(r"-exit(\d+)\.json$",p.name).group(1)); r=run(p); self.assertEqual(r.returncode,expected,f"{p.name}: {r.stdout} {r.stderr}")
 def test_pilot_passes(self):
  r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
 def test_typed_record_coverage(self):
  b=json.loads(PILOT.read_text()); self.assertEqual({x["record_type"] for x in b["records"]},set(["USER_LED_COMMITMENT", "PAUSE_OR_REVISE_PATH"])); self.assertEqual(set(b["facts"]),set(["goal_user_declared", "commitment_informed", "consent_reversible", "no_goal_substitution", "no_shame_pressure", "multiple_narratives_preserved", "process_outcome_separate", "support_not_control", "escalation_boundary_enforced"]))
 def test_every_field_is_evidence_bound(self):
  b=json.loads(PILOT.read_text());
  for rec in b["records"]:
   for field in ["user_declared_goal", "informed_commitment", "plan_checkpoints", "deviations", "support_options", "revise_pause_stop", "non_manipulation_constraint", "multi_perspective_narrative", "autonomy_consent", "outcome_process_separation", "escalation", "claim_ceiling"]: self.assertTrue(rec[field]["evidence_refs"])
 def test_git_object_binding_is_enforced(self):
  import copy as _copy
  import tempfile as _tf
  base=json.loads(PILOT.read_text())
  cases=[]
  t1=_copy.deepcopy(base); b0=t1["evidence_registry"][0]["blob_sha"]; t1["evidence_registry"][0]["blob_sha"]=b0[:-1]+("0" if b0[-1]!="0" else "1"); cases.append(t1)
  t2=_copy.deepcopy(base); t2["evidence_registry"][1]["sha256"]="sha256:"+"0"*64; cases.append(t2)
  t3=_copy.deepcopy(base); t3["evidence_registry"][2]["commit_sha"]="0"*40; cases.append(t3)
  for i,c in enumerate(cases):
   p=Path(_tf.mkdtemp())/("tamper%d.json"%i); p.write_text(json.dumps(c))
   self.assertEqual(run(p).returncode,4,f"tamper case {i}: {run(p).stdout}")
 def test_q43_predecessor_regression(self):
  import copy as _copy
  import tempfile as _tf
  base=json.loads(PILOT.read_text())
  wrong=_copy.deepcopy(base); wrong["parent_binding"]["exact_head"]="3756cd6453135a333771243ffa6eb3d4f86344a0"
  p=Path(_tf.mkdtemp())/"wrong_parent.json"; p.write_text(json.dumps(wrong))
  self.assertEqual(run(p).returncode,3,f"predecessor regression: {run(p).stdout}")
if __name__=="__main__": unittest.main()
