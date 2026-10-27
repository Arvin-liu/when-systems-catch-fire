#!/usr/bin/env python3
"""Fail-closed Q39 append-only failure-lineage validator."""
import argparse, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.observation.validate_observation_prediction_gate import _verify_git_binding
SCHEMA = ROOT / "schemas/failure/failure-lineage-contract.schema.json"
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
NAMES = {0:"GATE_PASS",2:"SCHEMA_ERROR",3:"HASH_CHAIN_BROKEN",4:"FAILURE_HISTORY_OVERWRITTEN",5:"CAUSAL_STATUS_OVERCLAIM",6:"UNCONDITIONAL_RETRY",7:"REPAIR_PROPAGATION_MISSING",8:"FAILURE_HAS_NO_PLAN_EFFECT",9:"RETRACTED_CLAIM_DRIVES_ACTION",10:"ENVIRONMENT_AS_THEORY",11:"NEGATIVE_RESULT_LOST",12:"SOURCE_OR_REFERENCE_INVALID",13:"RECURRENCE_OR_CLOSURE_INVALID",14:"CLAIM_CEILING_OVERREACH",15:"TARGET_EFFECT_OR_AUTHORITY_INVALID"}

def digest(value):
    if isinstance(value, str): raw=value.encode()
    else: raw=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return "sha256:"+hashlib.sha256(raw).hexdigest()

def event_digest(event):
    return digest({k:v for k,v in event.items() if k!="event_digest"})

def schema_errors(bundle):
    try:
        import jsonschema
        v=jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text()))
        return [f"{'.'.join(map(str,e.absolute_path)) or '<root>'}: {e.message}" for e in sorted(v.iter_errors(bundle),key=lambda e:list(e.absolute_path))][:25]
    except ImportError:
        return [f"missing {k}" for k in ("events","source_bindings","propagation_targets","conclusion") if k not in bundle]

def check_chain(b):
    errors=[]; previous="GENESIS"
    for index,event in enumerate(b["events"],1):
        if event.get("sequence")!=index: errors.append(f"{event.get('event_id')}: non-contiguous sequence")
        if event.get("previous_event_digest")!=previous: errors.append(f"{event.get('event_id')}: previous digest mismatch")
        if event.get("event_digest")!=event_digest(event): errors.append(f"{event.get('event_id')}: event digest mismatch")
        previous=event.get("event_digest")
    return errors

def check_append_only(b):
    errors=[]
    if b.get("declared_event_count")!=len(b["events"]): errors.append("declared event count differs from retained history")
    ids=[e.get("event_id") for e in b["events"]]
    if len(ids)!=len(set(ids)): errors.append("event ids are not append-only unique")
    for e in b["events"]:
        if e.get("overwrites_event"): errors.append(f"{e.get('event_id')}: repair/closure attempts overwrite")
    return errors

def check_cause(b):
    errors=[]
    for e in b["events"]:
        text=e.get("causal_claim","").lower()
        if any(x in text for x in ("proven cause","established mechanism","causally proven")):
            errors.append(f"{e.get('event_id')}: unknown/candidate cause upgraded to proof")
    return errors

def check_retry(b):
    errors=[]
    for e in b["events"]:
        if e["event_type"]=="FAILURE" and (not e.get("retry_preconditions") or not e.get("prohibited_retry")):
            errors.append(f"{e.get('event_id')}: unchanged retry not blocked")
    return errors

def check_propagation(b):
    targets={t.get("target_id"):t for t in b["propagation_targets"]}; errors=[]
    for e in b["events"]:
        if e["event_type"]!="FAILURE": continue
        for tid in e.get("propagation_target_ids",[]):
            t=targets.get(tid)
            application_ok = bool(t) and (
                (t.get("application_status") == "REQUEST_ONLY" and t.get("applied") is False)
                or (t.get("application_status") == "APPLIED_REPOSITORY_RECORD" and t.get("applied") is True)
            )
            if not t or e["event_id"] not in t.get("event_ids",[]) or not t.get("authorized") or not application_ok:
                errors.append(f"{e['event_id']}: propagation target {tid} absent or unapplied")
        if e.get("repair_event_id") and e["repair_event_id"] not in {x["event_id"] for x in b["events"]}:
            errors.append(f"{e['event_id']}: repair event missing")
    return errors

