#!/usr/bin/env python3
import json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VALIDATOR=ROOT/"tools/decision/validate_decision_integrity_gate.py"; FIXTURES=ROOT/"data/decision/fixtures"; PILOT=ROOT/"data/decision/pilot-decision-integrity-i1.json"
def run(p): return subprocess.run([sys.executable,str(VALIDATOR),"--bundle",str(p)],capture_output=True,text=True)
class CapabilityGateTests(unittest.TestCase):
 def test_real_cli_matrix(self):
  paths=sorted(FIXTURES.glob("[0-9][0-9]-*.json")); self.assertEqual(len(paths),24)
  for p in paths:
   expected=int(re.search(r"-exit(\d+)\.json$",p.name).group(1)); r=run(p); self.assertEqual(r.returncode,expected,f"{p.name}: {r.stdout} {r.stderr}")
 def test_pilot_passes(self):
  r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
 def test_typed_record_coverage(self):
  b=json.loads(PILOT.read_text()); self.assertEqual({x["record_type"] for x in b["records"]},set(["BAD_PROCESS_GOOD_OUTCOME", "GOOD_PROCESS_BAD_OUTCOME"])); self.assertEqual(set(b["facts"]),set(["success_not_process_proof", "failure_not_process_disproof", "ex_ante_record_immutable", "principle_relabel_blocked", "competence_required", "utility_before_bargain", "fomo_not_need", "intake_not_integration", "integration_requires_output", "revision_versioned_authorized", "original_record_preserved", "claim_ceiling_preserved"]))
 def test_every_field_is_evidence_bound(self):
  b=json.loads(PILOT.read_text());
  for rec in b["records"]:
   for field in ["principle_registry", "principle_version", "revision_authority", "ex_ante_decision_record", "known_unknown_assumptions", "decision_hierarchy", "competence_boundary", "risk_reversibility_stop", "process_quality", "outcome_quality", "process_outcome_quadrant", "result_bias_audit", "post_hoc_narrative_diff", "principle_capture", "legitimate_revision", "usefulness_necessity_gate", "bargain_fomo_signal", "information_intake", "integration_evidence", "learning_update", "claim_ceiling"]: self.assertTrue(rec[field]["evidence_refs"])
if __name__=="__main__": unittest.main()
