#!/usr/bin/env python3
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from tools.governance.structured_capability_gate import run, result
from tools.governance.r3_capability_evaluators import evaluate_open_scientific_context_protocol, get_matrix
CONFIG=json.loads("{\"task_id\": \"SCIENTIFIC-CONTEXT-PROTOCOL-I1\", \"capability\": \"open_scientific_context_protocol\", \"parent_id\": \"Q44-I1\", \"parent_head\": \"7532b4b34cf841c09faab8c835c5fc7f896d30d8\", \"fields\": [\"protocol_version\", \"source_rights_context\", \"model_tool_executor_identity\", \"authority_capability\", \"observation_prediction\", \"analogy_search_case\", \"intervention_failure\", \"symbolic_perspectives\", \"decision_integrity\", \"epistemic_state\", \"latent_multi_history_counterfactual\", \"experiment_hardware_request_result\", \"exact_head_provenance_digest\", \"stop_rollback\", \"sensitive_data_network_local_first\", \"capability_negotiation\", \"request_response_envelope\", \"identity_authorization\", \"artifact_binding\", \"failure_retry_semantics\", \"compatibility_policy\", \"local_mock_adapter\", \"claim_ceiling\"], \"rules\": [\"version_negotiated\", \"identity_authorized\", \"capability_not_authority\", \"artifact_exact_head_bound\", \"rights_preserved\", \"failure_retry_typed\", \"compatibility_fail_closed\", \"sensitive_local_first\", \"hardware_request_only\", \"no_ecosystem_overclaim\", \"stop_rollback_present\"], \"schema\": \"schemas/context_protocol/open_scientific_context_protocol-contract.schema.json\", \"forbidden_claims\": [\"no deployed ecosystem\", \"no hardware execution\", \"no platform model copying\", \"no sensitive-data/network boundary bypass\", \"universal truth\", \"causal proof established\", \"ecosystem deployed\"]}")
CONFIG["evaluator"] = evaluate_open_scientific_context_protocol
CONFIG["evidence_matrix"] = get_matrix("open_scientific_context_protocol")

def _git(args):
    try:
        return subprocess.run(["git","-C",str(ROOT)]+args, capture_output=True, text=True).stdout.strip()
    except Exception:
        return None

def _git_bytes(args):
    try:
        return subprocess.run(["git","-C",str(ROOT)]+args, capture_output=True).stdout or b""
    except Exception:
        return b""

def reference_integrity_check(bundle_path):
    """Fail-closed check that every evidence object carrying the six reference
    fields actually resolves to a real Git object. Real bundles carry the fields;
    minimal negative fixtures omit them and are skipped (the shared gate still
    enforces their digest/head format)."""
    try:
        b=json.loads(Path(bundle_path).read_text())
    except Exception as exc:
        return f"bundle unreadable: {exc}"
    for e in (b.get("evidence_registry") or []):
        eid=e.get("evidence_id")
        ref=e.get("repository_relative_path"); csha=e.get("commit_sha")
        bsha=e.get("blob_sha"); dsha=e.get("sha256")
        if not (ref and csha and bsha and dsha):
            continue  # minimal fixture without reference fields: skip
        if not (isinstance(csha,str) and len(csha)==40 and all(ch in "0123456789abcdef" for ch in csha)):
            return f"{eid}: commit_sha not a 40-hex resolvable reference"
        if e.get("artifact") and e["artifact"]!=ref:
            return f"{eid}: repository_relative_path ({ref}) != artifact ({e['artifact']})"
        actual_blob=_git(["rev-parse", f"{csha}:{ref}"])
        if actual_blob!=bsha:
            return f"{eid}: blob_sha ({bsha}) does not match real Git object {csha}:{ref} ({actual_blob})"
        content=_git_bytes(["show", f"{csha}:{ref}"])
        if not content:
            return f"{eid}: cannot read real Git object {csha}:{ref}"
        actual_sha="sha256:"+hashlib.sha256(content).hexdigest()
        if actual_sha!=dsha:
            return f"{eid}: sha256 ({dsha}) does not match recomputed digest of real Git object {csha}:{ref}"
    return None

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--bundle",required=True); a=ap.parse_args()
    err=reference_integrity_check(a.bundle)
    if err:
        print(json.dumps(result(CONFIG["capability"],4,"EVIDENCE_BINDING_INVALID",[err]),sort_keys=True)); sys.exit(4)
    sys.exit(run(CONFIG))
