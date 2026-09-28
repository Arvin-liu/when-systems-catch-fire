#!/usr/bin/env python3
"""Fail-closed pre-freeze design and frozen-tree validator for Task227."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[5]
SUBTREE=REPO/"ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0"
BASE="b6acf6856128833677c35d85a9f088cb49b5d4f2"
FAMILIES=("FAMILY01","FAMILY02","FAMILY03")
RUNS={"foundation-validation":36345482994,"repository-path-accounting-preflight":36345483024,"architecture-pages":36345482985,"q33-governance-validation":36345482980}

def fail(message:str)->None:raise SystemExit("TASK227_DESIGN_INVALID: "+message)
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path:Path):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:fail(f"invalid JSON {path}: {exc}")

def main()->None:
    required=[
      "README.md","design/protocol.md","design/taxonomy-to-schema.md",
      "design/task226-evidence-binding-receipt.md","design/formal-anchor-receipt.md",
      "reference/builder-prompt.md","reference/policy-schema.json","reference/validity-criteria.md",
      "reference/reviewer-criteria.md","reference/criteria.json","reference/evaluator-schema.json",
      "revision/prompt.md","revision/evaluator/criteria.md","revision/evaluator/schema.json","revision/outcome-rule.json",
      "transfer/prompt.md","transfer/response-schema.json","transfer/template.md",
      "transfer/interpretation.md","transfer/outcome-rule.json","transfer/evaluator-schema.json","transfer/evaluator-criteria.md",
      "transfer/evaluator-criteria.md","transfer/input-integrity-recipe.md","freeze/condition-map-recipe.md",
      "tools/build_freeze_manifest.py","tools/validate_policy.py","tools/validate_transfer_response.py","tools/sanitize_transfer_packet.py","tools/requirements.txt"
    ]
    for rel in required:
        if not (SUBTREE/rel).is_file():fail(f"missing required file {rel}")
    for rel in ("reference/policy-schema.json","reference/criteria.json","reference/evaluator-schema.json",
                "transfer/response-schema.json","transfer/evaluator-schema.json","transfer/outcome-rule.json",
                "revision/evaluator/schema.json","revision/outcome-rule.json"):
        load(SUBTREE/rel)
    policy=load(SUBTREE/"reference/policy-schema.json")
    fields={"policy_id","evidence_basis","selector","applicability","action_table","preserved_rules","fallback","stop_conditions","scope_ceiling","provenance"}
    if set(policy.get("required",[]))!=fields:fail("policy schema top-level contract changed")
    if not {"condition","input","scopeClaim","provenance"}.issubset(policy.get("$defs",{})):fail("policy schema lacks typed conditions, inputs, scopes, or provenance")
    transfer_schema=load(SUBTREE/"transfer/response-schema.json")
    if "evidence_provenance" in json.dumps(transfer_schema):fail("transfer output exposes free-form source provenance")
    outcome=load(SUBTREE/"transfer/outcome-rule.json")
    if outcome.get("fixed_denominator")!=6:fail("Component-A denominator must be six")
    if outcome.get("per_lineage",{}).get("CHAIN")!="REF_A AND NOT O_A AND REF_B AND REF_C":fail("complete-case Component-A chain changed")
    missing=outcome.get("missingness",{})
    if "force that lineage CHAIN=false" not in missing.get("negative_control_gate",""):fail("missing negative-control data can satisfy NOT O_A")
    if "O_A_CONTROL_OBSERVED=false" not in (SUBTREE/"transfer/interpretation.md").read_text(encoding="utf-8"):fail("negative-control missingness semantics missing")
    evaluator_schema=load(SUBTREE/"transfer/evaluator-schema.json")
    item=evaluator_schema.get("properties",{}).get("scores",{}).get("items",{})
    if "valid_response" not in item.get("required",[]) or "valid_response" not in item.get("properties",{}):fail("transfer evaluator validity field absent")
    if "valid_response" not in (SUBTREE/"transfer/evaluator-criteria.md").read_text(encoding="utf-8"):fail("transfer evaluator criteria/schema mismatch")
    # Run the policy contract's official schema-only mode.
    result=subprocess.run([sys.executable,str(SUBTREE/"tools/validate_policy.py"),"--schema-only"],cwd=REPO,text=True,capture_output=True)
    if result.returncode!=0:fail("policy schema validator failed: "+result.stdout+result.stderr)
    expected_sources={}
    for family in FAMILIES:
        expected_sources[family]={
          f"ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/{family}/m0.md",
          f"ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/{family}/revision-evidence-e1.md"
        }
    for folder,prefix,prompt in (
      ("reference/manifests","REF-","reference/builder-prompt.md"),
      ("revision/manifests","REV-","revision/prompt.md")
    ):
        paths=sorted((SUBTREE/folder).glob("*.json"))
        if len(paths)!=6:fail(f"{folder} must contain exactly six manifests")
        ids=set()
        for path in paths:
            data=load(path);tid=data.get("builder_id",data.get("revision_id"))
            if not isinstance(tid,str) or not tid.startswith(prefix) or tid in ids:fail(f"duplicate or malformed ID in {path.name}")
            ids.add(tid)
            family=data.get("family_id")
            if family not in FAMILIES:fail(f"{tid} has unknown family")
            allowed=data.get("permitted_inputs")
            if not isinstance(allowed,list) or len(allowed)!=4:fail(f"{tid} must have four allowed inputs")
            paths_set={x.get("path") for x in allowed if isinstance(x,dict)}
            expected=expected_sources[family]|{
              "ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/reference/policy-schema.json",
              f"ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/{prompt}"
            }
            if paths_set!=expected or len(paths_set)!=4:fail(f"{tid} allowlist differs from contract")
            for entry in allowed:
                target=REPO/entry["path"]
                if not target.is_file() or sha(target)!=entry.get("sha256"):fail(f"{tid} input hash mismatch: {entry.get('path')}")
                lower=entry["path"].lower()
                if any(token in lower for token in ("/cases/","/sealed/","target","task226","r7")):fail(f"{tid} includes prohibited input {entry['path']}")
            if data.get("fresh_session") is not True:fail(f"{tid} is not fresh")
    receipt=(SUBTREE/"design/task226-evidence-binding-receipt.md").read_text(encoding="utf-8")
    for token in ("R7_RESULT_PRESERVED=NOT_SUPPORTED","LINEAGES_ANALYZED=6","EVALUATORS_ANALYZED=2","R6_QUARANTINE_BREACH=false","NEW_EXPERIMENTS_RUN=0","FORMAL_REPO_MODIFIED=false","PRIMARY_FAILURE_MODE=MIXED_REVISION_GENERATION_TARGET_COMPATIBILITY_AND_M1_TRANSFER_INTERFACE","SECONDARY_FAILURE_MODE=EVALUATOR_SENSITIVE_CRITICAL_ERROR_FLAGS_AND_EDGE_HANDLING","PRIMARY_NEXT_DIRECTION=MIXED_REPAIR"):
        if token not in receipt:fail(f"Task226 evidence receipt missing {token}")
    anchor=(SUBTREE/"design/formal-anchor-receipt.md").read_text(encoding="utf-8")
    for token in (BASE,"8989a7c58e602f1e02c5de95af1cde418ad827a9","OPEN + DRAFT + unmerged","36345482994","36345483024","36345482985","36345482980"):
        if token not in anchor:fail(f"Formal anchor receipt missing {token}")
    for label in "ABCDE":
        report=SUBTREE/"review"/f"reviewer-{label}.md"
        if not report.is_file() or "RESULT=PASS" not in report.read_text(encoding="utf-8"):fail(f"review {label} is not PASS")
    if "TASK227_REFERENCE_M1_TARGET_LEAKAGE" in (SUBTREE/"review/reviewer-B.md").read_text(encoding="utf-8"):fail("reference M1 leakage stop")
    if "TASK227_TARGET_COMPATIBILITY_FAILED_PREOUTPUT" in (SUBTREE/"review/reviewer-C.md").read_text(encoding="utf-8"):fail("target compatibility stop")
    outputs=SUBTREE/"outputs"
    if outputs.exists() and any(p.is_file() for p in outputs.rglob("*")):fail("Task227 outputs must be zero at freeze")
    manifest_path=SUBTREE/"freeze/freeze-manifest.json";side=SUBTREE/"freeze/freeze.sha256"
    if not manifest_path.is_file() or not side.is_file():fail("freeze manifest/sidecar missing")
    manifest=load(manifest_path)
    if manifest.get("study_class")!="POST_RESULT_EXPLORATORY_COMPONENT_ISOLATION_R0":fail("study class mismatch")
    if manifest.get("formal_anchor",{}).get("head")!=BASE or manifest.get("formal_anchor",{}).get("required_ci_runs")!=RUNS:fail("anchor refs mismatch")
    if manifest.get("design_gate",{}).get("hard_issues_unresolved")!=0:fail("unresolved pre-freeze issues")
    if manifest.get("outputs_at_scientific_freeze")!={"reference_m1":0,"transfer":0,"revision_generation":0,"evaluator":0}:fail("freeze output counts are not zero")
    actual={}
    for path in SUBTREE.rglob("*"):
        if not path.is_file() or path in (manifest_path,side) or "outputs" in path.relative_to(SUBTREE).parts:continue
        actual[path.relative_to(REPO).as_posix()]=sha(path)
    recorded={x["path"]:x["sha256"] for x in manifest.get("frozen_files",[])}
    if set(actual)!=set(recorded):fail(f"frozen inventory mismatch missing={sorted(set(actual)-set(recorded))} extra={sorted(set(recorded)-set(actual))}")
    for path,digest in recorded.items():
        if actual[path]!=digest:fail(f"frozen hash mismatch: {path}")
    sources=manifest.get("external_m0_e1_inputs",[])
    if len(sources)!=6:fail("expected six M0/E1 source hashes")
    for entry in sources:
        source=REPO/entry["path"]
        if not source.is_file() or sha(source)!=entry.get("sha256"):fail(f"M0/E1 hash mismatch {entry.get('path')}")
    for key in ("task226_evidence_binding","formal_anchor"):
        evidence=manifest[key];evidence_path=REPO/evidence["receipt_path"]
        if not evidence_path.is_file() or sha(evidence_path)!=evidence["receipt_sha256"]:fail(f"{key} receipt hash mismatch")
    if side.read_text(encoding="utf-8")!=f"{sha(manifest_path)}  freeze-manifest.json\n":fail("freeze sidecar mismatch")
    print("TASK227_DESIGN_VALIDATION=PASS")
    print("PREFREEZE_REVIEWERS=5/5_PASS")
    print("REFERENCE_BUILDERS=6")
    print("COMPONENT_A_TRANSFERS=18")
    print("REVISION_SESSIONS=6")
    print("SCIENTIFIC_OUTPUTS_AT_FREEZE=0")

if __name__=="__main__":
    try:main()
    except SystemExit:raise
    except Exception as exc:fail(str(exc))
