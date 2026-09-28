#!/usr/bin/env python3
"""Create the local sealed 6 x 3 Task227 map after both policy reviews lock."""
from __future__ import annotations
import argparse, json, os, secrets
from pathlib import Path

REPO=Path(__file__).resolve().parents[5]
SUBTREE=REPO/"ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0"
CONDITIONS=("M0_ONLY","M0_PLUS_E1","REFERENCE_M1")
EXPECTED={f"REF-{i:02d}" for i in range(1,7)}

def load(path):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:raise SystemExit(f"TASK227_MAP_INVALID: {path}: {exc}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    policies=SUBTREE/"outputs/reference-m1"
    for evaluator in ("EVAL-A","EVAL-B"):
        sheet=load(SUBTREE/f"outputs/reference-policy-review/{evaluator}.json")
        ids={row.get("policy_id") for row in sheet.get("scores",[])}
        if sheet.get("locked") is not True or ids!=EXPECTED:raise SystemExit(f"TASK227_MAP_INVALID: {evaluator} is not a complete locked six-policy sheet")
    lineage_family={}
    for i in range(1,7):
        lineage=f"REF-{i:02d}"
        p=policies/f"{lineage}.raw"
        if not p.is_file():raise SystemExit(f"TASK227_MAP_INVALID: missing immutable policy {lineage}")
        manifest=load(SUBTREE/f"reference/manifests/{lineage}.json")
        lineage_family[lineage]=manifest["family_id"]
    rows=[]
    for lineage,family in lineage_family.items():
        for condition in CONDITIONS:
            rows.append({"trial_id":secrets.token_hex(16),"lineage_id":lineage,"family_id":family,"condition":condition})
    secrets.SystemRandom().shuffle(rows)
    ids=[r["trial_id"] for r in rows]
    if len(set(ids))!=18:raise SystemExit("TASK227_MAP_INVALID: opaque IDs not unique")
    for lineage in lineage_family:
        pairs=[(r["family_id"],r["condition"]) for r in rows if r["lineage_id"]==lineage]
        if set(pairs)!={(lineage_family[lineage],c) for c in CONDITIONS}:raise SystemExit("TASK227_MAP_INVALID: matrix mismatch")
    payload={"map_version":"TASK227_COMPONENT_A_R0","trials":rows}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    os.chmod(args.output,0o600)
    print("TASK227_SEALED_MAP=18_TRIALS")
    print("LINEAGES=6")
    print("CONDITIONS_PER_LINEAGE=3")
    print("OPAQUE_IDS_UNIQUE=true")

if __name__=="__main__":main()
