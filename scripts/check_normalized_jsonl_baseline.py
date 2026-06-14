#!/usr/bin/env python3
"""Write and check the normalized JSONL sealed baseline."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "normalized-jsonl"
REBUILD = ROOT / "data" / "rebuild"
BASELINE = BASE / "baseline.json"
AUDIT_JSON = REBUILD / "normalized-jsonl-final-audit-report.json"
AUDIT_MD = REBUILD / "normalized-jsonl-final-audit-report.md"

REQUIRED_JSONL = [
    ("functions.jsonl", "function"),
    ("cases.jsonl", "case"),
    ("effect-leads.jsonl", "effect_lead"),
    ("effects.jsonl", "effect"),
    ("discoveries.jsonl", "discovery"),
    ("predictions.jsonl", "prediction"),
    ("answers.jsonl", "answer"),
    ("analytic-solutions.jsonl", "analytic_solution"),
    ("function-case-relations.jsonl", "function_case_relation"),
    ("object-classification-crosswalk.jsonl", "classification_crosswalk"),
]

REQUIRED_RULES = {
    "counts_are_dynamic": True,
    "canonical_data_not_replaced": True,
    "inference_not_conclusion": True,
    "function_case_relations_non_entailing": True,
    "zero_function_case_relations_allowed_if_diagnosed": True,
    "lead_not_active": True,
    "eff_numbering_not_effect_proof": True,
    "novelty_passed_not_generated": True,
    "active_promotion_not_executed": True,
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def line_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(text.splitlines()) if text.strip() else 0


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def build_files() -> list[dict]:
    files = []
    for name, object_class in REQUIRED_JSONL:
        path = BASE / name
        files.append(
            {
                "path": rel(path),
                "line_count": line_count(path),
                "sha256": file_sha(path),
                "object_class": object_class,
            }
        )
    return files


def build_baseline() -> dict:
    return {
        "name": "normalized-jsonl-baseline",
        "schema_version": "normalized-jsonl-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": git_head(),
        "files": build_files(),
        "rules": dict(REQUIRED_RULES),
    }


def validate_baseline(baseline: dict) -> list[str]:
    errors = []
    if baseline.get("name") != "normalized-jsonl-baseline":
        errors.append("baseline name mismatch")
    if baseline.get("schema_version") != "normalized-jsonl-v1":
        errors.append("baseline schema_version mismatch")
    files = baseline.get("files")
    if not isinstance(files, list):
        return ["baseline files must be a list"]
    by_path = {item.get("path"): item for item in files if isinstance(item, dict)}
    for name, object_class in REQUIRED_JSONL:
        path = BASE / name
        path_key = rel(path)
        item = by_path.get(path_key)
        if item is None:
            errors.append(f"baseline missing {path_key}")
            continue
        if item.get("object_class") != object_class:
            errors.append(f"object_class mismatch for {path_key}: {item.get('object_class')} != {object_class}")
        actual_count = line_count(path)
        if item.get("line_count") != actual_count:
            errors.append(f"line_count mismatch for {path_key}: {item.get('line_count')} != {actual_count}")
        if item.get("sha256") != file_sha(path):
            errors.append(f"sha256 mismatch for {path_key}")
    rules = baseline.get("rules", {})
    if not isinstance(rules, dict):
        errors.append("baseline rules must be an object")
    else:
        for key, value in REQUIRED_RULES.items():
            if rules.get(key) is not value:
                errors.append(f"baseline rule {key} must be {value}")
    return errors


def load_dirty_summary() -> dict:
    path = REBUILD / "worktree-dirty-inventory-report.json"
    if not path.exists():
        return {
            "total_dirty_items_before": None,
            "unrelated_dirty_files_left_unstaged": None,
            "unknown_items_left_unstaged": None,
            "prior_dirty_commit": None,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "total_dirty_items_before": data.get("total_dirty_items"),
        "unrelated_dirty_files_left_unstaged": data.get("unrelated_dirty_files_left_unstaged"),
        "unknown_items_left_unstaged": data.get("unknown_items_left_unstaged"),
        "prior_dirty_commit": data.get("prior_dirty_commit"),
    }


def build_audit(baseline: dict, errors: list[str]) -> dict:
    fcr = next(
        item
        for item in baseline.get("files", [])
        if item.get("path") == "data/normalized-jsonl/function-case-relations.jsonl"
    )
    diag_path = ROOT / "data" / "rebuild" / "function-case-relations-source-diagnostic-report.json"
    diag = json.loads(diag_path.read_text(encoding="utf-8")) if diag_path.exists() else {}
    return {
        "report_name": "normalized-jsonl-final-audit-report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "head": git_head(),
        "baseline_path": "data/normalized-jsonl/baseline.json",
        "baseline_passed": not errors,
        "errors": errors,
        "files": baseline.get("files", []),
        "function_case_relations": {
            "output_line_count": fcr.get("line_count"),
            "zero_relations_is_valid": diag.get("zero_relations_is_valid"),
            "do_not_synthesize_relations": diag.get("do_not_synthesize_relations"),
        },
        "dirty_files": load_dirty_summary(),
        "safety": {
            "canonical_data_not_replaced": True,
            "full_bootstrap_not_run": True,
            "academic_search_not_run": True,
            "novelty_passed_not_generated": True,
            "active_promotion_not_executed": True,
            "no_relation_synthesized": True,
            "uncertain_dirty_files_not_processed": True,
        },
    }


def render_audit_md(audit: dict) -> str:
    lines = [
        "# Normalized JSONL Final Audit Report",
        "",
        f"- Generated at: {audit['generated_at']}",
        f"- HEAD: `{audit['head']}`",
        f"- Baseline passed: {str(audit['baseline_passed']).lower()}",
        f"- Baseline path: `{audit['baseline_path']}`",
        "",
        "## Baseline Files",
        "",
        "| File | Lines | SHA256 | Object class |",
        "|---|---:|---|---|",
    ]
    for item in audit["files"]:
        lines.append(f"| `{item['path']}` | {item['line_count']} | `{item['sha256']}` | `{item['object_class']}` |")
    fcr = audit["function_case_relations"]
    dirty = audit["dirty_files"]
    lines.extend(
        [
            "",
            "## Function-Case Relations",
            "",
            f"- output line_count: {fcr['output_line_count']}",
            f"- zero_relations_is_valid: {str(fcr['zero_relations_is_valid']).lower()}",
            f"- do_not_synthesize_relations: {str(fcr['do_not_synthesize_relations']).lower()}",
            "",
            "## Dirty Files",
            "",
            f"- total_dirty_items before: {dirty['total_dirty_items_before']}",
            f"- unrelated_dirty_files_left_unstaged: {dirty['unrelated_dirty_files_left_unstaged']}",
            f"- unknown_items_left_unstaged: {dirty['unknown_items_left_unstaged']}",
            f"- prior_dirty_commit: {dirty['prior_dirty_commit']}",
            "",
            "## Safety",
            "",
            "- canonical data not replaced: true",
            "- full bootstrap not run: true",
            "- academic search not run: true",
            "- novelty passed not generated: true",
            "- active promotion not executed: true",
            "- no relation synthesized: true",
            "- uncertain dirty files not processed: true",
        ]
    )
    if audit["errors"]:
        lines.extend(["", "## Errors", ""])
        for error in audit["errors"]:
            lines.append(f"- {error}")
    return "\n".join(lines) + "\n"


def write_all() -> int:
    baseline = build_baseline()
    BASELINE.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    errors = validate_baseline(baseline)
    audit = build_audit(baseline, errors)
    REBUILD.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AUDIT_MD.write_text(render_audit_md(audit), encoding="utf-8")
    print(f"Wrote {rel(BASELINE)}")
    print(f"Wrote {rel(AUDIT_JSON)}")
    print(f"Wrote {rel(AUDIT_MD)}")
    return 0 if not errors else 1


def check() -> int:
    if not BASELINE.exists():
        print("FAIL: data/normalized-jsonl/baseline.json is missing")
        return 1
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    errors = validate_baseline(baseline)
    if errors:
        print("BASELINE CHECK FAILED")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("BASELINE CHECK PASSED")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check normalized JSONL baseline.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        return write_all()
    if args.check:
        return check()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
