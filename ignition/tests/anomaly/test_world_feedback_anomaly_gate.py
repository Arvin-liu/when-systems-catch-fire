#!/usr/bin/env python3
import json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VALIDATOR=ROOT/"tools/anomaly/validate_world_feedback_anomaly_gate.py"; FIXTURES=ROOT/"data/anomaly/fixtures"; PILOT=ROOT/"data/anomaly/pilot-q41-i1.json"
def run(p): return subprocess.run([sys.executable,str(VALIDATOR),"--bundle",str(p)],capture_output=True,text=True)
class CapabilityGateTests(unittest.TestCase):
 def test_real_cli_matrix(self):
  paths=sorted(FIXTURES.glob("[0-9][0-9]-*.json")); self.assertEqual(len(paths),24)
  for p in paths:
   expected=int(re.search(r"-exit(\d+)\.json$",p.name).group(1)); r=run(p); self.assertEqual(r.returncode,expected,f"{p.name}: {r.stdout} {r.stderr}")
 def test_pilot_passes(self):
  r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
 def test_typed_record_coverage(self):
  b=json.loads(PILOT.read_text()); self.assertEqual({x["record_type"] for x in b["records"]},set(["RECURRING_REPOSITORY_DIVERGENCE", "SINGLE_DEVIATION_NEGATIVE_CONTROL"])); self.assertEqual(set(b["facts"]),set(["anomaly_not_hidden_system", "recurrence_required", "threshold_declared", "single_deviation_no_rebuild", "repair_budget_bounded", "authority_required", "stop_rollback_present", "failure_sampling_balanced", "q39_updated", "metacognition_updated"]))
 def test_every_field_is_evidence_bound(self):
  b=json.loads(PILOT.read_text());
  for rec in b["records"]:
   for field in ["world_feedback_anomaly", "recurrence_window", "residual_failure_aggregation", "expected_observed_divergence", "model_repair_budget", "governance_decision", "escalation_authority", "stop_rollback", "q39_update", "metacognition_update", "claim_ceiling"]: self.assertTrue(rec[field]["evidence_refs"])
 def test_git_object_binding_is_enforced(self):
  # correctly-bound pilot carries immutable Git-object references and passes
  r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
  b=json.loads(PILOT.read_text()); b["evidence_registry"][0]["sha256"]="sha256:"+"0"*64
  tmp=PILOT.with_suffix(".tmp-gitobj.json"); tmp.write_text(json.dumps(b))
  try:
   rt=run(tmp); self.assertEqual(rt.returncode,4,rt.stdout)
  finally: tmp.unlink()
 def test_scientific_metacognition_predecessor_regression(self):
  sm_pilot=ROOT/"data/metacognition/pilot-scientific-metacognition-i1.json"
  sm_validator=ROOT/"tools/metacognition/validate_epistemic_state_control_plane_gate.py"
  r=subprocess.run([sys.executable,str(sm_validator),"--bundle",str(sm_pilot)],capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stdout)
if __name__=="__main__": unittest.main()
