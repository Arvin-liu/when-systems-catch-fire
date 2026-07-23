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
    # Only use pool files that actually exist at the target commit (earlier r3
    # checkpoints do not yet carry later capability gate files in their tree).
    pool_paths = [
        p for p in pool_paths
        if git("cat-file", "-e", f"{head}:{p}").returncode == 0
    ]
    if not pool_paths:
        raise RuntimeError(f"no usable pool paths exist at head {head}")
    # One evidence object per distinct (declared_role, record_type) pair used by
    # the matrix, so every rule's evidence matches its OWN role/type constraint
    # exactly. A single role can be required with DIFFERENT types by different
    # rules, so per-role evidence would fail the evaluator's type gate.
    rt_map = {}      # (role, type) -> eid
    ev_text = {}     # eid -> authoritative text
    evidence_registry = []
    rt_index = 0

    def _make_evidence(role, rtype):
        nonlocal rt_index
        key = (role, rtype)
        if key in rt_map:
            return rt_map[key]
        eid = f"evidence.rt.{rt_index}"
        rt_index += 1
        path = pool_paths[rt_index % len(pool_paths)]
        blob, sha = blob_and_sha(head, path)
        evidence_registry.append({
            "evidence_id": eid,
            "artifact": path,
            "exact_head": head,
            "artifact_digest": sha,
            "rights_status": "REPOSITORY_INTERNAL",
            "repository_relative_path": path,
            "commit_sha": head,
            "blob_sha": blob,
            "sha256": sha,
            "record_type": rtype,
            "declared_role": role,
        })
        ev_text[eid] = git_text(head, path)
        rt_map[key] = eid
        return eid

    record_fields = schema_record_fields(config["schema"])
    rec_rt = schema_record_type_enum(config["schema"])
    effect = schema_effect_enum(config["schema"])
    rec = {"record_id": "record.1", "record_type": rec_rt}
    rule_eid = {}
    for rid in config["rules"]:
        role = matrix[rid]["roles"][0]
        rtype = matrix[rid]["types"][0]
        eid = _make_evidence(role, rtype)
        rule_eid[rid] = eid
        fld = rule_fields.get(rid)
        if fld is None or fld not in record_fields:
            fld = record_fields[config["rules"].index(rid) % len(record_fields)]
        rec[fld] = {
            "status": "RECORDED",
            "value": ev_text[eid],
            "evidence_refs": [eid],
        }
    # Any remaining record fields (not bound to a rule) get a default evidence.
    default_eid = next(iter(rt_map.values()))
    for fld in record_fields:
        if fld not in rec:
            rec[fld] = {
                "status": "RECORDED",
                "value": ev_text[default_eid],
                "evidence_refs": [default_eid],
            }
    # Schemas require records.minItems >= 2. Emit two identical records so the
    # bundle is schema-valid; the evaluator indexes record values regardless.
    rec2 = json.loads(json.dumps(rec))
    rec2["record_id"] = "record.2"
    records = [rec, rec2]

    # A distinct single blob for the laundering test (its own real file).
    launder_role = matrix[config["rules"][0]]["roles"][0]
    launder_type = matrix[config["rules"][0]]["types"][0]
    launder_path = pool_paths[(len(evidence_registry) + 1) % len(pool_paths)]
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
        "record_type": launder_type,
        "declared_role": launder_role,
    })
    ev_text["evidence.launder"] = git_text(head, launder_path)

    rule_assertions = []
    for rid in config["rules"]:
        rule_assertions.append({
            "rule_id": rid,
            "status": "PASS",
            "evidence_refs": [rule_eid[rid]],
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
