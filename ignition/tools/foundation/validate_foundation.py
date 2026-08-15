#!/usr/bin/env python3
"""Validate the 078 migration/adjudication separation and core artifacts."""
from __future__ import annotations
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import jsonschema

ROOT=Path(__file__).resolve().parents[2]
REPO_ROOT=ROOT.parent
GIT_ROOT=ROOT if (ROOT/".git").exists() else REPO_ROOT
checks=[]

def check(name, ok, detail=""):
    checks.append((name,bool(ok),detail))

def load(rel):
    p=ROOT/rel
    rows=[]
    if p.exists():
        rows=[json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    return rows

def repo_path(rel):
    """Resolve app-root and split-root paths in production and fixtures."""
    if rel.startswith(".github/") or rel in {"AGENTS.md", "LICENSE"}:
        candidates=[REPO_ROOT/rel, ROOT/rel]
    else:
        candidates=[ROOT/rel, REPO_ROOT/"ignition"/rel, REPO_ROOT/rel]
    return next((path for path in candidates if path.exists()), candidates[0])

def legacy_tables_preserved():
    """Verify the retired tables through the task-118 migration manifest."""
    checker = ROOT / "tools/foundation/legacy_table_migration.py"
    return subprocess.run([sys.executable, str(checker), "--check"], cwd=ROOT, stdout=subprocess.DEVNULL).returncode == 0

def schema_ok(schema_rel, rows):
    schema=json.loads((ROOT/schema_rel).read_text(encoding="utf-8"))
    try:
        for row in rows:
            jsonschema.validate(row,schema)
    except jsonschema.ValidationError as exc:
        return False,exc.message
    return True,f"rows={len(rows)}"

def main():
    objects=load("data/foundation/formal-objects/objects.jsonl")
    claims=load("data/foundation/claims/claims.jsonl")
    args=load("data/foundation/arguments/arguments.jsonl")
    evidence=load("data/foundation/evidence/evidence.jsonl")
    maps=load("data/foundation/mappings/legacy-mappings.jsonl")
    obligations=load("data/foundation/proofs/obligations.jsonl")
    validations=load("data/foundation/validations/records.jsonl")
    counterexamples=load("data/foundation/validations/counterexamples.jsonl")
    adjudications=load("data/foundation/adjudications/core-kernel.jsonl")
    overrides=load("data/foundation/adjudications/classification-overrides.jsonl")
    queue=load("data/foundation/work-queues/content-proof-queue.jsonl")
    proof_artifacts=load("data/foundation/proofs/core-artifacts.jsonl")
    core_counterexamples=load("data/foundation/validations/core-counterexamples.jsonl")
    logic_checks=load("data/foundation/validations/core-logic-checks.jsonl")
    method_079=load("data/foundation/adjudications/079-method-audit.jsonl")
    reviews_079=load("data/foundation/adjudications/079-independent-semantic-review.jsonl")
    dossiers_079=load("data/foundation/proofs/079-proof-dossiers.jsonl")
    equivalence_079=load("data/foundation/validations/079-equivalence-checks.jsonl")
    expected={"objects":622,"claims":678,"arguments":678,"evidence":828,"mappings":622,"obligations":622,"validations":6,"counterexamples":4,"adjudications":630,"overrides":621,"queue":1,"proof_artifacts":1,"core_counterexamples":2,"logic_checks":2}
    actual={"objects":len(objects),"claims":len(claims),"arguments":len(args),"evidence":len(evidence),"mappings":len(maps),"obligations":len(obligations),"validations":len(validations),"counterexamples":len(counterexamples)}
    actual.update({"adjudications":len(adjudications),"overrides":len(overrides),"queue":len(queue),"proof_artifacts":len(proof_artifacts),"core_counterexamples":len(core_counterexamples),"logic_checks":len(logic_checks)})
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
    minimum={"stable_id","legacy_id","title","source_paths","provenance_status","original_natural_language_claim","controlled_semantic_proposition","claim_type","formal_object_type","typed_variables","domain","codomain_or_target_type","units_or_dimensions","parameters","assumptions","formal_expression_or_ast","scope_boundary_stopping_condition","known_counterexamples","dependencies","proof_obligations","proof_artifacts","related_cases","status","unresolved_blockers","classification_status","classification_basis","classification_confidence","semantic_justification","source_excerpt_refs","adjudication_date","adjudicator","review_required","legacy_label","adjudicated_label"}
    check("objects:minimum-record",all(minimum <= set(x) for x in objects))
    check("classification:counts",Counter(x["classification_status"] for x in objects)==Counter({"ADJUDICATED":621,"PROVISIONAL":1}))
    check("classification:provisional-title-heuristic",all(x["classification_basis"]==["TITLE_HEURISTIC"] and x["review_required"] for x in objects if x["classification_status"]=="PROVISIONAL"))
    check("classification:only-d598-provisional",{x["id"] for x in objects if x["classification_status"]=="PROVISIONAL"}=={"D598"})
    check("classification:078-labels-retained-as-legacy",all("SOURCE_TEXT" in x["classification_basis"] and x["semantic_justification"] and x["source_excerpt_refs"] for x in objects if x["classification_status"]=="ADJUDICATED"))
    object_by_id={x["id"]:x for x in objects}
    check("classification:override-preserved",all(object_by_id[x["stable_id"]]["formal_object_type"]==x["formal_object_type"] and object_by_id[x["stable_id"]]["classification_status"]=="ADJUDICATED" for x in overrides))
    adjudication_min={"adjudication_id","stable_id","legacy_id","original_title","earliest_source","current_source","original_natural_language_proposition","controlled_semantic_proposition","subject","object","conditions","quantifiers","modal_terms","applicability_scope","formal_object_type","claim_type","why_not_other_object_types","typed_variables","domain","codomain_or_target_type","parameters","units_or_dimensions","assumptions_and_boundaries","premise_set","inference_type","inference_rule","conclusion","hidden_premises","known_counterexamples_or_countermodels","proof_obligations","evidence_status","final_disposition","unresolved_questions"}
    check("adjudication:complete-records",all(adjudication_min <= set(x) for x in adjudications))
    check("adjudication:078-self-label-not-independent-proof",len(method_079)==622 and all(not x["semantic_adjudication_verified"] for x in method_079))
    check("adjudication:registry-coverage",len({x["stable_id"] for x in adjudications if x["stable_id"] in object_by_id})==621)
    for name,schema_rel,rows in [
        ("formal-objects","data/foundation/schemas/formal-object.schema.json",objects),
        ("adjudications","data/foundation/schemas/adjudication.schema.json",adjudications),
        ("classification-overrides","data/foundation/schemas/classification-override.schema.json",overrides),
        ("content-work-queue","data/foundation/schemas/content-work-item.schema.json",queue),
        ("079-independent-reviews","data/foundation/schemas/independent-semantic-review.schema.json",reviews_079),
    ]:
        ok,detail=schema_ok(schema_rel,rows)
        check(f"schema:{name}",ok,detail)
    coverage=json.loads((ROOT/"data/foundation/coverage/migration-vs-semantic-coverage-20260713.json").read_text(encoding="utf-8"))
    ok,detail=schema_ok("data/foundation/schemas/coverage.schema.json",[coverage])
    check("schema:coverage",ok,detail)
    check("gate:t2-legacy-not-proved",any(x["id"]=="T2" and x["equivalence"]=="NOT_EQUIVALENT_WEAKENED_LEMMA" for x in equivalence_079))
    check("gate:no-strict-isomorphism",all(x.get("claim_type")!="STRICT_ISOMORPHISM_CLAIM" for x in objects))
    check("gate:no-established-causal",all(x.get("claim_type")!="EMPIRICAL_CAUSAL_CLAIM" for x in objects))
    check("gate:t16-refuted",object_by_id["T16"]["status"]["proof_status"]=="REFUTED")
    check("gate:d220-countermodel",object_by_id["D220"]["status"]["logic_status"]=="COUNTERMODEL_FOUND")
    check("gate:t23-pending",object_by_id["T23"]["status"]["proof_status"]=="UNPROVED_PROPOSITION")
    check("079:method-split",Counter(x["adjudication_method"] for x in method_079)==Counter({"REGEX_PRECLASSIFICATION":548,"HARDCODED_MAPPING":74}))
    check("079:verified-registry-only-five",sum(x["registry_object"] for x in reviews_079)==5)
    check("079:proof-dossiers-forty",len(dossiers_079)==40 and len({x["id"] for x in dossiers_079})==40)
    required_ce={"target_claim","domain","assumptions","input","derivation","violated_conclusion","source","replay","expected_result"}
    check("counterexample:replay-contract",all(required_ce <= set(x) for x in counterexamples))
    check("migration:legacy-byte-preservation",legacy_tables_preserved())
    check("schemas:count",len(list((ROOT/"schemas/foundation").glob("*.json")))>=7)
    required=["ARCHITECTURE.md","FOUNDATION.md","AI-START-HERE.md","AI-HANDOFF.md",".github/workflows/foundation-validation.yml","formal/lean/Foundation.lean","views/manifest.json","data/foundation/project-state.json"]
    for rel in required: check(f"file:{rel}",repo_path(rel).is_file())
    check("generator:adjudication-deterministic",subprocess.run([sys.executable,"tools/foundation/adjudicate_core.py","--check"],cwd=ROOT,stdout=subprocess.DEVNULL).returncode==0)
    check("generator:migration-deterministic",subprocess.run([sys.executable,"tools/foundation/migrate_legacy.py","--check"],cwd=ROOT,stdout=subprocess.DEVNULL).returncode==0)
    claim_governance=subprocess.run([sys.executable,"tools/foundation/validate_claim_governance.py"],cwd=ROOT,text=True,capture_output=True)
    check("claim-governance:integrated",claim_governance.returncode==0,claim_governance.stdout+claim_governance.stderr if claim_governance.returncode else "")
    function_asset_closure=subprocess.run([sys.executable,"tools/foundation/validate_function_asset_closure.py"],cwd=ROOT,text=True,capture_output=True)
    check("function-asset-closure:integrated",function_asset_closure.returncode==0,function_asset_closure.stdout+function_asset_closure.stderr if function_asset_closure.returncode else "")
    nonfunction_claim_closure=subprocess.run([sys.executable,"tools/foundation/validate_nonfunction_claim_closure.py"],cwd=ROOT,text=True,capture_output=True)
    check("nonfunction-claim-closure:integrated",nonfunction_claim_closure.returncode==0,nonfunction_claim_closure.stdout+nonfunction_claim_closure.stderr if nonfunction_claim_closure.returncode else "")
    for name,ok,detail in checks:
        print(("PASS" if ok else "FAIL")+" "+name+(" "+detail if detail else ""))
    passed=sum(x[1] for x in checks)
    print(f"CHECKS_TOTAL={len(checks)} CHECKS_PASSED={passed} CHECKS_FAILED={len(checks)-passed}")
    if passed==len(checks):
        print("ALL_FOUNDATION_VALID")
        return 0
    return 1

if __name__=="__main__": raise SystemExit(main())
