#!/usr/bin/env python3
"""
Minimal normalized JSONL layer builder.
Reads canonical sources and generates functions.jsonl, cases.jsonl, effect-leads.jsonl.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CANONICAL_SRC = BASE / "data"
OUTPUT_DIR = BASE / "data" / "normalized-jsonl"
REBUILD_DIR = BASE / "data" / "rebuild"

def sha256_file(path):
    """Compute sha256 of file content."""
    try:
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()[:16]
    except Exception:
        return ""

def git_short_head():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(BASE), stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"

def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def safe_str(val):
    return val if val is not None else ""

def safe_list(val):
    return val if isinstance(val, list) else []

def canonical_page_from_path(path_str):
    """Extract page reference from canonical source path."""
    if not path_str:
        return None
    parts = path_str.split("#")
    return parts[1] if len(parts) > 1 else None

def load_jsonl(path):
    """Load JSONL file, return list of dicts."""
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows

def load_json_items(items_dir):
    """Load all JSON files from items directory."""
    rows = []
    d = Path(items_dir)
    if not d.exists():
        return rows
    for f in sorted(d.glob("*.json")):
        try:
            rows.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return rows

def build_functions(build_unified, build_items):
    """Build functions.jsonl entries."""
    entries = []
    all_items = []
    if build_unified:
        all_items.extend(load_jsonl(CANONICAL_SRC / "functions" / "unified-functions.jsonl"))
    all_items.extend(load_json_items(CANONICAL_SRC / "functions" / "items"))

    source_file = str(CANONICAL_SRC / "functions" / "unified-functions.jsonl") if build_unified else ""
    source_sha = sha256_file(CANONICAL_SRC / "functions" / "unified-functions.jsonl") if build_unified else ""

    for obj in all_items:
        obj_id = obj.get("id", obj.get("ID", ""))
        if not obj_id:
            continue
        entries.append({
            "id": str(obj_id),
            "object_class": "function",
            "name": safe_str(obj.get("name", obj.get("NAME", obj.get("名称", "")))),
            "name_en": safe_str(obj.get("name_en", obj.get("NAME_EN", obj.get("英文名", "")))),
            "definition": safe_str(obj.get("definition", obj.get("DEFINITION", obj.get("定义", "")))),
            "definition_en": safe_str(obj.get("definition_en", obj.get("DEFINITION_EN", obj.get("英文定义", "")))),
            "expression": safe_str(obj.get("expression", obj.get("EXPRESSION", obj.get("公式", "")))),
            "derivation": safe_str(obj.get("derivation", obj.get("DERIVATION", obj.get("推导", "")))),
            "related_cases": safe_list(obj.get("related_cases", obj.get("RELATED_CASES", obj.get("关联案例", [])))),
            "extended_notes": safe_str(obj.get("extended_notes", obj.get("EXTENDED_NOTES", obj.get("扩展说明", "")))),
            "canonical_source": source_file,
            "canonical_page": canonical_page_from_path(source_file) if source_file else None,
            "schema_version": "normalized-jsonl-v1",
            "generated_at": utc_now_iso(),
            "source_commit": git_short_head(),
            "source_sha": source_sha,
            "inference_not_conclusion": True,
        })
    return entries

def build_cases(build_unified, build_items):
    """Build cases.jsonl entries."""
    entries = []
    all_items = []
    if build_unified:
        all_items.extend(load_jsonl(CANONICAL_SRC / "cases" / "unified-cases.jsonl"))
    all_items.extend(load_json_items(CANONICAL_SRC / "cases" / "items"))

    source_file = str(CANONICAL_SRC / "cases" / "unified-cases.jsonl") if build_unified else ""
    source_sha = sha256_file(CANONICAL_SRC / "cases" / "unified-cases.jsonl") if build_unified else ""

    for obj in all_items:
        obj_id = obj.get("id", obj.get("ID", ""))
        if not obj_id:
            continue
        entries.append({
            "id": str(obj_id),
            "object_class": "case",
            "get_brain_alias": safe_str(obj.get("get_brain_alias", obj.get("GET_BRAIN_ALIAS", obj.get("得到别名", "")))),
            "layer": safe_str(obj.get("layer", obj.get("LAYER", obj.get("层级", "")))),
            "grid": safe_str(obj.get("grid", obj.get("GRID", obj.get("网格", "")))),
            "status": safe_str(obj.get("status", obj.get("STATUS", obj.get("状态", "")))),
            "core_function": safe_str(obj.get("core_function", obj.get("CORE_FUNCTION", obj.get("核心函数", "")))),
            "core_functions": safe_list(obj.get("core_functions", obj.get("CORE_FUNCTIONS", obj.get("核心函数列表", [])))),
            "description": safe_str(obj.get("description", obj.get("DESCRIPTION", obj.get("描述", "")))),
            "description_en": safe_str(obj.get("description_en", obj.get("DESCRIPTION_EN", obj.get("英文描述", "")))),
            "key_discovery": safe_str(obj.get("key_discovery", obj.get("KEY_DISCOVERY", obj.get("关键发现", "")))),
            "related_functions": safe_list(obj.get("related_functions", obj.get("RELATED_FUNCTIONS", obj.get("关联函数", [])))),
            "entailment_status": "non_entailing",
            "canonical_source": source_file,
            "canonical_page": canonical_page_from_path(source_file) if source_file else None,
            "schema_version": "normalized-jsonl-v1",
            "generated_at": utc_now_iso(),
            "source_commit": git_short_head(),
            "source_sha": source_sha,
            "inference_not_conclusion": True,
        })
    return entries

def build_effect_leads():
    """Build effect-leads.jsonl entries from identity audit."""
    entries = []
    source_path = CANONICAL_SRC / "rebuild" / "effect-leads-identity-audit.jsonl"
    source_file = str(source_path)

    if not source_path.exists():
        return entries

    # Also check for JSON variant
    source_json_path = CANONICAL_SRC / "rebuild" / "effect-leads-identity-audit.json"
    source_sha = sha256_file(source_path)

    items = load_jsonl(source_path)
    if not items:
        items = load_json_items(source_path.parent.glob("effect-leads-identity-audit*.json"))

    for obj in items:
        obj_id = obj.get("id", obj.get("ID", ""))
        if not obj_id:
            continue
        entries.append({
            "id": str(obj_id),
            "object_class": "effect_lead",
            "current_label": "effect_lead",
            "suggested_class": safe_str(obj.get("suggested_class", obj.get("SUGGESTED_CLASS", obj.get("建议分类", "")))),
            "name": safe_str(obj.get("name", obj.get("NAME", obj.get("名称", "")))),
            "name_en": safe_str(obj.get("name_en", obj.get("NAME_EN", obj.get("英文名", "")))),
            "definition": safe_str(obj.get("definition", obj.get("DEFINITION", obj.get("定义", "")))),
            "expression": safe_str(obj.get("expression", obj.get("EXPRESSION", obj.get("公式", "")))),
            "derivation": safe_str(obj.get("derivation", obj.get("DERIVATION", obj.get("推导", "")))),
            "related_functions": safe_list(obj.get("related_functions", obj.get("RELATED_FUNCTIONS", obj.get("关联函数", [])))),
            "related_cases": safe_list(obj.get("related_cases", obj.get("RELATED_CASES", obj.get("关联案例", [])))),
            "audit_reason_zh": safe_str(obj.get("audit_reason_zh", obj.get("AUDIT_REASON_ZH", obj.get("审查原因_中文", "")))),
            "audit_reason_en": safe_str(obj.get("audit_reason_en", obj.get("AUDIT_REASON_EN", obj.get("审查原因_英文", "")))),
            "should_keep_eff_id": bool(obj.get("should_keep_eff_id", obj.get("SHOULD_KEEP_EFF_ID", False))),
            "should_migrate_now": False,
            "is_likely_misnumbered": bool(obj.get("is_likely_misnumbered", obj.get("IS_LIKELY_MISNUMBERED", False))),
            "status": "lead",
            "canonical_source": source_file,
            "canonical_page": canonical_page_from_path(source_file) if source_file else None,
            "schema_version": "normalized-jsonl-v1",
            "generated_at": utc_now_iso(),
            "source_commit": git_short_head(),
            "source_sha": source_sha,
            "inference_not_conclusion": True,
        })
    return entries

def write_jsonl(path, entries):
    """Write entries to JSONL file."""
    with open(path, "w", encoding="utf-8") as f:
        for obj in entries:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def build_manifest(functions_count, cases_count, leads_count):
    """Build manifest.json."""
    sha_funcs = sha256_file(OUTPUT_DIR / "functions.jsonl")
    sha_cases = sha256_file(OUTPUT_DIR / "cases.jsonl")
    sha_leads = sha256_file(OUTPUT_DIR / "effect-leads.jsonl")

    manifest = {
        "schema_version": "normalized-jsonl-v1",
        "format": "jsonl",
        "generated_at": utc_now_iso(),
        "source_commit": git_short_head(),
        "rules": {
            "counts_are_dynamic": True,
            "canonical_data_not_replaced": True,
            "do_not_hardcode_counts": True,
            "inference_not_conclusion": True
        },
        "files": {
            "functions.jsonl": {
                "line_count": functions_count,
                "sha256": sha_funcs
            },
            "cases.jsonl": {
                "line_count": cases_count,
                "sha256": sha_cases
            },
            "effect-leads.jsonl": {
                "line_count": leads_count,
                "sha256": sha_leads
            }
        }
    }
    with open(OUTPUT_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest

def main():
    parser = argparse.ArgumentParser(description="Build minimal normalized JSONL layer")
    parser.add_argument("--dry-run", action="store_true", help="Show counts without writing")
    parser.add_argument("--all", action="store_true", help="Build all JSONL files")
    args = parser.parse_args()

    if not args.all and not args.dry_run:
        print("Usage: --dry-run or --all")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REBUILD_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading canonical sources...")
    funcs = build_functions(build_unified=True, build_items=True)
    cases = build_cases(build_unified=True, build_items=True)
    leads = build_effect_leads()

    print(f"  functions: {len(funcs)}")
    print(f"  cases: {len(cases)}")
    print(f"  effect_leads: {len(leads)}")

    if args.dry_run:
        print("Dry run complete. No files written.")
        return

    print("Writing JSONL files...")
    write_jsonl(OUTPUT_DIR / "functions.jsonl", funcs)
    write_jsonl(OUTPUT_DIR / "cases.jsonl", cases)
    write_jsonl(OUTPUT_DIR / "effect-leads.jsonl", leads)

    print("Building manifest...")
    manifest = build_manifest(len(funcs), len(cases), len(leads))

    # Generate report
    report_json = {
        "phase": "minimal_normalized_jsonl_layer",
        "is_recovery_run": True,
        "is_not_get_brain_only_adapter": True,
        "canonical_data_not_replaced": True,
        "full_bootstrap_not_run": True,
        "academic_search_not_run": True,
        "novelty_passed_not_generated": True,
        "active_promotion_not_executed": True,
        "files": {
            "functions.jsonl": {"line_count": len(funcs), "sha256": manifest["files"]["functions.jsonl"]["sha256"]},
            "cases.jsonl": {"line_count": len(cases), "sha256": manifest["files"]["cases.jsonl"]["sha256"]},
            "effect-leads.jsonl": {"line_count": len(leads), "sha256": manifest["files"]["effect-leads.jsonl"]["sha256"]}
        },
        "required_fields_present": True,
        "counts_dynamic": True,
        "workdir_clean_check": "to_be_verified"
    }
    with open(REBUILD_DIR / "normalized-jsonl-layer-minimal-report.json", "w", encoding="utf-8") as f:
        json.dump(report_json, f, ensure_ascii=False, indent=2)

    # Markdown report
    report_md = f"""# Normalized JSONL Layer Minimal Report

- Phase: minimal_normalized_jsonl_layer
- Recovery run: yes
- Not Get Brain only adapter: yes
- Canonical data replaced: no
- Full bootstrap: not run
- Academic search: not run
- Novelty passed: not generated
- Active promotion: not executed

## Generated files

| File | Line Count | SHA256 |
|------|-----------|--------|
| functions.jsonl | {len(funcs)} | {report_json["files"]["functions.jsonl"]["sha256"]} |
| cases.jsonl | {len(cases)} | {report_json["files"]["cases.jsonl"]["sha256"]} |
| effect-leads.jsonl | {len(leads)} | {report_json["files"]["effect-leads.jsonl"]["sha256"]} |

- Required fields: all present
- Counts: dynamic (not hardcoded)
"""
    with open(REBUILD_DIR / "normalized-jsonl-layer-minimal-report.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    print("Build complete.")
    print(f"  functions.jsonl: {len(funcs)} lines")
    print(f"  cases.jsonl: {len(cases)} lines")
    print(f"  effect-leads.jsonl: {len(leads)} lines")

if __name__ == "__main__":
    main()
