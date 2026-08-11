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
CANONICAL_PROFILES={
 "claim_authority":("action_permission","privacy_eligibility","owner_acceptance"),
 "language_authority":("truth","mathematical_maturity","external_evidence_maturity","ceiling_upgrade","layer_creation"),
 "charter_authority":("truth","external_evidence_maturity","non_action_release"),
 "operations_authority":("truth","causality","mechanism_confirmation","mathematical_maturity","external_evidence_maturity"),
 "publication_authority":("truth","mathematical_maturity","external_evidence_maturity","owner_acceptance","ceiling_upgrade"),
 "privacy_authority":("truth","mathematical_maturity","external_evidence_maturity"),
 "model_authority":("external_truth","foundation_status_upgrade","external_evidence_maturity"),
 "review_authority":("truth","external_evidence_maturity","owner_acceptance")
}
AUTHORITY_PROFILE={"foundation.claims":"claim_authority","foundation.lifecycle":"claim_authority","language_thought.plane":"language_authority","charter.normative":"charter_authority","operations.iteration":"operations_authority","publication.results_book":"publication_authority","publication.privacy":"privacy_authority","models.local":"model_authority","review.scoped":"review_authority","history.meta_protocol":"review_authority","pressure_test.getnote":"operations_authority"}
RELATION_EFFECT={"foundation.provenance_route":"REQUIRE_PROVENANCE_AND_LOCAL_CEILING","language_thought.transform":"PRESERVE_FRAMING_RESIDUE","operations.repository_dependency":"REQUEST_PROJECTION_REFRESH","operations.feedback_to_l0":"SUBMIT_PROVENANCE_BOUND_L0_CANDIDATE","models.capability_boundary":"REFERENCE_LOCAL_CAPABILITY_ONLY","foundation.epistemic_dependency":"REQUIRE_DOWNSTREAM_REVIEW_ON_UPSTREAM_DOWNGRADE","foundation.revision_lineage":"REQUIRE_APPEND_ONLY_SUPERSESSION_OR_WITHDRAWAL","pressure_test.internal_projection":"REPORT_INTERNAL_PRESSURE_TEST_ONLY","history.current_mapping":"PRESERVE_HISTORICAL_LINEAGE","publication.privacy_gate":"BLOCK_OR_NARROW_PUBLICATION"}
REQUIRED_EDGE_PROHIBITIONS.update({"foundation.provenance_route":{"TRUTH_UPGRADE","CEILING_WIDENING","E_UPGRADE"},"operations.repository_dependency":{"TRUTH_UPGRADE","CAUSALITY_INFERENCE","MECHANISM_CONFIRMATION"},"publication.privacy_gate":{"TRUTH_UPGRADE","E_UPGRADE","CEILING_WIDENING"},"history.current_mapping":{"TRUTH_UPGRADE","SILENT_REVIVAL","SUPERIORITY_INFERENCE"}})
FEDERATIONS={
 "non_action_public_statement_release":("NON_ACTION_STATEMENT",{"foundation.claims","publication.results_book","publication.privacy"}),
 "action_linked_public_statement_release":("ACTION_LINKED_STATEMENT",{"foundation.claims","publication.results_book","publication.privacy","charter.normative"})
}
ROUTES={
 "README.md":("PUBLICATIONS/pointfire-results-book/RESULT-REGISTRY.jsonl","publication.results_book","LOCAL_AUTHORITY_REFERENCE",None,"publication.privacy"),
 "docs/architecture/epistemic-governance-kernel-and-federated-planes.md":("PUBLICATIONS/pointfire-results-book/RESULT-REGISTRY.jsonl","publication.results_book","LOCAL_AUTHORITY_REFERENCE",None,"publication.privacy"),
 "docs/architecture/getnote-1329-epistemic-governance-pressure-test.md":("data/governance/getnote-1329-epistemic-governance-pressure-test.json","pressure_test.getnote","LOCAL_AUTHORITY_REFERENCE",None,"publication.privacy"),
 "PUBLICATIONS/pointfire-results-book/09-正式仓库最新成果.md":("PUBLICATIONS/pointfire-results-book/RESULT-REGISTRY.jsonl","publication.results_book","LOCAL_AUTHORITY_REFERENCE",None,"publication.privacy"),
 "data/architecture/interactive-system-map.json":("data/architecture/interactive-system-map.json","publication.results_book","NOT_APPLICABLE","RELATIONSHIP_MAP_NOT_CLAIM_STATUS","publication.privacy"),
 "KNOWLEDGE/README.md":("data/foundation/registry-manifest.json","publication.results_book","NOT_APPLICABLE","NAVIGATION_PROJECTION_ONLY","publication.privacy")
}
OBLIGATIONS={"K1_FORMALIZATION_NOT_CONFIRMATION":("MACHINE_ENFORCED","negative permission profiles and closed effects"),"K2_M_E_ORTHOGONALITY":("MACHINE_ENFORCED","closed effects prohibit M/E upgrades"),"K3_NO_AXIS_AUTO_UPGRADE":("MACHINE_ENFORCED","closed prohibited effects"),"K4_SOURCE_FAMILY_INDEPENDENCE":("HUMAN_REVIEW_ONLY","source-family semantic adjudication"),"K5_PUBLIC_CEILING":("MACHINE_ENFORCED","closed public surface route inventory"),"K6_DEPENDENCY_REVIEW":("MACHINE_ENFORCED","r-dependency"),"K7_NO_WORKFLOW_TRUTH":("MACHINE_ENFORCED","operations profile and closed effects"),"K8_SUSPENSION_NON_EQUIVALENCE":("MACHINE_ENFORCED","suspension contracts"),"K9_APPEND_ONLY_REVISION":("MACHINE_ENFORCED","r-revision"),"K10_NO_SECOND_AUTHORITY":("MACHINE_ENFORCED","strict schema and REFERENTIAL_ONLY"),"K11_FEEDBACK_RETURNS_TO_L0":("MACHINE_ENFORCED","r-feedback"),"K12_TYPED_RELATIONS":("MACHINE_ENFORCED","closed relation/effect schema"),"EXTERNAL_VALIDITY":("HUMAN_REVIEW_ONLY","independent evidence review absent"),"UNIVERSAL_CEILING_ORDER":("UNBOUND","local vocabularies remain incomparable")}
SUSPENSIONS={
 "ABSTAIN":("review.scoped","CAN_REVIEWER_DECIDE",{"REJECT","NOT_ASSIGNED","UNKNOWN_TRUTH"},"NEW_EVIDENCE_OR_RESCOPED_REVIEW"),
 "NOT_ASSIGNED":("foundation.lifecycle","WAS_TARGET_LABEL_ASSIGNED",{"UNKNOWN_TRUTH","ABSTAIN","REJECT"},"EXPLICIT_LINEAGE_BOUND_ASSIGNMENT"),
 "NOT_IDENTIFIABLE":("foundation.lifecycle","CAN_IDENTITY_BE_ESTABLISHED",{"REJECT","NOT_ASSIGNED"},"NEW_IDENTIFYING_MATERIAL"),
 "BODY_RECOVERY_BLOCKED":("foundation.lifecycle","WAS_REQUIRED_SOURCE_BODY_RECOVERED",{"REJECT","NOT_ASSIGNED"},"PROVENANCE_BOUND_BODY_RECOVERY"),
 "WITHDRAWN":("foundation.lifecycle","DOES_CURRENT_PERMISSION_REMAIN",{"REJECT","HISTORICAL_ONLY"},"NEW_SUCCESSOR_WITH_NEW_GOVERNED_EVIDENCE")
}

