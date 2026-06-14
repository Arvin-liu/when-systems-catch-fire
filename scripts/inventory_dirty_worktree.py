#!/usr/bin/env python3
"""Inventory dirty worktree files without staging, deleting, or reading diffs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_JSON = ROOT / "data" / "rebuild" / "worktree-dirty-inventory-report.json"
REPORT_MD = ROOT / "data" / "rebuild" / "worktree-dirty-inventory-report.md"

CURRENT_TASK_SAFE_PATHS = {
    "AGENT_ENTRY.md",
    "llms.txt",
    "data/normalized-jsonl/README.md",
    "data/normalized-jsonl/baseline.json",
    "data/rebuild/worktree-dirty-inventory-report.md",
    "data/rebuild/worktree-dirty-inventory-report.json",
    "data/rebuild/normalized-jsonl-final-validation-report.md",
    "data/rebuild/normalized-jsonl-final-validation-report.json",
    "data/rebuild/normalized-jsonl-final-audit-report.md",
    "data/rebuild/normalized-jsonl-final-audit-report.json",
    "scripts/inventory_dirty_worktree.py",
    "scripts/validate_normalized_jsonl_all.py",
    "scripts/check_normalized_jsonl_baseline.py",
    "scripts/validate_project_identity_lock.py",
}


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def parse_status_line(line: str) -> tuple[str, str]:
    raw_status = line[:2]
    path = line[3:]
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return raw_status.strip() or raw_status.replace(" ", ""), path


def get_status_items() -> list[tuple[str, str]]:
    output = run_git(["status", "--short"])
    return [parse_status_line(line) for line in output.splitlines() if line.strip()]


def classify_path(path: str) -> tuple[str, str]:
    lower = path.lower()
    if (
        "worktree-dirty-inventory-report" in lower
        or "dirty-inventory" in lower
        or "inventory_dirty_worktree" in lower
    ):
        return "current_inventory_artifact", "dirty inventory artifact for the current takeover run"
    if (
        "normalized-jsonl" in lower
        or "jsonl baseline" in lower
        or "baseline" in lower
        or path in {"AGENT_ENTRY.md", "llms.txt"}
        or path in CURRENT_TASK_SAFE_PATHS
    ):
        return "normalized_jsonl_related", "normalized-jsonl baseline, report, script, or maintenance rule"
    if "get-note" in lower or "get_note" in lower or "getnote" in lower:
        return "get_note_dirty", "get-note artifact unrelated to the current baseline commit"
    if "link-entry" in lower or "link_entry" in lower or "link-entry-merge" in lower:
        return "link_entry_dirty", "link-entry artifact unrelated to the current baseline commit"
    if (
        "entailment" in lower
        or "function-case" in lower
        or "function_case" in lower
        or "non-entailment" in lower
    ):
        return "entailment_dirty", "function-case entailment artifact unrelated to the current baseline commit"
    if path.endswith(".md") and path.startswith("data/rebuild/"):
        return "report_only", "rebuild report that still needs explicit review before inclusion"
    return "unknown", "path does not match a known safe current-task category"


def action_for(path: str, category: str) -> tuple[bool, bool, str]:
    if path in CURRENT_TASK_SAFE_PATHS or category == "current_inventory_artifact":
        return True, False, "include_in_current_commit"
    if category == "unknown":
        return False, False, "needs_user_review"
    return False, False, "leave_unstaged"


def load_previous_paths() -> set[str]:
    if not REPORT_JSON.exists():
        return set()
    try:
        data = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    except Exception:
        return set()
    return {item.get("path", "") for item in data.get("items", []) if item.get("path")}


def build_report() -> dict:
    previous_paths = load_previous_paths()
    status_items = get_status_items()
    diff_stat = run_git(["diff", "--stat"])
    head = run_git(["rev-parse", "--short", "HEAD"]).strip()
    branch = run_git(["branch", "--show-current"]).strip()

    items = []
    for status, path in status_items:
        category, reason = classify_path(path)
        safe_to_commit, safe_to_discard, recommended_action = action_for(path, category)
        items.append(
            {
                "path": path,
                "git_status": status,
                "category": category,
                "appeared_before_current_run": path in previous_paths,
                "safe_to_commit_now": safe_to_commit,
                "safe_to_discard": safe_to_discard,
                "recommended_action": recommended_action,
                "reason": reason,
            }
        )

    unrelated_categories = {"get_note_dirty", "link_entry_dirty", "entailment_dirty", "unknown", "report_only"}
    unknown_items = [item for item in items if item["category"] == "unknown"]
    unrelated_items = [item for item in items if item["category"] in unrelated_categories]
    return {
        "report_name": "worktree-dirty-inventory-report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "head": head,
        "branch": branch,
        "total_dirty_items": len(items),
        "unrelated_dirty_items": len(unrelated_items),
        "unknown_items": len(unknown_items),
        "prior_dirty_commit": None,
        "unknown_items_left_unstaged": len(unknown_items),
        "unrelated_dirty_files_left_unstaged": len(unrelated_items),
        "diff_stat": diff_stat,
        "items": items,
        "safety": {
            "no_files_discarded": True,
            "no_files_staged": True,
            "no_commit_executed_by_script": True,
            "no_push_executed_by_script": True,
            "no_full_diff_written": True,
            "no_sensitive_env_content_read": True,
        },
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# 工作区脏文件清单报告 / Worktree Dirty Inventory Report",
        "",
        f"- HEAD: `{report['head']}`",
        f"- Branch: `{report['branch']}`",
        f"- total_dirty_items: {report['total_dirty_items']}",
        f"- unrelated_dirty_items: {report['unrelated_dirty_items']}",
        f"- unknown_items: {report['unknown_items']}",
        f"- prior_dirty_commit: {report['prior_dirty_commit']}",
        f"- unknown_items_left_unstaged: {report['unknown_items_left_unstaged']}",
        f"- unrelated_dirty_files_left_unstaged: {report['unrelated_dirty_files_left_unstaged']}",
        "",
        "## 条目 / Items",
        "",
        "| status | category | path | appeared_before_current_run | safe_to_commit_now | recommended_action |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in report["items"]:
        lines.append(
            "| {git_status} | {category} | `{path}` | {appeared} | {safe} | {action} |".format(
                git_status=item["git_status"],
                category=item["category"],
                path=item["path"],
                appeared=str(item["appeared_before_current_run"]).lower(),
                safe=str(item["safe_to_commit_now"]).lower(),
                action=item["recommended_action"],
            )
        )
    lines.extend(
        [
            "",
            "## 安全边界 / Safety",
            "",
            "- 未删除文件 / No files discarded",
            "- 未暂存文件 / No files staged by this script",
            "- 未提交 / No commit executed by this script",
            "- 未推送 / No push executed by this script",
            "- 未写入完整 diff / No full diff written",
            "- 未读取敏感环境文件内容 / No sensitive env file content read",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: dict) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")


def comparable_items(report: dict) -> list[dict]:
    keys = ["path", "git_status", "category", "safe_to_commit_now", "safe_to_discard", "recommended_action"]
    return sorted([{key: item.get(key) for key in keys} for item in report.get("items", [])], key=lambda x: x["path"])


def check_report() -> int:
    if not REPORT_JSON.exists() or not REPORT_MD.exists():
        print("FAIL: dirty inventory report files are missing")
        return 1
    current = build_report()
    existing = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    if comparable_items(current) != comparable_items(existing):
        print("FAIL: dirty inventory report is stale")
        print(f"  current_dirty_items={current['total_dirty_items']}")
        print(f"  reported_dirty_items={existing.get('total_dirty_items')}")
        return 1
    print("PASS: dirty inventory report is current")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory dirty worktree files.")
    parser.add_argument("--write", action="store_true", help="Write JSON and Markdown reports.")
    parser.add_argument("--check", action="store_true", help="Check that reports match current git status.")
    args = parser.parse_args()

    if args.write:
        report = build_report()
        write_report(report)
        print(f"Wrote {REPORT_JSON.relative_to(ROOT)}")
        print(f"Wrote {REPORT_MD.relative_to(ROOT)}")
        print(f"Dirty items: {report['total_dirty_items']}")
        return 0
    if args.check:
        return check_report()

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
