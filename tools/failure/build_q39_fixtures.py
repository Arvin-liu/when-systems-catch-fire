#!/usr/bin/env python3
"""Build deterministic Q39 pilot and attack fixtures."""
import copy, hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"data/failure/fixtures"
PILOT=ROOT/"data/failure/pilot-q39-failure-lineage.json"
HEADS={"q36":"e4ca5350a3c68e61031e3205eaca9f2665799a08","q37":"7a01b1958c3f6b6eff559be85ec5e47eecff313c","q38":"d5cf0f0846206d3c47463f66697d2d8bf7d4aca3","q39":"824ff7f713303b18bca94b05de3f4b6530ffff51"}
AUTH_COMMIT="167f254e637259d57b7ce09623de982dda527f54"
AUTH_PATH="data/agent/pilot-q34-pr-controlled-op.json"
EFFECT_COMMIT="cdfb20ae8219432275dc5cc356c5516a1190414c"
EFFECT_PATH="data/failure/q39-repair-effect-records.json"

def digest(value):
    raw=value.encode() if isinstance(value,str) else json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return "sha256:"+hashlib.sha256(raw).hexdigest()

def git_binding(path,head):
    raw=subprocess.check_output(["git","show",f"{head}:{path}"],cwd=ROOT)
    blob=subprocess.check_output(["git","rev-parse",f"{head}:{path}"],cwd=ROOT,text=True).strip()
    return {"path":path,"exact_commit":head,"git_blob":blob,"sha256":"sha256:"+hashlib.sha256(raw).hexdigest()}

def source(sid,task,path,head):
    binding=git_binding(path,head)
    return {"source_id":sid,"task_id":task,"artifact":path,"exact_head":head,"artifact_digest":binding["sha256"],"binding":binding}

def target(tid,event_ids,path,effect,application_status,head):
    target_binding=git_binding(path,head)
    return {"target_id":tid,"event_ids":event_ids,"target_artifact":path,"plan_effect":effect,
            "authorized":True,"applied":application_status=="APPLIED_REPOSITORY_RECORD",
            "verification_digest":target_binding["sha256"],
            "authorization_status":"VERIFIED_REPOSITORY_GRANT",
            "authorization_binding":git_binding(AUTH_PATH,AUTH_COMMIT),
            "authority_actor_id":"q35-builder","authority_grant_id":"grant-q34-pilot","authority_action_id":"act-q34-pilot",
            "application_status":application_status,"target_binding":target_binding,
            "effect_id":"effect."+tid,"effect_binding":git_binding(EFFECT_PATH,EFFECT_COMMIT)}

def rechain(b):
    prev="GENESIS"
    for i,e in enumerate(b["events"],1):
        e["sequence"]=i; e["previous_event_digest"]=prev; e.pop("event_digest",None); e["event_digest"]=digest(e); prev=e["event_digest"]
    return b

def event(eid,kind,klass,sid,task,path,head,symptom,neg,target,rec,env=False):
    return {"event_id":eid,"sequence":0,"event_type":kind,"failure_class":klass,"source_binding_id":sid,"originating_task":task,"originating_artifact":path,"originating_exact_head":head,"observed_symptom":symptom,"causal_status":"NOT_ESTABLISHED","causal_claim":"cause not established; preserve competing explanations","negative_evidence":[neg],"affected_claims_actions":["q37.restricted_seed"],"retry_preconditions":["new independent evidence or changed authorized scope"],"prohibited_retry":["repeat unchanged action and discard the failure"],"repair_proposal":"propagate failure into the next bounded plan","repair_event_id":None,"propagation_target_ids":[target],"recurrence_signature_id":rec,"supersedes_event_id":None,"closure_status":"OPEN","unresolved_residue":["real-world cause remains unidentified"],"claim_ceiling_impact":"HOLD","environment_origin":env,"overwrites_event":False,"previous_event_digest":"","event_digest":""}

