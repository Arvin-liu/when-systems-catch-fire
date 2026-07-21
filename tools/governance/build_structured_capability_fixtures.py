#!/usr/bin/env python3
"""Shared deterministic fixture builder for structured capability gates."""
import copy, hashlib, json
from pathlib import Path

def digest(text): return "sha256:"+hashlib.sha256(text.encode()).hexdigest()
def dump(path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n")

def build(config,root):
    evidence=[]
    for i,path in enumerate(config["sources"],1):
        p=root/path
        evidence.append({"evidence_id":f"evidence.{i}","artifact":path,"exact_head":config["parent_head"],"artifact_digest":digest(p.read_text(errors="replace")),"rights_status":"REPOSITORY_INTERNAL"})
    records=[]
    for i,rtype in enumerate(config["record_types"],1):
        rec={"record_id":f"record.{i}","record_type":rtype}
        for j,field in enumerate(config["fields"]):
            rec[field]={"status":"RECORDED","value":f"bounded {field} for {rtype}","evidence_refs":[f"evidence.{1+(j%len(evidence))}"]}
        records.append(rec)
    b={"contract_version":"1.0.0","task_id":config["task_id"],"capability_id":config["capability"],"parent_binding":{"task_id":config["parent_id"],"exact_head":config["parent_head"]},"evidence_registry":evidence,"records":records,"facts":{r:True for r in config["rules"]},"rule_assertions":[{"rule_id":r,"status":"PASS","evidence_refs":[f"evidence.{1+(i%len(evidence))}"],"effect":"ALLOW_WITHIN_CEILING"} for i,r in enumerate(config["rules"])],"conclusion":{"statement":config["conclusion"],"claim_ceiling":"candidate_only_repository_governance","history_preserved":True,"external_action_performed":False}}
    pilot=root/config["pilot_path"]; dump(pilot,b)
    out=root/config["fixtures_path"]; out.mkdir(parents=True,exist_ok=True)
    cases=[(1,"valid",0,None),(2,"schema",2,"schema"),(3,"parent",3,"parent"),(4,"evidence",4,"evidence")]
    for n in range(5,23): cases.append((n,f"rule-{config['rules'][(n-5)%len(config['rules'])]}",5+((n-5)%len(config['rules'])),("rule",(n-5)%len(config['rules']))))
    cases += [(23,"ceiling",20,"ceiling"),(24,"external-action",21,"external")]
    for n,name,expected,mutation in cases:
        x=copy.deepcopy(b)
        if mutation=="schema": x.pop("task_id")
        elif mutation=="parent": x["parent_binding"]["exact_head"]="0"*40
        elif mutation=="evidence": x["evidence_registry"][0]["artifact_digest"]="sha256:"+"0"*64
        elif isinstance(mutation,tuple):
            rid=config["rules"][mutation[1]]; x["facts"][rid]=False
        elif mutation=="ceiling": x["conclusion"]["claim_ceiling"]="universal truth and causal proof"
        elif mutation=="external": x["conclusion"]["external_action_performed"]=True
        dump(out/f"{n:02d}-{name}-exit{expected:02d}.json",x)
    print(json.dumps({"task_id":config["task_id"],"fixtures":24,"pilot":config["pilot_path"]},sort_keys=True))
