#!/usr/bin/env python3
"""Validate 076 registries without optional third-party dependencies."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
checks=[]

def check(name, ok, detail=""):
    checks.append((name,bool(ok),detail))

def load(rel):
    p=ROOT/rel
    rows=[]
    if p.exists():
        rows=[json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    return rows

def main():
    objects=load("data/foundation/formal-objects/objects.jsonl")
    claims=load("data/foundation/claims/claims.jsonl")
    args=load("data/foundation/arguments/arguments.jsonl")
    evidence=load("data/foundation/evidence/evidence.jsonl")
    maps=load("data/foundation/mappings/legacy-mappings.jsonl")
    obligations=load("data/foundation/proofs/obligations.jsonl")
    validations=load("data/foundation/validations/records.jsonl")
    counterexamples=load("data/foundation/validations/counterexamples.jsonl")
    expected={"objects":622,"claims":678,"arguments":678,"evidence":828,"mappings":622,"obligations":622,"validations":6,"counterexamples":2}
    actual={"objects":len(objects),"claims":len(claims),"arguments":len(args),"evidence":len(evidence),"mappings":len(maps),"obligations":len(obligations),"validations":len(validations),"counterexamples":len(counterexamples)}
    for k,n in expected.items(): check(f"count:{k}",actual[k]==n,f"expected={n} actual={actual[k]}")
    for name,rows in [("objects",objects),("claims",claims),("arguments",args),("evidence",evidence)]:
        keys=[x.get("entity_key") for x in rows]
        check(f"unique:{name}",len(keys)==len(set(keys)),f"rows={len(keys)} unique={len(set(keys))}")
    ids={x["entity_key"] for x in objects}
    check("refs:claims-to-objects",all(x.get("object_ref") in ids for x in claims if x.get("object_ref")))
    claim_ids={x["entity_key"] for x in claims}
    check("refs:arguments-to-claims",all(x.get("claim_ref") in claim_ids for x in args))
    axes={"workflow_status","semantic_status","formal_status","logic_status","proof_status","evidence_status","scope_status","provenance_status","migration_status"}
    check("status:nine-axes",all(axes==set(x["status"]) for x in claims))
    check("taxonomy:mf",{x["id"] for x in objects if x["id"].startswith("MF")}=={"MF1","MF2","MF3","MF4","MF5"})
    check("taxonomy:y1",sum(x["id"]=="Y1" for x in objects)==1)
    minimum={"stable_id","legacy_id","title","source_paths","provenance_status","original_natural_language_claim","controlled_semantic_proposition","claim_type","formal_object_type","typed_variables","domain","codomain_or_target_type","units_or_dimensions","parameters","assumptions","formal_expression_or_ast","scope_boundary_stopping_condition","known_counterexamples","dependencies","proof_obligations","proof_artifacts","related_cases","status","unresolved_blockers"}
    check("objects:minimum-record",all(minimum <= set(x) for x in objects))
    check("gate:no-unproved-theorem",all(x.get("formal_object_type")!="THEOREM" for x in objects))
    required_ce={"target_claim","domain","assumptions","input","derivation","violated_conclusion","source","replay","expected_result"}
    check("counterexample:replay-contract",all(required_ce <= set(x) for x in counterexamples))
    legacy_diff=subprocess.run(["git","diff","--quiet","--","统一函数总表","统一案例总表"],cwd=ROOT).returncode
    check("migration:legacy-byte-preservation",legacy_diff==0)
    check("schemas:count",len(list((ROOT/"schemas/foundation").glob("*.json")))>=7)
    required=["ARCHITECTURE.md","FOUNDATION.md","AI-START-HERE.md","AI-HANDOFF.md",".github/workflows/foundation-validation.yml","formal/lean/Foundation.lean","views/manifest.json","data/foundation/project-state.json"]
    for rel in required: check(f"file:{rel}",(ROOT/rel).is_file())
    check("generator:deterministic",subprocess.run([sys.executable,"tools/foundation/migrate_legacy.py","--check"],cwd=ROOT,stdout=subprocess.DEVNULL).returncode==0)
    for name,ok,detail in checks:
        print(("PASS" if ok else "FAIL")+" "+name+(" "+detail if detail else ""))
    passed=sum(x[1] for x in checks)
    print(f"CHECKS_TOTAL={len(checks)} CHECKS_PASSED={passed} CHECKS_FAILED={len(checks)-passed}")
    if passed==len(checks):
        print("ALL_FOUNDATION_VALID")
        return 0
    return 1

if __name__=="__main__": raise SystemExit(main())
