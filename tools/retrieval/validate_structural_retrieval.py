#!/usr/bin/env python3
"""LAB-Q38 Structural Retrieval Validator"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "retrieval"

class Result:
    def __init__(self):
        self.passed, self.failed = [], []
    def ok(self, m): self.passed.append(m)
    def fail(self, m): self.failed.append(m)
    @property
    def is_pass(self): return not self.failed
    def report(self):
        lines = [f"Retrieval: {'PASS' if self.is_pass else 'FAIL'} ({len(self.passed)} pass, {len(self.failed)} fail)"]
        for p in self.passed: lines.append(f"  [PASS] {p}")
        for f in self.failed: lines.append(f"  [FAIL] {f}")
        return "\n".join(lines)

def validate_all():
    r = Result()
    # Relation signatures
    sig = json.loads((DATA_DIR / "relation-signatures.json").read_text())
    for e in sig.get("entries", []):
        if not e.get("relation_type"):
            r.fail(f"{e['id']}: missing relation_type")
        if not e.get("arguments"):
            r.fail(f"{e['id']}: missing arguments")
    r.ok(f"Signatures: {len(sig['entries'])} valid")
    
    # Cases must reference valid signatures
    cases = json.loads((DATA_DIR / "case-structures.json").read_text())
    sig_ids = {e["id"] for e in sig["entries"]}
    for e in cases.get("entries", []):
        for sid in e.get("relation_signature_ids", []):
            if sid not in sig_ids:
                r.fail(f"{e['id']}: references unknown signature {sid}")
        if not e.get("claim_ceiling"):
            r.fail(f"{e['id']}: missing claim_ceiling")
    r.ok(f"Cases: {len(cases['entries'])} valid")
    
    # Counterexamples must reference valid case pairs
    cx = json.loads((DATA_DIR / "counterexample-set.json").read_text())
    case_ids = {e["id"] for e in cases["entries"]}
    for e in cx.get("entries", []):
        for cid in e.get("case_pair", []):
            if cid not in case_ids:
                r.fail(f"{e['id']}: references unknown case {cid}")
    r.ok(f"Counterexamples: {len(cx['entries'])} valid")
    return r

if __name__ == "__main__":
    r = validate_all()
    print(r.report())
    sys.exit(0 if r.is_pass else 1)