def base():
    q36="data/intervention/pilot-controlled-intervention.json"; q37="data/analogy/pilot-real-repo-analogy-audit.json"; q38="data/retrieval/pilot-q38-repository-evidence-retrieval.json"
    events=[
      event("fail.q36.rollback","ROLLBACK","EXECUTION","src.q36","121Q36-INT-I1",q36,HEADS["q36"],"controlled rollback retained residual","intervention residual","target.intervention","rec.execution"),
      event("fail.q37.mismatch","FAILURE","MECHANISM","src.q37","121Q37-I1",q37,HEADS["q37"],"analogy mismatch blocks mechanism upgrade","counteranalogy retained","target.analogy","rec.mechanism"),
      event("fail.q38.counterexample","FAILURE","SCOPE","src.q38","121Q38-I1",q38,HEADS["q38"],"counterexample limits transportability","ev.counter.q36","target.search","rec.scope"),
      event("fail.q38.negative","RETRACTION","MODEL","src.q38","121Q38-I1",q38,HEADS["q38"],"negative result retracts broad candidate","ev.negative.external-validity","target.ceiling","rec.model"),
      event("fail.q38.environment","FAILURE","ENVIRONMENT","src.q38","121Q38-I1",q38,HEADS["q38"],"external retrieval deliberately unperformed","ev.failed.external-search","target.defer","rec.environment",True),
      event("repair.q39.plan","REPAIR","SCOPE","src.q38","121Q38-I1",q38,HEADS["q38"],"repair appends bounded downstream plan effects","all prior failures retained","target.search","rec.scope")
    ]
    events[2]["repair_event_id"]="repair.q39.plan"; events[5]["supersedes_event_id"]="fail.q38.counterexample"; events[5]["closure_status"]="REPAIRED_WITH_RESIDUE"
    recs=[]
    for rid in ["rec.execution","rec.mechanism","rec.scope","rec.model","rec.environment"]:
        ids=[e["event_id"] for e in events if e["recurrence_signature_id"]==rid]
        recs.append({"signature_id":rid,"signature_digest":digest("|".join(ids)),"event_ids":ids,"repeat_policy":"BLOCK_UNCHANGED_RETRY"})
    targets=[
      target("target.intervention",["fail.q36.rollback"],q36,"INTERVENE","REQUEST_ONLY",HEADS["q36"]),
      target("target.analogy",["fail.q37.mismatch"],q37,"ANALOGY_AUDIT","APPLIED_REPOSITORY_RECORD",HEADS["q37"]),
      target("target.search",["fail.q38.counterexample","repair.q39.plan"],q38,"SEARCH","APPLIED_REPOSITORY_RECORD",HEADS["q38"]),
      target("target.ceiling",["fail.q38.negative"],"docs/failure/q39-interfaces.md","CLAIM_CEILING_CHANGE","APPLIED_REPOSITORY_RECORD",HEADS["q39"]),
      target("target.defer",["fail.q38.environment"],"docs/failure/q39-interfaces.md","DEFER","APPLIED_REPOSITORY_RECORD",HEADS["q39"])
    ]
    b={"contract_version":"1.0.0","task_id":"121Q39-I1","lineage_id":"q39.pilot.q36-q38","declared_event_count":len(events),"source_bindings":[source("src.q36","121Q36-INT-I1",q36,HEADS["q36"]),source("src.q37","121Q37-I1",q37,HEADS["q37"]),source("src.q38","121Q38-I1",q38,HEADS["q38"])],"events":events,"recurrence_signatures":recs,"propagation_targets":targets,"unresolved_residue":["no external population validity","environment retrieval remains unperformed"],"active_action_claim_refs":[],"conclusion":{"statement":"Failures remain append-only and deterministically change bounded later plans without establishing their causes.","negative_history_preserved":True,"failures_change_future_plans":True,"claim_ceiling":"candidate_only_repository_failure_lineage"}}
    return rechain(b)

