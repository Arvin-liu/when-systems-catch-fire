#!/usr/bin/env python3
"""LAB-Q35 Agent Duty Validator"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "agent"

class Result:
    def __init__(self):
        self.passed, self.failed = [], []
    def ok(self, m): self.passed.append(m)
    def fail(self, m): self.failed.append(m)
    @property
    def is_pass(self): return not self.failed
    def report(self):
        lines = [f"Agent Duty: {'PASS' if self.is_pass else 'FAIL'} ({len(self.passed)} pass, {len(self.failed)} fail)"]
        for p in self.passed: lines.append(f"  [PASS] {p}")
        for f in self.failed: lines.append(f"  [FAIL] {f}")
        return "\n".join(lines)

def validate_state_transitions():
    r = Result()
    states_doc = json.loads((DATA_DIR / "task-states.json").read_text())
    valid = set(states_doc["valid_states"])
    transitions = states_doc["valid_transitions"]
    for src, targets in transitions.items():
        if src not in valid:
            r.fail(f"Unknown source state: {src}")
        for tgt in targets:
            if tgt not in valid:
                r.fail(f"Unknown target state: {tgt} from {src}")
    r.ok(f"State machine: {len(valid)} states, {len(transitions)} transitions valid")
    return r

def validate_contracts():
    r = Result()
    doc = json.loads((DATA_DIR / "duty-contracts.json").read_text())
    for e in doc.get("entries", []):
        eid = e.get("id", "?")
        if not e.get("rule"):
            r.fail(f"{eid}: missing rule")
        if not e.get("blocked_actions"):
            r.fail(f"{eid}: missing blocked_actions")
        if not e.get("requires_human_decision"):
            r.fail(f"{eid}: missing requires_human_decision")
        if not e.get("claim_ceiling"):
            r.fail(f"{eid}: missing claim_ceiling")
    r.ok(f"Duty contracts: {len(doc['entries'])} contracts valid")
    return r

def validate_permissions():
    r = Result()
    doc = json.loads((DATA_DIR / "tool-permissions.json").read_text())
    for e in doc.get("entries", []):
        eid = e.get("id", "?")
        if e.get("target") == "main" and e.get("allowed") is True:
            r.fail(f"{eid}: main push must not be allowed")
        if e.get("allowed") is True and e.get("requires_human_decision") is True:
            r.ok(f"{eid}: allowed but requires human decision")
    r.ok(f"Tool permissions: {len(doc['entries'])} entries valid")
    return r

def validate_traces():
    r = Result()
    states_doc = json.loads((DATA_DIR / "task-states.json").read_text())
    valid = set(states_doc["valid_states"])
    transitions = states_doc["valid_transitions"]
    doc = json.loads((DATA_DIR / "action-traces.json").read_text())
    for e in doc.get("entries", []):
        eid = e.get("id", "?")
        sf, st = e.get("state_from"), e.get("state_to")
        if sf not in valid:
            r.fail(f"{eid}: invalid state_from {sf}")
        if st not in valid:
            r.fail(f"{eid}: invalid state_to {st}")
        if sf and st and st not in transitions.get(sf, []):
            r.fail(f"{eid}: invalid transition {sf}->{st}")
    r.ok(f"Action traces: {len(doc['entries'])} traces valid")
    return r

def validate_all():
    r = Result()
    for fn in [validate_state_transitions, validate_contracts, validate_permissions, validate_traces]:
        sub = fn()
        r.passed.extend(sub.passed)
        r.failed.extend(sub.failed)
    return r

if __name__ == "__main__":
    r = validate_all()
    print(r.report())
    sys.exit(0 if r.is_pass else 1)