def check_plan_effect(b):
    target_ids={t["target_id"] for t in b["propagation_targets"] if t.get("plan_effect")}
    return [f"{e['event_id']}: failure does not change a later plan or ceiling" for e in b["events"] if e["event_type"]=="FAILURE" and not (set(e.get("propagation_target_ids",[])) & target_ids)]

def check_retracted(b):
    retracted={c for e in b["events"] if e["event_type"]=="RETRACTION" for c in e.get("affected_claims_actions",[])}
    return [f"retracted claim still drives action: {c}" for c in sorted(retracted & set(b["active_action_claim_refs"]))]

def check_environment(b):
    return [f"{e['event_id']}: environment failure relabeled as theoretical" for e in b["events"] if e.get("environment_origin") and e.get("failure_class")!="ENVIRONMENT"]

def check_negative(b):
    errors=[]
    if not b["conclusion"].get("negative_history_preserved"): errors.append("conclusion does not preserve negative history")
    for e in b["events"]:
        if e["event_type"]=="FAILURE" and not e.get("negative_evidence"): errors.append(f"{e['event_id']}: negative evidence deleted")
        if "missing data only" in e.get("observed_symptom","").lower() and e.get("failure_class")!="DATA": errors.append(f"{e['event_id']}: negative result rewritten and lost")
    return errors

def check_sources(b):
    bindings={x.get("source_id"):x for x in b["source_bindings"]}; errors=[]
    for x in b["source_bindings"]:
        _, binding_error = _verify_git_binding(x.get("binding"))
        if binding_error:
            errors.append(f"{x.get('source_id')}: source binding invalid: {binding_error}")
        elif (x.get("artifact") != x["binding"].get("path") or
              x.get("exact_head") != x["binding"].get("exact_commit") or
              x.get("artifact_digest") != x["binding"].get("sha256")):
            errors.append(f"{x.get('source_id')}: source artifact/head/digest does not match actual Git bytes")
    for e in b["events"]:
        x=bindings.get(e.get("source_binding_id"))
        if not x or e.get("originating_task")!=x.get("task_id") or e.get("originating_artifact")!=x.get("artifact") or e.get("originating_exact_head")!=x.get("exact_head"):
            errors.append(f"{e.get('event_id')}: origin binding mismatch")
    return errors

