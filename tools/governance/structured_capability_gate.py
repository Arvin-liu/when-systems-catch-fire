#!/usr/bin/env python3
"""Shared fail-closed engine for evidence-bound structured capability bundles."""
import argparse, hashlib, json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HEAD_RE=re.compile(r"^[0-9a-f]{40}$")

def digest(text): return "sha256:"+hashlib.sha256(text.encode()).hexdigest()
def result(gate,code,name,errors): return {"gate":gate,"exit_code":code,"exit_name":name,"errors":errors,"boundary":"repository candidate only; no external action or truth-layer upgrade"}

def run(config):
    p=argparse.ArgumentParser(); p.add_argument("--bundle",required=True); a=p.parse_args()
    try: b=json.loads(Path(a.bundle).read_text())
    except Exception as exc:
        print(json.dumps(result(config["capability"],2,"SCHEMA_ERROR",[str(exc)]),sort_keys=True)); return 2
    try:
        import jsonschema
        schema=json.loads((ROOT/config["schema"]).read_text()); v=jsonschema.Draft202012Validator(schema)
        errors=[f"{'.'.join(map(str,e.absolute_path)) or '<root>'}: {e.message}" for e in sorted(v.iter_errors(b),key=lambda e:list(e.absolute_path))][:25]
    except ImportError:
        errors=[f"missing {k}" for k in ("task_id","parent_binding","evidence_registry","records","facts","rule_assertions","conclusion") if k not in b]
    if errors:
        code,name=2,"SCHEMA_ERROR"
    elif b["parent_binding"].get("task_id")!=config["parent_id"] or b["parent_binding"].get("exact_head")!=config["parent_head"]:
        code,name,errors=3,"PARENT_BINDING_INVALID",["direct parent task/head mismatch"]
    else:
        evidence={e["evidence_id"]:e for e in b["evidence_registry"]}; errors=[]
        if len(evidence)!=len(b["evidence_registry"]): errors.append("duplicate evidence id")
        for eid,e in evidence.items():
            path=ROOT/e.get("artifact","")
            if not path.is_file() or not HEAD_RE.match(str(e.get("exact_head",""))): errors.append(f"{eid}: artifact/head invalid")
            elif e.get("artifact_digest")!=digest(path.read_text(errors="replace")): errors.append(f"{eid}: digest mismatch")
        for rec in b["records"]:
            for field in config["fields"]:
                for ref in rec[field].get("evidence_refs",[]):
                    if ref not in evidence: errors.append(f"{rec.get('record_id')}.{field}: unknown evidence {ref}")
        if errors: code,name=4,"EVIDENCE_BINDING_INVALID"
        else:
            assertions=b["rule_assertions"]; amap={x["rule_id"]:x for x in assertions}
            if set(amap)!=set(config["rules"]) or len(amap)!=len(assertions):
                code,name,errors=4,"EVIDENCE_BINDING_INVALID",["rule assertion coverage is incomplete or duplicated"]
            else:
                for rid in config["rules"]:
                    if not amap[rid].get("evidence_refs") or any(ref not in evidence for ref in amap[rid].get("evidence_refs",[])):
                        errors.append(f"{rid}: assertion lacks registered evidence")
                if errors: code,name=4,"EVIDENCE_BINDING_INVALID"
                else:
                    code=0; name="GATE_PASS"; errors=[]
                    for i,rid in enumerate(config["rules"]):
                        if b["facts"].get(rid) is not True or amap[rid].get("status")!="PASS":
                            code=5+i; name="RULE_BLOCKED"; errors=[f"{rid}: required fail-closed rule is not satisfied"]; break
                    if code==0:
                        text=(b["conclusion"].get("statement","")+" "+b["conclusion"].get("claim_ceiling","")).lower()
                        if "candidate_only" not in b["conclusion"].get("claim_ceiling","").lower() or not b["conclusion"].get("history_preserved") or any(x.lower() in text for x in config["forbidden_claims"]):
                            code,name,errors=20,"CLAIM_CEILING_OVERREACH",["candidate ceiling or history preservation violated"]
                        elif b["conclusion"].get("external_action_performed"):
                            code,name,errors=21,"EXTERNAL_ACTION_FORBIDDEN",["repository candidate cannot perform external action"]
    print(json.dumps(result(config["capability"],code,name,errors),sort_keys=True)); return code
