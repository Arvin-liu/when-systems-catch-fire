#!/usr/bin/env python3
"""Fail-closed structural and cross-reference validator for Task227 M1 policies."""
from __future__ import annotations
import argparse, json
from pathlib import Path
try:
    from jsonschema import Draft202012Validator
except ImportError as exc:
    raise SystemExit("TASK227_POLICY_INVALID: jsonschema 4.x is required by the official policy validator") from exc

REPO=Path(__file__).resolve().parents[5]
SUBTREE=REPO/"ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0"
SCHEMA_PATH=SUBTREE/"reference/policy-schema.json"
FAMILIES={"FAMILY01","FAMILY02","FAMILY03"}
OPS={"eq","neq","lt","lte","gt","gte","in","not_in","between","present","absent","stable","complete","reproducible","matches"}
CATEGORIES={"KEEP_BASELINE","APPLY_EVIDENCE_RULE","COLLECT_MEASUREMENT","REPEAT_OR_REACQUIRE","ROUTE_FOR_REVIEW","RECONCILE","UNSCORABLE","REPORT","OTHER"}

def fail(msg:str)->None:raise SystemExit("TASK227_POLICY_INVALID: "+msg)
def load(path:Path):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:fail(f"invalid JSON {path}: {exc}")
def obj(v,w):
    if not isinstance(v,dict):fail(f"{w} must be object")
    return v
def arr(v,w,nonempty=True):
    if not isinstance(v,list) or (nonempty and not v):fail(f"{w} must be {'nonempty ' if nonempty else ''}array")
    return v
def string(v,w):
    if not isinstance(v,str) or not v.strip():fail(f"{w} must be nonempty string")
    return v
def exact(v,keys,w):
    obj(v,w)
    if set(v)!=set(keys):fail(f"{w} keys mismatch: expected {sorted(keys)} got {sorted(v)}")
def unique(v,w):
    if len(v)!=len(set(v)):fail(f"{w} IDs must be unique")
def typed(value,kind):
    return (kind=="number" and isinstance(value,(int,float)) and not isinstance(value,bool)) or (kind=="string" and isinstance(value,str)) or (kind=="boolean" and isinstance(value,bool))

def verify_schema():
    schema=load(SCHEMA_PATH)
    try:Draft202012Validator.check_schema(schema)
    except Exception as exc:fail(f"policy JSON Schema is invalid: {exc}")
    req={"policy_id","evidence_basis","selector","applicability","action_table","preserved_rules","fallback","stop_conditions","scope_ceiling","provenance"}
    if set(schema.get("required",[]))!=req:fail("schema top-level required fields mismatch")
    if not {"condition","input","scopeClaim","provenance"}.issubset(schema.get("$defs",{})):fail("schema lacks typed field definitions")
    print("TASK227_POLICY_SCHEMA=PASS")

