#!/usr/bin/env python3
"""R0 reproduction helper for RB09-CALLER-ASSERTED-SEMANTICS, per capability, using the AUTHENTIC r2 engine.

For each capability:
  * extract the r2 (pre-repair) shared engine from ``<r2_start_head>:tools/governance/structured_capability_gate.py``
  * build a SCHEMA-VALID but SEMANTICALLY-CONTRADICTORY bundle (record values contradict the
    rules; caller-asserted facts / rule_assertions declare everything PASS)
  * run it through the r2 engine (which only checks that evidence is *registered and referenced*
    and never recomputes the rule predicate from record values / evidence bytes)
  * the r2 engine returns GATE_PASS (exit 0): the unclosed defect.

After the r3 evaluator is wired (R1), the SAME capability gate recomputes every rule from
record values + authoritative Git evidence bytes and rejects the contradictory bundle.

This script is committed as a historical R0 artifact and is NOT part of the run-at-freeze
unit-test suite.
"""
import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
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
# r2 (pre-repair) start heads — the capability gates as they existed before repair-r3.
R2_START = {
    "decision_integrity": "1a51d1b3fd1bab4eb1c80a7429e0b629bcae69a9",
    "epistemic_state_control_plane": "25f937ea8d53b4b14f31fc9c8779995f3c516bac",
    "world_feedback_anomaly": "e92e7d3eadbb67da288077052f635e3c052bd3a1",
    "latent_system_identifiability": "95405ae791dc0359c2ab6597bfd7c50224c2c59c",
    "multi_history_world_projection": "ea447ed7f6331f8ed5e58526f4c2341d3a41d6a6",
    "counterfactual_unrealized_path": "3283ef6e76788b30a467467083f0d5ad7086b5a0",
    "graded_intervention_escalation": "e5181c83efba68f847b55e13c7b5a1ee1fd6888e",
    "coaching_commitment_subcapability": "7532b4b34cf841c09faab8c835c5fc7f896d30d8",
    "open_scientific_context_protocol": "20e598d75d8c40ed3e8af6aa1de14320c1cd0d3a",
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


def _build_contradictory_bundle(cap):
    from tests.r3_evaluator_testlib import build_bundle, flip_value
    from tools.governance.r3_capability_evaluators import get_matrix, CAPABILITY_SPECS

    gate = GATES[cap]
    cfg = _extract_config(gate)
    matrix = get_matrix(cap)
    rule_fields = CAPABILITY_SPECS[cap]["rule_fields"]
    b = build_bundle(cfg, matrix, rule_fields)
    for rid in cfg["rules"]:
        flip_value(b, rule_fields, rid, "X_CONTRADICTS_EVIDENCE_NOT_IN_BYTES")
    return b


def main():
    cap = sys.argv[1] if len(sys.argv) > 1 else "epistemic_state_control_plane"
    r2 = R2_START[cap]
    engine_src = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{r2}:tools/governance/structured_capability_gate.py"],
        capture_output=True, text=True,
    ).stdout
    if not engine_src.strip():
        print(f"ERROR: cannot extract r2 engine from {r2}")
        return 2
    snap = REPO / "tools" / "governance" / "_r2_engine_snapshot.py"
    snap.write_text(engine_src)
    try:
        b = _build_contradictory_bundle(cap)
        bp = Path(tempfile.mkdtemp(prefix="r0-")) / "bundle.json"
        bp.write_text(json.dumps(b))
        cfg = _extract_config(GATES[cap])
        r = subprocess.run(
            [sys.executable, str(snap), "--bundle", str(bp), "--config-json", json.dumps(cfg)],
            capture_output=True, text=True, cwd=str(REPO),
        )
    finally:
        snap.unlink(missing_ok=True)
    out = (
        f"=== R0 RB09-CALLER-ASSERTED-SEMANTICS reproduction (authentic r2 engine) :: {cap} ===\n"
        f"r2_engine_commit={r2}\n"
        f"gate={GATES[cap]} exit={r.returncode}\n"
        f"stdout={r.stdout.strip()[:600]}\n"
    )
    if r.returncode == 0:
        out += (
            "DEFECT REPRODUCED: r2 engine returned GATE_PASS (exit 0) for a schema-valid but "
            "SEMANTICALLY-FALSE bundle (record values contradict the rules; the engine only "
            "verified evidence registration/reference and trusted the caller-asserted PASS). "
            "RB09-CALLER-ASSERTED-SEMANTICS not closed in r2.\n"
        )
    else:
        out += f"NOTE: r2 engine exited {r.returncode} (unexpected for the r2 defect reproduction).\n"
    print(out)
    ev = REPO / "tests" / f"repro_rb09_{cap}_r2_evidence.txt"
    ev.write_text(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