def mutate(b,n):
    if n==2: b.pop("source_bindings")
    elif n==3: b["events"][1]["previous_event_digest"]="sha256:"+"0"*64; return b
    elif n in (4,15): b["events"][5]["overwrites_event"]=True
    elif n in (5,16): b["events"][1]["causal_claim"]="established mechanism"
    elif n in (6,17): b["events"][1]["retry_preconditions"]=[]
    elif n==7: b["propagation_targets"][1]["applied"]=False
    elif n==18: b["events"][1]["propagation_target_ids"]=["missing.target"]
    elif n in (8,19): b["events"][1]["propagation_target_ids"]=[]
    elif n in (9,20): b["active_action_claim_refs"]=["q37.restricted_seed"]
    elif n in (10,21): b["events"][4]["failure_class"]="MODEL"
    elif n==11: b["events"][2]["negative_evidence"]=[]
    elif n==22: b["events"][1]["negative_evidence"]=[]
    elif n==12: b["events"][2]["originating_exact_head"]="0"*40
    elif n==23: b["events"][2]["source_binding_id"]="missing.source"
    elif n==13: b["events"][5]["supersedes_event_id"]="missing.event"
    elif n==24: b["events"][2]["closure_status"]="CLOSED"
    elif n==14: b["conclusion"]["claim_ceiling"]="universal truth and mechanism proven"
    elif n==25:
        t=b["propagation_targets"][0]; t["target_artifact"]="data/failure/nonexistent/claimed-applied-target.json"; t["target_binding"]={"path":t["target_artifact"],"exact_commit":"f"*40,"git_blob":"f"*40,"sha256":"sha256:"+"0"*64}; t["verification_digest"]="sha256:"+"0"*64; t["application_status"]="APPLIED_REPOSITORY_RECORD"; t["applied"]=True
    elif n==26:
        t=b["propagation_targets"][1]; t["target_binding"]["sha256"]="sha256:"+"1"*64; t["verification_digest"]="sha256:"+"1"*64
    elif n==27:
        t=b["propagation_targets"][1]; t["target_binding"]["exact_commit"]="f"*40
    elif n==28:
        b["propagation_targets"][1]["effect_binding"]["sha256"]="sha256:"+"1"*64
    elif n==29:
        b["propagation_targets"][1]["authority_grant_id"]="grant-fictional"
    elif n==30:
        b["propagation_targets"][0]["applied"]=True
    return rechain(b)

def main():
    OUT.mkdir(parents=True,exist_ok=True); b=base(); PILOT.parent.mkdir(parents=True,exist_ok=True); PILOT.write_text(json.dumps(b,indent=2,ensure_ascii=False)+"\n")
    names={1:"valid-pilot",2:"schema-missing-sources",3:"hash-chain-broken",4:"history-overwritten",5:"causal-overclaim",6:"unconditional-retry",7:"repair-unapplied",8:"failure-no-plan-effect",9:"retracted-drives-action",10:"environment-as-model",11:"negative-deleted",12:"exact-head-mismatch",13:"supersession-missing",14:"ceiling-overreach",15:"success-overwrites-failure",16:"unknown-cause-proven",17:"repeat-unchanged-action",18:"propagation-target-missing",19:"failure-archived-only",20:"retracted-action-reused",21:"environment-theory-failure",22:"negative-rewritten-missing",23:"source-binding-missing",24:"closed-with-residue",25:"nonexistent-target-zero-digest-boolean-bypass",26:"target-actual-byte-digest-mismatch",27:"target-wrong-exact-head",28:"effect-record-digest-mismatch",29:"fictional-authority-grant",30:"request-only-boolean-applied"}
    for n,name in names.items():
        value=copy.deepcopy(b) if n==1 else mutate(copy.deepcopy(b),n)
        (OUT/f"{n:02d}-{name}.json").write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"pilot":str(PILOT.relative_to(ROOT)),"fixtures":len(names)},sort_keys=True))

if __name__=="__main__": main()
