#!/usr/bin/env python3
import json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VALIDATOR=ROOT/"tools/escalation/validate_graded_intervention_escalation_gate.py"; FIXTURES=ROOT/"data/escalation/fixtures"; PILOT=ROOT/"data/escalation/pilot-q43-i1.json"
def run(p): return subprocess.run([sys.executable,str(VALIDATOR),"--bundle",str(p)],capture_output=True,text=True)
class CapabilityGateTests(unittest.TestCase):
 def test_real_cli_matrix(self):
  paths=sorted(FIXTURES.glob("[0-9][0-9]-*.json")); self.assertEqual(len(paths),24)
  for p in paths:
   expected=int(re.search(r"-exit(\d+)\.json$",p.name).group(1)); r=run(p); self.assertEqual(r.returncode,expected,f"{p.name}: {r.stdout} {r.stderr}")
 def test_pilot_passes(self):
  r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
 def test_typed_record_coverage(self):
  b=json.loads(PILOT.read_text()); self.assertEqual({x["record_type"] for x in b["records"]},set(["REPOSITORY_LOCAL_REVERSIBLE", "HIGH_RISK_REQUEST_ONLY"])); self.assertEqual(set(b["facts"]),set(["risk_class_required", "reversibility_required", "evidence_grade_required", "authority_required", "expertise_boundary_enforced", "automatic_only_repository_local", "confirmation_for_external", "high_risk_request_only", "prohibited_never_executed", "stop_rollback_return_present"]))
 def test_every_field_is_evidence_bound(self):
  b=json.loads(PILOT.read_text());
  for rec in b["records"]:
   for field in ["action_risk_class", "reversibility", "evidence_grade", "authority", "expertise_requirement", "automatic_repository_local_action", "user_confirmation_required", "expert_escalation", "institutional_approval", "prohibited_action", "request_only_external_action", "stop_rollback_result_return", "claim_ceiling"]: self.assertTrue(rec[field]["evidence_refs"])
if __name__=="__main__": unittest.main()
