#!/usr/bin/env python3
import json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VALIDATOR=ROOT/"tools/context_protocol/validate_open_scientific_context_protocol_gate.py"; FIXTURES=ROOT/"data/context_protocol/fixtures"; PILOT=ROOT/"data/context_protocol/pilot-scientific-context-protocol-i1.json"
def run(p): return subprocess.run([sys.executable,str(VALIDATOR),"--bundle",str(p)],capture_output=True,text=True)
class CapabilityGateTests(unittest.TestCase):
 def test_real_cli_matrix(self):
  paths=sorted(FIXTURES.glob("[0-9][0-9]-*.json")); self.assertEqual(len(paths),24)
  for p in paths:
   expected=int(re.search(r"-exit(\d+)\.json$",p.name).group(1)); r=run(p); self.assertEqual(r.returncode,expected,f"{p.name}: {r.stdout} {r.stderr}")
 def test_pilot_passes(self):
  r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
 def test_typed_record_coverage(self):
  b=json.loads(PILOT.read_text()); self.assertEqual({x["record_type"] for x in b["records"]},set(["LOCAL_MOCK_REQUEST", "LOCAL_MOCK_RESPONSE"])); self.assertEqual(set(b["facts"]),set(["version_negotiated", "identity_authorized", "capability_not_authority", "artifact_exact_head_bound", "rights_preserved", "failure_retry_typed", "compatibility_fail_closed", "sensitive_local_first", "hardware_request_only", "no_ecosystem_overclaim", "stop_rollback_present"]))
 def test_every_field_is_evidence_bound(self):
  b=json.loads(PILOT.read_text());
  for rec in b["records"]:
   for field in ["protocol_version", "source_rights_context", "model_tool_executor_identity", "authority_capability", "observation_prediction", "analogy_search_case", "intervention_failure", "symbolic_perspectives", "decision_integrity", "epistemic_state", "latent_multi_history_counterfactual", "experiment_hardware_request_result", "exact_head_provenance_digest", "stop_rollback", "sensitive_data_network_local_first", "capability_negotiation", "request_response_envelope", "identity_authorization", "artifact_binding", "failure_retry_semantics", "compatibility_policy", "local_mock_adapter", "claim_ceiling"]: self.assertTrue(rec[field]["evidence_refs"])
 def test_git_object_binding_is_enforced(self):
  import tempfile,os
  b=json.loads(PILOT.read_text())
  r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
  fn=tempfile.mktemp(suffix=".json")
  t=json.loads(PILOT.read_text()); t["evidence_registry"][0]["blob_sha"]="0"*40
  json.dump(t,open(fn,"w")); r=run(fn); self.assertEqual(r.returncode,4,r.stdout)
  t=json.loads(PILOT.read_text()); t["evidence_registry"][1]["sha256"]="sha256:"+"0"*64
  json.dump(t,open(fn,"w")); r=run(fn); self.assertEqual(r.returncode,4,r.stdout)
  t=json.loads(PILOT.read_text()); t["evidence_registry"][2]["commit_sha"]="0"*40
  json.dump(t,open(fn,"w")); r=run(fn); self.assertEqual(r.returncode,4,r.stdout)
  os.remove(fn)
 def test_q44_predecessor_regression(self):
  import tempfile,os
  t=json.loads(PILOT.read_text())
  t["parent_binding"]["exact_head"]="e603e4503b424cea7c85639ec83f96b7e1bc7efb"
  fn=tempfile.mktemp(suffix=".json"); json.dump(t,open(fn,"w")); r=run(fn); self.assertEqual(r.returncode,3,r.stdout)
  os.remove(fn)
if __name__=="__main__": unittest.main()
