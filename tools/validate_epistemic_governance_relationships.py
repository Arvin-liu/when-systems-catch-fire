#!/usr/bin/env python3
import argparse, json
from pathlib import Path

FORBIDDEN_STATE_KEYS={"truth","truth_status","status","maturity_m","maturity_e","mathematical_maturity","external_evidence_maturity","claim_rows","claims","disposition","ceiling_value"}
REQUIRED_NEG={"publication_implies_truth","review_implies_external_evidence","owner_acceptance_implies_external_evidence","repository_dependency_implies_causality","copied_local_state","language_creates_L7"}

def validate(doc, repo_root):
    errors=[]
    if doc.get("architecture_disposition")!="FEDERATED_ARCHITECTURE_ONLY": errors.append("architecture disposition must remain federated")
    if doc.get("authority_mode")!="REFERENTIAL_ONLY": errors.append("relationship index must be referential only")
    def walk(x, path="$"):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in FORBIDDEN_STATE_KEYS: errors.append(f"copied local state forbidden at {path}.{k}")
                walk(v,f"{path}.{k}")
        elif isinstance(x,list):
            for i,v in enumerate(x): walk(v,f"{path}[{i}]")
    walk(doc)
    auths=doc.get("authorities",[]); ids=[a.get("id") for a in auths]
    if len(ids)!=len(set(ids)): errors.append("duplicate authority id")
    for a in auths:
        for rel in a.get("canonical_paths",[]):
            if rel.startswith("/") or ".." in Path(rel).parts: errors.append(f"unsafe canonical path: {rel}")
            elif not (repo_root/rel).exists(): errors.append(f"canonical path does not exist: {rel}")
    for fed in doc.get("responsibility_federations",[]):
        if fed.get("overlap_mode")!="EXPLICIT_FEDERATION": errors.append("overlap must be explicit federation")
        if len(fed.get("authorities",[]))<2: errors.append("federation needs multiple authorities")
        for aid in fed.get("authorities",[]):
            if aid not in ids: errors.append(f"unknown federated authority: {aid}")
    rels=doc.get("relationships",[]); rids={r.get("id") for r in rels}
    forbidden=set(doc.get("global_prohibited_inferences",[]))
    if not REQUIRED_NEG <= forbidden: errors.append("required global negative permissions missing")
    bad_tokens={"raises_truth","implies_truth","raises_external_evidence","implies_external_evidence","implies_causality","assigns_maturity"}
    for r in rels:
        for field in ("from","to","authority"):
            if r.get(field) not in ids: errors.append(f"{r.get('id')}: unknown {field} authority")
        typ=r.get("type","")
        if "." not in typ: errors.append(f"{r.get('id')}: relation type must be namespaced")
        norm=r.get("allowed_inference","").lower().replace(" ","_")
        if any(t in norm for t in bad_tokens): errors.append(f"{r.get('id')}: forbidden truth/causality upgrade")
        if r.get("public_surface") and (r.get("ceiling_route")!="LOCAL_AUTHORITY_REFERENCE" or r.get("provenance_route")!="REQUIRED"):
            errors.append(f"{r.get('id')}: public surface lacks ceiling/provenance route")
        if typ=="language_thought.transforms_for" and "language_creates_L7" not in r.get("prohibited_inferences",[]): errors.append("language plane must explicitly prohibit L7")
        rec=r.get("reciprocal_id")
        if rec:
            peer=next((p for p in rels if p.get("id")==rec),None)
            if not peer or peer.get("reciprocal_id")!=r.get("id") or peer.get("from")!=r.get("to") or peer.get("to")!=r.get("from"): errors.append(f"{r.get('id')}: broken reciprocal link")
    if not any(r.get("type")=="publication.historical_mapping" for r in rels): errors.append("historical mapping relationship missing")
    if not any(r.get("type")=="human_machine.bidirectional_link" and r.get("reciprocal_id") in rids for r in rels): errors.append("human/machine bidirectional links missing")
    return errors

def main():
    p=argparse.ArgumentParser(); p.add_argument("spec",type=Path); p.add_argument("--repo-root",type=Path,required=True); a=p.parse_args()
    errors=validate(json.loads(a.spec.read_text()),a.repo_root.resolve())
    if errors:
        print("FAIL"); [print(f"- {e}") for e in errors]; return 1
    print("PASS: referential relationship spec satisfies ROLE-D invariants"); return 0
if __name__=="__main__": raise SystemExit(main())
