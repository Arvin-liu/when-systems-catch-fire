#!/usr/bin/env python3
"""Build deterministic Task227 freeze manifest and sidecar after all five reviews pass."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

REPO=Path(__file__).resolve().parents[5]
SUBTREE=REPO/"ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0"
MANIFEST=SUBTREE/"freeze/freeze-manifest.json"
SIDECAR=SUBTREE/"freeze/freeze.sha256"
BASE="b6acf6856128833677c35d85a9f088cb49b5d4f2"
PRE_FREEZE_HEAD="eefa2126e9bbdcf684d43e5000395420240f35ea"
RECOVERY_COMMAND_SHA="737cf17b7eec263537d60da1f6c9174645f40614"
COMPONENT_COMMAND_SHA="d339343803ee4269f1ee96ed191930919acd6b5c"
REQUIRED_RUNS={
 "foundation-validation":36345482994,
 "repository-path-accounting-preflight":36345483024,
 "architecture-pages":36345482985,
 "q33-governance-validation":36345482980
}

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rel(path:Path)->str:
    return path.relative_to(REPO).as_posix()

def main()->None:
    reviews=[SUBTREE/"review"/f"reviewer-{role}.md" for role in "ABCDE"]
    for path in reviews:
        if not path.is_file() or "RESULT=PASS" not in path.read_text(encoding="utf-8"):
            raise SystemExit(f"pre-freeze reviewer not PASS: {path.name}")
    anchor_receipt=SUBTREE/"design/formal-anchor-receipt.md"
    if not anchor_receipt.is_file():raise SystemExit("formal anchor receipt missing")
    anchor_text=anchor_receipt.read_text(encoding="utf-8")
    required_tokens=[
      "OPEN + DRAFT + unmerged",BASE,"8989a7c58e602f1e02c5de95af1cde418ad827a9",
      "36345482994","36345483024","36345482985","36345482980"
    ]
    if any(token not in anchor_text for token in required_tokens):
        raise SystemExit("formal anchor receipt does not prove required anchor")
    frozen=[]
    for path in sorted(SUBTREE.rglob("*")):
        if not path.is_file() or path in (MANIFEST,SIDECAR):continue
        if "outputs" in path.relative_to(SUBTREE).parts:continue
        frozen.append({"path":rel(path),"sha256":sha(path)})
    source_root=REPO/"ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families"
    source=[]
    for family in ("FAMILY01","FAMILY02","FAMILY03"):
        for name in ("m0.md","revision-evidence-e1.md"):
            path=source_root/family/name
            source.append({"path":rel(path),"sha256":sha(path)})
    payload={
      "freeze_version":"TASK227_COMPONENT_ISOLATION_R0",
      "study_class":"POST_RESULT_EXPLORATORY_COMPONENT_ISOLATION_R0",
      "commands":[
        {"repository":"Arvin-liu/1111","path":"agent-commands/IGNITION-20260928-227-R1-RECOVER-TASK226-AND-RESUME.md","sha256":RECOVERY_COMMAND_SHA},
        {"repository":"Arvin-liu/1111","path":"agent-commands/IGNITION-20260928-227-COMPONENT-ISOLATION-R0-MIXED-REPAIR.md","sha256":COMPONENT_COMMAND_SHA}
      ],
      "formal_anchor":{
        "pr":236,"state":"OPEN_DRAFT_UNMERGED",
        "head":BASE,"base":"8989a7c58e602f1e02c5de95af1cde418ad827a9",
        "required_ci_runs":REQUIRED_RUNS,
        "receipt_path":rel(anchor_receipt),"receipt_sha256":sha(anchor_receipt)
      },
      "task227_branch":"work/IGNITION-20260928-227-cognitive-evolution-component-isolation-r0",
      "task227_pr":237,"task227_state":"OPEN_DRAFT_UNMERGED",
      "starting_head_before_freeze":PRE_FREEZE_HEAD,
      "design_gate":{"reviewers":{"A":"PASS","B":"PASS","C":"PASS","D":"PASS","E":"PASS"},"target_families":"3/3","hard_issues_unresolved":0},
      "fixed_design":{"reference_builders":6,"component_a_transfers":18,"revision_sessions":6,"component_a_evaluators":2,"component_b_evaluators":2,"denominator":6},
      "outputs_at_scientific_freeze":{"reference_m1":0,"transfer":0,"revision_generation":0,"evaluator":0},
      "task226_evidence_binding":{"receipt_path":rel(SUBTREE/"design/task226-evidence-binding-receipt.md"),"receipt_sha256":sha(SUBTREE/"design/task226-evidence-binding-receipt.md")},
      "external_m0_e1_inputs":source,
      "frozen_files":frozen
    }
    MANIFEST.parent.mkdir(parents=True,exist_ok=True)
    MANIFEST.write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    SIDECAR.write_text(f"{sha(MANIFEST)}  freeze-manifest.json\n",encoding="utf-8")

if __name__=="__main__":
    main()
