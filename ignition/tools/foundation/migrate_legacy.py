#!/usr/bin/env python3
"""Build the 076 foundation registries and compatibility views deterministically."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
GIT_ROOT = ROOT if (ROOT / ".git").exists() else REPO_ROOT
OUT = ROOT / "data/foundation"
ARCH = ROOT / "data/foundation-architecture"
VIEWS = ROOT / "views"
REPORTS = ROOT / "reports/foundation-architecture"
BASE = "e55b1d366195fd1cc05babf2010774862157924b"
AXES = ["workflow_status", "semantic_status", "formal_status", "logic_status", "proof_status", "evidence_status", "scope_status", "provenance_status", "migration_status"]

def dump(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def write(path: Path, content: str, check: bool, changed: list[str]):
    content = content.rstrip() + "\n"
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old != content:
        changed.append(str(path.relative_to(ROOT)))
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

def jsonl(rows):
    return "\n".join(dump(x) for x in rows)

def load_jsonl(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def load_classification_overrides():
    path = OUT / "adjudications/classification-overrides.jsonl"
    return {row["stable_id"]: row for row in load_jsonl(path)}

def git_blob(path: str):
    candidates = [path]
    if path.startswith("ignition/"):
        candidates.append(path.removeprefix("ignition/"))
    else:
        candidates.append(f"ignition/{path}")
    for candidate in dict.fromkeys(candidates):
        try:
            return subprocess.check_output(["git", "rev-parse", f"{BASE}:{candidate}"], cwd=GIT_ROOT, text=True).strip()
        except subprocess.CalledProcessError:
            continue
    return None

def oid_from_name(name: str):
    if "Ψ" in name:
        return "Y1"
    m = re.search(r"-(MF-?\d+|A\d+|T\d+|D\d+)-", name, re.I)
    if not m:
        return None
    raw = m.group(1).upper().replace("MF-", "MF")
    return f"MF{int(raw[2:])}" if raw.startswith("MF") else raw

def title_from_file(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")[:4000]
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        return m.group(1).strip()
    return re.sub(r"^\d+-[^-]+-?", "", path.stem)

def classify(oid: str, title: str):
    if oid == "Y1": return "ALGORITHM"
    if oid in {"MF1", "MF2", "MF3", "MF5"}: return "PREDICATE"
    if oid == "MF4": return "STATE_TRANSITION"
    if any(x in title for x in ["定理", "同构律", "因果律"]): return "RELATION"
    if any(x in title for x in ["指标", "指数", "度量", "率", "距离"]): return "METRIC"
    if "判定" in title: return "PREDICATE"
    if any(x in title for x in ["协议", "规则", "机制"]): return "ARGUMENT_SCHEMA"
    return "NATURAL_LANGUAGE_CANDIDATE"

def status_axes(kind="NATURAL_LANGUAGE_CONSTRUCT", claim="UNVERIFIED"):
    return {
        "workflow_status": "REGISTERED",
        "semantic_status": claim,
        "formal_status": "UNFORMALIZED" if kind == "NATURAL_LANGUAGE_CANDIDATE" else "FORMALIZATION_INCOMPLETE",
        "logic_status": "NOT_ASSESSED",
        "proof_status": "UNPROVED_PROPOSITION",
        "evidence_status": "SOURCE_ONLY",
        "scope_status": "BOUNDARY_REVIEW_REQUIRED",
        "provenance_status": "LEGACY_PATH_IDENTIFIED",
        "migration_status": "REGISTERED_COMPATIBILITY_VIEW"
    }

def object_rows():
    grouped = {}
    overrides = load_classification_overrides()
    for p in sorted((ROOT / "统一函数总表").glob("*.md")):
        if "INDEX" in p.name: continue
        oid = oid_from_name(p.name)
        if not oid: continue
        if oid == "Y1" and "legacy_path" in p.read_text(encoding="utf-8", errors="ignore")[:300]:
            continue
        grouped[oid] = p
    rows = []
    order = {"MF":0, "Y":1, "A":2, "T":3, "D":4}
    def key(item):
        oid = item[0]
        n = int(re.search(r"\d+", oid).group())
        return (order[oid[0:2] if oid.startswith("MF") else oid[0]], n)
    for oid, p in sorted(grouped.items(), key=key):
        rel = str(p.relative_to(ROOT))
        title = title_from_file(p)
        kind = classify(oid, title)
        row = {
            "entity_key": f"formal-object:{oid}", "id": oid, "namespace": oid[:2] if oid.startswith("MF") else oid[0],
            "stable_id":oid,"legacy_id":oid,"title": title, "asset_kind": "formal_object", "object_type": kind,"formal_object_type":kind,
            "foundation_layer": "L2_FORMAL_MODEL" if oid.startswith("MF") else "L1_CONCEPTUAL_MODEL",
            "assertion_grade": "UNVERIFIED", "legacy_path": rel, "legacy_git_blob_sha": git_blob(rel),
            "source_paths":[rel],"provenance_status":"LEGACY_PATH_IDENTIFIED","original_natural_language_claim":title,
            "controlled_semantic_proposition":None,"claim_type":"EXPLANATORY_HYPOTHESIS","typed_variables":[],"domain":None,"codomain_or_target_type":None,
            "units_or_dimensions":[],"parameters":[],"assumptions":[],"formal_expression_or_ast":None,
            "scope_boundary_stopping_condition":None,"known_counterexamples":[],"dependencies":[],"proof_obligations":[f"proof-obligation:{oid}"],
            "proof_artifacts":[],"related_cases":[],"unresolved_blockers":["controlled semantics, typing, scope and proof artifact require item-level review"],
            "classification_status":"PROVISIONAL","classification_basis":["TITLE_HEURISTIC"],"classification_confidence":0.25,
            "semantic_justification":"Conservative migration placeholder generated from the legacy ID and title; not an item-level semantic judgment.",
            "source_excerpt_refs":[f"{rel}#L1"],"adjudication_date":None,"adjudicator":"tools/foundation/migrate_legacy.py",
            "review_required":True,"legacy_label":"LEGACY_FUNCTION","adjudicated_label":None,
            "status": status_axes(kind)
        }
        override = overrides.get(oid)
        if override:
            for key, value in override.items():
                if key not in {"semantic_status", "formal_status", "logic_status", "proof_status", "evidence_status"}:
                    row[key] = value
            row["object_type"] = override["formal_object_type"]
            row["formal_object_type"] = override["formal_object_type"]
            row["unresolved_blockers"] = override.get("unresolved_questions", [])
            row["status"].update({
                "semantic_status": override["semantic_status"],
                "formal_status": override["formal_status"],
                "logic_status": override["logic_status"],
                "proof_status": override["proof_status"],
                "evidence_status": override["evidence_status"],
            })
        rows.append(row)
    return rows

def case_rows():
    rows=[]
    for p in sorted((ROOT / "统一案例总表").glob("*.md")):
        if "INDEX" in p.name: continue
        m=re.match(r"(\d+)-C-(\d+)-", p.name)
        if not m: continue
        cid=f"C{int(m.group(2)):04d}"
        rel=str(p.relative_to(ROOT))
        rows.append({"entity_key":f"evidence:{cid}","id":cid,"case_id":cid,"asset_kind":"formal_case","title":title_from_file(p),"legacy_path":rel,"legacy_git_blob_sha":git_blob(rel),"source":rel,"observed_facts":[],"interpretation":title_from_file(p),"disputed_facts":[],"related_claims_or_objects":[],"relation":"illustrate","evidence_strength":"SOURCE_ONLY_NOT_REPLAYED","scope":None,"provenance":"LEGACY_PATH_IDENTIFIED","evidence_status":"LEGACY_CASE_NOT_REPLAYED","claim_refs":[]})
    return rows

def ledger_candidates():
    rows=[]
    for line in (ROOT/"data/math-foundation/function-provenance-ledger.jsonl").read_text(encoding="utf-8").splitlines():
        x=json.loads(line)
        if str(x.get("id","")).startswith("BC-"):
            rows.append({"entity_key":f"evidence:{x['id']}","id":x["id"],"case_id":x["id"],"asset_kind":"candidate_case","title":x.get("title"),"legacy_path":x.get("current_path"),"legacy_git_blob_sha":git_blob(x.get("current_path", "")),"source":x.get("current_path"),"observed_facts":[],"interpretation":x.get("original_natural_language_claim"),"disputed_facts":[],"related_claims_or_objects":[],"relation":"illustrate","evidence_strength":"CANDIDATE_ONLY","scope":None,"provenance":x.get("provenance_status"),"evidence_status":"CANDIDATE_ONLY","claim_refs":[],"candidate_text":x.get("original_natural_language_claim")})
    return rows

def schemas():
    object_types=["FUNCTION","PARTIAL_FUNCTION","PREDICATE","RELATION","STATE_TRANSITION","CAUSAL_MODEL","PROBABILISTIC_MODEL","METRIC","ORDER","OPTIMIZATION_PROBLEM","OPERATOR","ALGORITHM","FORMAL_PROPOSITION","ARGUMENT_SCHEMA","MECHANISM_MODEL","NATURAL_LANGUAGE_CANDIDATE"]
    claim_types=["DEFINITION","MATHEMATICAL_PROPOSITION","ALGORITHMIC_CLAIM","EMPIRICAL_ASSOCIATION","EMPIRICAL_CAUSAL_CLAIM","HISTORICAL_INTERPRETATION","STRUCTURAL_ANALOGY","STRICT_ISOMORPHISM_CLAIM","NORMATIVE_CLAIM","PHILOSOPHICAL_CLAIM","EXPLANATORY_HYPOTHESIS","EXTERNAL_THEOREM_REFERENCE"]
    status={"type":"object","required":AXES,"properties":{
      "workflow_status":{"type":"string"},"semantic_status":{"type":"string"},
      "formal_status":{"enum":["UNFORMALIZED","FORMALIZATION_INCOMPLETE","WELL_TYPED","TYPE_ERROR","SEMANTICALLY_UNDEFINED","DIMENSION_ERROR","COUNTEREXAMPLE_FOUND","FORMALLY_REFUTED"]},
      "logic_status":{"enum":["NOT_ASSESSED","VALID_DEDUCTION","INVALID_INFERENCE","DEFEASIBLE_SUPPORT","COUNTERMODEL_FOUND","HIDDEN_PREMISE","CIRCULAR","INCONSISTENT_PREMISES","NOT_APPLICABLE"]},
      "proof_status":{"type":"string"},"evidence_status":{"type":"string"},"scope_status":{"type":"string"},"provenance_status":{"type":"string"},"migration_status":{"type":"string"}},"additionalProperties":False}
    base={"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","required":["entity_key","id","asset_kind"],"properties":{"entity_key":{"type":"string"},"id":{"type":"string"},"asset_kind":{"type":"string"}},"additionalProperties":True}
    out={name:{**base,"title":name.replace("-"," ").title()} for name in ["formal-object","claim","argument","evidence","source","mapping","proof-obligation","validation-record","counterexample"]}
    classification_basis={"type":"array","items":{"enum":["TITLE_HEURISTIC","SOURCE_TEXT","FORMAL_DEFINITION","PROOF_ARTIFACT","EXTERNAL_REFERENCE","HUMAN_REVIEW"]},"minItems":1,"uniqueItems":True}
    out["formal-object"]["required"]=["entity_key","id","asset_kind","stable_id","legacy_id","formal_object_type","claim_type","status","classification_status","classification_basis","classification_confidence","semantic_justification","source_excerpt_refs","adjudication_date","adjudicator","review_required","legacy_label","adjudicated_label"]
    out["formal-object"]["properties"]={**base["properties"],"stable_id":{"type":"string"},"legacy_id":{"type":"string"},"formal_object_type":{"enum":object_types},"claim_type":{"enum":claim_types},"classification_status":{"enum":["PROVISIONAL","ADJUDICATED","CONTESTED"]},"classification_basis":classification_basis,"classification_confidence":{"type":"number","minimum":0,"maximum":1},"semantic_justification":{"type":"string","minLength":1},"source_excerpt_refs":{"type":"array","items":{"type":"string"}},"adjudication_date":{"type":["string","null"]},"adjudicator":{"type":"string"},"review_required":{"type":"boolean"},"legacy_label":{"type":"string"},"adjudicated_label":{"type":["string","null"]},"status":status}
    out["claim"]["required"]=["entity_key","id","asset_kind","status"]
    out["claim"]["properties"]={**base["properties"],"status":status}
    return out

def build(check=False):
    changed=[]
    objects=object_rows()
    cases=case_rows()
    candidates=ledger_candidates()
    pending=json.loads((ROOT/"data/pending_claims.json").read_text(encoding="utf-8"))
    claims=[]
    arguments=[]
    obligations=[]
    mappings=[]
    sources=[]
    for o in objects:
        claims.append({"entity_key":f"claim:{o['id']}","id":o["id"],"asset_kind":"formal_object_claim","statement":o.get("controlled_semantic_proposition") or o["title"],"object_ref":o["entity_key"],"assertion_grade":o["status"]["semantic_status"],"classification_status":o["classification_status"],"status":o["status"]})
        arguments.append({"entity_key":f"argument:{o['id']}","id":o["id"],"asset_kind":"legacy_argument","claim_ref":f"claim:{o['id']}","premises":[],"conclusion":o.get("controlled_semantic_proposition") or o["title"],"validity":o["status"]["logic_status"],"adjudication_ref":f"adjudication:{o['id']}" if o["classification_status"]=="ADJUDICATED" else None})
        obligation_status="DISCHARGED" if o["status"]["proof_status"]=="PROVED" else "REFUTED" if o["status"]["proof_status"]=="REFUTED" else "OPEN"
        obligations.append({"entity_key":f"proof-obligation:{o['id']}","id":o["id"],"asset_kind":"proof_obligation","claim_ref":f"claim:{o['id']}","required_artifact":"MACHINE_CHECKED_PROOF_OR_REPLAYABLE_COUNTEREXAMPLE","status":obligation_status,"proof_artifacts":o.get("proof_artifacts",[])})
        mappings.append({"entity_key":f"mapping:formal-object:{o['id']}","id":o["id"],"asset_kind":"legacy_mapping","legacy_path":o["legacy_path"],"target_ref":o["entity_key"],"relation":"COMPATIBILITY_VIEW_OF"})
        sources.append({"entity_key":f"source:formal-object:{o['id']}","id":o["id"],"asset_kind":"source_manifest","path":o["legacy_path"],"git_blob_sha":o["legacy_git_blob_sha"],"source_status":"PATH_AND_BLOB_IDENTIFIED"})
    for e in candidates:
        claims.append({"entity_key":f"claim:{e['id']}","id":e["id"],"asset_kind":"candidate_case_claim","statement":e.get("candidate_text"),"evidence_ref":e["entity_key"],"assertion_grade":"CANDIDATE_ONLY","status":status_axes("NATURAL_LANGUAGE_CANDIDATE","PENDING")})
        arguments.append({"entity_key":f"argument:{e['id']}","id":e["id"],"asset_kind":"candidate_argument","claim_ref":f"claim:{e['id']}","premises":[],"conclusion":e.get("candidate_text"),"validity":"NOT_FORMALIZED"})
    for p in pending:
        pid=p["id"]
        claims.append({"entity_key":f"claim:{pid}","id":pid,"asset_kind":"pending_claim","statement":p.get("claim"),"assertion_grade":"PENDING","status":status_axes("OPEN_PROBLEM_OR_GOVERNED_CLAIM","PENDING"),"legacy_record":p})
        arguments.append({"entity_key":f"argument:{pid}","id":pid,"asset_kind":"pending_argument","claim_ref":f"claim:{pid}","premises":[],"conclusion":p.get("recommended_wording"),"validity":"PENDING"})
    core=[{"entity_key":"core-system:Y1","id":"Y1","asset_kind":"core_system","role":"workflow_orchestrator","not_a_proof_oracle":True},{"entity_key":"core-system:JPLUS","id":"JPLUS","asset_kind":"core_system","role":"positive_evidence_channel"},{"entity_key":"core-system:JMINUS","id":"JMINUS","asset_kind":"core_system","role":"negative_evidence_channel"}]
    protocol_roles=[]
    for i in range(1,13):
        protocol_roles.append({"entity_key":f"protocol:P{i:02d}","id":f"P{i:02d}","asset_kind":"protocol_role","role":"heuristic_or_governance_operator","normative_status":"NOT_A_THEOREM"})
    validations=[{"entity_key":"validation:076-math-true","id":"076-MATH-TRUE","asset_kind":"validation_record","claim":"binomial square identity","result":"PROVED_BY_NORMALIZATION","replay":"python3 tools/foundation/run_benchmarks.py --check"},{"entity_key":"validation:076-math-false","id":"076-MATH-FALSE","asset_kind":"validation_record","claim":"forall rational x, x squared is at least x","result":"COUNTEREXAMPLE_VERIFIED","counterexample":"x=1/2","replay":"python3 tools/foundation/run_benchmarks.py --check"},{"entity_key":"validation:076-math-pending","id":"076-MATH-PENDING","asset_kind":"validation_record","claim":"Goldbach conjecture","result":"PENDING_NOT_PROVED"},{"entity_key":"validation:076-logic-valid","id":"076-LOGIC-VALID","asset_kind":"validation_record","claim":"modus ponens","result":"VALID_BY_TRUTH_TABLE","replay":"python3 tools/foundation/run_benchmarks.py --check"},{"entity_key":"validation:076-logic-invalid","id":"076-LOGIC-INVALID","asset_kind":"validation_record","claim":"affirming the consequent","result":"COUNTERMODEL_VERIFIED","counterexample":"p=false,q=true","replay":"python3 tools/foundation/run_benchmarks.py --check"},{"entity_key":"validation:076-analogy","id":"076-ANALOGY","asset_kind":"validation_record","claim":"cross-domain analogy","result":"DEFEASIBLE_SUPPORT"}]
    counterexamples=[{"entity_key":"counterexample:076-math-false","id":"076-MATH-FALSE","asset_kind":"counterexample","target_claim":"forall rational x, x squared is at least x","domain":"rational numbers","assumptions":[],"input":"x=1/2","derivation":"1/4 is not at least 1/2","violated_conclusion":"x squared is at least x","source":"076 benchmark fixture","replay":"python3 tools/foundation/run_benchmarks.py --check","expected_result":"COUNTEREXAMPLE_VERIFIED"},{"entity_key":"counterexample:076-logic-invalid","id":"076-LOGIC-INVALID","asset_kind":"counterexample","target_claim":"if p implies q and q then p","domain":"Boolean valuations","assumptions":["p implies q","q"],"input":"p=false,q=true","derivation":"both premises true while conclusion p is false","violated_conclusion":"p","source":"076 benchmark fixture","replay":"python3 tools/foundation/run_benchmarks.py --check","expected_result":"COUNTERMODEL_VERIFIED"}]
    core_artifacts=load_jsonl(OUT/"proofs/core-artifacts.jsonl")
    core_counterexamples=load_jsonl(OUT/"validations/core-counterexamples.jsonl")
    counterexamples.extend(core_counterexamples)
    files={
      OUT/"formal-objects/objects.jsonl":jsonl(objects), OUT/"core-systems/systems.jsonl":jsonl(core), OUT/"core-systems/protocol-roles.jsonl":jsonl(protocol_roles),
      OUT/"claims/claims.jsonl":jsonl(claims), OUT/"arguments/arguments.jsonl":jsonl(arguments), OUT/"evidence/evidence.jsonl":jsonl(cases+candidates),
      OUT/"sources/sources.jsonl":jsonl(sources), OUT/"mappings/legacy-mappings.jsonl":jsonl(mappings), OUT/"proofs/obligations.jsonl":jsonl(obligations),
      OUT/"mappings/object-evidence-mappings.jsonl":jsonl(mappings), OUT/"proofs/artifacts.jsonl":jsonl(core_artifacts), OUT/"proofs/proof-artifacts.jsonl":jsonl(core_artifacts),
      OUT/"validations/records.jsonl":jsonl(validations), OUT/"validations/validation-records.jsonl":jsonl(validations), OUT/"validations/counterexamples.jsonl":jsonl(counterexamples),
      VIEWS/"legacy-functions.jsonl":jsonl([{"id":o["id"],"title":o["title"],"source":o["legacy_path"],"registry_ref":o["entity_key"]} for o in objects]),
      VIEWS/"legacy-cases.jsonl":jsonl([{"id":e["id"],"title":e["title"],"source":e["legacy_path"],"registry_ref":e["entity_key"]} for e in cases]),
    }
    schema_alias={"formal-object":"formal-object","claim":"claim","argument":"argument","evidence":"evidence","proof-obligation":"proof-artifact","validation-record":"validation-record","mapping":"mapping"}
    for name,schema in schemas().items():
        files[OUT/f"schemas/{name}.schema.json"]=json.dumps(schema,ensure_ascii=False,indent=2)
        if name in schema_alias: files[ROOT/f"schemas/foundation/{schema_alias[name]}.schema.json"]=json.dumps(schema,ensure_ascii=False,indent=2)
    classification_counts=dict(Counter(o["classification_status"] for o in objects))
    counts={"formal_objects":len(objects),"formal_cases":len(cases),"candidate_cases":len(candidates),"pending_claims":len(pending),"scope_entities":len(claims),"verified_legacy_counterexamples":0,"benchmark_and_core_counterexamples":len(counterexamples),"object_types":dict(Counter(o["object_type"] for o in objects)),"classification_status":classification_counts}
    toolchain_status=json.loads((OUT/"toolchain-status.json").read_text(encoding="utf-8")) if (OUT/"toolchain-status.json").exists() else {"lean":{"available":False},"sympy":{"available":False},"z3":{"available":False}}
    census_summary=json.loads((OUT/"function-assets/census-summary.json").read_text(encoding="utf-8"))
    counts["function_asset_census"]={key:census_summary[key] for key in ["tracked_text_files_scanned","registered_assets","explicit_undefined_ids","implicit_named_assets","deduplicated_assets","source_occurrence_records","source_mentions","duplicate_mentions","dependency_edges","assets_with_dependencies","human_adjudicated_task98","queued_for_human_review"]}
    closure_summary=json.loads((OUT/"function-assets/closure-summary.json").read_text(encoding="utf-8"))
    counts["function_asset_deep_adjudication"]={key:closure_summary[key] for key in ["canonical_identity_cards","adjudication_ledger_records","explicit_quarantine_or_pending","counterexample_records","dependency_edges","public_strong_claim_candidates","semantic_rebound_candidates","blocked_semantic_rebounds","registry_closed"]}
    nonfunction_summary=json.loads((OUT/"nonfunction-claims/closure-summary.json").read_text(encoding="utf-8"))
    counts["nonfunction_claim_evidence_lineage"]={key:nonfunction_summary[key] for key in ["tracked_files_accounted","candidate_fragments","canonical_claims","existing_claims_mapped","explicit_quarantine_or_pending","dependency_edges","explicitly_unresolved_dependency_edges","public_surface_records","public_surface_violations","conclusion_rebound_candidates","blocked_conclusion_rebounds","active_conclusion_rebounds","registry_closed"]}
    project={
      "snapshot_id":"IGNITION-20260729-100",
      "status":"NONFUNCTION_CLAIM_EVIDENCE_LINEAGE_CLOSED_WITH_EXPLICIT_QUARANTINE",
      "base_076_head":"fc3f2ae309ad3dd485716ab5675948a6a46cd75d",
      "counts":counts,
      "migration_coverage":"complete",
      "semantic_adjudication":"function_identity_and_nonfunction_claim_registries_closed_by_disposition_or_explicit_quarantine; proofs, external evidence, novelty and replication obligations remain independently open",
      "classification_basis_076":"heuristic_title_and_id_rules",
      "content_truth_status_076":"pending_item_level_review",
      "semantic_adjudication_counts":{"adjudicated":classification_counts.get("ADJUDICATED",0),"provisional":classification_counts.get("PROVISIONAL",0),"total":len(objects)},
      "toolchain_status":toolchain_status,
      "authority":{"machine_readable":"data/foundation","human_entry":"FOUNDATION.md","legacy_views":"views","adjudications":"data/foundation/adjudications","function_identity_and_claim_corrections":"data/foundation/function-assets/corrections.jsonl","automatic_census_candidates":"data/foundation/function-assets/census.jsonl","canonical_function_asset_identity_cards":"data/foundation/function-assets/identity-cards.jsonl","function_asset_adjudication_ledger":"data/foundation/function-assets/adjudication-ledger.jsonl","function_asset_quarantine":"data/foundation/function-assets/unresolved-quarantine.jsonl","canonical_nonfunction_claim_registry":"data/foundation/nonfunction-claims/claim-registry.jsonl","nonfunction_evidence_lineage":"data/foundation/nonfunction-claims/evidence-lineage.jsonl","nonfunction_dependency_graph":"data/foundation/nonfunction-claims/dependency-graph.jsonl","nonfunction_claim_quarantine":"data/foundation/nonfunction-claims/unresolved-quarantine.jsonl","future_claim_admission_protocol":"docs/foundation/future-claim-admission-protocol.md"},
      "invariants":{"legacy_tables_immutable":True,"old_statistics_historical_only":True,"J_channels_are_evidence_not_truth_oracles":True,"protocols_are_not_automatically_theorems":True,"migration_cannot_overwrite_adjudicated":True,"migration_coverage_is_not_semantic_adjudication":True,"automatic_census_is_not_authoritative_adjudication":True,"registry_closure_can_be_satisfied_by_explicit_quarantine":True,"quarantine_is_not_validation":True,"mathematical_maturity_does_not_raise_external_evidence":True,"internal_tests_do_not_establish_external_truth":True,"local_model_failure_does_not_prove_universal_impossibility":True,"analogy_does_not_establish_isomorphism":True,"renaming_does_not_restore_withdrawn_conclusions":True,"source_anchor_does_not_establish_external_evidence":True},
      "validation_commands":["python3 tools/foundation/adjudicate_core.py --check","python3 tools/foundation/migrate_legacy.py --check","python3 tools/foundation/validate_foundation.py","python3 tools/foundation/verify_core_claims.py --check","python3 tools/foundation/build_function_asset_census.py --check","python3 tools/foundation/adjudicate_function_assets.py --check","python3 tools/foundation/validate_claim_governance.py","python3 tools/foundation/validate_function_asset_closure.py","python3 tools/foundation/run_function_asset_math_checks.py --check","python3 tools/foundation/adjudicate_nonfunction_claims.py --check","python3 tools/foundation/validate_nonfunction_claim_closure.py","python3 -m unittest tests.foundation.test_foundation","python3 -m unittest tests.foundation.test_claim_governance","python3 -m unittest tests.foundation.test_function_asset_closure","python3 -m unittest tests.foundation.test_nonfunction_claim_closure"]
    }
    files[OUT/"project-state.json"]=json.dumps(project,ensure_ascii=False,indent=2)
    extra_registries=["data/foundation/adjudications/core-kernel.jsonl","data/foundation/adjudications/classification-overrides.jsonl","data/foundation/work-queues/content-proof-queue.jsonl","data/foundation/proofs/core-artifacts.jsonl","data/foundation/validations/core-counterexamples.jsonl","data/foundation/validations/core-logic-checks.jsonl","data/foundation/function-assets/discovery.jsonl","data/foundation/function-assets/census.jsonl","data/foundation/function-assets/dependencies.jsonl","data/foundation/function-assets/audit-queue.jsonl","data/foundation/function-assets/corrections.jsonl","data/foundation/function-assets/dependency-actions.jsonl","data/foundation/function-assets/claim-ledger.jsonl","data/foundation/function-assets/identity-cards.jsonl","data/foundation/function-assets/adjudication-ledger.jsonl","data/foundation/function-assets/proof-empirical-obligations.jsonl","data/foundation/function-assets/counterexample-registry.jsonl","data/foundation/function-assets/unresolved-quarantine.jsonl","data/foundation/function-assets/dependency-closure.jsonl","data/foundation/function-assets/public-claim-lineage.jsonl","data/foundation/function-assets/semantic-rebound-report.jsonl","data/foundation/function-assets/withdrawn-historical-claims.jsonl","data/foundation/nonfunction-claims/claim-registry.jsonl","data/foundation/nonfunction-claims/source-discovery.jsonl","data/foundation/nonfunction-claims/adjudication-ledger.jsonl","data/foundation/nonfunction-claims/evidence-lineage.jsonl","data/foundation/nonfunction-claims/dependency-graph.jsonl","data/foundation/nonfunction-claims/inference-risk-report.jsonl","data/foundation/nonfunction-claims/conclusion-rebound-report.jsonl","data/foundation/nonfunction-claims/public-surface-report.jsonl","data/foundation/nonfunction-claims/unresolved-quarantine.jsonl","data/foundation/nonfunction-claims/supersession-lineage.jsonl"]
    files[OUT/"registry-manifest.json"]=json.dumps({"snapshot_id":"IGNITION-20260729-100","counts":counts,"registries":[str(p.relative_to(ROOT)) for p in files if str(p).endswith("jsonl")]+extra_registries},ensure_ascii=False,indent=2)
    files[OUT/"migration-summary.json"]=json.dumps({"source_commit":BASE,"method":"conservative_non_destructive_migration_projection_with_task98_99_function_authority_and_task100_nonfunction_claim_disposition_or_quarantine_closure","migration_coverage":"complete","semantic_adjudication":"function_identity_and_nonfunction_claim_registries_closed_by_disposition_or_explicit_quarantine; proofs, external evidence, novelty and replication obligations remain independently open","classification_basis":"TITLE_HEURISTIC for provisional migration placeholders; SOURCE_TEXT for adjudication overrides; task 98-99 function identities plus task 100 source discovery and explicit disposition/quarantine for non-function claims","counts":counts,"dedup_key":["asset_kind","normalized_namespace","normalized_id"],"representation_key":["entity_key","path","git_blob_sha"]},ensure_ascii=False,indent=2)
    files[OUT/"unresolved-obligations.json"]=json.dumps({"open_proof_obligations":sum(o["status"]=="OPEN" for o in obligations),"toolchain_status":toolchain_status,"note":"Only T2 is retained as a proved core theorem; other theorem-layer labels remain downgraded or pending."},ensure_ascii=False,indent=2)
    files[OUT/"unresolved-obligations.jsonl"]=jsonl(obligations)
    files[OUT/"migrations/legacy-coverage.jsonl"]=jsonl(mappings)
    files[OUT/"migrations/legacy-assets.jsonl"]=jsonl(mappings)
    files[VIEWS/"README.md"]="# Compatibility views\n\nGenerated, read-only projections. They are not the source of truth; edit data/foundation through reviewed migration tooling."
    files[VIEWS/"legacy-functions.md"]=f"# Legacy function view\n\nRegistered formal objects: {len(objects)}. Historical table titles are preserved but are not authoritative counts."
    files[VIEWS/"legacy-cases.md"]=f"# Legacy case view\n\nRegistered formal cases: {len(cases)}. Candidate-only records are excluded."
    files[VIEWS/"manifest.json"]=json.dumps({"generated_by":"tools/foundation/migrate_legacy.py","source_commit":BASE,"formal_objects":len(objects),"formal_cases":len(cases)},ensure_ascii=False,indent=2)
    report_text={
      "architecture-rebuild-summary-20260712.md":"# Architecture rebuild summary\n\nThe seven-layer architecture, separated registries, nine status axes, gates, deterministic migration, compatibility views and executable benchmarks are installed. Status: ARCHITECTURE_COMPLETE_PENDING_CONTENT_PROOFS. Architecture completion does not prove the registered content.",
      "075-truth-audit-20260712.md":f"# 075 truth audit\n\nStatus: PARTIAL_UNVERIFIED_COUNTS. Recomputed: {len(objects)} formal objects, {len(cases)} formal cases, {len(candidates)} candidate cases, {len(pending)} pending claims. The 075 values 608, 546 and 714 were heuristic row hits, not proof results. Verified replayable legacy counterexamples: 0.",
      "object-classification-20260712.md":"# Object classification\n\nClassification is conservative. Names containing function do not establish totality, single-valuedness, a domain or codomain. Strong labels remain unverified until a proof artifact is linked.",
      "strong-term-audit-20260712.md":"# Strong-term audit\n\nTheorem, law, isomorphism and causality wording in legacy titles is preserved as historical text and downgraded to unverified claim status in the registry.",
      "counterexample-replay-audit-20260712.md":"# Counterexample replay audit\n\nNo 075 keyword hit satisfied the replay contract. Two new 076 benchmark counterexamples are concrete and replayable; neither is presented as a legacy counterexample.",
      "claim-argument-evidence-audit-20260712.md":"# Claim argument evidence audit\n\nClaims, arguments and evidence now have separate registries. Legacy prose is not silently promoted to a valid argument or proof.",
      "schema-and-integrity-audit-20260712.md":"# Schema and integrity audit\n\nNine JSON Schemas and a standard-library integrity validator cover identities, references, counts, status axes, replay contracts and non-destructive migration.",
      "formalization-roadmap-20260712.md":"# Formalization roadmap\n\nPrioritize MF predicates, Y1 operational semantics, protocol typing, theorem candidates, then high-risk D records. Each promotion requires a linked proof or replay artifact.",
      "ai-entrypoint-audit-20260712.md":"# AI entrypoint audit\n\nAI-START-HERE.md, AI-HANDOFF.md, docs/AI-USAGE.md and docs/AI-PROMPT-TEMPLATES.md point agents to the same machine-readable authority and validation commands.",
      "migration-and-rollback-20260712.md":"# Migration and rollback\n\nMigration is additive. Old tables remain byte-identical. Roll back by removing generated foundation registries and views; no legacy content must be rewritten.",
      "validation-summary-20260712.md":f"# Validation summary\n\nExpected registry counts: {dump(counts)}\n\nThe final authoritative pass is produced by tools/foundation/validate_foundation.py and the benchmark runner."
    }
    report_text.update({
      "count-reconciliation-20260712.md":f"# Count reconciliation\n\n622 formal objects + 22 candidate-only records + 34 pending claims = 678 scoped claim entities. The separate evidence registry contains 806 formal cases + 22 candidate cases = 828 records.",
      "full-migration-coverage-20260712.md":"# Full migration coverage\n\nEvery deduplicated formal object has an object, claim, argument, source, mapping and open proof-obligation record. Every formal case and candidate case has an evidence record. Pending claims remain pending.",
      "core-system-reclassification-20260712.md":"# Core system reclassification\n\nY1 is a workflow orchestrator; JPLUS and JMINUS are internal evidence channels; the twelve protocols are heuristic or governance operators; the 64 combinations are a design space. None is a proof oracle.",
      "strong-claim-gate-audit-20260712.md":"# Strong claim gate audit\n\nLegacy theorem, axiom, isomorphism, causal and proved language was not promoted. All proof obligations remain open unless an indexed machine-checkable artifact exists.",
      "math-proof-backend-report-20260712.md":"# Math proof backend report\n\nLean 4, SymPy and Z3 were not available locally. A deterministic Python normalization proof fixture, a rational counterexample and a correctly pending open conjecture exercise the architecture without claiming Lean success.",
      "logic-validation-report-20260712.md":"# Logic validation report\n\nTruth-table fixtures establish modus ponens validity, replay a countermodel to affirming the consequent and keep analogy at DEFEASIBLE_SUPPORT.",
      "legacy-compatibility-report-20260712.md":"# Legacy compatibility report\n\nThe old tables are byte-preserved and mapped to generated compatibility views. Legacy IDs remain stable; new truth/status authority is data/foundation.",
      "unresolved-obligations-20260712.md":f"# Unresolved obligations\n\n{len(obligations)} item-level proof obligations remain open. Missing controlled semantics, types, boundaries, external evidence and proof artifacts must be repaired incrementally."
    })
    # Reports dated 20260712 and the 075 count snapshot are historical 076 outputs.
    # 078 writes new dated reports through adjudicate_core.py and must not rewrite history.
    for path,content in files.items(): write(path,content,check,changed)
    if check and changed:
        print("OUT_OF_DATE")
        print("\n".join(changed))
        return 1
    print(dump(counts))
    print("MIGRATION_CHECK_OK" if check else "MIGRATION_WRITE_OK")
    return 0

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--check",action="store_true")
    raise SystemExit(build(ap.parse_args().check))
