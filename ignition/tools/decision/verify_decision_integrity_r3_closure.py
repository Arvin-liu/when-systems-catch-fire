#!/usr/bin/env python3
"""R3 propagation-closure verification for DECISION-INTEGRITY-I1 repair-r1.

Fail-closed: recomputes the canonical closure hash from real closure content and
asserts closure_complete=true and residue=0. Any mismatch -> non-zero exit so the
repair train stops rather than publishing an unverified closure.
"""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLOSURE = ROOT / "data/operations/propagation/DECISION-INTEGRITY-I1-closure.json"
RESIDUE = ROOT / "data/operations/propagation/DECISION-INTEGRITY-I1-residue.json"


def canonical_closure_hash(closure):
    body = {k: v for k, v in closure.items() if k != "closure_hash"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()


def main():
    closure = json.loads(CLOSURE.read_text())
    declared = closure.get("closure_hash")
    recomputed = canonical_closure_hash(closure)
    errors = []
    if recomputed != declared:
        errors.append(f"closure_hash mismatch: declared {declared} recomputed {recomputed}")
    if not closure.get("closure_complete"):
        errors.append("closure_complete is not true")
    if closure.get("residue"):
        errors.append(f"residue not empty: {closure.get('residue')}")
    residue = json.loads(RESIDUE.read_text())
    if residue.get("residue"):
        errors.append(f"residue not empty: {residue.get('residue')}")
    if not residue.get("closure_complete"):
        errors.append("residue.closure_complete is not true")
    # cross-check: residue.closure_hash must equal closure.closure_hash
    if residue.get("closure_hash") != declared:
        errors.append(f"residue.closure_hash {residue.get('closure_hash')} != closure.closure_hash {declared}")

    if errors:
        for e in errors:
            print("R3 CLOSURE VERIFICATION FAILED:", e)
        return 1
    print("R3 CLOSURE VERIFICATION PASSED:")
    print(f"  closure_hash={declared}")
    print(f"  closure_complete={residue.get('closure_complete')} residue={residue.get('residue')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
