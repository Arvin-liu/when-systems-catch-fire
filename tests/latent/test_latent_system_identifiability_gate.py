#!/usr/bin/env python3
import json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VALIDATOR=ROOT/"tools/latent/validate_latent_system_identifiability_gate.py"; FIXTURES=ROOT/"data/latent/fixtures"; PILOT=ROOT/"data/latent/pilot-f15-d1-i1.json"
def run(p): return subprocess.run([sys.executable,str(VALIDATOR),"--bundle",str(p)],capture_output=True,text=True)
class CapabilityGateTests(unittest.TestCase):
 def test_real_cli_matrix(self):
  paths=sorted(FIXTURES.glob("[0-9][0-9]-*.json")); self.assertEqual(len(paths),24)
  for p in paths:
   expected=int(re.search(r"-exit(\d+)\.json$",p.name).group(1)); r=run(p); self.assertEqual(r.returncode,expected,f"{p.name}: {r.stdout} {r.stderr}")
 def test_pilot_passes(self):
  r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
 def test_typed_record_coverage(self):
  b=json.loads(PILOT.read_text()); self.assertEqual({x["record_type"] for x in b["records"]},set(["IDENTIFIABLE_CANDIDATE", "NON_IDENTIFIABLE_EQUIVALENCE_SET"])); self.assertEqual(set(b["facts"]),set(["residual_not_entity", "pattern_not_common_cause", "equivalent_decompositions_preserved", "distinguishing_evidence_required", "non_identifiable_stays_unresolved", "contradictions_preserved", "unsupported_not_promoted", "claim_ceiling_preserved"]))
 def test_every_field_is_evidence_bound(self):
  b=json.loads(PILOT.read_text());
  for rec in b["records"]:
   for field in ["latent_system_candidate", "cross_system_ancestor_graph", "missing_system_search_plan", "identifiability_gate", "observational_signature", "equivalent_decompositions", "distinguishing_evidence_request", "candidate_status", "contradictions", "unsupported_elements", "claim_ceiling"]: self.assertTrue(rec[field]["evidence_refs"])
if __name__=="__main__": unittest.main()
