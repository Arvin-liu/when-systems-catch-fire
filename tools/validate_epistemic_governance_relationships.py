#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from jsonschema import Draft202012Validator

REQUIRED_OBLIGATIONS={f"K{i}_{x}" for i,x in [(1,"FORMALIZATION_NOT_CONFIRMATION"),(2,"M_E_ORTHOGONALITY"),(3,"NO_AXIS_AUTO_UPGRADE"),(4,"SOURCE_FAMILY_INDEPENDENCE"),(5,"PUBLIC_CEILING"),(6,"DEPENDENCY_REVIEW"),(7,"NO_WORKFLOW_TRUTH"),(8,"SUSPENSION_NON_EQUIVALENCE"),(9,"APPEND_ONLY_REVISION"),(10,"NO_SECOND_AUTHORITY"),(11,"FEEDBACK_RETURNS_TO_L0"),(12,"TYPED_RELATIONS")]}
REQUIRED_RELATIONS={"foundation.provenance_route","language_thought.transform","operations.repository_dependency","operations.feedback_to_l0","models.capability_boundary","foundation.epistemic_dependency","foundation.revision_lineage","pressure_test.internal_projection","history.current_mapping","publication.privacy_gate"}
REQUIRED_SURFACES={"README.md","docs/architecture/epistemic-governance-kernel-and-federated-planes.md","docs/architecture/getnote-1329-epistemic-governance-pressure-test.md","PUBLICATIONS/pointfire-results-book/09-正式仓库最新成果.md","data/architecture/interactive-system-map.json","KNOWLEDGE/README.md"}
REQUIRED_EDGE_PROHIBITIONS={
 "language_thought.transform":{"CREATE_L7","TRUTH_UPGRADE","CEILING_WIDENING"},
 "foundation.revision_lineage":{"SILENT_REVIVAL","HISTORY_ERASURE"},
 "pressure_test.internal_projection":{"EXTERNAL_VALIDITY_INFERENCE","SOURCE_FAMILY_INDEPENDENCE_INFERENCE"},
 "operations.feedback_to_l0":{"TRUTH_UPGRADE","MECHANISM_CONFIRMATION"},
 "models.capability_boundary":{"FOUNDATION_STATUS_UPGRADE","E_UPGRADE"},
 "foundation.epistemic_dependency":{"TRUTH_INHERITANCE","CAUSALITY_INFERENCE"}
}

def validate(doc, repo_root, schema=None):
    errors=[]; root=Path(repo_root)
    schema=schema or json.loads((root/"schemas/governance/epistemic-governance-relationships.schema.json").read_text())
    for e in sorted(Draft202012Validator(schema).iter_errors(doc),key=lambda x:list(x.absolute_path)):
        errors.append("schema: "+(".".join(map(str,e.absolute_path)) or "$")+": "+e.message)
    if errors: return errors
    profiles=doc["negative_permission_profiles"]; auths={a["id"]:a for a in doc["authorities"]}
    for a in auths.values():
        if a["profile"] not in profiles: errors.append(f"{a['id']}: unknown negative permission profile")
        elif set(a["cannot_decide"]) != set(profiles[a["profile"]]): errors.append(f"{a['id']}: cannot_decide must exactly bind profile {a['profile']}")
        for p in a["canonical_paths"]:
            if p.startswith("/") or ".." in Path(p).parts or not (root/p).exists(): errors.append(f"{a['id']}: invalid or missing canonical path: {p}")
    for f in doc["responsibility_federations"]:
        if any(a not in auths for a in f["authorities"]): errors.append(f"{f['responsibility']}: unknown authority")
        has_charter="charter.normative" in f["authorities"]
        if has_charter != (f["condition"]=="ACTION_LINKED_STATEMENT"): errors.append(f"{f['responsibility']}: Charter is permitted only for action-linked statements")
        if "publication.privacy" not in f["authorities"]: errors.append(f"{f['responsibility']}: privacy authority missing")
    types={r["type"] for r in doc["relationships"]}
    if types != REQUIRED_RELATIONS: errors.append(f"relationship coverage mismatch: {sorted(REQUIRED_RELATIONS-types)} missing, {sorted(types-REQUIRED_RELATIONS)} extra")
    for r in doc["relationships"]:
        for key in ("from","to","authority"):
            if r[key] not in auths: errors.append(f"{r['id']}: unknown {key}")
        if not r["prohibited_effects"]: errors.append(f"{r['id']}: negative permissions required")
        missing=REQUIRED_EDGE_PROHIBITIONS.get(r["type"],set())-set(r["prohibited_effects"])
        if missing: errors.append(f"{r['id']}: relationship coverage missing prohibitions {sorted(missing)}")
    contracts={s["name"]:s for s in doc["suspension_contracts"]}
    if len(contracts)!=len(doc["suspension_contracts"]): errors.append("duplicate suspension contract")
    for s in contracts.values():
        if s["authority"] not in auths: errors.append(f"{s['name']}: unknown authority")
        if s["name"] in s["non_equivalent_to"]: errors.append(f"{s['name']}: cannot be equivalent to itself")
    if "REJECT" not in contracts["ABSTAIN"]["non_equivalent_to"]: errors.append("ABSTAIN must remain non-equivalent to REJECT")
    if "UNKNOWN_TRUTH" not in contracts["NOT_ASSIGNED"]["non_equivalent_to"]: errors.append("NOT_ASSIGNED must remain non-equivalent to UNKNOWN_TRUTH")
    routes={r["path"]:r for r in doc["public_surface_routes"]}
    if set(routes)!=REQUIRED_SURFACES: errors.append("public surface coverage must exactly match closed canonical route inventory")
    for p,r in routes.items():
        for q in (p,r["registry"]):
            if q.startswith("/") or ".." in Path(q).parts or not (root/q).exists(): errors.append(f"public route missing canonical path: {q}")
        if r["authority"] not in auths: errors.append(f"{p}: unknown route authority")
    obligations={o["id"]:o for o in doc["obligation_inventory"]}
    if not REQUIRED_OBLIGATIONS <= set(obligations): errors.append("doc-to-spec kernel obligation coverage incomplete")
    if obligations["K4_SOURCE_FAMILY_INDEPENDENCE"]["coverage"]!="HUMAN_REVIEW_ONLY": errors.append("source-family independence may not be machine-certified")
    if obligations.get("UNIVERSAL_CEILING_ORDER",{}).get("coverage")!="UNBOUND": errors.append("universal ceiling order must remain UNBOUND")
    return errors

def main():
    p=argparse.ArgumentParser(); p.add_argument("spec",type=Path); p.add_argument("--repo-root",type=Path,required=True); p.add_argument("--schema",type=Path); a=p.parse_args()
    schema=json.loads((a.schema or a.repo_root/"schemas/governance/epistemic-governance-relationships.schema.json").read_text())
    errors=validate(json.loads(a.spec.read_text()),a.repo_root.resolve(),schema)
    if errors:
        print("FAIL"); [print("- "+e) for e in errors]; return 1
    print("PASS: strict schema, authority profiles, typed effects, obligations and closed public routes validated"); return 0
if __name__=="__main__": raise SystemExit(main())
