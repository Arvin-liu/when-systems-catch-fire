#!/usr/bin/env python3
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from tools.governance.build_structured_capability_fixtures import build, dump
CONFIG=json.loads("{\"task_id\": \"SCIENTIFIC-CONTEXT-PROTOCOL-I1\", \"task_slug\": \"scientific-context-protocol-i1\", \"slug\": \"context_protocol\", \"capability\": \"open_scientific_context_protocol\", \"title\": \"Open Scientific Context Protocol\", \"branch\": \"repair/scientific-context-protocol-r1-context-capability-binding\", \"tag\": \"archive/scientific-context-protocol-repair-r1-frozen-head\", \"marker\": \"SCIENTIFIC_CONTEXT_PROTOCOL_I1_OPEN_RESEARCH_CONTEXT_CHECKPOINT_FROZEN\", \"parent_task\": \"Q44-I1\", \"parent_id\": \"Q44-I1\", \"parent_branch\": \"repair/q44-r1-coaching-consent-binding\", \"parent_pr\": 97, \"conclusion\": \"A minimal versioned local protocol can negotiate capabilities and exchange identity-, authority-, artifact-, failure-, retry- and boundary-bound scientific context without copying a platform or executing hardware actions.\", \"nonclaims\": [\"no deployed ecosystem\", \"no hardware execution\", \"no platform model copying\", \"no sensitive-data/network boundary bypass\"], \"fields\": [\"protocol_version\", \"source_rights_context\", \"model_tool_executor_identity\", \"authority_capability\", \"observation_prediction\", \"analogy_search_case\", \"intervention_failure\", \"symbolic_perspectives\", \"decision_integrity\", \"epistemic_state\", \"latent_multi_history_counterfactual\", \"experiment_hardware_request_result\", \"exact_head_provenance_digest\", \"stop_rollback\", \"sensitive_data_network_local_first\", \"capability_negotiation\", \"request_response_envelope\", \"identity_authorization\", \"artifact_binding\", \"failure_retry_semantics\", \"compatibility_policy\", \"local_mock_adapter\", \"claim_ceiling\"], \"rules\": [\"version_negotiated\", \"identity_authorized\", \"capability_not_authority\", \"artifact_exact_head_bound\", \"rights_preserved\", \"failure_retry_typed\", \"compatibility_fail_closed\", \"sensitive_local_first\", \"hardware_request_only\", \"no_ecosystem_overclaim\", \"stop_rollback_present\"], \"record_types\": [\"LOCAL_MOCK_REQUEST\", \"LOCAL_MOCK_RESPONSE\"], \"sources\": [\"data/coaching/pilot-q44-i1.json\", \"data/escalation/pilot-q43-i1.json\", \"FOUNDATION.md\"], \"next_task\": \"FINAL_BUILD_SUMMARY\", \"parent_head\": \"4d15ccaf2e574248c0e224c05716c3af46203a39\", \"pilot_path\": \"data/context_protocol/pilot-scientific-context-protocol-i1.json\", \"fixtures_path\": \"data/context_protocol/fixtures\"}")
CONFIG["parent_head"] = "7532b4b34cf841c09faab8c835c5fc7f896d30d8"
Q45_SAMPLE_HEAD = "833c3e5f25c25c8f225ade19e6b3111f1a60e695"
Q44_EVIDENCE_HEAD = "4d15ccaf2e574248c0e224c05716c3af46203a39"
Q44_PARENT_HEAD = "7532b4b34cf841c09faab8c835c5fc7f896d30d8"
REPO_ROOT = ROOT.parent
RULE_SOURCE_FIELDS = {
    "version_negotiated": ("data/context_protocol/repro/scp-r0-context-protocol-sample.json", Q45_SAMPLE_HEAD, ["local_mock_request", "protocol_version", "value"]),
    "identity_authorized": ("data/context_protocol/repro/scp-r0-context-protocol-sample.json", Q45_SAMPLE_HEAD, ["local_mock_request", "identity_authorization", "value"]),
    "capability_not_authority": ("data/context_protocol/repro/scp-r0-context-protocol-sample.json", Q45_SAMPLE_HEAD, ["local_mock_request", "authority_capability", "value"]),
    "artifact_exact_head_bound": ("data/context_protocol/repro/scp-r0-context-protocol-sample.json", Q45_SAMPLE_HEAD, ["local_mock_request", "artifact_binding", "value"]),
    "rights_preserved": ("data/coaching/pilot-q44-i1.json", Q44_PARENT_HEAD, ["evidence_registry", 0, "rights_status"]),
    "failure_retry_typed": ("data/context_protocol/repro/scp-r0-context-protocol-sample.json", Q45_SAMPLE_HEAD, ["local_mock_request", "failure_retry_semantics", "value"]),
    "compatibility_fail_closed": ("data/context_protocol/repro/scp-r0-context-protocol-sample.json", Q45_SAMPLE_HEAD, ["local_mock_request", "compatibility_policy", "value"]),
    "sensitive_local_first": ("data/context_protocol/repro/scp-r0-context-protocol-sample.json", Q45_SAMPLE_HEAD, ["local_mock_request", "sensitive_data_network_local_first", "value"]),
    "hardware_request_only": ("data/context_protocol/repro/scp-r0-context-protocol-sample.json", Q45_SAMPLE_HEAD, ["local_mock_request", "experiment_hardware_request_result", "value"]),
    "no_ecosystem_overclaim": ("data/context_protocol/repro/scp-r0-context-protocol-sample.json", Q45_SAMPLE_HEAD, ["negative_constraints", "no_ecosystem_overclaim"]),
    "stop_rollback_present": ("data/context_protocol/repro/scp-r0-context-protocol-sample.json", Q45_SAMPLE_HEAD, ["local_mock_request", "stop_rollback_present", "value"]),
}
BASE_EVIDENCE = [
    ("data/coaching/pilot-q44-i1.json", Q44_EVIDENCE_HEAD, "predecessor_q44_evidence", "COACHING_PILOT"),
    ("data/escalation/pilot-q43-i1.json", Q44_EVIDENCE_HEAD, "predecessor_q43_evidence", "ESCALATION_PILOT"),
    ("FOUNDATION.md", Q44_EVIDENCE_HEAD, "foundation_evidence", "FOUNDATION"),
]

