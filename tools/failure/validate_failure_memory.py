#!/usr/bin/env python3
"""LAB-Q39 Failure Memory Validator"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "failure"

class Result:
    def __init__(self):
        self.passed, self.failed = [], []
    def ok(self, m): self.passed.append(m)
    def fail(self, m): self.failed.append(m)
    @property
    def is_pass(self): return not self.failed
    def report(self):
        lines = [f"Failure Memory: {'PASS' if self.is_pass else 'FAIL'} ({len(self.passed)} pass, {len(self.failed)} fail)"]
        for p in self.passed: lines.append(f"  [PASS] {p}")
        for f in self.failed: lines.append(f"  [FAIL] {f}")
        return "\n".join(lines)

def validate_all():
    r = Result()
    # Failure records
    fr = json.loads((DATA_DIR / "failure-records.json").read_text())
    fail_ids = set()
    for e in fr.get("entries", []):
        eid = e.get("id", "?")
        fail_ids.add(eid)
        for field in ["failure_class", "mechanism", "source_iteration", "missed_gate", "repair_type", "regression_test"]:
            if field not in e or not e[field]:
                r.fail(f"{eid}: missing {field}")
        if not e.get("claim_ceiling"):
            r.fail(f"{eid}: missing claim_ceiling")
        # Must answer: which gate should have caught it
        if not e.get("missed_gate"):
            r.fail(f"{eid}: must identify which gate should have prevented this")
    r.ok(f"Failure records: {len(fr['entries'])} valid")
    
    # Recurrence signatures
    rec = json.loads((DATA_DIR / "recurrence-signatures.json").read_text())
    for e in rec.get("entries", []):
        for fid in e.get("failure_ids", []):
            if fid not in fail_ids:
                r.fail(f"{e['id']}: references unknown failure {fid}")
    r.ok(f"Recurrence signatures: {len(rec['entries'])} valid")
    
    # Repair propagation
    rep = json.loads((DATA_DIR / "repair-propagation.json").read_text())
    for e in rep.get("entries", []):
        for fid in e.get("failure_ids", []):
            if fid not in fail_ids:
                r.fail(f"{e['id']}: references unknown failure {fid}")
        if not e.get("overfitting_risk"):
            r.fail(f"{e['id']}: missing overfitting_risk assessment")
    r.ok(f"Repair propagation: {len(rep['entries'])} valid")
    return r

if __name__ == "__main__":
    r = validate_all()
    print(r.report())
    sys.exit(0 if r.is_pass else 1)
