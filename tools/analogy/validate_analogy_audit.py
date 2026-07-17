#!/usr/bin/env python3
"""LAB-Q37 Analogy Audit Validator"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "analogy"

class Result:
    def __init__(self):
        self.passed, self.failed = [], []
    def ok(self, m): self.passed.append(m)
    def fail(self, m): self.failed.append(m)
    @property
    def is_pass(self): return not self.failed
    def report(self):
        lines = [f"Analogy: {'PASS' if self.is_pass else 'FAIL'} ({len(self.passed)} pass, {len(self.failed)} fail)"]
        for p in self.passed: lines.append(f"  [PASS] {p}")
        for f in self.failed: lines.append(f"  [FAIL] {f}")
        return "\n".join(lines)

def validate_all():
    r = Result()
    doc = json.loads((DATA_DIR / "analogy-candidates.json").read_text())
    for e in doc.get("entries", []):
        eid = e.get("id", "?")
        # Must have both domains
        if not e.get("source_domain") or not e.get("target_domain"):
            r.fail(f"{eid}: missing domain specification")
        # Must have structural correspondence
        if not e.get("structural_correspondence"):
            r.fail(f"{eid}: no structural correspondence listed")
        # Must have non-correspondence residue
        if not e.get("non_correspondence_residue"):
            r.fail(f"{eid}: no non-correspondence residue - analogy is suspiciously clean")
        # Must have hidden premise transfer
        if not e.get("hidden_premise_transfer"):
            r.fail(f"{eid}: no hidden premise transfer analysis")
        # Must have claim ceiling
        if not e.get("claim_ceiling"):
            r.fail(f"{eid}: no claim ceiling")
        # Claim ceiling must not be "formal_equivalence" unless proven
        if e.get("claim_ceiling") == "formal_equivalence":
            r.fail(f"{eid}: cannot claim formal equivalence without proof")
        # Must have negative transfer analysis
        if not e.get("negative_transfer"):
            r.fail(f"{eid}: no negative transfer analysis")
    r.ok(f"Analogies: {len(doc['entries'])} valid")
    
    # Residue linkage
    res = json.loads((DATA_DIR / "non-correspondence-residue.json").read_text())
    ana_ids = {e["id"] for e in doc["entries"]}
    for e in res.get("entries", []):
        if e.get("analogy_id") and e["analogy_id"] not in ana_ids:
            r.fail(f"residue {e['id']}: references unknown analogy {e['analogy_id']}")
    r.ok(f"Residue: {len(res['entries'])} entries linked")
    return r

if __name__ == "__main__":
    r = validate_all()
    print(r.report())
    sys.exit(0 if r.is_pass else 1)
