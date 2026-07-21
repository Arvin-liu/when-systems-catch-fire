#!/usr/bin/env python3
import json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VALIDATOR=ROOT/"tools/counterfactual/validate_counterfactual_unrealized_path_gate.py"; FIXTURES=ROOT/"data/counterfactual/fixtures"; PILOT=ROOT/"data/counterfactual/pilot-q42-i1.json"
def run(p): return subprocess.run([sys.executable,str(VALIDATOR),"--bundle",str(p)],capture_output=True,text=True)
class CapabilityGateTests(unittest.TestCase):
 def test_real_cli_matrix(self):
  paths=sorted(FIXTURES.glob("[0-9][0-9]-*.json")); self.assertEqual(len(paths),24)
  for p in paths:
   expected=int(re.search(r"-exit(\d+)\.json$",p.name).group(1)); r=run(p); self.assertEqual(r.returncode,expected,f"{p.name}: {r.stdout} {r.stderr}")
 def test_pilot_passes(self):
  r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
 def test_typed_record_coverage(self):
  b=json.loads(PILOT.read_text()); self.assertEqual({x["record_type"] for x in b["records"]},set(["IDENTIFIABLE_COUNTERFACTUAL", "SPECULATIVE_UNREALIZED_PATH"])); self.assertEqual(set(b["facts"]),set(["types_separated", "identifiability_gate_required", "unobservable_not_promoted", "evidence_required", "intervention_difference_explicit", "speculation_labeled", "no_if_then_causal_upgrade", "claim_ceiling_preserved"]))
 def test_every_field_is_evidence_bound(self):
  b=json.loads(PILOT.read_text());
  for rec in b["records"]:
   for field in ["counterfactuals", "alternative_decompositions", "unrealized_paths", "speculative_narratives", "intervention_differences", "identifiability_status", "observable_portion", "unobservable_portion", "evidence", "claim_ceiling"]: self.assertTrue(rec[field]["evidence_refs"])
if __name__=="__main__": unittest.main()
