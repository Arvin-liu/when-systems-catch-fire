#!/usr/bin/env python3
"""R0 reproduction helper for RB09-CALLER-ASSERTED-SEMANTICS, per capability.

Usage:
  python tests/repro_rb09_capability.py <capability>

Builds a SCHEMA-VALID bundle for the capability whose record values are all
*contradictory* (they do not appear in the authoritative evidence bytes) while
the caller-asserted facts/rule_assertions declare everything PASS, binds a single
REAL Git evidence object, and runs the capability gate. On the pre-fix (r2) engine
the gate returns GATE_PASS (exit 0): the engine verified evidence registration +
git-object binding + assertion coverage but NEVER recomputed rule predicates from
record values / evidence bytes. That is the unclosed defect.

After the r3 evaluator is wired (R1), the same capability gate recomputes from
evidence and rejects the contradictory bundle. This script is committed as a
historical R0 artifact and is NOT part of the run-at-freeze unit-test suite.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATES = {
    "decision_integrity": "tools/decision/validate_decision_integrity_gate.py",
    "epistemic_state_control_plane": "tools/metacognition/validate_epistemic_state_control_plane_gate.py",
    "world_feedback_anomaly": "tools/anomaly/validate_world_feedback_anomaly_gate.py",
    "latent_system_identifiability": "tools/latent/validate_latent_system_identifiability_gate.py",
    "multi_history_world_projection": "tools/multihistory/validate_multi_history_world_projection_gate.py",
    "counterfactual_unrealized_path": "tools/counterfactual/validate_counterfactual_unrealized_path_gate.py",
    "graded_intervention_escalation": "tools/escalation/validate_graded_intervention_escalation_gate.py",
    "coaching_commitment_subcapability": "tools/coaching/validate_coaching_commitment_subcapability_gate.py",
    "open_scientific_context_protocol": "tools/context_protocol/validate_open_scientific_context_protocol_gate.py",
}


def _extract_config(gate_path):
    txt = Path(gate_path).read_text()
    s = txt.split("json.loads(", 1)[1]
    q = s.index('"')
    rest = s[q + 1:]
    i, n = 0, len(rest)
    while i < n:
        if rest[i] == '"' and (i == 0 or rest[i - 1] != '\\'):
            j = i + 1
            while j < n and rest[j] == ' ':
                j += 1
            if j < n and rest[j] == ')':
                lit = rest[:i]
                break
        i += 1
    return json.loads(ast.literal_eval('"' + lit + '"'))


def _real_evidence(path):
    head = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    blob = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", f"{head}:{path}"],
        capture_output=True, text=True,
    ).stdout.strip()
    content = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{head}:{path}"], capture_output=True
    ).stdout
    sha = "sha256:" + __import__("hashlib").sha256(content).hexdigest()
    return head, path, blob, sha


_POOL = [
    "tools/governance/structured_capability_gate.py",
    "schemas/decision/decision_integrity-contract.schema.json",
    "README.md",
]


def main():
    cap = sys.argv[1] if len(sys.argv) > 1 else "decision_integrity"
    gate = GATES[cap]
    cfg = _extract_config(gate)
    schema = json.loads(Path(cfg["schema"]).read_text())
    rec_req = [
        p for p in schema["properties"]["records"]["items"]["required"]
        if p not in ("record_id", "record_type")
    ]
    head, path, blob, sha = _real_evidence(_POOL[0])
    evidence = []
    eids = []
    for i, p in enumerate(_POOL):
        h, pp, b, s = _real_evidence(p)
        eid = f"evidence.real.{i}"
        eids.append(eid)
        evidence.append({
            "evidence_id": eid,
            "artifact": pp,
            "exact_head": h,
            "artifact_digest": s,
            "rights_status": "REPOSITORY_INTERNAL",
            "repository_relative_path": pp,
            "commit_sha": h,
            "blob_sha": b,
            "sha256": s,
            "record_type": "CAPABILITY_RECORD",
            "declared_role": "SOURCE_OF_TRUTH",
        })
    records = [{"record_id": "record.1", "record_type": "GOOD_PROCESS_BAD_OUTCOME"}]
    for f in rec_req:
        records[0][f] = {
            "status": "RECORDED",
            "value": "X_CONTRADICTS_EVIDENCE_NOT_IN_BYTES",
            "evidence_refs": list(eids),
        }
    rec2 = json.loads(json.dumps(records[0]))
    rec2["record_id"] = "record.2"
    records.append(rec2)
    bundle = {
        "contract_version": "1.0.0",
        "task_id": cfg["task_id"],
        "capability_id": cfg["capability"],
        "parent_binding": {"task_id": cfg["parent_id"], "exact_head": cfg["parent_head"]},
        "evidence_registry": evidence,
        "records": records,
        "facts": {rid: True for rid in cfg["rules"]},
        "rule_assertions": [
            {"rule_id": rid, "status": "PASS", "evidence_refs": list(eids),
             "effect": "ALLOW_WITHIN_CEILING"}
            for rid in cfg["rules"]
        ],
        "conclusion": {
            "statement": "r2 reproduction",
            "claim_ceiling": "candidate_only_repository_governance",
            "history_preserved": True,
            "external_action_performed": False,
        },
    }
    bp = REPO / "tests" / f"_repro_bundle_{cap}.json"
    bp.write_text(json.dumps(bundle))
    r = subprocess.run(
        [sys.executable, gate, "--bundle", str(bp)],
        capture_output=True, text=True, cwd=str(REPO),
    )
    print(f"=== R0 RB09-CALLER-ASSERTED-SEMANTICS reproduction :: {cap} ===")
    print(f"gate={gate} exit={r.returncode}")
    print(f"stdout={r.stdout.strip()[:400]}")
    if r.returncode == 0:
        print(
            "DEFECT REPRODUCED: r2 engine returned GATE_PASS (exit 0) for a "
            "schema-valid but SEMANTICALLY-FALSE bundle (record values contradict "
            "the rules; engine ignored them). RB09-CALLER-ASSERTED-SEMANTICS not closed."
        )
        return 0
    print(
        f"NOTE: gate exited {r.returncode} (not GATE_PASS). If this is the hardened "
        "engine, the defect is already closed for this capability."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
