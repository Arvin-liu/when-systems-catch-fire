#!/usr/bin/env python3
import json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VALIDATOR=ROOT/"tools/counterfactual/validate_counterfactual_unrealized_path_gate.py"; FIXTURES=ROOT/"data/counterfactual/fixtures"; PILOT=ROOT/"data/counterfactual/pilot-q42-i1.json"
D2_HEAD="1904628103d8c23133107d501a22e3f17d08221d"
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
 def test_git_object_binding_is_enforced(self):
  # pilot already carries valid Git-object binding -> must pass
  self.assertEqual(run(PILOT).returncode,0)
  # corrupt sha256 -> must fail closed (EVIDENCE_BINDING_INVALID exit 4)
  b=json.loads(PILOT.read_text()); b["evidence_registry"][0]["sha256"]="sha256:"+"0"*64
  tmp=ROOT/"data/counterfactual/fixtures/_tmp_tamper_sha.json"; tmp.write_text(json.dumps(b,indent=2))
  try: self.assertEqual(run(tmp).returncode,4)
  finally: tmp.unlink()
  # corrupt blob_sha -> must fail closed (exit 4)
  b=json.loads(PILOT.read_text()); b["evidence_registry"][0]["blob_sha"]="0"*40
  tmp=ROOT/"data/counterfactual/fixtures/_tmp_tamper_blob.json"; tmp.write_text(json.dumps(b,indent=2))
  try: self.assertEqual(run(tmp).returncode,4)
  finally: tmp.unlink()
  # unresolvable commit_sha -> must fail closed (exit 4)
  b=json.loads(PILOT.read_text()); b["evidence_registry"][0]["commit_sha"]="0"*40
  tmp=ROOT/"data/counterfactual/fixtures/_tmp_tamper_commit.json"; tmp.write_text(json.dumps(b,indent=2))
  try: self.assertEqual(run(tmp).returncode,4)
  finally: tmp.unlink()
 def test_d2_predecessor_regression(self):
  # Q42 must bind to the D2-I1 R4 frozen head, never to a stale/foreign head
  b=json.loads(PILOT.read_text())
  self.assertEqual(b["parent_binding"]["task_id"],"D2-I1")
  self.assertEqual(b["parent_binding"]["exact_head"],D2_HEAD)
  for e in b["evidence_registry"]:
   self.assertEqual(e.get("commit_sha"),D2_HEAD)
   self.assertTrue(e.get("repository_relative_path"))
   self.assertTrue(re.fullmatch(r"[0-9a-f]{40}",e.get("blob_sha","")))
   self.assertTrue(e.get("sha256","").startswith("sha256:"))
  self.assertEqual(run(PILOT).returncode,0)
  # regression guard: a wrong predecessor head must be rejected (PARENT_BINDING_INVALID exit 3)
  b=json.loads(PILOT.read_text()); b["parent_binding"]["exact_head"]="0"*40
  tmp=ROOT/"data/counterfactual/fixtures/_tmp_wrong_parent.json"; tmp.write_text(json.dumps(b,indent=2))
  try: self.assertEqual(run(tmp).returncode,3)
  finally: tmp.unlink()
if __name__=="__main__": unittest.main()
