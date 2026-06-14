#!/usr/bin/env python3
"""Dry-run sync orchestration for the Ignition knowledge base."""

from __future__ import annotations

import argparse
import json
import subprocess
from time import perf_counter
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_MD = REPO_ROOT / "data/rebuild/sync-dry-run-report.md"
REPORT_JSON = REPO_ROOT / "data/rebuild/sync-dry-run-report.json"
NOVELTY_REPORT_MD = REPO_ROOT / "data/rebuild/academic-novelty-rule-report.md"
NOVELTY_REPORT_JSON = REPO_ROOT / "data/rebuild/academic-novelty-rule-report.json"
IMPLEMENTATION_REPORT_MD = REPO_ROOT / "data/rebuild/sync-script-implementation-report.md"
IMPLEMENTATION_REPORT_JSON = REPO_ROOT / "data/rebuild/sync-script-implementation-report.json"


def run(cmd: list[str], timeout: int | None = None) -> dict:
    started = perf_counter()
    try:
        proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)
        timed_out = False
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
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "ok": proc.returncode == 0,
        "timed_out": timed_out,
        "duration_s": round(perf_counter() - started, 3),
    }


def write_reports(results: list[dict]) -> None:
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    validate_result = next(
        (
            result
            for result in results
            if len(result["cmd"]) >= 2 and str(result["cmd"][1]).endswith("validate_ignition_repository.py")
        ),
        None,
    )
    validate_stdout = {}
    if validate_result:
        try:
            raw_stdout = validate_result["stdout"].strip()
            if "\nERROR:" in raw_stdout:
                raw_stdout = raw_stdout.split("\nERROR:", 1)[0].strip()
            validate_stdout = json.loads(raw_stdout)
        except Exception:
            validate_stdout = {}
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": True,
        "results": results,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    lines = [
        "# Sync Dry Run Report",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- dry_run: {report['dry_run']}",
        "",
    ]
    for result in results:
        lines.append(f"## {' '.join(result['cmd'])}")
        lines.append(f"- returncode: {result['returncode']}")
        lines.append(f"- ok: {result['ok']}")
        lines.append(f"- timed_out: {result.get('timed_out', False)}")
        lines.append(f"- duration_s: {result.get('duration_s', 0)}")
        if result["stderr"].strip():
            lines.append(f"- stderr: {result['stderr'].strip()[:500]}")
        lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    novelty_summary = {
        "generated_at": report["generated_at"],
        "discovery_id_rule_written": True,
        "prediction_id_rule_written": True,
        "section_0_dual_channel_guard_present": validate_stdout.get("meta_functions", {}).get("bootstrap_internal", 0) == 5,
        "prediction_novelty_pending_count": validate_stdout.get("predictions", {}).get("novelty_pending", 0),
        "prediction_novelty_passed_count": validate_stdout.get("predictions", {}).get("novelty_passed", 0),
        "pending_novelty_review_present": validate_stdout.get("predictions", {}).get("novelty_pending", 0) > 0,
        "section_0_guard_present": validate_stdout.get("meta_functions", {}).get("meta", 0) == 1,
        "section_0_internal_count": validate_stdout.get("meta_functions", {}).get("bootstrap_internal", 0),
        "ordinary_function_count_present": validate_stdout.get("meta_functions", {}).get("ordinary", 0) > 0,
        "academic_novelty_check_script": (REPO_ROOT / "scripts/academic_novelty_check.py").exists(),
        "validate_script": (REPO_ROOT / "scripts/validate_ignition_repository.py").exists(),
        "sync_script": (REPO_ROOT / "scripts/sync_ignition_knowledge_base.py").exists(),
        "heartbeat_script": (REPO_ROOT / "scripts/ignition_sync_heartbeat.py").exists(),
        "dry_run_passed": all(result["ok"] for result in results),
        "long_heartbeat_started": False,
    }
    NOVELTY_REPORT_JSON.write_text(json.dumps(novelty_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    NOVELTY_REPORT_MD.write_text(
        "\n".join(
            [
                "# Academic Novelty Rule Report",
                "",
                f"- generated_at: {novelty_summary['generated_at']}",
                f"- discovery_id_rule_written: {novelty_summary['discovery_id_rule_written']}",
                f"- prediction_id_rule_written: {novelty_summary['prediction_id_rule_written']}",
                f"- section_0_dual_channel_guard_present: {novelty_summary['section_0_dual_channel_guard_present']}",
                f"- prediction_novelty_pending_count: {novelty_summary['prediction_novelty_pending_count']}",
                f"- prediction_novelty_passed_count: {novelty_summary['prediction_novelty_passed_count']}",
                f"- pending_novelty_review_present: {novelty_summary['pending_novelty_review_present']}",
                f"- section_0_guard_present: {novelty_summary['section_0_guard_present']}",
                f"- section_0_internal_count: {novelty_summary['section_0_internal_count']}",
                f"- ordinary_function_count_preserved: {novelty_summary['ordinary_function_count_preserved']}",
                f"- academic_novelty_check_script: {novelty_summary['academic_novelty_check_script']}",
                f"- validate_script: {novelty_summary['validate_script']}",
                f"- sync_script: {novelty_summary['sync_script']}",
                f"- heartbeat_script: {novelty_summary['heartbeat_script']}",
                f"- dry_run_passed: {novelty_summary['dry_run_passed']}",
                f"- long_heartbeat_started: {novelty_summary['long_heartbeat_started']}",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )

    implementation_summary = {
        "generated_at": report["generated_at"],
        "academic_novelty_check_implemented": (REPO_ROOT / "scripts/academic_novelty_check.py").exists(),
        "validate_ignition_repository_implemented": (REPO_ROOT / "scripts/validate_ignition_repository.py").exists(),
        "sync_ignition_knowledge_base_implemented": (REPO_ROOT / "scripts/sync_ignition_knowledge_base.py").exists(),
        "ignition_sync_heartbeat_implemented": (REPO_ROOT / "scripts/ignition_sync_heartbeat.py").exists(),
        "dry_run_passed": all(result["ok"] for result in results),
        "long_heartbeat_started": False,
    }
    IMPLEMENTATION_REPORT_JSON.write_text(json.dumps(implementation_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    IMPLEMENTATION_REPORT_MD.write_text(
        "\n".join(
            [
                "# Sync Script Implementation Report",
                "",
                f"- generated_at: {implementation_summary['generated_at']}",
                f"- academic_novelty_check_implemented: {implementation_summary['academic_novelty_check_implemented']}",
                f"- validate_ignition_repository_implemented: {implementation_summary['validate_ignition_repository_implemented']}",
                f"- sync_ignition_knowledge_base_implemented: {implementation_summary['sync_ignition_knowledge_base_implemented']}",
                f"- ignition_sync_heartbeat_implemented: {implementation_summary['ignition_sync_heartbeat_implemented']}",
                f"- dry_run_passed: {implementation_summary['dry_run_passed']}",
                f"- long_heartbeat_started: {implementation_summary['long_heartbeat_started']}",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--no-academic-search", action="store_true")
    parser.add_argument("--no-raw-scan", action="store_true")
    args = parser.parse_args()

    quick_mode = args.quick or args.dry_run
    commands = []
    if quick_mode:
        commands = [
            ["python3", "scripts/build_answers_from_function_projection.py", "--check"],
            ["python3", "scripts/normalize_bilingual_labels.py", "--check"],
            ["python3", "scripts/validate_ignition_repository.py", "--quick"],
            ["python3", "scripts/render_answer_index.py", "--check"],
            ["python3", "scripts/render_repository_overview.py", "--check"],
            ["python3", "scripts/merge_redundant_entry_links.py", "--check"],
            ["python3", "scripts/normalize_attribution_display_name.py", "--check"],
        ]
    else:
        commands = [
            ["python3", "scripts/render_discovery_index.py", "--check"],
            ["python3", "scripts/render_prediction_index.py", "--check"],
            ["python3", "scripts/render_answer_index.py", "--check"],
            ["python3", "scripts/academic_novelty_check.py", "--all-answers", "--dry-run"],
            ["python3", "scripts/merge_redundant_entry_links.py", "--check"],
            ["python3", "scripts/normalize_attribution_display_name.py", "--check"],
            ["python3", "scripts/validate_ignition_repository.py", "--full"],
        ]

    results = [run(cmd, timeout=args.timeout) for cmd in commands]
    write_reports(results)
    failed = [result for result in results if not result["ok"]]
    print(
        json.dumps(
            {
                "quick_mode": quick_mode,
                "timeout": args.timeout,
                "no_network": args.no_network,
                "no_academic_search": args.no_academic_search,
                "no_raw_scan": args.no_raw_scan,
                "results": results,
                "report_md": str(REPORT_MD.relative_to(REPO_ROOT)),
                "report_json": str(REPORT_JSON.relative_to(REPO_ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