def check_target_effects(b):
    errors=[]
    for target in b["propagation_targets"]:
        tid=target.get("target_id")
        _, target_error=_verify_git_binding(target.get("target_binding"))
        if target_error:
            errors.append(f"{tid}: target binding invalid: {target_error}")
        elif (target.get("target_artifact") != target["target_binding"].get("path") or
              target.get("verification_digest") != target["target_binding"].get("sha256")):
            errors.append(f"{tid}: verification digest does not match actual target bytes")

        auth_bytes, auth_error=_verify_git_binding(target.get("authorization_binding"))
        if auth_error:
            errors.append(f"{tid}: authorization binding invalid: {auth_error}")
        else:
            try: auth=json.loads(auth_bytes)
            except (TypeError,json.JSONDecodeError): auth={}
            grants={x.get("grant_id"):x for x in auth.get("grants",[])}
            actions={x.get("action_id"):x for x in auth.get("actions",[])}
            grant=grants.get(target.get("authority_grant_id")); action=actions.get(target.get("authority_action_id"))
            if (target.get("authorization_status") != "VERIFIED_REPOSITORY_GRANT" or
                not grant or grant.get("status") != "active" or grant.get("revoked") is not False or
                not action or action.get("grant_id") != target.get("authority_grant_id") or
                action.get("initiator") != target.get("authority_actor_id")):
                errors.append(f"{tid}: authorization is not supported by canonical grant/action bytes")

        effect_bytes, effect_error=_verify_git_binding(target.get("effect_binding"))
        if effect_error:
            errors.append(f"{tid}: effect binding invalid: {effect_error}")
            effect={}
        else:
            try:
                effect_doc=json.loads(effect_bytes)
                effect=next((x for x in effect_doc.get("effects",[]) if x.get("effect_id")==target.get("effect_id")),{})
            except (TypeError,json.JSONDecodeError): effect={}
        expected={
            "target_id":tid,"event_ids":target.get("event_ids"),"target_artifact":target.get("target_artifact"),
            "plan_effect":target.get("plan_effect"),"application_status":target.get("application_status")
        }
        if not effect or any(effect.get(key)!=value for key,value in expected.items()):
            errors.append(f"{tid}: declared effect does not match the bound structured effect record")
        elif (effect.get("authorization",{}).get("actor_id") != target.get("authority_actor_id") or
              effect.get("authorization",{}).get("grant_id") != target.get("authority_grant_id") or
              effect.get("authorization",{}).get("action_id") != target.get("authority_action_id")):
            errors.append(f"{tid}: effect authority does not match canonical authority fields")

        if target.get("plan_effect")=="INTERVENE":
            if target.get("application_status")!="REQUEST_ONLY" or target.get("applied") is not False or not effect.get("high_risk"):
                errors.append(f"{tid}: high-risk intervention effect must remain request-only")
        elif target.get("application_status")=="APPLIED_REPOSITORY_RECORD" and target.get("applied") is not True:
            errors.append(f"{tid}: applied boolean disagrees with structured repository-record status")
        if target.get("authorized") is not True:
            errors.append(f"{tid}: authorized boolean disagrees with verified structured authority")
    return errors

def check_recurrence_closure(b):
    events={e["event_id"]:e for e in b["events"]}; signatures={r["signature_id"]:r for r in b["recurrence_signatures"]}; errors=[]
    for e in b["events"]:
        r=signatures.get(e.get("recurrence_signature_id"))
        if not r or e["event_id"] not in r.get("event_ids",[]): errors.append(f"{e['event_id']}: recurrence signature missing")
        sup=e.get("supersedes_event_id")
        if sup and sup not in events: errors.append(f"{e['event_id']}: supersedes missing event")
        if e.get("closure_status")=="CLOSED" and e.get("unresolved_residue"): errors.append(f"{e['event_id']}: closed event retains unresolved residue")
    if len(signatures)!=len(b["recurrence_signatures"]): errors.append("duplicate recurrence signature")
    return errors

def check_ceiling(b):
    text=(b["conclusion"].get("claim_ceiling","")+" "+b["conclusion"].get("statement","")).lower()
    if not b["conclusion"].get("failures_change_future_plans") or any(x in text for x in ("universal truth","mechanism proven","causal proof")):
        return ["failure lineage conclusion exceeds repository candidate ceiling"]
    return []

CHECKS=[(3,check_chain),(4,check_append_only),(5,check_cause),(6,check_retry),(7,check_propagation),(8,check_plan_effect),(9,check_retracted),(10,check_environment),(11,check_negative),(12,check_sources),(15,check_target_effects),(13,check_recurrence_closure),(14,check_ceiling)]

def main():
    p=argparse.ArgumentParser(); p.add_argument("--bundle",required=True); a=p.parse_args()
    try: b=json.loads(Path(a.bundle).read_text())
    except Exception as exc:
        print(json.dumps({"gate":"q39_failure_lineage","exit_code":2,"exit_name":NAMES[2],"errors":[str(exc)]})); return 2
    errors=schema_errors(b)
    if errors: code=2
    else:
        code=0
        for candidate,fn in CHECKS:
            errors=fn(b)
            if errors: code=candidate; break
    print(json.dumps({"gate":"q39_failure_lineage","exit_code":code,"exit_name":NAMES[code],"errors":errors,"boundary":"append-only repository lineage; no causal proof or external retry"},sort_keys=True))
    return code

if __name__=="__main__": sys.exit(main())
