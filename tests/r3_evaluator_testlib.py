#!/usr/bin/env python3
"""Shared test helper for repair-r3 semantic-evaluator bundles (RB09-CALLER-ASSERTED-SEMANTICS).

Builds valid capability bundles from REAL Git objects in this repository (so the
engine has authoritative bytes to recompute against), runs a capability gate as a
real CLI subprocess, and provides adversarial mutations:

  * flip_value   – mutate a single record value so the bound rule recomputes FAIL
  * launder      – point every rule's evidence_refs at ONE unrelated-but-valid blob

The positive bundle passes (exit 0); the semantic-false / laundering mutations must
return a nonzero EVALUATOR_RULE_FAILED (30+index) because the engine recomputes
from record values + evidence bytes and IGNORES caller facts/status.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

MANAGED_PY = "/Users/zhiyuan/.workbuddy/binaries/python/envs/default/bin/python"

REPO_ROOT = Path(
    subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    ).stdout.strip()
)

# A pool of real repo files that exist at every r3 head (used as Git evidence).
POOL_PATHS = [
    "tools/governance/structured_capability_gate.py",
    "tools/governance/semantic_evaluator.py",
    "tools/governance/r3_capability_evaluators.py",
    "tools/decision/validate_decision_integrity_gate.py",
    "tools/metacognition/validate_epistemic_state_control_plane_gate.py",
    "tools/anomaly/validate_world_feedback_anomaly_gate.py",
    "tools/latent/validate_latent_system_identifiability_gate.py",
    "tools/multihistory/validate_multi_history_world_projection_gate.py",
    "tools/counterfactual/validate_counterfactual_unrealized_path_gate.py",
    "tools/escalation/validate_graded_intervention_escalation_gate.py",
    "tools/coaching/validate_coaching_commitment_subcapability_gate.py",
    "tools/context_protocol/validate_open_scientific_context_protocol_gate.py",
    "schemas/decision/decision_integrity-contract.schema.json",
    "README.md",
]


def git(*args):
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT)] + list(args), capture_output=True, text=True
    )


def head_sha():
    return git("rev-parse", "HEAD").stdout.strip()


def blob_and_sha(commit, path):
    blob = git("rev-parse", f"{commit}:{path}").stdout.strip()
    out = git("show", f"{commit}:{path}").stdout
    sha = "sha256:" + __import__("hashlib").sha256(out.encode()).hexdigest()
    return blob, sha


def git_text(commit, path):
    return git("show", f"{commit}:{path}").stdout


def schema_record_fields(schema_path):
    doc = json.loads((REPO_ROOT / schema_path).read_text())
    req = doc["properties"]["records"]["items"]["required"]
    return [p for p in req if p not in ("record_id", "record_type")]


def schema_record_type_enum(schema_path):
    doc = json.loads((REPO_ROOT / schema_path).read_text())
    enum = doc["properties"]["records"]["items"]["properties"]["record_type"].get("enum")
    return enum[0] if enum else "CAPABILITY_RECORD"


def schema_effect_enum(schema_path):
    doc = json.loads((REPO_ROOT / schema_path).read_text())
    enum = doc["properties"]["rule_assertions"]["items"]["properties"]["effect"].get("enum")
    return enum[0] if enum else "ALLOW_WITHIN_CEILING"


def _role_type(matrix, role):
    for spec in matrix.values():
        if role in spec["roles"]:
            return spec["types"][0]
    return "structured_record"


def build_bundle(config, matrix, rule_fields, pool_paths=None, head=None):
    """Build a valid positive bundle from real Git objects for ``config``."""
    pool_paths = pool_paths or POOL_PATHS
    head = head or head_sha()
    # One evidence object per distinct declared_role in the matrix.
    roles = sorted({r for spec in matrix.values() for r in spec["roles"]})
    role_ev = {}
    for i, role in enumerate(roles):
        path = pool_paths[i % len(pool_paths)]
        blob, sha = blob_and_sha(head, path)
        role_ev[role] = {"path": path, "blob": blob, "sha": sha, "text": git_text(head, path)}
    eid_by_role = {}
    evidence_registry = []
    for role in roles:
        eid = "evidence.role." + role
        eid_by_role[role] = eid
        ev = role_ev[role]
        evidence_registry.append({
            "evidence_id": eid,
            "artifact": ev["path"],
            "exact_head": head,
            "artifact_digest": ev["sha"],
            "rights_status": "REPOSITORY_INTERNAL",
            "repository_relative_path": ev["path"],
            "commit_sha": head,
            "blob_sha": ev["blob"],
            "sha256": ev["sha"],
            "record_type": _role_type(matrix, role),
            "declared_role": role,
        })
    # A distinct single blob for the laundering test (its own real file).
    launder_path = pool_paths[(len(roles) + 1) % len(pool_paths)]
    lblob, lsha = blob_and_sha(head, launder_path)
    evidence_registry.append({
        "evidence_id": "evidence.launder",
        "artifact": launder_path,
        "exact_head": head,
        "artifact_digest": lsha,
        "rights_status": "REPOSITORY_INTERNAL",
        "repository_relative_path": launder_path,
        "commit_sha": head,
        "blob_sha": lblob,
        "sha256": lsha,
        "record_type": _role_type(matrix, roles[0]),
        "declared_role": roles[0],
    })

    record_fields = schema_record_fields(config["schema"])
    rec_rt = schema_record_type_enum(config["schema"])
    effect = schema_effect_enum(config["schema"])
    rec = {"record_id": "record.1", "record_type": rec_rt}
    # Bind each rule's field to its role evidence.
    for rid in config["rules"]:
        fld = rule_fields.get(rid)
        if fld is None or fld not in record_fields:
            fld = record_fields[config["rules"].index(rid) % len(record_fields)]
        role = matrix[rid]["roles"][0]
        ev = role_ev[role]
        rec[fld] = {
            "status": "RECORDED",
            "value": ev["text"],
            "evidence_refs": [eid_by_role[role]],
        }
    # Any remaining record fields (not bound to a rule) get a default evidence.
    default_role = roles[0]
    dev = role_ev[default_role]
    for fld in record_fields:
        if fld not in rec:
            rec[fld] = {
                "status": "RECORDED",
                "value": dev["text"],
                "evidence_refs": [eid_by_role[default_role]],
            }
    records = [rec]

    rule_assertions = []
    for rid in config["rules"]:
        role = matrix[rid]["roles"][0]
        rule_assertions.append({
            "rule_id": rid,
            "status": "PASS",
            "evidence_refs": [eid_by_role[role]],
            "effect": effect,
        })
    facts = {rid: True for rid in config["rules"]}
    bundle = {
        "contract_version": "1.0.0",
        "task_id": config["task_id"],
        "capability_id": config["capability"],
        "parent_binding": {"task_id": config["parent_id"], "exact_head": config["parent_head"]},
        "evidence_registry": evidence_registry,
        "records": records,
        "facts": facts,
        "rule_assertions": rule_assertions,
        "conclusion": {
            "statement": "recomputed from authoritative Git evidence; candidate only",
            "claim_ceiling": "candidate_only_repository_governance",
            "history_preserved": True,
            "external_action_performed": False,
        },
    }
    return bundle


def write_bundle(bundle, suffix="bundle.json"):
    p = Path(tempfile.mkdtemp(prefix="r3-test-")) / suffix
    p.write_text(json.dumps(bundle))
    return p


def run_gate(gate_path, bundle_path):
    r = subprocess.run(
        [MANAGED_PY, str(gate_path), "--bundle", str(bundle_path)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def flip_value(bundle, rule_fields, rid, new_value):
    """Mutate the record value bound to ``rid`` (record values are NOT truth authority)."""
    fld = rule_fields.get(rid)
    for rec in bundle.get("records", []):
        if fld in rec:
            rec[fld] = {"status": "RECORDED", "value": new_value,
                        "evidence_refs": rec[fld].get("evidence_refs", [])}
            return
    raise KeyError(f"field {fld!r} for rule {rid!r} not found in records")


def launder(bundle, rule_fields, single_eid="evidence.launder"):
    """Point every rule's field + assertion evidence_refs at ONE unrelated-valid blob."""
    for rid in bundle["facts"]:
        fld = rule_fields.get(rid)
        for rec in bundle.get("records", []):
            if fld in rec and isinstance(rec[fld], dict):
                rec[fld]["evidence_refs"] = [single_eid]
        for a in bundle.get("rule_assertions", []):
            if a.get("rule_id") == rid:
                a["evidence_refs"] = [single_eid]
    return bundle
