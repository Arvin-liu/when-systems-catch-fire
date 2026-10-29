#!/usr/bin/env python3
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from tools.governance.structured_capability_gate import run, result
from tools.governance.r3_capability_evaluators import evaluate_latent_system_identifiability, get_matrix
CONFIG=json.loads("{\"task_id\": \"F15-D1-I1\", \"capability\": \"latent_system_identifiability\", \"parent_id\": \"Q41-I1\", \"parent_head\": \"e92e7d3eadbb67da288077052f635e3c052bd3a1\", \"fields\": [\"latent_system_candidate\", \"cross_system_ancestor_graph\", \"missing_system_search_plan\", \"identifiability_gate\", \"observational_signature\", \"equivalent_decompositions\", \"distinguishing_evidence_request\", \"candidate_status\", \"contradictions\", \"unsupported_elements\", \"claim_ceiling\"], \"rules\": [\"residual_not_entity\", \"pattern_not_common_cause\", \"equivalent_decompositions_preserved\", \"distinguishing_evidence_required\", \"non_identifiable_stays_unresolved\", \"contradictions_preserved\", \"unsupported_not_promoted\", \"claim_ceiling_preserved\"], \"schema\": \"schemas/latent/latent_system_identifiability-contract.schema.json\", \"forbidden_claims\": [\"residual is not a latent entity\", \"shared pattern is not a common cause\", \"non-identifiable decomposition remains unresolved\", \"no Q45+ numbering\", \"universal truth\", \"causal proof established\", \"ecosystem deployed\"]}")
CONFIG["evaluator"] = evaluate_latent_system_identifiability
CONFIG["evidence_matrix"] = get_matrix("latent_system_identifiability")

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
