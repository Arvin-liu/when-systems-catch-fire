#!/usr/bin/env python3
import json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VALIDATOR=ROOT/"tools/escalation/validate_graded_intervention_escalation_gate.py"; FIXTURES=ROOT/"data/escalation/fixtures"; PILOT=ROOT/"data/escalation/pilot-q43-i1.json"
Q42_HEAD="2f7777b26e1d52c5e6fff44fbf3d079cb38bdb98"
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
 def test_git_object_binding_is_enforced(self):
  # pilot already carries valid Git-object binding -> must pass
  self.assertEqual(run(PILOT).returncode,0)
  # corrupt sha256 -> must fail closed (EVIDENCE_BINDING_INVALID exit 4)
  b=json.loads(PILOT.read_text()); b["evidence_registry"][0]["sha256"]="sha256:"+"0"*64
  tmp=ROOT/"data/escalation/fixtures/_tmp_tamper_sha.json"; tmp.write_text(json.dumps(b,indent=2))
  try: self.assertEqual(run(tmp).returncode,4)
  finally: tmp.unlink()
  # corrupt blob_sha -> must fail closed (exit 4)
  b=json.loads(PILOT.read_text()); b["evidence_registry"][0]["blob_sha"]="0"*40
  tmp=ROOT/"data/escalation/fixtures/_tmp_tamper_blob.json"; tmp.write_text(json.dumps(b,indent=2))
  try: self.assertEqual(run(tmp).returncode,4)
  finally: tmp.unlink()
  # unresolvable commit_sha -> must fail closed (exit 4)
  b=json.loads(PILOT.read_text()); b["evidence_registry"][0]["commit_sha"]="0"*40
  tmp=ROOT/"data/escalation/fixtures/_tmp_tamper_commit.json"; tmp.write_text(json.dumps(b,indent=2))
  try: self.assertEqual(run(tmp).returncode,4)
  finally: tmp.unlink()
 def test_q42_predecessor_regression(self):
  # Q43 must bind to the Q42-I1 R4 frozen head, never to a stale/foreign head
  b=json.loads(PILOT.read_text())
  self.assertEqual(b["parent_binding"]["task_id"],"Q42-I1")
  self.assertEqual(b["parent_binding"]["exact_head"],Q42_HEAD)
  for e in b["evidence_registry"]:
   self.assertEqual(e.get("commit_sha"),Q42_HEAD)
   self.assertTrue(e.get("repository_relative_path"))
   self.assertTrue(re.fullmatch(r"[0-9a-f]{40}",e.get("blob_sha","")))
   self.assertTrue(e.get("sha256","").startswith("sha256:"))
  self.assertEqual(run(PILOT).returncode,0)
  # regression guard: a wrong predecessor head must be rejected (PARENT_BINDING_INVALID exit 3)
  b=json.loads(PILOT.read_text()); b["parent_binding"]["exact_head"]="0"*40
  tmp=ROOT/"data/escalation/fixtures/_tmp_wrong_parent.json"; tmp.write_text(json.dumps(b,indent=2))
  try: self.assertEqual(run(tmp).returncode,3)
  finally: tmp.unlink()
if __name__=="__main__": unittest.main()