def validate(doc, repo_root, schema=None):
    errors=[]; root=Path(repo_root)
    schema=schema or json.loads((root/"schemas/governance/epistemic-governance-relationships.schema.json").read_text())
    for e in sorted(Draft202012Validator(schema).iter_errors(doc),key=lambda x:list(x.absolute_path)):
        errors.append("schema: "+(".".join(map(str,e.absolute_path)) or "$")+": "+e.message)
    if errors: return errors
    profiles=doc["negative_permission_profiles"]; auths={a["id"]:a for a in doc["authorities"]}
    if {k:tuple(v) for k,v in profiles.items()} != CANONICAL_PROFILES: errors.append("negative permission profiles must exactly equal canonical profile map")
    if set(auths)!=set(AUTHORITY_PROFILE): errors.append("authority inventory must exactly equal canonical authority map")
    for a in auths.values():
        if a["profile"] not in profiles: errors.append(f"{a['id']}: unknown negative permission profile")
        elif set(a["cannot_decide"]) != set(profiles[a["profile"]]): errors.append(f"{a['id']}: cannot_decide must exactly bind profile {a['profile']}")
        if AUTHORITY_PROFILE.get(a["id"]) != a["profile"]: errors.append(f"{a['id']}: profile must equal canonical authority-profile binding")
        for p in a["canonical_paths"]:
            if p.startswith("/") or ".." in Path(p).parts or not (root/p).exists(): errors.append(f"{a['id']}: invalid or missing canonical path: {p}")
    fed_by_id={f["responsibility"]:f for f in doc["responsibility_federations"]}
    if len(fed_by_id)!=len(doc["responsibility_federations"]) or set(fed_by_id)!=set(FEDERATIONS): errors.append("federation inventory must contain each canonical responsibility exactly once")
    for f in doc["responsibility_federations"]:
        if any(a not in auths for a in f["authorities"]): errors.append(f"{f['responsibility']}: unknown authority")
        has_charter="charter.normative" in f["authorities"]
        if has_charter != (f["condition"]=="ACTION_LINKED_STATEMENT"): errors.append(f"{f['responsibility']}: Charter is permitted only for action-linked statements")
        if "publication.privacy" not in f["authorities"]: errors.append(f"{f['responsibility']}: privacy authority missing")
        expected=FEDERATIONS.get(f["responsibility"])
        if expected and (f["condition"]!=expected[0] or set(f["authorities"])!=expected[1]): errors.append(f"{f['responsibility']}: condition and authorities must exactly match canonical federation")
    types={r["type"] for r in doc["relationships"]}
    if types != REQUIRED_RELATIONS: errors.append(f"relationship coverage mismatch: {sorted(REQUIRED_RELATIONS-types)} missing, {sorted(types-REQUIRED_RELATIONS)} extra")
    for r in doc["relationships"]:
        for key in ("from","to","authority"):
            if r[key] not in auths: errors.append(f"{r['id']}: unknown {key}")
        if not r["prohibited_effects"]: errors.append(f"{r['id']}: negative permissions required")
        if r["allowed_effect"] != RELATION_EFFECT[r["type"]]: errors.append(f"{r['id']}: allowed effect must match relation type")
        missing=REQUIRED_EDGE_PROHIBITIONS.get(r["type"],set())-set(r["prohibited_effects"])
        if missing: errors.append(f"{r['id']}: relationship coverage missing prohibitions {sorted(missing)}")
    contracts={s["name"]:s for s in doc["suspension_contracts"]}
    if len(contracts)!=len(doc["suspension_contracts"]): errors.append("duplicate suspension contract")
    if set(contracts)!=set(SUSPENSIONS): errors.append("suspension inventory must exactly match canonical names")
    for s in contracts.values():
        if s["authority"] not in auths: errors.append(f"{s['name']}: unknown authority")
        if s["name"] in s["non_equivalent_to"]: errors.append(f"{s['name']}: cannot be equivalent to itself")
        expected=SUSPENSIONS.get(s["name"])
        if expected and (s["authority"],s["decision_question"],set(s["non_equivalent_to"]),s["reentry"]) != (expected[0],expected[1],expected[2],expected[3]): errors.append(f"{s['name']}: suspension tuple must exactly match canonical contract")
    if "REJECT" not in contracts["ABSTAIN"]["non_equivalent_to"]: errors.append("ABSTAIN must remain non-equivalent to REJECT")
    if "UNKNOWN_TRUTH" not in contracts["NOT_ASSIGNED"]["non_equivalent_to"]: errors.append("NOT_ASSIGNED must remain non-equivalent to UNKNOWN_TRUTH")
    routes={r["path"]:r for r in doc["public_surface_routes"]}
    if set(routes)!=REQUIRED_SURFACES: errors.append("public surface coverage must exactly match closed canonical route inventory")
    for p,r in routes.items():
        for q in (p,r["registry"]):
            if q.startswith("/") or ".." in Path(q).parts or not (root/q).exists(): errors.append(f"public route missing canonical path: {q}")
        if r["authority"] not in auths: errors.append(f"{p}: unknown route authority")
        actual=(r["registry"],r["authority"],r["ceiling_route"],r.get("ceiling_reason"),r["privacy_authority"])
        if ROUTES.get(p)!=actual: errors.append(f"{p}: public route tuple must exactly match canonical binding")
    obligations={o["id"]:o for o in doc["obligation_inventory"]}
    if len(obligations)!=len(doc["obligation_inventory"]) or set(obligations)!=set(OBLIGATIONS): errors.append("obligation inventory must contain each canonical obligation exactly once")
    for oid,o in obligations.items():
        if oid in OBLIGATIONS and (o["coverage"],o["binding"])!=OBLIGATIONS[oid]: errors.append(f"{oid}: coverage and binding must exactly match canonical obligation")
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
