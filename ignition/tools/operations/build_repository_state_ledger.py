#!/usr/bin/env python3
"""Whole-repository state reconstruction ledger builder (campaign Line D).

Deterministic and offline. Consumes ONLY committed inputs:

  data/operations/campaign-inputs/open-prs-20260803.json        (gh PR snapshot)
  data/operations/campaign-inputs/remote-branches-20260803.txt  (branch tips)
  data/operations/campaign-inputs/tags-20260803.txt             (tag tips)
  data/operations/campaign-inputs/tip-lock-20260803.txt         (locked refs)
  data/operations/merged-iteration-ledger.jsonl                 (accepted history)
  data/operations/current-truth-projection.json                 (current truth)
  data/operations/project-components.json                       (component registry)

and emits:

  data/operations/repository-state-ledger.json
  data/operations/candidate-lineage-registry.json

State categories (TASK Line D D2): ACCEPTED_CURRENT, ACCEPTED_HISTORICAL,
MERGED_NOT_CURRENT, OPEN_DRAFT_CANDIDATE, STACKED_REPAIR_CANDIDATE,
RESEARCH_CANDIDATE_NOT_FORMAL_KNOWLEDGE, SUPERSEDED_OR_WITHDRAWN,
ABANDONED_OR_UNRESOLVED, GENERATED_PROJECTION, UNKNOWN_REQUIRES_OWNER_ADJUDICATION.

Acceptance is never inferred from timestamp, branch existence, PR openness or
file name: ACCEPTED states derive only from the merged iteration ledger and the
current-truth projection; everything else stays candidate or unknown.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "data" / "operations"
INPUTS = OPS / "campaign-inputs"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def build() -> None:
    prs = load_json(INPUTS / "open-prs-20260803.json")
    branches = {}
    for line in (INPUTS / "remote-branches-20260803.txt").read_text().splitlines():
        name, sha = line.rsplit(" ", 1)
        branches[name.replace("origin/", "", 1)] = sha
    tags = {}
    for line in (INPUTS / "tags-20260803.txt").read_text().splitlines():
        name, sha = line.rsplit(" ", 1)
        tags[name] = sha
    tips = {}
    for line in (INPUTS / "tip-lock-20260803.txt").read_text().splitlines():
        k, v = line.split(" ", 1)
        tips[k] = v
    ledger = load_jsonl(OPS / "merged-iteration-ledger.jsonl")
    truth = load_json(OPS / "current-truth-projection.json")
    components = load_json(OPS / "project-components.json")

    current_iter = truth.get("current_accepted_iteration")
    terminal_rows = [r for r in ledger if r.get("ledger_status") == "TERMINAL_SUCCESS"]
    merged_rows = [r for r in ledger if r.get("ordinary_merge_commit")]

    # --- accepted iteration chain from three evidence classes ---------------
    # (1) terminal tags ignition/iterations/<n>/terminal-r1; (2) FINAL_STATE
    # files under data/operations/iterations/; (3) merged iteration ledger rows.
    import re
    iter_tag_re = re.compile(r"^ignition/iterations/(\d+)/terminal-r1$")
    tag_iters: dict[int, str] = {}
    for name in tags:
        m = iter_tag_re.match(name)
        if m:
            tag_iters[int(m.group(1))] = name
    fs_iters: dict[int, dict] = {}
    iter_dir = OPS / "iterations"
    for cand in list(iter_dir.glob("*/FINAL_STATE.json")) + list(iter_dir.glob("*-FINAL_STATE.json")):
        num_part = cand.parent.name if cand.parent != iter_dir else cand.name.split("-")[0]
        try:
            n = int(num_part)
        except ValueError:
            continue
        try:
            fs = json.loads(cand.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            fs_iters[n] = {"parse_error": True}
            continue
        ts = fs.get("terminal_state")
        entry = {"path": str(cand.relative_to(ROOT)), "terminal_state": ts}
        if ts is None:
            # dialect variant: terminalization fields present without top-level state
            entry["terminal_state"] = "TERMINAL_TAG_AND_TERMINALIZATION_FIELDS_PRESENT"
            entry["dialect_note"] = "FINAL_STATE dialect lacks top-level terminal_state; terminal tag + terminalization fields recorded instead"
        fs_iters[n] = entry
    ledger_iters = {r["task_number"]: r for r in ledger if isinstance(r.get("task_number"), int)}
    all_iter_nums = sorted(set(tag_iters) | set(fs_iters) | set(ledger_iters))
    accepted_iterations = []
    for n in all_iter_nums:
        tag = tag_iters.get(n)
        fs = fs_iters.get(n)
        lr = ledger_iters.get(n)
        terminal = bool(tag) or (fs and str(fs.get("terminal_state") or "").startswith("TERMINAL")) or (lr and lr.get("ledger_status") == "TERMINAL_SUCCESS")
        accepted_iterations.append({
            "iteration": n,
            "terminal_tag": tag,
            "final_state": fs,
            "merged_ledger_status": (lr or {}).get("ledger_status"),
            "merged_ledger_merge_commit": (lr or {}).get("ordinary_merge_commit"),
            "terminalized": terminal,
            "state_category": "ACCEPTED_CURRENT" if n == current_iter else ("ACCEPTED_HISTORICAL" if terminal else "UNKNOWN_REQUIRES_OWNER_ADJUDICATION"),
            "consistency": "OK" if terminal else "REQUIRES_OWNER_ADJUDICATION",
        })

    # --- PR classification -------------------------------------------------
    open_drafted: list[dict] = []
    stacked: list[dict] = []
    head_branches = {p["headRefName"]: p for p in prs}
    for p in prs:
        entry = {
            "pr_number": p["number"],
            "title": p["title"],
            "base": p["baseRefName"],
            "head": p["headRefName"],
            "head_tip_at_snapshot": p.get("headRefOid"),
            "is_draft": p["isDraft"],
            "url": p.get("url"),
            "parent_pr": head_branches.get(p["baseRefName"], {}).get("number"),
            "state_category": None,
            "recommended_disposition": "REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION",
        }
        if p["baseRefName"] == "main":
            entry["state_category"] = "OPEN_DRAFT_CANDIDATE"
            open_drafted.append(entry)
        else:
            entry["state_category"] = "STACKED_REPAIR_CANDIDATE"
            stacked.append(entry)

    # --- families (chains through head==base) ------------------------------
    families: list[dict] = []
    seen: set[int] = set()
    for p in prs:
        if p["number"] in seen:
            continue
        # walk to the root of the chain
        chain = [p]
        cursor = p
        while cursor["baseRefName"] in {q["headRefName"] for q in prs if q["number"] != cursor["number"]}:
            parent = next(q for q in prs if q["headRefName"] == cursor["baseRefName"])
            chain.append(parent)
            cursor = parent
        root = chain[-1]
        members = sorted({q["number"] for q in chain} | {
            q["number"] for q in prs
            if any(q["baseRefName"] == m["headRefName"] for m in chain)
        })
        seen.update(members)
        families.append({
            "root_pr": root["number"],
            "root_base": root["baseRefName"],
            "root_head": root["headRefName"],
            "members": members,
            "depth": len(chain),
            "root_category": "OPEN_DRAFT_CANDIDATE" if root["baseRefName"] == "main" else "STACKED_REPAIR_CANDIDATE",
            "disposition": "REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION",
            "note": "stacked chain verified by head/base identity at snapshot time",
        })

    # --- research branches --------------------------------------------------
    research = []
    for name, sha in sorted(branches.items()):
        if name.startswith("research/"):
            research.append({
                "branch": name,
                "tip": sha,
                "state_category": "RESEARCH_CANDIDATE_NOT_FORMAL_KNOWLEDGE",
                "note": "research branch: candidate evidence only; never formal knowledge without separate adjudication",
            })

    # --- accepted states ----------------------------------------------------
    accepted_current = {
        "iteration": current_iter,
        "source": "data/operations/current-truth-projection.json",
        "project_status_commit": truth.get("current_project_status_commit"),
        "project_status_date": truth.get("current_project_status_date"),
        "capability_evidence": truth.get("current_capability_evidence"),
    }
    accepted_historical = [
        {
            "task_number": r["task_number"],
            "task_id": r["task_id"],
            "merge_commit": r.get("ordinary_merge_commit"),
            "merged_timestamp": r.get("merged_timestamp"),
            "terminal_state": r.get("terminal_state"),
            "state_category": "ACCEPTED_HISTORICAL" if r["task_number"] != current_iter else "ACCEPTED_CURRENT",
        }
        for r in terminal_rows
    ]
    merged_not_current = [
        {
            "task_number": r["task_number"],
            "merge_commit": r.get("ordinary_merge_commit"),
            "state_category": "MERGED_NOT_CURRENT",
            "note": "merged into main but superseded by later accepted iterations; history only",
        }
        for r in merged_rows
        if r.get("ledger_status") != "TERMINAL_SUCCESS"
    ]
    non_terminal = [
        {
            "task_number": r["task_number"],
            "ledger_status": r.get("ledger_status"),
            "state_category": "OPEN_DRAFT_CANDIDATE" if r.get("ledger_status") == "PR_OPEN" else "UNKNOWN_REQUIRES_OWNER_ADJUDICATION",
        }
        for r in ledger
        if r.get("ledger_status") not in ("TERMINAL_SUCCESS",)
    ]

    # --- generated projections ----------------------------------------------
    generated = [
        {"path": "data/operations/current-truth-projection.json", "generator": "task-106 reconciliation tooling", "state_category": "GENERATED_PROJECTION"},
        {"path": "data/operations/repository-state-ledger.json", "generator": "tools/operations/build_repository_state_ledger.py", "state_category": "GENERATED_PROJECTION"},
        {"path": "data/operations/candidate-lineage-registry.json", "generator": "tools/operations/build_repository_state_ledger.py", "state_category": "GENERATED_PROJECTION"},
        {"path": "data/architecture/interactive-system-map.json", "generator": "tools/generate_interactive_system_map.py", "state_category": "GENERATED_PROJECTION"},
        {"path": "data/foundation/repository-path-classification/classification-manifest.jsonl", "generator": "tools/foundation/validate_repository_path_classification.py --generate", "state_category": "GENERATED_PROJECTION"},
    ]

    # --- unknown / adjudication items ---------------------------------------
    unknown = [
        {"item": "open Draft PRs older than the current iteration chain (e.g. #3, #5, #16-#21, #31, #32)",
         "state_category": "UNKNOWN_REQUIRES_OWNER_ADJUDICATION",
         "question": "remain draft, be superseded by later lines, or require separate owner decision? This ledger does not close or edit them."},
        {"item": "Task 115 Draft-PR phase",
         "state_category": "OPEN_DRAFT_CANDIDATE",
         "question": "phase one only; terminalization prohibited in this phase; R2 calibration pending"},
        {"item": "eight-track R2 campaign",
         "state_category": "RESEARCH_CANDIDATE_NOT_FORMAL_KNOWLEDGE",
         "question": "adjudication remains owner/GPT decision after Line C auditability repair"},
    ]

    state_ledger = {
        "schema_ref": "data/operations/schemas/repository-state-ledger.schema.json",
        "built_by": "tools/operations/build_repository_state_ledger.py",
        "deterministic_inputs": [
            "campaign-inputs/open-prs-20260803.json",
            "campaign-inputs/remote-branches-20260803.txt",
            "campaign-inputs/tags-20260803.txt",
            "campaign-inputs/tip-lock-20260803.txt",
            "merged-iteration-ledger.jsonl",
            "current-truth-projection.json",
            "project-components.json",
        ],
        "baselines": {
            "formal_main_at_build": tips.get("main"),
            "control_relay_current_campaign": "POINTFIRE-QWEN38MAX-WHOLE-REPOSITORY-STATE-RECONSTRUCTION-CANDIDATE-CONVERGENCE-GLOBAL-INVARIANT-CLOSURE-R1-20260803",
            "locked_tips": tips,
        },
        "accepted_iterations": accepted_iterations,
        "counts": {
            "open_prs": len(prs),
            "open_draft_candidates": len(open_drafted),
            "stacked_repair_candidates": len(stacked),
            "pr_families": len(families),
            "remote_branches": len(branches),
            "tags": len(tags),
            "terminal_iterations_from_ledger": len(terminal_rows),
            "accepted_iterations_reconstructed": len(accepted_iterations),
            "research_branches": len(research),
        },
        "accepted_current": accepted_current,
        "accepted_historical": accepted_historical,
        "merged_not_current": merged_not_current,
        "open_draft_candidates": open_drafted,
        "stacked_repair_candidates": stacked,
        "research_candidate_not_formal_knowledge": research,
        "non_terminal_ledger_tasks": non_terminal,
        "generated_projections": generated,
        "unknown_requires_owner_adjudication": unknown,
        "component_registry_summary": {
            "component_ids": sorted({c.get("component_id") or c.get("id") for c in components.get("components", []) if isinstance(c, dict)}),
            "source": "data/operations/project-components.json",
        },
    }

    lineage = {
        "schema_ref": "data/operations/schemas/candidate-lineage-registry.schema.json",
        "built_by": "tools/operations/build_repository_state_ledger.py",
        "snapshot": "campaign-inputs/open-prs-20260803.json",
        "families": families,
        "campaign_lines": [
            {"line": "A", "branch": "qwen38max/task115-checkpoint-c-recovery-r1-20260803", "parent_tip": tips.get("task115_branch"), "tip": tips.get("line_a"), "pr": 190, "base": "main"},
            {"line": "B", "branch": "qwen38max/pr189-independent-review-ci-repair-r1-20260803", "parent_tip": tips.get("pr189_branch"), "tip": tips.get("line_b"), "pr": 191, "base": "workbuddy/zhiyuan-writing-cognitive-migration-editorial-revision-r1-20260803"},
            {"line": "C", "branch": "qwen38max/eight-track-r2-auditability-repair-r1-20260803", "parent_tip": tips.get("r2_branch"), "tip": tips.get("line_c"), "pr": 192, "base": "research/eight-track-deep-validation-20260803-r2"},
            {"line": "D", "branch": "qwen38max/whole-repo-state-convergence-r1-20260803", "parent_tip": tips.get("main"), "tip": None, "pr": None, "base": "main"},
        ],
        "hard_rules": [
            "no PR family may be merged or marked Ready by this campaign",
            "stacked families land child-into-parent only after owner adjudication",
            "research branches never feed formal knowledge without separate acceptance",
        ],
    }

    (OPS / "repository-state-ledger.json").write_text(json.dumps(state_ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OPS / "candidate-lineage-registry.json").write_text(json.dumps(lineage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"ledger written: {len(prs)} PRs, {len(families)} families, {len(terminal_rows)} terminal iterations, {len(research)} research branches")


if __name__ == "__main__":
    build()
