#!/usr/bin/env python3
"""Heartbeat wrapper for the Ignition sync dry-run flow."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from time import perf_counter


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCK_FILE = REPO_ROOT / "data/sync/.ignition-maintenance.lock"
STATE_FILE = REPO_ROOT / "data/sync/heartbeat-state.json"
REPORT_MD = REPO_ROOT / "data/sync/heartbeat-dry-run-report.md"
REPORT_JSON = REPO_ROOT / "data/sync/heartbeat-dry-run-report.json"
PERF_REPORT_MD = REPO_ROOT / "data/rebuild/sync-heartbeat-performance-report.md"
PERF_REPORT_JSON = REPO_ROOT / "data/rebuild/sync-heartbeat-performance-report.json"


def read_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else default


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def run(cmd: list[str], timeout: int | None = None) -> dict:
    started = perf_counter()
    try:
        proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "ok": proc.returncode == 0,
            "timed_out": False,
            "duration_s": round(perf_counter() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": (exc.stderr or "") + f"\nTIMEOUT after {timeout}s" if timeout else "\nTIMEOUT",
            "ok": False,
            "timed_out": True,
            "duration_s": round(perf_counter() - started, 3),
        }


def write_reports(payload: dict) -> None:
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    lines = [
        "# Ignition Heartbeat Dry Run Report",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- lock_present: {payload['lock_present']}",
        f"- validate_ok: {payload['validate_ok']}",
        "",
    ]
    lines.append("## Commands")
    lines.append("")
    for result in payload["commands"]:
        lines.append(f"- {' '.join(result['cmd'])}: {result['returncode']} ({result.get('duration_s', 0)}s, timed_out={result.get('timed_out', False)})")
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_performance_report(payload: dict) -> None:
    PERF_REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    PERF_REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    lines = [
        "# Sync / Heartbeat Performance Report",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- sync_dry_run_total_s: {payload['sync_dry_run_total_s']}",
        f"- heartbeat_once_dry_run_total_s: {payload['heartbeat_once_dry_run_total_s']}",
        f"- validate_quick_duration_s: {payload['validate_quick_duration_s']}",
        f"- within_60s: {payload['within_60s']}",
        f"- recommended_long_heartbeat: {payload['recommended_long_heartbeat']}",
        "",
        "## Skipped Steps",
        "",
    ]
    if "section_0_guard_present" in payload:
        lines.insert(7, f"- section_0_guard_present: {payload['section_0_guard_present']}")
    if "section_0_dual_channel_guard_present" in payload:
        insert_at = 8 if "section_0_guard_present" in payload else 7
        lines.insert(insert_at, f"- section_0_dual_channel_guard_present: {payload['section_0_dual_channel_guard_present']}")
    if "section_0_internal_count" in payload:
        insert_at = 9 if "section_0_guard_present" in payload and "section_0_dual_channel_guard_present" in payload else 8 if "section_0_guard_present" in payload or "section_0_dual_channel_guard_present" in payload else 7
        lines.insert(insert_at, f"- section_0_internal_count: {payload['section_0_internal_count']}")
    if "ordinary_function_count_preserved" in payload:
        insert_at = 10 if "section_0_guard_present" in payload and "section_0_dual_channel_guard_present" in payload and "section_0_internal_count" in payload else 9 if ("section_0_guard_present" in payload and "section_0_dual_channel_guard_present" in payload) or ("section_0_guard_present" in payload and "section_0_internal_count" in payload) or ("section_0_dual_channel_guard_present" in payload and "section_0_internal_count" in payload) else 8 if "section_0_guard_present" in payload or "section_0_dual_channel_guard_present" in payload or "section_0_internal_count" in payload else 7
        lines.insert(insert_at, f"- ordinary_function_count_preserved: {payload['ordinary_function_count_preserved']}")
    for step in payload["skipped_steps"]:
        lines.append(f"- {step}")
    lines.extend(["", "## Core Steps", ""])
    for step in payload["core_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    PERF_REPORT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args()

    state = read_json(STATE_FILE, {})
    if args.status and not args.once:
        payload = {
            "lock_present": LOCK_FILE.exists(),
            "state": state,
            "report_md": str(REPORT_MD.relative_to(REPO_ROOT)),
            "report_json": str(REPORT_JSON.relative_to(REPO_ROOT)),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.once and args.dry_run:
        started = perf_counter()
        commands = [
            run(
                [
                    "python3",
                    "scripts/sync_ignition_knowledge_base.py",
                    "--dry-run",
                    "--quick",
                    "--timeout",
                    str(args.timeout),
                    "--no-network",
                    "--no-academic-search",
                    "--no-raw-scan",
                ],
                timeout=args.timeout,
            )
        ]
        heartbeat_total = round(perf_counter() - started, 3)
        sync_report = read_json(REPO_ROOT / "data/rebuild/sync-dry-run-report.json", {})
        sync_command_durations = [result.get("duration_s", 0) for result in sync_report.get("results", [])]
        validate_quick_duration = 0
        validate_stdout = {}
        for result in sync_report.get("results", []):
            cmd = result.get("cmd", [])
            if len(cmd) >= 2 and str(cmd[1]).endswith("validate_ignition_repository.py"):
                validate_quick_duration = result.get("duration_s", 0)
                try:
                    raw_stdout = (result.get("stdout") or "").strip()
                    if "\nERROR:" in raw_stdout:
                        raw_stdout = raw_stdout.split("\nERROR:", 1)[0].strip()
                    validate_stdout = json.loads(raw_stdout) if raw_stdout else {}
                except Exception:
                    validate_stdout = {}
                break
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "lock_present": LOCK_FILE.exists(),
            "state": {
                "last_run_at": datetime.now(timezone.utc).isoformat(),
                "last_run_mode": "dry-run",
                "validate_ok": all(result["ok"] for result in commands),
                "quick": True,
            },
            "commands": commands,
            "validate_ok": all(result["ok"] for result in commands),
            "section_0_guard_present": validate_stdout.get("meta_functions", {}).get("meta", 0) == 1,
            "section_0_dual_channel_guard_present": validate_stdout.get("meta_functions", {}).get("bootstrap_internal", 0) == 5,
            "section_0_internal_count": validate_stdout.get("meta_functions", {}).get("bootstrap_internal", 0),
            "ordinary_function_count_preserved": validate_stdout.get("meta_functions", {}).get("ordinary", 0) == 470,
        }
        write_json(STATE_FILE, payload["state"])
        write_reports(payload)
        write_performance_report(
            {
                "generated_at": payload["generated_at"],
                "sync_dry_run_total_s": round(sum(sync_command_durations), 3),
                "heartbeat_once_dry_run_total_s": heartbeat_total,
                "validate_quick_duration_s": validate_quick_duration,
                "within_60s": heartbeat_total <= 60 and sum(sync_command_durations) <= 60,
                "recommended_long_heartbeat": False,
                "section_0_dual_channel_guard_present": payload["section_0_dual_channel_guard_present"],
                "section_0_internal_count": payload["section_0_internal_count"],
                "skipped_steps": [
                    "academic_novelty_check.py --all-answers --dry-run",
                    "detect_repetitive_text.py --check",
                    "render_discovery_index.py --check",
                    "render_prediction_index.py --check",
                ],
                "core_steps": [
                    "sync_ignition_knowledge_base.py --dry-run --quick",
                    "validate_ignition_repository.py --quick",
                    "render_answer_index.py --check",
                ],
            }
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["validate_ok"] else 1

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lock_present": LOCK_FILE.exists(),
        "commands": [],
        "validate_ok": False,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