def _git_bytes(revision, path):
    result = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{revision}:{path}"], capture_output=True)
    if result.returncode:
        raise RuntimeError(f"cannot read evidence object {revision}:{path}: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout

def _git_text(revision, path):
    return _git_bytes(revision, path).decode("utf-8")

def _object_evidence(evidence_id, path, revision, role, record_type):
    content = _git_bytes(revision, path)
    blob = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", f"{revision}:{path}"], capture_output=True, text=True, check=True).stdout.strip()
    digest = "sha256:" + hashlib.sha256(content).hexdigest()
    return {
        "evidence_id": evidence_id,
        "artifact": path,
        "exact_head": revision,
        "artifact_digest": digest,
        "commit_sha": revision,
        "repository_relative_path": path,
        "blob_sha": blob,
        "sha256": digest,
        "record_type": record_type,
        "declared_role": role,
        "rights_status": "REPOSITORY_INTERNAL",
    }, content

def _at(document, path):
    value = document
    for key in path:
        value = value[key]
    return value

def _r3_evidence(bundle):
    from tools.governance.r3_capability_evaluators import CAPABILITY_SPECS, get_matrix
    matrix = get_matrix(CONFIG["capability"])
    rule_fields = CAPABILITY_SPECS[CONFIG["capability"]]["rule_fields"]
    evidence = []
    for index, (path, revision, role, record_type) in enumerate(BASE_EVIDENCE, 1):
        item, _ = _object_evidence(f"evidence.{index}", path, revision, role, record_type)
        evidence.append(item)
    rule_ids = {}
    contents = {}
    for index, rule_id in enumerate(CONFIG["rules"], 4):
        path, revision, value_path = RULE_SOURCE_FIELDS[rule_id]
        spec = matrix[rule_id]
        evidence_id = f"evidence.{index}"
        item, content = _object_evidence(evidence_id, path, revision, spec["roles"][0], spec["types"][0])
        evidence.append(item)
        rule_ids[rule_id] = evidence_id
        doc = json.loads(content) if path.endswith(".json") else content.decode("utf-8")
        value = _at(doc, value_path)
        if not isinstance(value, str) or not value or value.encode("utf-8") not in content:
            raise ValueError(f"{rule_id} evidence value is absent from its bound Git object")
        contents[rule_id] = value
    for record in bundle["records"]:
        for rule_id, field in rule_fields.items():
            record[field] = {
                "status": "RECORDED",
                "value": contents[rule_id],
                "evidence_refs": [rule_ids[rule_id]],
            }
    for assertion in bundle["rule_assertions"]:
        assertion["evidence_refs"] = [rule_ids[assertion["rule_id"]]]
    bundle["evidence_registry"] = evidence
    return bundle

def build_current():
    build(CONFIG, ROOT)
    pilot_path = ROOT / CONFIG["pilot_path"]
    pilot = _r3_evidence(json.loads(pilot_path.read_text()))
    dump(pilot_path, pilot)
    fixtures = ROOT / CONFIG["fixtures_path"]
    for path in sorted(fixtures.glob("*.json")):
        fixture = json.loads(path.read_text())
        evidence_binding_negative = path.name == "04-evidence-exit04.json"
        fixture["records"] = json.loads(json.dumps(pilot["records"]))
        fixture["evidence_registry"] = json.loads(json.dumps(pilot["evidence_registry"]))
        fixture["rule_assertions"] = json.loads(json.dumps(pilot["rule_assertions"]))
        if evidence_binding_negative:
            fixture["evidence_registry"][0]["blob_sha"] = "0" * 40
        dump(path, fixture)

if __name__=="__main__": build_current()