def verify_policy(path:Path,family:str|None):
    p=obj(load(path),path.name)
    try:Draft202012Validator(load(SCHEMA_PATH)).validate(p)
    except Exception as exc:fail(f"{path.name} fails policy JSON Schema validation: {exc}")
    exact(p,{"policy_id","evidence_basis","selector","applicability","action_table","preserved_rules","fallback","stop_conditions","scope_ceiling","provenance"},path.name)
    string(p["policy_id"],"policy_id")
    evidence=arr(p["evidence_basis"],"evidence_basis")
    evidence_ids=[]
    for i,e in enumerate(evidence):
        exact(e,{"evidence_id","source_type","source_locator","supports","claim_type"},f"evidence_basis[{i}]")
        evidence_ids.append(string(e["evidence_id"],"evidence_id"))
        if e["source_type"] not in {"M0","E1"}:fail("source_type must be M0 or E1")
        string(e["source_locator"],"source_locator");string(e["supports"],"evidence support")
        if e["claim_type"] not in {"observed","derived","method_rule"}:fail("claim_type unsupported")
    unique(evidence_ids,"evidence")
    by_evidence={e["evidence_id"]:e for e in evidence}
    def refs(values,where,source_type=None):
        values=arr(values,where)
        for x in values:
            if x not in by_evidence:fail(f"{where} references unknown evidence {x}")
            if source_type and by_evidence[x]["source_type"]!=source_type:fail(f"{where} must reference {source_type}")
        return values
    selector=obj(p["selector"],"selector")
    exact(selector,{"required_inputs","rule"},"selector")
    inputs=arr(selector["required_inputs"],"required_inputs")
    input_ids=[]
    for i,x in enumerate(inputs):
        exact(x,{"input_id","description","value_type","unit","source_refs"},f"required_inputs[{i}]")
        input_ids.append(string(x["input_id"],"input_id"));string(x["description"],"input description")
        if x["value_type"] not in {"number","string","boolean"}:fail("input value_type unsupported")
        if x["unit"] is not None and not isinstance(x["unit"],str):fail("input unit must be string/null")
        refs(x["source_refs"],f"input {x['input_id']} source_refs")
    unique(input_ids,"input")
    by_input={x["input_id"]:x for x in inputs}
    def check_condition(c,where):
        exact(c,{"input_id","operator","value","unit"},where)
        iid=string(c["input_id"],where+" input_id")
        if iid not in by_input:fail(f"{where} uses undeclared input {iid}")
        inp=by_input[iid];op=c["operator"];value=c["value"]
        if op not in OPS:fail(f"{where} has unsupported operator {op}")
        if c["unit"]!=inp["unit"]:fail(f"{where} unit differs from input declaration")
        kind=inp["value_type"]
        if op in {"present","absent","stable","complete","reproducible"}:
            if value is not None:fail(f"{where} {op} requires null value")
        elif op=="between":
            if kind!="number" or not isinstance(value,list) or len(value)!=2 or any(not typed(v,"number") for v in value) or value[0]>value[1]:
                fail(f"{where} between requires two ordered numbers")
        elif op in {"in","not_in"}:
            if not isinstance(value,list) or not value or any(not typed(v,kind) for v in value):fail(f"{where} {op} values must match declared input type")
        elif op=="matches":
            if kind!="string" or not isinstance(value,str) or not value:fail(f"{where} matches requires a nonempty string input pattern")
        else:
            if not typed(value,kind):fail(f"{where} value does not match declared input type {kind}")
            if op in {"lt","lte","gt","gte"} and kind!="number":fail(f"{where} numeric comparison requires number input")
    def conds(values,where,allow_empty=False):
        for i,c in enumerate(arr(values,where,not allow_empty)):check_condition(c,f"{where}[{i}]")
    rules=arr(selector["rule"],"selector.rule")
    rule_ids=[]
    for i,r in enumerate(rules):
        exact(r,{"rule_id","when","action_ref"},f"selector.rule[{i}]")
        rule_ids.append(string(r["rule_id"],"rule_id"));conds(r["when"],f"selector.rule[{i}].when")
    unique(rule_ids,"selector rule")
    actions=arr(p["action_table"],"action_table")
    action_ids=[];by_action={}
    for i,a in enumerate(actions):
        exact(a,{"action_id","when","action","required_report_fields","evidence_refs"},f"action_table[{i}]")
        aid=string(a["action_id"],"action_id");action_ids.append(aid);by_action[aid]=a
        conds(a["when"],f"action {aid}.when")
        spec=obj(a["action"],f"action {aid}")
        exact(spec,{"category","name","parameters"},f"action {aid}")
        if spec["category"] not in CATEGORIES:fail(f"action category invalid for {aid}")
        string(spec["name"],f"action name {aid}")
        for j,param in enumerate(arr(spec["parameters"],f"action {aid}.parameters",False)):
            exact(param,{"name","value"},f"action {aid}.parameter[{j}]");string(param["name"],"parameter name")
        refs(a["evidence_refs"],f"action {aid} evidence_refs")
        for j,f in enumerate(arr(a["required_report_fields"],f"action {aid}.required_report_fields")):
            exact(f,{"field_id","description","unit","evidence_refs"},f"report field {aid}[{j}]")
            string(f["field_id"],"field_id");string(f["description"],"report field description")
            if f["unit"] is not None and not isinstance(f["unit"],str):fail("report field unit must be string/null")
            refs(f["evidence_refs"],f"report field {aid} evidence_refs")
    unique(action_ids,"action")
    action_refs=[r["action_ref"] for r in rules]
    if len(rules)!=len(actions) or len(action_refs)!=len(set(action_refs)) or set(action_refs)!=set(action_ids):
        fail("selector and action mappings must be one-to-one")
    for r in rules:
        if r["when"]!=by_action[r["action_ref"]]["when"]:fail(f"selector/action conditions differ for {r['action_ref']}")
    app=obj(p["applicability"],"applicability")
    exact(app,{"licensed_region","out_of_scope"},"applicability")
    licensed=arr(app["licensed_region"],"licensed_region");outside=arr(app["out_of_scope"],"out_of_scope")
    licensed_ids=[];outside_ids=[];mapped_rules=[]
    for i,r in enumerate(licensed):
        exact(r,{"region_id","conditions","rule_refs"},f"licensed_region[{i}]")
        licensed_ids.append(string(r["region_id"],"region_id"));conds(r["conditions"],f"licensed region {r['region_id']}")
        region_rule_refs=arr(r["rule_refs"],"rule_refs")
        if len(region_rule_refs)!=1 or region_rule_refs[0] not in set(rule_ids):fail(f"licensed region {r['region_id']} must reference exactly one known selector rule")
        rule=next(item for item in rules if item["rule_id"]==region_rule_refs[0])
        if r["conditions"]!=rule["when"]:fail(f"licensed region {r['region_id']} conditions differ from referenced selector rule")
        mapped_rules.append(region_rule_refs[0])
    unique(mapped_rules,"licensed-region selector mapping")
    if set(mapped_rules)!=set(rule_ids):fail("every selector rule must map to exactly one licensed region")
    for i,r in enumerate(outside):
        exact(r,{"region_id","conditions","fallback_ref"},f"out_of_scope[{i}]")
        outside_ids.append(string(r["region_id"],"region_id"));conds(r["conditions"],f"out-of-scope region {r['region_id']}",True)
        if r["fallback_ref"]!="fallback":fail(f"out-of-scope region {r['region_id']} must route to fallback")
    all_regions=licensed_ids+outside_ids;unique(all_regions,"applicability region")
    empty_outside=[r for r in outside if not r["conditions"]]
    if empty_outside and len(outside)!=1:fail("an empty out-of-scope condition list denotes the entire complement and must be the sole out-of-scope region")
    preserved=arr(p["preserved_rules"],"preserved_rules");pres_ids=[]
    for i,r in enumerate(preserved):
        exact(r,{"preservation_id","when","baseline_action","preservation_mode","m0_action_retired","evidence_refs"},f"preserved_rules[{i}]")
        pres_ids.append(string(r["preservation_id"],"preservation_id"));conds(r["when"],f"preserved rule {r['preservation_id']}",True)
        string(r["baseline_action"],"baseline_action")
        mode=r["preservation_mode"]
        if mode not in {"unconditional","selector_miss","additive_coexistence"}:fail("preservation mode invalid")
        if mode in {"unconditional","selector_miss"} and r["when"]:fail(f"preserved rule {r['preservation_id']} must have an empty when list for {mode} coverage")
        if mode=="additive_coexistence" and (not r["when"] or not any(rule["when"]==r["when"] for rule in rules)):
            fail(f"preserved rule {r['preservation_id']} additive_coexistence must match a selector rule condition set")
        if r["m0_action_retired"] is not False:fail("M0 retirement is prohibited")
        refs(r["evidence_refs"],"preserved-rule evidence_refs","M0")
    unique(pres_ids,"preserved rule")
    fb=obj(p["fallback"],"fallback")
    exact(fb,{"when","action","evidence_refs"},"fallback");conds(fb["when"],"fallback.when",True)
    if fb["when"]:
        fail("fallback.when must be [] to declare unconditional coverage of every out-of-scope or unresolved input")
    fa=obj(fb["action"],"fallback.action")
    exact(fa,{"outcome","instruction","required_report_fields"},"fallback action")
    if fa["outcome"] not in {"REACQUIRE","RECONCILE","UNSCORABLE","SAFE_HOLD","ROUTE_TO_M0","OTHER"}:fail("fallback outcome invalid")
    string(fa["instruction"],"fallback instruction");arr(fa["required_report_fields"],"fallback report fields");refs(fb["evidence_refs"],"fallback evidence refs")
    stops=arr(p["stop_conditions"],"stop_conditions");stop_ids=[]
    for i,x in enumerate(stops):
        exact(x,{"stop_id","when","outcome","instruction"},f"stop_conditions[{i}]")
        stop_ids.append(string(x["stop_id"],"stop_id"));conds(x["when"],f"stop {x['stop_id']}.when")
        if x["outcome"] not in {"STOP","UNSCORABLE","RECONCILE","REACQUIRE","ESCALATE"}:fail("stop outcome invalid")
        string(x["instruction"],"stop instruction")
    unique(stop_ids,"stop")
    ceiling=obj(p["scope_ceiling"],"scope_ceiling")
    exact(ceiling,{"licensed_claims","not_established","statement"},"scope ceiling")
    claim_ids=[];lic_claim_ids=[];not_claim_ids=[]
    for key,ids in (("licensed_claims",lic_claim_ids),("not_established",not_claim_ids)):
        for i,c in enumerate(arr(ceiling[key],key)):
            exact(c,{"claim_id","statement","region_refs","evidence_refs"},f"{key}[{i}]")
            cid=string(c["claim_id"],"claim_id");ids.append(cid);claim_ids.append(cid);string(c["statement"],"scope claim")
            allowed_regions=set(licensed_ids) if key=="licensed_claims" else set(all_regions)
            if not set(arr(c["region_refs"],"scope region_refs")).issubset(allowed_regions):fail(f"scope claim {cid} has dangling or non-licensed region")
            refs(c["evidence_refs"],f"scope claim {cid} evidence_refs")
    unique(claim_ids,"scope claim");string(ceiling["statement"],"scope ceiling statement")
    type_map={
      "selector_rule":set(rule_ids),"action":set(action_ids),"licensed_region":set(licensed_ids),
      "out_of_scope":set(outside_ids),"preserved_rule":set(pres_ids),"fallback":{"fallback"},
      "stop_condition":set(stop_ids),"scope_claim":set(lic_claim_ids),"scope_exclusion":set(not_claim_ids)
    }
    provenance=arr(p["provenance"],"provenance");pairs=[]
    for i,x in enumerate(provenance):
        exact(x,{"element_type","element_id","evidence_refs","locator_detail"},f"provenance[{i}]")
        et=x["element_type"];eid=string(x["element_id"],"provenance element_id")
        if et not in type_map or eid not in type_map[et]:fail(f"unknown provenance link {et}:{eid}")
        pairs.append((et,eid));refs(x["evidence_refs"],"provenance evidence_refs");string(x["locator_detail"],"provenance locator")
    unique(pairs,"provenance")
    expected={(kind,eid) for kind,ids in type_map.items() for eid in ids}
    if not expected.issubset(set(pairs)):fail(f"provenance omits typed links: {sorted(expected-set(pairs))}")
    if family:
        if family not in FAMILIES:fail("unknown family")
        source=REPO/"ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families"/family
        m0=(source/"m0.md").read_text(encoding="utf-8");e1=(source/"revision-evidence-e1.md").read_text(encoding="utf-8")
        for e in evidence:
            content=m0 if e["source_type"]=="M0" else e1
            if e["source_locator"] not in content:fail(f"source locator missing from family inputs for {e['evidence_id']}")
    print(f"TASK227_POLICY_VALID=PASS {path}")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--schema-only",action="store_true");ap.add_argument("--family",choices=sorted(FAMILIES));ap.add_argument("policies",nargs="*",type=Path);args=ap.parse_args()
    verify_schema()
    if args.schema_only:return
    if not args.policies:fail("provide one or more policy files or --schema-only")
    for path in args.policies:verify_policy(path,args.family)

if __name__=="__main__":
    try:main()
    except SystemExit:raise
    except Exception as exc:fail(str(exc))
