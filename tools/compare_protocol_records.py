#!/usr/bin/env python3
"""Compare two protocol record sets (e.g., 020-style vs canonical-style) and
report per-gate verdict differences. Read-only."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d["results"] if isinstance(d, dict) and "results" in d else d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="first result json")
    ap.add_argument("--b", required=True, help="second result json")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    A = {r["protocol_id"]: r for r in load(a.a)}
    B = {r["protocol_id"]: r for r in load(a.b)}
    diffs = []
    for pid in A:
        ga = {g["gate_id"]: g["result"] for g in A[pid].get("gate_results", [])}
        gb = {g["gate_id"]: g["result"] for g in B.get(pid, {}).get("gate_results", [])}
        for gid in set(ga) | set(gb):
            if ga.get(gid) != gb.get(gid):
                diffs.append({"protocol_id": pid, "gate_id": gid,
                              "a": ga.get(gid), "b": gb.get(gid)})
    Path(a.output).write_text(json.dumps(diffs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"compared {len(A)} protocols; {len(diffs)} gate-differences -> {a.output}")

if __name__ == "__main__":
    raise SystemExit(main())
