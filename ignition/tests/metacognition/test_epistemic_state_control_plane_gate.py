#!/usr/bin/env python3
import json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VALIDATOR=ROOT/"tools/metacognition/validate_epistemic_state_control_plane_gate.py"; FIXTURES=ROOT/"data/metacognition/fixtures"; PILOT=ROOT/"data/metacognition/pilot-scientific-metacognition-i1.json"
def run(p): return subprocess.run([sys.executable,str(VALIDATOR),"--bundle",str(p)],capture_output=True,text=True)
class CapabilityGateTests(unittest.TestCase):
 def test_real_cli_matrix(self):
  paths=sorted(FIXTURES.glob("[0-9][0-9]-*.json")); self.assertEqual(len(paths),24)
  for p in paths:
   expected=int(re.search(r"-exit(\d+)\.json$",p.name).group(1)); r=run(p); self.assertEqual(r.returncode,expected,f"{p.name}: {r.stdout} {r.stderr}")
 def test_pilot_passes(self):
  r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
 def test_typed_record_coverage(self):
  b=json.loads(PILOT.read_text()); self.assertEqual({x["record_type"] for x in b["records"]},set(["REAL_TRAIN_UNKNOWN_LEDGER", "NON_IDENTIFIABLE_UNKNOWN"])); self.assertEqual(set(b["facts"]),set(["self_rating_not_evidence", "unknown_needs_evidence_transition", "non_identifiable_not_solved", "dominant_view_not_fact", "good_outcome_not_bad_process_erasure", "failure_changes_plan", "retracted_not_active", "plan_authorized_and_stopped", "exploration_bounded", "cost_risk_present", "ceiling_noninflation", "no_circular_evidence"]))
 def test_every_field_is_evidence_bound(self):
  b=json.loads(PILOT.read_text());
  for rec in b["records"]:
   for field in ["epistemic_state_ledger", "committed_knowledge", "candidate_hypotheses", "conflicts", "retracted_states", "insufficient_evidence", "not_searched", "temporarily_unobservable", "structurally_unobservable", "non_identifiable", "known_unknowns", "unknown_acquisition_paths", "visibility_bias", "decision_integrity_risk", "unresolved_failures", "cost_risk_time_priority", "stop_condition", "evidence_requirement", "next_action_type", "voi_like_ranking", "authorized_acquisition_plan", "feedback_transition", "replanning", "claim_ceiling"]: self.assertTrue(rec[field]["evidence_refs"])
 def test_git_object_binding_is_enforced(self):
  # R1 fail-closed: a tampered sha256 must be rejected (EVIDENCE_BINDING_INVALID, exit 4)
  import copy as _c
  b=_c.deepcopy(json.loads(PILOT.read_text())); b["evidence_registry"][0]["sha256"]="sha256:"+"0"*64
  tmp=ROOT/"data/metacognition/fixtures/_tamper_sha256_tmp.json"; tmp.write_text(json.dumps(b))
  try:
   r=run(tmp); self.assertEqual(r.returncode,4,r.stdout)
  finally:
   tmp.unlink(missing_ok=True)
 def test_decision_integrity_predecessor_regression(self):
  # predecessor item must remain unaffected by the shared validator's opt-in Git-object check
  DI_VALIDATOR=ROOT/"tools/decision/validate_decision_integrity_gate.py"
  DI_PILOT=ROOT/"data/decision/pilot-decision-integrity-i1.json"
  DI_FIX=ROOT/"data/decision/fixtures"
  def di_run(p): return subprocess.run([sys.executable,str(DI_VALIDATOR),"--bundle",str(p)],capture_output=True,text=True)
  r=di_run(DI_PILOT); self.assertEqual(r.returncode,0,r.stdout)
  # predecessor evidence was also rebound to immutable Git objects (shared opt-in check active)
  di_b=json.loads(DI_PILOT.read_text())
  for e in di_b["evidence_registry"]:
   self.assertIn("commit_sha",e); self.assertIn("blob_sha",e); self.assertIn("sha256",e)
  # full predecessor fixture matrix must still pass unchanged
  for p in sorted(DI_FIX.glob("[0-9][0-9]-*.json")):
   exp=int(re.search(r"-exit(\d+)\.json$",p.name).group(1)); rr=di_run(p)
   self.assertEqual(rr.returncode,exp,f"DI regression {p.name}: {rr.stdout} {rr.stderr}")
if __name__=="__main__": unittest.main()
