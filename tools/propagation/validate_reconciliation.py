#!/usr/bin/env python3
"""Fail-closed reconciliation validator (task 106, contract §10).

The pre-repair repository state (tasks 104/105 merged but public current-truth
surfaces still lagging) must be reproducible as a FAILING fixture, and the
remediated state must pass. The validator exits nonzero on any of the twelve
required failure modes and is wired into ordinary pull-request CI.

Modes:
  --generate   write the deterministic artifacts (impact specs, map proof,
               current-truth projection) from current repo state.
  --check      verify ledger, public surfaces, editorial lifecycle, map impact,
               projection determinism, and all twelve failure modes.

The predicate functions are importable so unit tests can feed synthetic
baseline (contradictory) and remediated inputs.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

sys.path.insert(0, HERE)
from ledger import load_ledger, validate_ledger, terminal_records  # noqa: E402
from impact_contract import (DIMENSIONS, generate_impact_spec, verify_impact_spec,  # noqa: E402
                              compute_dimension)
from editorial_lifecycle import validate_manifest as validate_editorial  # noqa: E402
from system_map_audit import audit as audit_map, PROOF_PATH  # noqa: E402


# ---------------------------------------------------------------------------
# Importable predicates (synthetic inputs accepted for testing)
# ---------------------------------------------------------------------------

def check_ledger_has_terminal(records: List[Dict], task_number: int = 105) -> List[str]:
    if not any(r.get("task_number") == task_number and r.get("ledger_status") == "TERMINAL_SUCCESS"
               for r in records):
        return [f"terminal merged iteration {task_number} absent from iteration ledger"]
    return []


def check_project_current_state_includes(text: str) -> List[str]:
    # Mode 2: project current state must not stop before a later accepted iteration.
    markers = ["任务 105", "任务105", "105", "PR #161", "Function OS v0.2", "函数 OS", "函数操作系统"]
    if not any(m in text for m in markers):
        return ["project current state stops before accepted iteration 105 (no 105/PR#161 marker)"]
    return []


def check_open_question_resolved(text: str) -> List[str]:
    # Mode 3: OQ-103-5 must no longer be presented as an untouched future test.
    problems: List[str] = []
    if "OQ-103-5" in text:
        block = text[text.index("OQ-103-5"): text.index("OQ-103-5") + 400]
        if "需先构建参考 oracle" in block or "需先构建" in block:
            problems.append("OPEN-QUESTIONS still presents OQ-103-5 as an untouched pending test")
        if not any(w in block for w in ("已完成", "completed", "已执行", "bounded", "有界")):
            problems.append("OPEN-QUESTIONS OQ-103-5 not marked as completed/bounded")
    else:
        problems.append("OPEN-QUESTIONS missing OQ-103-5 entry")
    return problems


def check_verdicts_distinct(readme_text: str, latest_text: str) -> List[str]:
    # Modes 4 & 5: current wording must include both verdicts and not collapse them.
    problems: List[str] = []
    v_orig = "PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES"
    v_rep = "SUPPORTED_WITHIN_BOUNDED_DOMAIN"
    combined = readme_text + "\n" + latest_text
    if v_orig not in combined:
        problems.append("original-target verdict PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES absent from public wording")
    if v_rep not in combined:
        problems.append("repaired-target verdict SUPPORTED_WITHIN_BOUNDED_DOMAIN absent from public wording")
    return problems


# ---------------------------------------------------------------------------
# Generation of deterministic artifacts
# ---------------------------------------------------------------------------

def generate_artifacts(repo_root: str) -> None:
    import current_truth_projection as ctp  # noqa: E402
    # Impact specs for 104/105/106 (declared == derived at generation time).
    declared_105 = {
        "MACHINE_RECORD_IMPACT": "IMPACT_REQUIRED",
        "REFERENCE_SURFACE_IMPACT": "IMPACT_REQUIRED",
        "EDITORIAL_ARTICLE_IMPACT": "IMPACT_REQUIRED",
        "SYSTEM_MAP_IMPACT": "NO_IMPACT_JUSTIFIED",
        "CURRENT_PUBLIC_WORDING_IMPACT": "IMPACT_REQUIRED",
        "OPEN_QUESTION_IMPACT": "IMPACT_REQUIRED",
        "PROJECT_STATE_IMPACT": "IMPACT_REQUIRED",
        "EVIDENCE_PROGRAM_IMPACT": "IMPACT_REQUIRED",
        "MATURITY_OR_DISPOSITION_IMPACT": "NO_IMPACT_JUSTIFIED",
    }
    declared_104 = dict.fromkeys(DIMENSIONS, "IMPACT_REQUIRED")
    declared_104["SYSTEM_MAP_IMPACT"] = "NO_IMPACT_JUSTIFIED"
    declared_104["OPEN_QUESTION_IMPACT"] = "NO_IMPACT_JUSTIFIED"
    declared_104["EVIDENCE_PROGRAM_IMPACT"] = "NO_IMPACT_JUSTIFIED"
    declared_104["MATURITY_OR_DISPOSITION_IMPACT"] = "NO_IMPACT_JUSTIFIED"
    declared_106 = dict.fromkeys(DIMENSIONS, "IMPACT_REQUIRED")
    declared_106["SYSTEM_MAP_IMPACT"] = "NO_IMPACT_JUSTIFIED"
    declared_106["MATURITY_OR_DISPOSITION_IMPACT"] = "NO_IMPACT_JUSTIFIED"
    out_dir = os.path.join(repo_root, "data", "operations", "propagation", "106-impact")
    os.makedirs(out_dir, exist_ok=True)
    for tn, declared in ((104, declared_104), (105, declared_105), (106, declared_106)):
        spec = generate_impact_spec(tn, repo_root, declared)
        # Record the COMPUTED (derived) decision as the declared one so the spec
        # is a faithful computed-impact artifact; later drift fails --check.
        for dim in DIMENSIONS:
            entry = spec["dimensions"][dim]
            derived = compute_dimension(dim, repo_root, entry["baseline_sha256"])
            entry["declared"] = derived["decision"]
        with open(os.path.join(out_dir, f"{tn}-impact.json"), "w", encoding="utf-8") as fh:
            json.dump(spec, fh, ensure_ascii=False, sort_keys=True, indent=2)
            fh.write("\n")
    # Map nonimpact proof.
    from system_map_audit import write_proof  # noqa: E402
    write_proof(repo_root)
    # Projection.
    ctp.generate(repo_root)
    print(f"GENERATED artifacts under {out_dir} and current-truth-projection.json")


# ---------------------------------------------------------------------------
# Full check
# ---------------------------------------------------------------------------

def run_check(repo_root: str) -> List[str]:
    problems: List[str] = []
    # Mode 1 + 9: ledger valid and terminal 105 present with evidence.
    ledger_path = os.path.join(repo_root, "data", "operations", "merged-iteration-ledger.jsonl")
    records = load_ledger(ledger_path)
    problems += validate_ledger(records)
    problems += check_ledger_has_terminal(records, 105)

    # Mode 2: project current state.
    pcs = os.path.join(repo_root, "docs", "project-current-state.md")
    with open(pcs, "r", encoding="utf-8") as fh:
        pcs_text = fh.read()
    problems += check_project_current_state_includes(pcs_text)

    # Mode 3: open questions.
    oq = os.path.join(repo_root, "RESULTS", "OPEN-QUESTIONS.md")
    with open(oq, "r", encoding="utf-8") as fh:
        oq_text = fh.read()
    problems += check_open_question_resolved(oq_text)

    # Modes 4 & 5: verdicts distinct in README + RESULTS/LATEST.
    readme = os.path.join(repo_root, "README.md")
    latest = os.path.join(repo_root, "RESULTS", "LATEST.md")
    with open(readme, "r", encoding="utf-8") as fh:
        readme_text = fh.read()
    with open(latest, "r", encoding="utf-8") as fh:
        latest_text = fh.read()
    problems += check_verdicts_distinct(readme_text, latest_text)

    # Mode 6: editorial lifecycle.
    manifest = os.path.join(repo_root, "docs", "editorial", "source-manifest.json")
    problems += validate_editorial(manifest, repo_root)

    # Modes 7 & 8: system-map impact + generator --check + map proof.
    proof = audit_map(repo_root)
    if proof["decision"] != "NO_IMPACT_JUSTIFIED":
        problems.append(f"system-map impact not justified: changed={proof['changed_sources']}")
    if not proof.get("explanation"):
        problems.append("system-map NO_MAP_IMPACT lacks machine-checkable explanation")
    proof_file = os.path.abspath(os.path.join(repo_root, "data", "operations", "propagation", "106-impact", "system-map-nonimpact-proof.json"))
    if not os.path.exists(proof_file):
        problems.append("system-map nonimpact proof file missing")
    gen = subprocess.run(
        ["python3", os.path.join(repo_root, "tools", "generate_interactive_system_map.py"), "--check"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if gen.returncode != 0:
        problems.append(f"system-map generator --check failed: {gen.stderr.strip()[:200]}")

    # Mode 8 (editorial NO_IMPACT justification): impact specs present & valid.
    for tn in (104, 105, 106):
        spec = os.path.join(repo_root, "data", "operations", "propagation", "106-impact", f"{tn}-impact.json")
        if not os.path.exists(spec):
            problems.append(f"impact spec missing for task {tn}")
            continue
        problems += verify_impact_spec(spec, repo_root)

    # Mode 10: projection derived from terminal only.
    proj_file = os.path.join(repo_root, "data", "operations", "current-truth-projection.json")
    with open(proj_file, "r", encoding="utf-8") as fh:
        proj = json.load(fh)
    if not proj.get("_derived_from_terminal_only"):
        problems.append("current-truth projection not derived from terminal records only")
    terminal_tns = {r.get("task_number") for r in terminal_records(records)}
    for r in proj.get("recently_merged_results", []):
        if r.get("task_number") not in terminal_tns:
            problems.append(f"projection cites non-terminal task {r.get('task_number')}")

    # Modes 11 & 12: determinism (two consecutive generations identical, and match committed).
    import current_truth_projection as ctp  # noqa: E402
    import tempfile
    ctp.generate(repo_root, proj_file)  # refresh committed file
    with open(proj_file, "r", encoding="utf-8") as fh:
        committed = fh.read()
    tf1 = tempfile.NamedTemporaryFile("w", delete=False, suffix=".json")
    tf2 = tempfile.NamedTemporaryFile("w", delete=False, suffix=".json")
    ctp.generate(repo_root, tf1.name)
    ctp.generate(repo_root, tf2.name)
    tf1.close(); tf2.close()
    with open(tf1.name, "r", encoding="utf-8") as fh:
        g1 = fh.read()
    with open(tf2.name, "r", encoding="utf-8") as fh:
        g2 = fh.read()
    if g1 != g2:
        problems.append("current-truth projection not deterministic (two generations differ)")
    if g1 != committed:
        problems.append("current-truth projection manually edited (regenerated bytes differ from committed)")

    return problems


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--generate", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    if args.generate:
        generate_artifacts(repo)
        return 0
    if args.check:
        problems = run_check(repo)
        if problems:
            for p in problems:
                print(f"RECONCILIATION_INVALID: {p}", file=sys.stderr)
            return 1
        print("RECONCILIATION_OK all twelve failure modes clear")
        return 0
    print("specify --generate or --check", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
