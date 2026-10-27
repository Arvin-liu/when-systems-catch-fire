#!/usr/bin/env python3
"""Q34 discovery-commitment registry validator.

Cross-claim checks that a single-claim gate cannot perform:
- unique claim_ids
- supersession/retraction targets exist and are not silently still committed_current
- non-Current states never appear on the Current/Accepted surface
- retracted/superseded claims retain history (append-only)

Exit 0 on PASS, 11 on HISTORY_VIOLATION, 2 on schema/IO error.
"""
import argparse
import json
import sys
from pathlib import Path

HISTORY_VIOLATION = 11
SCHEMA_ERROR = 2


def _load(p: Path):
    try:
        return json.loads(p.read_text()), None
    except Exception as e:  # noqa: BLE001
        return None, f"{p}: {e}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims-dir", required=True)
    ap.add_argument("--current-surface", help="JSON list of claim_ids on Current/Accepted surface")
    ap.add_argument("--report")
    args = ap.parse_args(argv)

    claims_dir = Path(args.claims_dir)
    claims = {}
    errors = []
    for f in sorted(claims_dir.glob("*.json")):
        doc, err = _load(f)
        if err:
            errors.append(err)
            continue
        cid = doc.get("claim_id")
        if not cid:
            errors.append(f"{f.name}: missing claim_id")
            continue
        if cid in claims:
            errors.append(f"duplicate claim_id: {cid}")
        claims[cid] = doc

    current_surface = set()
    if args.current_surface:
        cs, err = _load(Path(args.current_surface))
        if err:
            errors.append(err)
        else:
            current_surface = set(cs if isinstance(cs, list) else cs.get("claim_ids", []))

    non_current = {"discovered", "hypothesis", "evidence_bound_candidate",
                   "validated_within_scope", "commitment_candidate",
                   "deferred", "rejected"}
    for cid, doc in claims.items():
        state = doc.get("state")
        # non-Current contamination
        if state in non_current and cid in current_surface:
            errors.append(f"{cid}: state '{state}' present on Current/Accepted surface")
        # supersession/retraction target consistency
        rel = doc.get("relations", {})
        for target in rel.get("supersedes", []) + rel.get("retracts", []):
            if target not in claims:
                errors.append(f"{cid}: supersedes/retracts unknown claim '{target}'")
                continue
            tgt = claims[target]
            if tgt.get("state") == "committed_current":
                errors.append(
                    f"{cid} supersedes/retracts '{target}' but target still committed_current (silent overwrite)")
            # target must retain history
            if not tgt.get("history"):
                errors.append(f"{cid}: superseded/retracted target '{target}' lost history")

    out = {
        "gate": "q34_commitment_registry",
        "claim_count": len(claims),
        "errors": errors,
        "exit_code": SCHEMA_ERROR if any("cannot read" in e or ".json" in e and ":" in e and "missing" in e or "duplicate" in e for e in errors) else (HISTORY_VIOLATION if errors else 0),
    }
    if args.report:
        Path(args.report).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return out["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
