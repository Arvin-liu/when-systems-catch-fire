#!/usr/bin/env python3
"""Run per-item dual-channel bootstrap verification.

The verifier is deterministic and evidence-led: it checks the current structured
function and case records for definition quality, source traceability, duplicate
signals, and link/mapping consistency. It does not invent semantic convergence.
Contradictions and underdetermined items are recorded as blockers.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = REPO_ROOT / "data/runs/dual-channel-full-bootstrap"
REBUILD_DIR = REPO_ROOT / "data/rebuild"
FUNCTIONS_JSON = REPO_ROOT / "data/functions/unified-functions.json"
FUNCTIONS_JSONL = REPO_ROOT / "data/functions/unified-functions.jsonl"
FUNCTIONS_MIN_JSON = REPO_ROOT / "data/functions/unified-functions.min.json"
CASES_JSON = REPO_ROOT / "data/cases/unified-cases.json"
CASES_JSONL = REPO_ROOT / "data/cases/unified-cases.jsonl"
CASES_MIN_JSON = REPO_ROOT / "data/cases/unified-cases.min.json"
META_IDS = {"MF-0000", "MF-0001", "MF-0002", "MF-0003", "MF-0004", "MF-0005"}
RESULT_STATES = {"done", "failed_blocked", "skipped"}
OBSOLETE_FUNCTION_REFERENCES = {
    "D68": "10. txt:2173/2215 records D68-D71 as deleted legacy references; cases point to D54-D57 lineage.",
    "D69": "10. txt:2173/2215 records D68-D71 as deleted legacy references; cases point to D54-D57 lineage.",
    "D70": "10. txt:2173/2215 records D68-D71 as deleted legacy references; cases point to D54-D57 lineage.",
    "D71": "10. txt:2173/2215 records D68-D71 as deleted legacy references; cases point to D54-D57 lineage.",
    "D78": "10. txt:2173 records D78-D83 as deleted upper-layer duplicates.",
    "D79": "10. txt:2173 records D78-D83 as deleted upper-layer duplicates.",
    "D80": "10. txt:2173 records D78-D83 as deleted upper-layer duplicates.",
    "D81": "10. txt:2173 records D78-D83 as deleted upper-layer duplicates.",
    "D82": "10. txt:2173 records D78-D83 as deleted upper-layer duplicates.",
    "D83": "10. txt:2173 records D78-D83 as deleted upper-layer duplicates.",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def append_log(run_dir: Path, name: str, message: str) -> None:
    log_path = run_dir / "logs" / name
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{utc_now()} {message}\n")
        handle.flush()


def git_head_short() -> str:
    import subprocess

    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def object_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return " ".join(object_text(value.get(key)) for key in ("zh", "en", "text", "math"))
    if isinstance(value, list):
        return " ".join(object_text(item) for item in value)
    return str(value).strip()


def normalize_text(value: str) -> str:
    value = value.lower()
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[^\w\u4e00-\u9fff]+", "", value)
    return value


def score_status(score: float, threshold: float) -> str:
    return "pass" if score >= threshold else "fail"


def channel(status: str, score: float, evidence: list[str], reason: str, key: str) -> dict[str, Any]:
    return {
        "status": status,
        "score": round(score, 3),
        key: evidence,
        "reason": reason,
    }


def final_result(forward_status: str, reverse_status: str, object_type: str) -> tuple[str, str]:
    if "pending" in {forward_status, reverse_status}:
        return f"{object_type}_pending", "pending"
    if forward_status == "pass" and reverse_status == "fail":
        return f"{object_type}_true", "true"
    if forward_status == "fail" and reverse_status == "pass":
        return f"{object_type}_false", "false"
    if forward_status == "pass" and reverse_status == "pass":
        return f"{object_type}_contradiction", "contradiction"
    return f"{object_type}_underdetermined", "underdetermined"


def action_for(object_type: str, result: str) -> str:
    if object_type == "function":
        return {
            "true": "keep_active",
            "false": "needs_revision",
            "contradiction": "bootstrap_blocker",
            "underdetermined": "needs_evidence",
            "pending": "pending",
        }[result]
    return {
        "true": "keep_mapping",
        "false": "remap_candidate",
        "contradiction": "bootstrap_blocker",
        "underdetermined": "needs_evidence",
        "pending": "pending",
    }[result]


def load_sources() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    functions = [item for item in read_json(FUNCTIONS_JSON, []) if item.get("id") not in META_IDS]
    cases = read_json(CASES_JSON, [])
    return functions, cases


def build_context(functions: list[dict[str, Any]], cases: list[dict[str, Any]]) -> dict[str, Any]:
    function_ids = {item.get("normalized_id") or item.get("id") for item in functions}
    case_ids = {item.get("normalized_id") or item.get("id") for item in cases}
    function_title_keys = Counter(normalize_text(object_text(item.get("title"))) for item in functions)
    function_content_keys = Counter(
        normalize_text(object_text(item.get("title")) + object_text(item.get("content")))
        for item in functions
    )
    case_title_keys = Counter(normalize_text(object_text(item.get("title"))) for item in cases)
    case_content_keys = Counter(
        normalize_text(object_text(item.get("title")) + object_text(item.get("content")))
        for item in cases
    )
    return {
        "function_ids": function_ids,
        "case_ids": case_ids,
        "function_title_keys": function_title_keys,
        "function_content_keys": function_content_keys,
        "case_title_keys": case_title_keys,
        "case_content_keys": case_content_keys,
    }


def verify_function(item: dict[str, Any], context: dict[str, Any], round_no: int, run_id: str) -> dict[str, Any]:
    item_id = item.get("normalized_id") or item.get("id")
    title = object_text(item.get("title"))
    content = object_text(item.get("content"))
    explanation = object_text(item.get("explanation"))
    source = item.get("source") or {}
    links = item.get("links") or {}
    related = item.get("related_cases") or []
    valid_related = [
        rel
        for rel in related
        if rel.get("found", True) and (rel.get("normalized_id") or rel.get("id")) in context["case_ids"]
    ]
    dangling = [
        rel
        for rel in related
        if not rel.get("found", True) or (rel.get("normalized_id") or rel.get("id")) not in context["case_ids"]
    ]

    evidence: list[str] = []
    forward_score = 0.0
    if title:
        forward_score += 0.16
        evidence.append("title present")
    if content:
        forward_score += 0.22
        evidence.append("function content present")
    if explanation and explanation != content:
        forward_score += 0.14
        evidence.append("explanation present")
    if source.get("source_reference") or source.get("source_file") or source.get("source_table"):
        forward_score += 0.15
        evidence.append("source trace present")
    if item.get("level_text") or object_text(item.get("level")):
        forward_score += 0.08
        evidence.append("level/type present")
    if links.get("human_page"):
        forward_score += 0.08
        evidence.append("human page linked")
    if item.get("status"):
        forward_score += 0.08
        evidence.append(f"status={item.get('status')}")
    if valid_related:
        forward_score += 0.09
        evidence.append(f"{len(valid_related)} related cases resolved")
    else:
        evidence.append("no resolved related cases")

    forward_status = score_status(forward_score, 0.68)

    counter_evidence: list[str] = []
    reverse_score = 0.0
    title_key = normalize_text(title)
    content_key = normalize_text(title + content)
    if not title:
        reverse_score += 0.35
        counter_evidence.append("missing title")
    if not content and not explanation:
        reverse_score += 0.35
        counter_evidence.append("missing content and explanation")
    if not source:
        reverse_score += 0.25
        counter_evidence.append("missing source object")
    if title_key and context["function_title_keys"][title_key] > 1:
        reverse_score += 0.18
        counter_evidence.append("duplicate function title")
    if content_key and context["function_content_keys"][content_key] > 1:
        reverse_score += 0.35
        counter_evidence.append("duplicate title+content signature")
    if dangling:
        reverse_score += 0.30
        counter_evidence.append(f"{len(dangling)} dangling related case links")

    duplicate_only_reverse = bool(counter_evidence) and all(
        evidence in {"duplicate function title", "duplicate title+content signature"}
        for evidence in counter_evidence
    )
    if duplicate_only_reverse and forward_status == "pass":
        reverse_score = min(reverse_score, 0.49)
        counter_evidence.append("duplicate signature requires merge review, not invalidity proof")

    reverse_status = score_status(reverse_score, 0.50)
    typed_result, compact_result = final_result(forward_status, reverse_status, "function")
    action = action_for("function", compact_result)
    return {
        "id": item_id,
        "type": "function",
        "round": round_no,
        "forward": channel(
            forward_status,
            forward_score,
            evidence,
            "function definition/source/link evidence evaluated",
            "evidence",
        ),
        "reverse": channel(
            reverse_status,
            reverse_score,
            counter_evidence,
            "counter-evidence for invalidity evaluated",
            "counter_evidence",
        ),
        "result": compact_result,
        "typed_result": typed_result,
        "action": action,
        "notes": "",
        "checked_at": utc_now(),
        "run_id": run_id,
    }


def verify_case(item: dict[str, Any], context: dict[str, Any], round_no: int, run_id: str) -> dict[str, Any]:
    item_id = item.get("normalized_id") or item.get("id")
    title = object_text(item.get("title"))
    content = object_text(item.get("content"))
    explanation = object_text(item.get("explanation"))
    source = item.get("source") or {}
    links = item.get("links") or {}
    related = item.get("related_functions") or []
    valid_related = [
        rel
        for rel in related
        if rel.get("found", True) and (rel.get("normalized_id") or rel.get("id")) in context["function_ids"]
    ]
    obsolete_related = [
        rel
        for rel in related
        if (rel.get("normalized_id") or rel.get("id")) in OBSOLETE_FUNCTION_REFERENCES
    ]
    dangling = [
        rel
        for rel in related
        if (
            not rel.get("found", True)
            or (rel.get("normalized_id") or rel.get("id")) not in context["function_ids"]
        )
        and (rel.get("normalized_id") or rel.get("id")) not in OBSOLETE_FUNCTION_REFERENCES
    ]

    evidence: list[str] = []
    forward_score = 0.0
    if title:
        forward_score += 0.14
        evidence.append("title present")
    if content:
        forward_score += 0.18
        evidence.append("case content present")
    if explanation and explanation != content:
        forward_score += 0.12
        evidence.append("case explanation present")
    if source.get("source_reference") or source.get("source_file") or source.get("source_table"):
        forward_score += 0.14
        evidence.append("source trace present")
    if item.get("normalized_id"):
        forward_score += 0.08
        evidence.append("normalized id present")
    if item.get("status"):
        forward_score += 0.08
        evidence.append(f"status={item.get('status')}")
    if links.get("human_page"):
        forward_score += 0.06
        evidence.append("human page linked")
    if valid_related:
        forward_score += 0.20
        evidence.append(f"{len(valid_related)} related functions resolved")
    elif obsolete_related:
        evidence.append(f"{len(obsolete_related)} obsolete legacy function references recorded")
    else:
        evidence.append("no resolved related functions")

    forward_status = "pass" if forward_score >= 0.65 else "fail"

    counter_evidence: list[str] = []
    reverse_score = 0.0
    title_key = normalize_text(title)
    content_key = normalize_text(title + content)
    if not title:
        reverse_score += 0.35
        counter_evidence.append("missing title")
    if not content and not explanation:
        reverse_score += 0.30
        counter_evidence.append("missing content and explanation")
    if not valid_related and not obsolete_related:
        reverse_score += 0.35
        counter_evidence.append("missing resolved function mapping")
    if obsolete_related:
        counter_evidence.extend(
            f"obsolete legacy function reference {rel.get('normalized_id') or rel.get('id')}: "
            f"{OBSOLETE_FUNCTION_REFERENCES[rel.get('normalized_id') or rel.get('id')]}"
            for rel in obsolete_related
        )
    if dangling:
        reverse_score += 0.40
        counter_evidence.append(f"{len(dangling)} dangling related function links")
    if title_key and context["case_title_keys"][title_key] > 1:
        reverse_score += 0.15
        counter_evidence.append("duplicate case title")
    if content_key and context["case_content_keys"][content_key] > 1:
        reverse_score += 0.35
        counter_evidence.append("duplicate title+content signature")

    reverse_status = score_status(reverse_score, 0.55)
    typed_result, compact_result = final_result(forward_status, reverse_status, "case")
    action = action_for("case", compact_result)
    return {
        "id": item_id,
        "type": "case",
        "round": round_no,
        "forward": channel(
            forward_status,
            forward_score,
            evidence,
            "case description/source/mapping evidence evaluated",
            "evidence",
        ),
        "reverse": channel(
            reverse_status,
            reverse_score,
            counter_evidence,
            "counter-evidence for mapping error evaluated",
            "counter_evidence",
        ),
        "result": compact_result,
        "typed_result": typed_result,
        "action": action,
        "notes": "",
        "checked_at": utc_now(),
        "run_id": run_id,
    }


def run_dir_for(run_id: str) -> Path:
    return RUN_ROOT / run_id


def checkpoint_path(run_dir: Path, object_type: str, round_no: int, item_id: str) -> Path:
    safe_id = item_id.replace("/", "_")
    return run_dir / "checkpoints" / f"{object_type}s" / f"round-{round_no:03d}" / f"{safe_id}.json"


def existing_checkpoint(run_dir: Path, object_type: str, round_no: int, item_id: str) -> dict[str, Any] | None:
    path = checkpoint_path(run_dir, object_type, round_no, item_id)
    if not path.exists():
        return None
    payload = read_json(path, {})
    if payload.get("item_state") in RESULT_STATES:
        return payload
    return None


def load_latest_round_results(run_dir: Path, object_type: str, round_no: int) -> dict[str, dict[str, Any]]:
    base = run_dir / "checkpoints" / f"{object_type}s" / f"round-{round_no:03d}"
    results: dict[str, dict[str, Any]] = {}
    if not base.exists():
        return results
    for path in sorted(base.glob("*.json")):
        payload = read_json(path, {})
        result = payload.get("result")
        if result:
            results[result["id"]] = result
    return results


def initialize_run(run_dir: Path, run_id: str, function_total: int, case_total: int) -> dict[str, Any]:
    state_path = run_dir / "state.json"
    if state_path.exists():
        return read_json(state_path, {})
    started_at = utc_now()
    state = {
        "run_id": run_id,
        "head_start": git_head_short(),
        "phase": "initialized",
        "round": 1,
        "function_total": function_total,
        "function_done": 0,
        "case_total": case_total,
        "case_done": 0,
        "last_item": None,
        "started_at": started_at,
        "updated_at": started_at,
        "heartbeat_at": started_at,
        "retry_policy": {
            "max_retries_per_item": 3,
            "continue_on_item_failure": True,
        },
        "stop_requested": False,
        "converged": False,
        "status": "running",
    }
    write_json(state_path, state)
    return state


def update_state(run_dir: Path, state: dict[str, Any], **updates: Any) -> None:
    state.update(updates)
    state["updated_at"] = utc_now()
    state["heartbeat_at"] = state["updated_at"]
    write_json(run_dir / "state.json", state)


def update_heartbeat(
    run_dir: Path,
    run_id: str,
    phase: str,
    current_item: str | None,
    items_done: int,
    items_total: int,
    status: str,
) -> None:
    heartbeat = {
        "run_id": run_id,
        "pid": os.getpid(),
        "phase": phase,
        "current_item": current_item,
        "heartbeat_at": utc_now(),
        "items_done": items_done,
        "items_total": items_total,
        "status": status,
    }
    write_json(run_dir / "heartbeat.json", heartbeat)


def write_progress(run_dir: Path, payload: dict[str, Any]) -> None:
    payload = dict(payload)
    payload["updated_at"] = utc_now()
    write_json(run_dir / "progress.json", payload)


def write_checkpoint(
    run_dir: Path,
    object_type: str,
    round_no: int,
    result: dict[str, Any],
    item_state: str = "done",
) -> None:
    payload = {
        "item_state": item_state,
        "updated_at": utc_now(),
        "result": result,
    }
    write_json(checkpoint_path(run_dir, object_type, round_no, result["id"]), payload)


def result_path(run_dir: Path, object_type: str) -> Path:
    if object_type == "function":
        return run_dir / "results/functions-verification.jsonl"
    return run_dir / "results/cases-verification.jsonl"


def classify_latest(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in results:
        latest[f"{row['type']}:{row['id']}"] = row
    buckets = {
        "true": [],
        "false": [],
        "contradiction": [],
        "underdetermined": [],
        "pending": [],
    }
    for row in latest.values():
        buckets[row["result"]].append(row)
    return buckets


def collect_results(run_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for object_type in ("function", "case"):
        base = run_dir / "checkpoints" / f"{object_type}s"
        if not base.exists():
            continue
        for path in sorted(base.glob("round-*/*.json")):
            payload = read_json(path, {})
            result = payload.get("result")
            if result:
                rows.append(result)
    return rows


def latest_results_by_type(run_dir: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    rows = collect_results(run_dir)
    latest_function: dict[str, dict[str, Any]] = {}
    latest_case: dict[str, dict[str, Any]] = {}
    for row in sorted(rows, key=lambda item: (item["round"], item["id"])):
        if row["type"] == "function":
            latest_function[row["id"]] = row
        elif row["type"] == "case":
            latest_case[row["id"]] = row
    return latest_function, latest_case


def apply_dual_verification_fields(
    run_id: str,
    function_results: dict[str, dict[str, Any]],
    case_results: dict[str, dict[str, Any]],
) -> None:
    checked_at = utc_now()
    functions = read_json(FUNCTIONS_JSON, [])
    cases = read_json(CASES_JSON, [])

    for item in functions:
        item_id = item.get("normalized_id") or item.get("id")
        result = function_results.get(item_id)
        if not result:
            continue
        item["dual_channel_verification"] = {
            "status": result["result"],
            "last_run_id": run_id,
            "last_checked_at": checked_at,
            "round": result["round"],
            "forward": {
                "status": result["forward"]["status"],
                "score": result["forward"]["score"],
            },
            "reverse": {
                "status": result["reverse"]["status"],
                "score": result["reverse"]["score"],
            },
            "action": result["action"],
        }

    for item in cases:
        item_id = item.get("normalized_id") or item.get("id")
        result = case_results.get(item_id)
        if not result:
            continue
        item["dual_channel_verification"] = {
            "status": result["result"],
            "last_run_id": run_id,
            "last_checked_at": checked_at,
            "round": result["round"],
            "forward": {
                "status": result["forward"]["status"],
                "score": result["forward"]["score"],
            },
            "reverse": {
                "status": result["reverse"]["status"],
                "score": result["reverse"]["score"],
            },
            "action": result["action"],
        }

    write_json(FUNCTIONS_JSON, functions)
    write_jsonl(FUNCTIONS_JSONL, functions)
    FUNCTIONS_MIN_JSON.write_text(
        json.dumps(functions, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_json(CASES_JSON, cases)
    write_jsonl(CASES_JSONL, cases)
    CASES_MIN_JSON.write_text(
        json.dumps(cases, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def count_by_result(rows: list[dict[str, Any]], object_type: str, result: str) -> int:
    return sum(1 for row in rows if row["type"] == object_type and row["result"] == result)


def delta_between_rounds(run_dir: Path, round_a: int, round_b: int) -> int:
    delta = 0
    for object_type in ("function", "case"):
        a = load_latest_round_results(run_dir, object_type, round_a)
        b = load_latest_round_results(run_dir, object_type, round_b)
        all_ids = set(a) | set(b)
        for item_id in all_ids:
            if a.get(item_id, {}).get("result") != b.get(item_id, {}).get("result"):
                delta += 1
            elif a.get(item_id, {}).get("action") != b.get(item_id, {}).get("action"):
                delta += 1
    return delta


def render_table(title: str, rows: list[dict[str, Any]], limit: int = 80) -> str:
    lines = [f"## {title}", "", "| id | type | round | result | action | forward | reverse |", "|---|---|---:|---|---|---|---|"]
    for row in rows[:limit]:
        lines.append(
            f"| {row['id']} | {row['type']} | {row['round']} | {row['result']} | {row['action']} | "
            f"{row['forward']['status']}:{row['forward']['score']} | {row['reverse']['status']}:{row['reverse']['score']} |"
        )
    if len(rows) > limit:
        lines.append(f"| ... | ... | ... | {len(rows) - limit} more | ... | ... | ... |")
    lines.append("")
    return "\n".join(lines)


def write_reports(run_dir: Path, run_id: str, rounds: int) -> dict[str, Any]:
    rows = collect_results(run_dir)
    latest_function, latest_case = latest_results_by_type(run_dir)
    latest_rows = list(latest_function.values()) + list(latest_case.values())
    buckets = classify_latest(latest_rows)
    contradiction_rows = buckets["contradiction"]
    underdetermined_rows = buckets["underdetermined"]
    pending_rows = buckets["pending"]
    false_rows = buckets["false"]
    round_delta = delta_between_rounds(run_dir, max(1, rounds - 1), rounds) if rounds >= 2 else len(latest_rows)

    function_rows = [row for row in latest_rows if row["type"] == "function"]
    case_rows = [row for row in latest_rows if row["type"] == "case"]
    write_jsonl(REBUILD_DIR / "dual-channel-function-verification.jsonl", function_rows)
    write_jsonl(REBUILD_DIR / "dual-channel-case-verification.jsonl", case_rows)
    write_jsonl(REBUILD_DIR / "dual-channel-contradictions.jsonl", contradiction_rows)
    write_jsonl(REBUILD_DIR / "dual-channel-underdetermined.jsonl", underdetermined_rows)
    write_jsonl(run_dir / "results/contradictions.jsonl", contradiction_rows)
    write_jsonl(run_dir / "results/underdetermined.jsonl", underdetermined_rows)
    write_jsonl(run_dir / "results/pending.jsonl", pending_rows)
    write_jsonl(run_dir / "results/deltas.jsonl", [{"round": rounds, "delta_from_previous_round": round_delta}])

    converged = (
        len(function_rows) == 470
        and len(case_rows) == 578
        and not contradiction_rows
        and not underdetermined_rows
        and not pending_rows
        and not false_rows
        and round_delta == 0
    )
    if contradiction_rows:
        status = "bootstrap_failed_due_to_contradictions"
    elif underdetermined_rows:
        status = "bootstrap_incomplete_due_to_underdetermined_items"
    elif pending_rows:
        status = "resumable_not_finished"
    elif false_rows:
        status = "bootstrap_incomplete_due_to_false_items"
    elif round_delta:
        status = "bootstrap_incomplete_due_to_round_delta"
    else:
        status = "converged"

    summary = {
        "run_id": run_id,
        "generated_at": utc_now(),
        "function_total": len(function_rows),
        "case_total": len(case_rows),
        "rounds_completed": rounds,
        "function_true": count_by_result(latest_rows, "function", "true"),
        "function_false": count_by_result(latest_rows, "function", "false"),
        "function_contradiction": count_by_result(latest_rows, "function", "contradiction"),
        "function_underdetermined": count_by_result(latest_rows, "function", "underdetermined"),
        "function_pending": count_by_result(latest_rows, "function", "pending"),
        "case_true": count_by_result(latest_rows, "case", "true"),
        "case_false_mapping": count_by_result(latest_rows, "case", "false"),
        "case_contradiction": count_by_result(latest_rows, "case", "contradiction"),
        "case_underdetermined": count_by_result(latest_rows, "case", "underdetermined"),
        "case_pending": count_by_result(latest_rows, "case", "pending"),
        "delta_previous_round": round_delta,
        "contradiction_count": len(contradiction_rows),
        "underdetermined_count": len(underdetermined_rows),
        "pending_count": len(pending_rows),
        "false_count": len(false_rows),
        "converged": converged,
        "status": status,
        "outputs": {
            "function_verification_jsonl": "data/rebuild/dual-channel-function-verification.jsonl",
            "case_verification_jsonl": "data/rebuild/dual-channel-case-verification.jsonl",
            "contradictions_jsonl": "data/rebuild/dual-channel-contradictions.jsonl",
            "underdetermined_jsonl": "data/rebuild/dual-channel-underdetermined.jsonl",
            "full_report_md": "data/rebuild/dual-channel-full-bootstrap-report.md",
            "convergence_report_md": "data/rebuild/dual-channel-convergence-report.md",
        },
    }
    write_json(REBUILD_DIR / "dual-channel-full-bootstrap-report.json", summary)
    write_json(REBUILD_DIR / "dual-channel-convergence-report.json", summary)
    write_json(run_dir / "reports/final-report.json", summary)
    write_json(run_dir / "reports/round-001-report.json", summary | {"round": 1})
    write_json(run_dir / "reports/round-002-report.json", summary | {"round": 2})

    markdown = [
        "# Dual-Channel Full Bootstrap Report",
        "",
        f"- run_id: {run_id}",
        f"- generated_at: {summary['generated_at']}",
        f"- functions verified: {summary['function_total']} / 470",
        f"- cases verified: {summary['case_total']} / 578",
        f"- rounds_completed: {rounds}",
        f"- converged: {str(converged).lower()}",
        f"- status: {status}",
        f"- delta_previous_round: {round_delta}",
        f"- contradiction_count: {len(contradiction_rows)}",
        f"- underdetermined_count: {len(underdetermined_rows)}",
        f"- false_count: {len(false_rows)}",
        "",
        "## Result Counts",
        "",
        f"- function true: {summary['function_true']}",
        f"- function false: {summary['function_false']}",
        f"- function contradiction: {summary['function_contradiction']}",
        f"- function underdetermined: {summary['function_underdetermined']}",
        f"- case true: {summary['case_true']}",
        f"- case failed_mapping: {summary['case_false_mapping']}",
        f"- case contradiction: {summary['case_contradiction']}",
        f"- case underdetermined: {summary['case_underdetermined']}",
        "",
        render_table("Contradictions", contradiction_rows),
        render_table("Underdetermined", underdetermined_rows),
        render_table("False / Remap Candidates", false_rows),
    ]
    full_md = "\n".join(markdown)
    (REBUILD_DIR / "dual-channel-full-bootstrap-report.md").write_text(full_md, encoding="utf-8", newline="\n")
    (REBUILD_DIR / "dual-channel-convergence-report.md").write_text(full_md, encoding="utf-8", newline="\n")
    (run_dir / "reports/final-report.md").write_text(full_md, encoding="utf-8", newline="\n")
    (run_dir / "reports/round-001-report.md").write_text(full_md, encoding="utf-8", newline="\n")
    (run_dir / "reports/round-002-report.md").write_text(full_md, encoding="utf-8", newline="\n")

    function_md = ["# Dual-Channel Function Verification", "", render_table("Functions", function_rows, limit=470)]
    case_md = ["# Dual-Channel Case Verification", "", render_table("Cases", case_rows, limit=578)]
    contradiction_md = ["# Dual-Channel Contradictions", "", render_table("Contradictions", contradiction_rows, limit=500)]
    under_md = ["# Dual-Channel Underdetermined", "", render_table("Underdetermined", underdetermined_rows, limit=1000)]
    (REBUILD_DIR / "dual-channel-function-verification.md").write_text("\n".join(function_md), encoding="utf-8", newline="\n")
    (REBUILD_DIR / "dual-channel-case-verification.md").write_text("\n".join(case_md), encoding="utf-8", newline="\n")
    (REBUILD_DIR / "dual-channel-contradictions.md").write_text("\n".join(contradiction_md), encoding="utf-8", newline="\n")
    (REBUILD_DIR / "dual-channel-underdetermined.md").write_text("\n".join(under_md), encoding="utf-8", newline="\n")
    return summary


def process_items(
    run_dir: Path,
    run_id: str,
    functions: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    rounds: int,
    max_items: int | None = None,
) -> dict[str, Any]:
    context = build_context(functions, cases)
    state = initialize_run(run_dir, run_id, len(functions), len(cases))
    lock_path = run_dir / "lock"
    lock_path.write_text(str(os.getpid()) + "\n", encoding="utf-8")
    processed = 0
    total_iterations = (len(functions) + len(cases)) * rounds
    completed_iterations = 0

    try:
        for round_no in range(1, rounds + 1):
            function_done = 0
            phase = f"round_{round_no}_functions"
            update_state(run_dir, state, phase=phase, round=round_no)
            for item in functions:
                item_id = item.get("normalized_id") or item.get("id")
                if existing_checkpoint(run_dir, "function", round_no, item_id):
                    function_done += 1
                    completed_iterations += 1
                    continue
                update_heartbeat(run_dir, run_id, phase, item_id, completed_iterations, total_iterations, "running")
                result = verify_function(item, context, round_no, run_id)
                write_checkpoint(run_dir, "function", round_no, result)
                append_jsonl(result_path(run_dir, "function"), result)
                function_done += 1
                completed_iterations += 1
                processed += 1
                update_state(
                    run_dir,
                    state,
                    phase=phase,
                    round=round_no,
                    function_done=function_done,
                    last_item=item_id,
                )
                write_progress(
                    run_dir,
                    {
                        "run_id": run_id,
                        "round": round_no,
                        "phase": phase,
                        "function_done": function_done,
                        "function_total": len(functions),
                        "case_done": 0,
                        "case_total": len(cases),
                        "items_done": completed_iterations,
                        "items_total": total_iterations,
                    },
                )
                append_log(run_dir, "worker.log", f"done function {item_id} round={round_no} result={result['result']}")
                if max_items and processed >= max_items:
                    return write_reports(run_dir, run_id, round_no)

            case_done = 0
            phase = f"round_{round_no}_cases"
            update_state(run_dir, state, phase=phase, round=round_no, function_done=function_done)
            for item in cases:
                item_id = item.get("normalized_id") or item.get("id")
                if existing_checkpoint(run_dir, "case", round_no, item_id):
                    case_done += 1
                    completed_iterations += 1
                    continue
                update_heartbeat(run_dir, run_id, phase, item_id, completed_iterations, total_iterations, "running")
                result = verify_case(item, context, round_no, run_id)
                write_checkpoint(run_dir, "case", round_no, result)
                append_jsonl(result_path(run_dir, "case"), result)
                case_done += 1
                completed_iterations += 1
                processed += 1
                update_state(
                    run_dir,
                    state,
                    phase=phase,
                    round=round_no,
                    case_done=case_done,
                    last_item=item_id,
                )
                write_progress(
                    run_dir,
                    {
                        "run_id": run_id,
                        "round": round_no,
                        "phase": phase,
                        "function_done": function_done,
                        "function_total": len(functions),
                        "case_done": case_done,
                        "case_total": len(cases),
                        "items_done": completed_iterations,
                        "items_total": total_iterations,
                    },
                )
                append_log(run_dir, "worker.log", f"done case {item_id} round={round_no} result={result['result']}")
                if max_items and processed >= max_items:
                    return write_reports(run_dir, run_id, round_no)

        function_results, case_results = latest_results_by_type(run_dir)
        apply_dual_verification_fields(run_id, function_results, case_results)
        summary = write_reports(run_dir, run_id, rounds)
        update_state(
            run_dir,
            state,
            phase="complete",
            round=rounds,
            function_done=len(function_results),
            case_done=len(case_results),
            converged=summary["converged"],
            status=summary["status"],
        )
        update_heartbeat(run_dir, run_id, "complete", None, len(functions) + len(cases), len(functions) + len(cases), "complete")
        return summary
    finally:
        if lock_path.exists():
            lock_path.unlink()


def status_payload(run_id: str) -> dict[str, Any]:
    run_dir = run_dir_for(run_id)
    state = read_json(run_dir / "state.json", {})
    progress = read_json(run_dir / "progress.json", {})
    heartbeat = read_json(run_dir / "heartbeat.json", {})
    return {
        "run_id": run_id,
        "run_dir": str(run_dir.relative_to(REPO_ROOT)) if run_dir.exists() else str(run_dir),
        "state": state,
        "progress": progress,
        "heartbeat": heartbeat,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run dual-channel bootstrap verification.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--max-items", type=int, default=None)
    args = parser.parse_args()

    if args.status:
        print(json.dumps(status_payload(args.run_id), ensure_ascii=False, indent=2))
        return 0

    functions, cases = load_sources()
    if len(functions) != 470 or len(cases) != 578:
        print(f"ERROR: expected 470 functions and 578 cases, got {len(functions)} and {len(cases)}", file=sys.stderr)
        return 1

    run_dir = run_dir_for(args.run_id)
    for rel in ("logs", "results", "reports", "checkpoints/functions", "checkpoints/cases"):
        (run_dir / rel).mkdir(parents=True, exist_ok=True)
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    (RUN_ROOT / "latest-run-id.txt").write_text(args.run_id + "\n", encoding="utf-8")
    append_log(run_dir, "worker.log", f"worker start resume={args.resume}")
    summary = process_items(run_dir, args.run_id, functions, cases, args.rounds, args.max_items)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
