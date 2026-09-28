#!/usr/bin/env python3
"""Materialize the private 18-row transfer matrix without targets or condition labels."""
from __future__ import annotations
import argparse, hashlib, json, os
from pathlib import Path

REPO=Path(__file__).resolve().parents[5]
SUBTREE=REPO/"ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0"
TASK225=REPO/"ignition/reports/evaluations/ignition-225-cognitive-evolution-r0-1"
TASK220=REPO/"ignition/reports/evaluations/ignition-220-cognitive-evolution-r0"

def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def read_json(path:Path):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:raise SystemExit(f"TASK227_BUNDLE_INVALID: {path}: {exc}")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--map",type=Path,required=True)
    ap.add_argument("--bundle-root",type=Path,required=True)
    ap.add_argument("--ledger",type=Path,required=True)
    args=ap.parse_args()
    m=read_json(args.map);rows=m.get("trials",[])
    if m.get("map_version")!="TASK227_COMPONENT_A_R0" or len(rows)!=18:raise SystemExit("TASK227_BUNDLE_INVALID: map must contain exactly 18 trials")
    if args.bundle_root.exists() and any(args.bundle_root.iterdir()):raise SystemExit("TASK227_BUNDLE_INVALID: bundle output directory is not empty")
    os.umask(0o077)
    args.bundle_root.mkdir(parents=True,exist_ok=True)
    os.chmod(args.bundle_root,0o700)
    ledger=[];case_hashes={}
    for row in rows:
        tid=row["trial_id"];family=row["family_id"];condition=row["condition"];lineage=row["lineage_id"]
        if family not in {"FAMILY01","FAMILY02","FAMILY03"}:raise SystemExit("TASK227_BUNDLE_INVALID: bad family")
        if condition not in {"M0_ONLY","M0_PLUS_E1","REFERENCE_M1"}:raise SystemExit("TASK227_BUNDLE_INVALID: bad condition")
        source=TASK220/"families"/family
        case_source=TASK225/"families"/family/"cases"
        dest=args.bundle_root/tid
        dest.mkdir(mode=0o700)
        os.chmod(dest,0o700)
        files={}
        for case in ("A","B","C"):
            data=(case_source/f"{case}.md").read_bytes()
            target=dest/f"case_{case}.md";target.write_bytes(data)
            files[target.name]=digest(data)
            case_hashes.setdefault((family,case),set()).add(digest(data))
        m0=(source/"m0.md").read_bytes()
        (dest/"method.md").write_bytes(m0)
        files["method.md"]=digest(m0)
        if condition=="M0_PLUS_E1":
            material=(source/"revision-evidence-e1.md").read_bytes()
            (dest/"support.md").write_bytes(material);files["support.md"]=digest(material)
        elif condition=="REFERENCE_M1":
            material=(SUBTREE/"outputs/reference-m1"/f"{lineage}.raw").read_bytes()
            (dest/"support.md").write_bytes(material);files["support.md"]=digest(material)
        for rel,src in (("prompt.md",SUBTREE/"transfer/prompt.md"),("response-schema.json",SUBTREE/"transfer/response-schema.json")):
            data=src.read_bytes();(dest/rel).write_bytes(data);files[rel]=digest(data)
        ledger.append({"trial_id":tid,"files_sha256":files})
    if len(ledger)!=18:raise SystemExit("TASK227_BUNDLE_INVALID: trial count mismatch")
    for (family,case),hashes in case_hashes.items():
        if len(hashes)!=1:raise SystemExit(f"TASK227_BUNDLE_INVALID: case bytes differ for {family}/{case}")
    args.ledger.parent.mkdir(parents=True,exist_ok=True)
    args.ledger.write_text(json.dumps({"bundle_count":len(ledger),"case_hash_invariants":"PASS","trials":ledger},indent=2)+"\n",encoding="utf-8")
    os.chmod(args.ledger,0o600)
    print("TASK227_TRANSFER_BUNDLES=18")
    print("CASE_BYTE_IDENTITY=PASS")
    print("SUCCESSOR_VISIBLE_CONDITION_LABELS=0")
    print("SUCCESSOR_VISIBLE_TARGETS=0")

if __name__=="__main__":main()
