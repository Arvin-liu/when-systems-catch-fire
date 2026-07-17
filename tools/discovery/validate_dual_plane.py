#!/usr/bin/env python3
"""LAB-Q34 Dual Plane Validator
LAB / SPECULATIVE / NON-AUTHORITATIVE / NOT CURRENT / NOT MERGE-AUTHORIZED
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "discovery"

VALID_PLANES = {"exploration", "commitment"}
VALID_STATUSES = {"discovered", "hypothesized", "candidates_proposed", "gates_passed", "committed", "demoted", "residue", "blocked"}
VALID_EPISTEMIC = {"analogy", "inspiration", "conjecture", "model_sketch", "validated_hypothesis", "tested_claim", "accepted_fact"}
GATE_VALUES = {"pass", "fail", "pending"}

class Result:
    def __init__(self):
        self.passed, self.failed = [], []
    def ok(self, m): self.passed.append(m)
    def fail(self, m): self.failed.append(m)
    @property
    def is_pass(self): return not self.failed
    def report(self):
        lines = [f"Dual Plane: {'PASS' if self.is_pass else 'FAIL'} ({len(self.passed)} pass, {len(self.failed)} fail)"]
        for p in self.passed: lines.append(f"  [PASS] {p}")
        for f in self.failed: lines.append(f"  [FAIL] {f}")
        return "\n".join(lines)

def validate_all():
    r = Result()
    for f in sorted(DATA_DIR.glob("*.json")):
        doc = json.loads(f.read_text())
        name = f.name
        for e in doc.get("entries", []):
            eid = e.get("id", "?")
            # Plane validation
            if e.get("plane") not in VALID_PLANES:
                r.fail(f"{name}[{eid}]: invalid plane")
            # Status validation
            if e.get("status") not in VALID_STATUSES:
                r.fail(f"{name}[{eid}]: invalid status")
            # Gate validation: commitment plane requires all gates pass
            if e.get("plane") == "commitment" and e.get("status") == "committed":
                gates = e.get("gates", {})
                for g in ["rights_gate", "epistemic_gate", "action_authority_gate"]:
                    if gates.get(g) != "pass":
                        r.fail(f"{name}[{eid}]: committed but {g} != pass")
            # Exploration items cannot be in commitment plane
            if doc.get("plane_type") == "discovery" and e.get("plane") == "commitment":
                r.fail(f"{name}[{eid}]: discovery registry has commitment plane entry")
            # Residue must have blocked reasons
            if e.get("status") == "residue" and not e.get("promotion_blocked_reasons"):
                r.fail(f"{name}[{eid}]: residue without blocked reasons")
            # Epistemic level: commitment requires tested_claim or higher
            if e.get("plane") == "commitment":
                el = e.get("epistemic_level", "")
                if el in ("analogy", "inspiration", "conjecture", "model_sketch"):
                    r.fail(f"{name}[{eid}]: commitment plane with low epistemic level '{el}'")
        r.ok(f"{name}: {len(doc.get('entries',[]))} entries valid")
    return r

if __name__ == "__main__":
    r = validate_all()
    print(r.report())
    sys.exit(0 if r.is_pass else 1)
