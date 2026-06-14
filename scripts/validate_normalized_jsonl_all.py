#!/usr/bin/env python3
"""Validate the full normalized JSONL data layer and write final reports."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "normalized-jsonl"
REBUILD = ROOT / "data" / "rebuild"
REPORT_JSON = REBUILD / "normalized-jsonl-final-validation-report.json"
REPORT_MD = REBUILD / "normalized-jsonl-final-validation-report.md"

REQUIRED_JSONL = [
    "functions.jsonl",
    "cases.jsonl",
    "effect-leads.jsonl",
    "effects.jsonl",
    "discoveries.jsonl",
    "predictions.jsonl",
    "answers.jsonl",
    "analytic-solutions.jsonl",
    "function-case-relations.jsonl",
    "object-classification-crosswalk.jsonl",
]
REQUIRED_FIELDS = [
    "id",
    "object_class",
    "schema_version",
    "generated_at",
    "source_commit",
    "source_sha",
    "canonical_source",
    "inference_not_conclusion",
]
ARRAY_FIELDS = [
    "related_function_ids",
    "related_case_ids",
    "related_effect_ids",
    "related_discovery_ids",
    "related_prediction_ids",
    "related_answer_ids",
    "parent_ids",
    "child_ids",
    "referenced_function_ids",
    "referenced_case_ids",
    "effect_ids",
    "function_ids",
    "related_functions",
    "related_cases",
    "related_effects",
    "related_discoveries",
    "related_predictions",
    "related_answers",
    "related_analytic_solutions",
    "core_functions",
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def read_jsonl(path: Path, allow_empty: bool = False) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if text.lstrip().startswith("["):
        raise AssertionError(f"{rel(path)} appears to be a JSON array, not JSONL")
    if not text.strip():
        if allow_empty:
            return []
        raise AssertionError(f"{rel(path)} is empty and not allowed")
    rows = []
    for line_number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            raise AssertionError(f"Empty line at {rel(path)}:{line_number}")
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"Invalid JSON at {rel(path)}:{line_number}: {exc}") from exc
        if not isinstance(obj, dict):
            raise AssertionError(f"Not JSON object at {rel(path)}:{line_number}, got {type(obj).__name__}")
        rows.append(obj)
    return rows


def validate_file(name: str, rows: list[dict]) -> list[str]:
    errors = []
    for obj in rows:
        obj_id = obj.get("id", "?")
        for field in REQUIRED_FIELDS:
            if field not in obj:
                errors.append(f"Missing field '{field}' in object {obj_id} ({name})")
        if obj.get("schema_version") != "normalized-jsonl-v1":
            errors.append(f"Bad schema_version '{obj.get('schema_version')}' for {obj_id} ({name})")
        if obj.get("inference_not_conclusion") is not True:
            errors.append(f"inference_not_conclusion is not true for {obj_id} ({name})")
        for field in ARRAY_FIELDS:
            if field in obj and not isinstance(obj[field], list):
                errors.append(f"Array field '{field}' is not a list in {obj_id} ({name})")
        if obj.get("object_class") == "effect_lead" and obj.get("status") == "active":
            errors.append(f"effect_lead has status=active: {obj_id} ({name})")
        if obj.get("object_class") == "effect_lead" and name != "effect-leads.jsonl":
            errors.append(f"effect_lead appears outside effect-leads.jsonl: {obj_id} ({name})")
        if name == "effect-leads.jsonl" and obj.get("object_class") != "effect_lead":
            errors.append(f"effect-leads.jsonl contains non-effect_lead object: {obj_id}")
        if obj.get("status") == "active" and str(obj.get("object_class", "")).endswith("_lead"):
            errors.append(f"lead object has active status: {obj_id} ({name})")
    return errors


def manifest_entry(file_map: object, name: str) -> dict | None:
    path_key = f"data/normalized-jsonl/{name}"
    if not isinstance(file_map, dict):
        return None
    for key, value in file_map.items():
        if key in {path_key, name} and isinstance(value, dict):
            return value
        if isinstance(value, dict) and value.get("path") == path_key:
            return value
    return None


def validate_manifest() -> tuple[list[str], list[dict]]:
    errors = []
    details = []
    manifest_path = BASE / "manifest.json"
    if not manifest_path.exists():
        return ["manifest.json not found"], details
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    file_map = manifest.get("files", {})
    for name in REQUIRED_JSONL:
        path = BASE / name
        path_key = f"data/normalized-jsonl/{name}"
        if not path.exists():
            errors.append(f"File missing: {path_key}")
            continue
        actual_text = path.read_text(encoding="utf-8")
        actual_count = len(actual_text.splitlines()) if actual_text.strip() else 0
        actual_sha = sha256(path)
        entry = manifest_entry(file_map, name)
        if entry is None:
            errors.append(f"No manifest entry for {path_key}")
            continue
        expected_count = entry.get("line_count")
        expected_sha = entry.get("sha256", "")
        if expected_count != actual_count:
            errors.append(f"Manifest line_count mismatch for {path_key}: manifest={expected_count}, actual={actual_count}")
        sha_matches = bool(expected_sha) and (expected_sha == actual_sha or actual_sha.startswith(expected_sha))
        if expected_sha and not sha_matches:
            errors.append(f"Manifest sha256 mismatch for {path_key}: manifest={expected_sha}, actual={actual_sha}")
        details.append(
            {
                "path": path_key,
                "manifest_line_count": expected_count,
                "actual_line_count": actual_count,
                "manifest_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "sha256_match": sha_matches,
                "manifest_sha256_is_full": expected_sha == actual_sha,
            }
        )
    return errors, details


def read_relation_diagnostic() -> dict:
    diag_path = ROOT / "data" / "rebuild" / "function-case-relations-source-diagnostic-report.json"
    if not diag_path.exists():
        return {}
    return json.loads(diag_path.read_text(encoding="utf-8"))


def build_report() -> dict:
    all_errors = []
    file_details = []
    relation_rows: list[dict] = []

    for name in REQUIRED_JSONL:
        path = BASE / name
        allow_empty = name == "function-case-relations.jsonl"
        if not path.exists():
            all_errors.append(f"MISSING: {rel(path)}")
            file_details.append({"path": rel(path), "name": name, "line_count": 0, "sha256": None, "errors": ["MISSING"]})
            continue
        try:
            rows = read_jsonl(path, allow_empty=allow_empty)
        except AssertionError as exc:
            all_errors.append(str(exc))
            file_details.append({"path": rel(path), "name": name, "line_count": 0, "sha256": sha256(path), "errors": [str(exc)]})
            continue
        if name == "function-case-relations.jsonl":
            relation_rows = rows
        errors = validate_file(name, rows)
        all_errors.extend(errors)
        file_details.append({"path": rel(path), "name": name, "line_count": len(rows), "sha256": sha256(path), "errors": errors})

    manifest_errors, manifest_details = validate_manifest()
    all_errors.extend(manifest_errors)

    diag = read_relation_diagnostic()
    if not relation_rows:
        if not diag:
            all_errors.append("Missing diagnostic report for zero function-case-relations")
        if diag.get("zero_relations_is_valid") is not True:
            all_errors.append("zero function-case-relations is not diagnosed as valid")
        if diag.get("do_not_synthesize_relations") is not True:
            all_errors.append("diagnostic does not set do_not_synthesize_relations=true")

    return {
        "report_name": "normalized-jsonl-final-validation-report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "head": git_head(),
        "schema_version": "normalized-jsonl-v1",
        "files_checked": len(REQUIRED_JSONL),
        "files": file_details,
        "manifest": {
            "path": "data/normalized-jsonl/manifest.json",
            "errors": manifest_errors,
            "files": manifest_details,
        },
        "function_case_relations": {
            "output_line_count": len(relation_rows),
            "diagnostic_path": "data/rebuild/function-case-relations-source-diagnostic-report.json",
            "zero_relations_is_valid": diag.get("zero_relations_is_valid"),
            "do_not_synthesize_relations": diag.get("do_not_synthesize_relations"),
        },
        "rules": {
            "canonical_data_not_replaced": True,
            "inference_not_conclusion_required": True,
            "lead_not_active": True,
            "eff_numbering_not_effect_proof": True,
            "zero_function_case_relations_allowed_if_diagnosed": True,
        },
        "total_errors": len(all_errors),
        "errors": all_errors,
        "passed": len(all_errors) == 0,
    }


def render_md(report: dict) -> str:
    lines = [
        "# Normalized JSONL Final Validation Report",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- HEAD: `{report['head']}`",
        f"- Schema version: `{report['schema_version']}`",
        f"- Passed: {str(report['passed']).lower()}",
        f"- Total errors: {report['total_errors']}",
        "",
        "## Files",
        "",
        "| File | Lines | SHA256 | Errors |",
        "|---|---:|---|---:|",
    ]
    for item in report["files"]:
        digest = item["sha256"] or ""
        lines.append(f"| `{item['path']}` | {item['line_count']} | `{digest}` | {len(item['errors'])} |")
    fcr = report["function_case_relations"]
    lines.extend(
        [
            "",
            "## Function-Case Relations",
            "",
            f"- output line_count: {fcr['output_line_count']}",
            f"- zero_relations_is_valid: {str(fcr['zero_relations_is_valid']).lower()}",
            f"- do_not_synthesize_relations: {str(fcr['do_not_synthesize_relations']).lower()}",
            "",
            "## Rules",
            "",
            "- canonical data not replaced: true",
            "- inference_not_conclusion required: true",
            "- lead is not active: true",
            "- EFF numbering does not prove effect identity: true",
            "- zero function-case-relations is allowed only when diagnosed: true",
        ]
    )
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        for error in report["errors"]:
            lines.append(f"- {error}")
    return "\n".join(lines) + "\n"


def write_report(report: dict) -> None:
    REBUILD.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")


def print_summary(report: dict) -> None:
    print(f"Normalized JSONL validation passed: {report['passed']}")
    for item in report["files"]:
        status = "OK" if not item["errors"] else f"FAIL ({len(item['errors'])})"
        print(f"  {item['name']}: lines={item['line_count']} {status}")
    if report["errors"]:
        print(f"Errors: {report['total_errors']}")
        for error in report["errors"]:
            print(f"  - {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate normalized JSONL data layer.")
    parser.add_argument("--report", action="store_true", help="Write final JSON and Markdown reports.")
    parser.add_argument("--check", action="store_true", help="Exit with non-zero status on failure.")
    args = parser.parse_args()

    report = build_report()
    if args.report:
        write_report(report)
        print_summary(report)
        print(f"Wrote {rel(REPORT_JSON)}")
        print(f"Wrote {rel(REPORT_MD)}")
    if args.check:
        print_summary(report)
        return 0 if report["passed"] else 1
    if not args.report and not args.check:
        parser.print_help()
        return 2
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
