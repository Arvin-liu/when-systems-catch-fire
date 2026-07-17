#!/usr/bin/env python3
"""LAB-Q36 Temporal Causality Validator"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "temporal"

class Result:
    def __init__(self):
        self.passed, self.failed = [], []
    def ok(self, m): self.passed.append(m)
    def fail(self, m): self.failed.append(m)
    @property
    def is_pass(self): return not self.failed
    def report(self):
        lines = [f"Temporal: {'PASS' if self.is_pass else 'FAIL'} ({len(self.passed)} pass, {len(self.failed)} fail)"]
        for p in self.passed: lines.append(f"  [PASS] {p}")
        for f in self.failed: lines.append(f"  [FAIL] {f}")
        return "\n".join(lines)

def validate_predictions():
    r = Result()
    doc = json.loads((DATA_DIR / "prediction-records.json").read_text())
    for e in doc.get("entries", []):
        eid = e.get("id", "?")
        for field in ["object", "mechanism", "time_range", "trigger_conditions", "falsification_conditions", "observation_period", "expiry_status"]:
            if field not in e or not e[field]:
                r.fail(f"{eid}: missing {field}")
        # No auto-causal proof
        if e.get("claim_ceiling") and "proof" in e.get("claim_ceiling", ""):
            r.fail(f"{eid}: cannot claim causal proof")
    r.ok(f"Predictions: {len(doc['entries'])} valid")
    return r

def validate_interventions():
    r = Result()
    doc = json.loads((DATA_DIR / "intervention-candidates.json").read_text())
    for e in doc.get("entries", []):
        eid = e.get("id", "?")
        if not e.get("counterfactual"):
            r.fail(f"{eid}: missing counterfactual")
    r.ok(f"Interventions: {len(doc['entries'])} valid")
    return r

def validate_no_reachability_as_causation():
    r = Result()
    doc = json.loads((DATA_DIR / "prediction-records.json").read_text())
    for e in doc.get("entries", []):
        mech = e.get("mechanism", "")
        forbidden = ["repository reachability", "agent repetition", "analogy relation", "synchronization obligation"]
        for f in forbidden:
            if f.lower() in mech.lower():
                r.fail(f"{e['id']}: mechanism uses '{f}' as causal proof")
    r.ok("No forbidden causal shortcuts")
    return r

def validate_all():
    r = Result()
    for fn in [validate_predictions, validate_interventions, validate_no_reachability_as_causation]:
        sub = fn()
        r.passed.extend(sub.passed)
        r.failed.extend(sub.failed)
    return r

if __name__ == "__main__":
    r = validate_all()
    print(r.report())
    sys.exit(0 if r.is_pass else 1)
