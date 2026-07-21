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
if __name__=="__main__": unittest.main()
