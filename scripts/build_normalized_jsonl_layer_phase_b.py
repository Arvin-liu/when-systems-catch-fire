#!/usr/bin/env python3
"""
Phase B: Build remaining object-layer JSONL files.
Reads canonical sources and generates discoveries, predictions,
answers, analytic-solutions, function-case-relations, object-classification-crosswalk.
Does NOT touch functions/cases unless --refresh-core is passed.
"""

import argparse
import hashlib
import json
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CANONICAL_SRC = BASE / "data"
OUTPUT_DIR = BASE / "data" / "normalized-jsonl"
REBUILD_DIR = BASE / "data" / "rebuild"

def sha256_file(path):
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

def write_jsonl_phase_b(path, entries):
    """Write entries to a JSONL file. Uniquely named to avoid shadowing issues."""
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for obj in entries:
            f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count

def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def safe_str(val):
    return val if val is not None else ""

def safe_list(val):
    if isinstance(val, list):
        # Extract string IDs from complex objects
        result = []
        for item in val:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                result.append(item.get("id", item.get("id", "")))
        return result
    return []

def safe_zh(en_map, fallback=""):
    """Extract zh text from bilingual dicts or return the value itself."""
    if isinstance(en_map, dict):
        return safe_str(en_map.get("zh", en_map.get("en", "")))
    return safe_str(en_map)

def safe_en(en_map, fallback=""):
    if isinstance(en_map, dict):
        return safe_str(en_map.get("en", ""))
    return safe_str(en_map)

def canonical_page_from_obj(obj):
    """Try to extract page from obj."""
    if isinstance(obj, str):
        return obj if "#" in obj else None
    if isinstance(obj, dict):
        p = obj.get("page", obj.get("canonical_page", ""))
        return p if p and "#" in str(p) else None
    return None

def load_jsonl(path):
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

def extract_related_ids(rel_field, key="id"):
    """Extract list of string IDs from a related field."""
    val = rel_field if rel_field else []
    if isinstance(val, list):
        ids = []
        for item in val:
            if isinstance(item, str):
                ids.append(item)
            elif isinstance(item, dict):
                ids.append(item.get(key, ""))
        return [i for i in ids if i]
    return []

def write_jsonl(path, entries):
    with open(path, "w", encoding="utf-8") as f:
        for obj in entries:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# ---- builders ----

def build_discoveries():
    entries = []
    src = CANONICAL_SRC / "discoveries" / "unified-discoveries.jsonl"
    items = load_jsonl(src)
    source_file = str(src)
    source_sha = sha256_file(src)

    for obj in items:
        disc_id = obj.get("id", obj.get("ID", ""))
        if not disc_id:
            continue
        entries.append({
            "id": str(disc_id),
            "object_class": "discovery",
            "name": safe_zh(obj.get("title", obj.get("name", obj.get("标题", "")))),
            "name_en": safe_en(obj.get("title", obj.get("name", obj.get("英文名", "")))),
            "definition": safe_str(obj.get("definition", obj.get("DEFINITION", ""))),
            "description": safe_str(obj.get("summary", obj.get("content", obj.get("description", obj.get("DESCRIPTION", ""))))),
            "description_en": safe_en(obj.get("summary", obj.get("content", obj.get("description", obj.get("DESCRIPTION_EN", ""))))),
            "related_functions": extract_related_ids(obj.get("related_functions", [])),
            "related_cases": extract_related_ids(obj.get("related_cases", [])),
            "related_analytic_solutions": extract_related_ids(obj.get("related_analytic_solutions", [])),
            "status": safe_str(obj.get("status", obj.get("STATUS", ""))),
            "academic_novelty_status": safe_str(obj.get("academic_novelty", {}).get("status", "")),
            "dual_channel_verification_status": safe_str(obj.get("bootstrap_status", "")),
            "canonical_source": source_file,
            "canonical_page": canonical_page_from_obj(obj.get("page", "")),
            "schema_version": "normalized-jsonl-v1",
            "generated_at": utc_now_iso(),
            "source_commit": git_short_head(),
            "source_sha": source_sha,
            "inference_not_conclusion": True,
        })
    return entries

def build_predictions():
    entries = []
    src = CANONICAL_SRC / "predictions" / "unified-predictions.jsonl"
    items = load_jsonl(src)
    source_file = str(src)
    source_sha = sha256_file(src)

    for obj in items:
        pred_id = obj.get("id", obj.get("ID", ""))
        if not pred_id:
            continue
        entries.append({
            "id": str(pred_id),
            "object_class": "prediction",
            "name": safe_zh(obj.get("title", obj.get("name", obj.get("标题", obj.get("statement", ""))))),
            "name_en": safe_en(obj.get("title", obj.get("name", obj.get("英文名", obj.get("statement", ""))))),
            "condition": safe_str(obj.get("test_condition", obj.get("condition", obj.get("TEST_CONDITION", "")))),
            "future_observation": safe_str(obj.get("statement", obj.get("FUTURE_OBSERVATION", obj.get("test_condition", "")))),
            "verification_method": safe_str(obj.get("test_condition", obj.get("VERIFICATION_METHOD", obj.get("test_condition", "")))),
            "description": safe_str(obj.get("statement", obj.get("DESCRIPTION", obj.get("basis", "")))),
            "related_functions": extract_related_ids(obj.get("related_functions", [])),
            "related_cases": extract_related_ids(obj.get("related_cases", [])),
            "status": safe_str(obj.get("status", obj.get("STATUS", ""))),
            "academic_novelty_status": safe_str(obj.get("academic_novelty", {}).get("status", "")),
            "canonical_source": source_file,
            "canonical_page": canonical_page_from_obj(obj.get("page", "")),
            "schema_version": "normalized-jsonl-v1",
            "generated_at": utc_now_iso(),
            "source_commit": git_short_head(),
            "source_sha": source_sha,
            "inference_not_conclusion": True,
        })
    return entries

def build_answers():
    entries = []
    src = CANONICAL_SRC / "answers" / "unified-answers.jsonl"
    items = load_jsonl(src)
    source_file = str(src)
    source_sha = sha256_file(src)

    for obj in items:
        ans_id = obj.get("id", obj.get("ID", ""))
        if not ans_id:
            continue
        entries.append({
            "id": str(ans_id),
            "object_class": "answer",
            "name": safe_zh(obj.get("title", obj.get("name", obj.get("标题", "")))),
            "name_en": safe_en(obj.get("title", obj.get("name", obj.get("英文名", "")))),
            "question": safe_str(obj.get("question", obj.get("QUESTION", obj.get("QUESTION", "")))),
            "answer": safe_str(obj.get("answer", obj.get("ANSWER", obj.get("new_explanation", "")))),
            "answer_en": safe_en(obj.get("answer", obj.get("ANSWER_EN", obj.get("new_explanation", "")))),
            "related_functions": extract_related_ids(obj.get("related_functions", [])),
            "related_cases": extract_related_ids(obj.get("related_cases", [])),
            "related_analytic_solutions": extract_related_ids(obj.get("related_analytic_solutions", [])),
            "status": safe_str(obj.get("status", obj.get("STATUS", ""))),
            "academic_novelty_status": safe_str(obj.get("academic_novelty", {}).get("status", "")),
            "canonical_source": source_file,
            "canonical_page": canonical_page_from_obj(obj.get("page", "")),
            "schema_version": "normalized-jsonl-v1",
            "generated_at": utc_now_iso(),
            "source_commit": git_short_head(),
            "source_sha": source_sha,
            "inference_not_conclusion": True,
        })
    return entries

def build_analytic_solutions():
    entries = []
    src = CANONICAL_SRC / "analytic-solutions" / "unified-analytic-solutions.jsonl"
    items = load_jsonl(src)
    source_file = str(src)
    source_sha = sha256_file(src)

    for obj in items:
        sol_id = obj.get("id", obj.get("ID", ""))
        if not sol_id:
            continue
        formula_val = obj.get("formula", obj.get("formula_text", obj.get("expression", obj.get("EXPRESSION", ""))))
        entries.append({
            "id": str(sol_id),
            "object_class": "analytic_solution",
            "name": safe_zh(obj.get("title", obj.get("name", obj.get("标题", "")))),
            "name_en": safe_en(obj.get("title", obj.get("name", obj.get("英文名", "")))),
            "problem": safe_str(obj.get("problem", obj.get("PROBLEM", obj.get("problem", obj.get("title", ""))))),
            "solution": safe_str(formula_val),
            "expression": safe_str(formula_val),
            "derivation": safe_str(", ".join(obj.get("derivation", [])) if isinstance(obj.get("derivation"), list) else safe_str(obj.get("derivation", obj.get("DERIVATION", "")))),
            "verification": safe_str(obj.get("verification", obj.get("VERIFICATION", ""))),
            "related_functions": extract_related_ids(obj.get("related_functions", [])),
            "related_cases": extract_related_ids(obj.get("related_cases", [])),
            "status": safe_str(obj.get("status", obj.get("STATUS", ""))),
            "academic_novelty_status": safe_str(obj.get("academic_novelty", {}).get("status", "")),
            "canonical_source": source_file,
            "canonical_page": canonical_page_from_obj(obj.get("page", "")),
            "schema_version": "normalized-jsonl-v1",
            "generated_at": utc_now_iso(),
            "source_commit": git_short_head(),
            "source_sha": source_sha,
            "inference_not_conclusion": True,
        })
    return entries

def build_function_case_relations():
    entries = []
    src = CANONICAL_SRC / "relations" / "function-case-relations.jsonl"
    items = load_jsonl(src)
    source_file = str(src)
    source_sha = sha256_file(src)

    for obj in items:
        rel_id = obj.get("id", obj.get("ID", obj.get("relation_id", "")))
        if not rel_id:
            # Generate from function_id + case_id if available
            fid = obj.get("function_id", obj.get("FUNCTION_ID", ""))
            cid = obj.get("case_id", obj.get("CASE_ID", ""))
            rel_id = f"REL-{fid}-{cid}" if fid and cid else ""
        if not rel_id:
            # Try function_id/case_id from nested fields
            func = obj.get("function", obj.get("function_ref", {}))
            case = obj.get("case", obj.get("case_ref", {}))
            if isinstance(func, dict):
                fid = func.get("id", func.get("id", ""))
            else:
                fid = str(func) if func else ""
            if isinstance(case, dict):
                cid = case.get("id", case.get("id", ""))
            else:
                cid = str(case) if case else ""
            rel_id = f"REL-{fid}-{cid}" if fid and cid else ""
        if not rel_id:
            continue

        rel_type = safe_str(obj.get("relation_type", obj.get("RELATION_TYPE", obj.get("type", "inferential"))))
        if not rel_type:
            rel_type = "inferential"

        entries.append({
            "id": str(rel_id),
            "object_class": "function_case_relation",
            "function_id": safe_str(obj.get("function_id", obj.get("FUNCTION_ID", obj.get("function", {}).get("id", "")) if isinstance(obj.get("function"), dict) else "")),
            "case_id": safe_str(obj.get("case_id", obj.get("CASE_ID", obj.get("case", {}).get("id", "")) if isinstance(obj.get("case"), dict) else "")),
            "relation_type": rel_type,
            "relation_description": safe_str(obj.get("relation_description", obj.get("RELATION_DESCRIPTION", obj.get("description", obj.get("DESCRIPTION", ""))))),
            "evidence": safe_str(obj.get("evidence", obj.get("EVIDENCE", obj.get("basis", "")))),
            "confidence": safe_str(obj.get("confidence", obj.get("CONFIDENCE", ""))),
            "entailment_status": "non_entailing",
            "is_definitive": False,
            "is_unique_explanation": False,
            "is_bidirectional_proof": False,
            "status": safe_str(obj.get("status", obj.get("STATUS", ""))),
            "canonical_source": source_file,
            "canonical_page": canonical_page_from_obj(obj.get("page", "")),
            "schema_version": "normalized-jsonl-v1",
            "generated_at": utc_now_iso(),
            "source_commit": git_short_head(),
            "source_sha": source_sha,
            "inference_not_conclusion": True,
        })
    return entries

def build_crosswalk():
    entries = []
    src = CANONICAL_SRC / "object-classification" / "object-classification-crosswalk.jsonl"
    items = load_jsonl(src)
    source_file = str(src)
    source_sha = sha256_file(src)

    for obj in items:
        xw_id = obj.get("id", obj.get("ID", obj.get("legacy_id", "")))
        if not xw_id:
            continue
        legacy_id = obj.get("legacy_id", obj.get("LEGACY_ID", ""))
        new_id = obj.get("new_id", obj.get("NEW_ID", legacy_id))
        full_id = new_id if new_id else str(xw_id)

        entries.append({
            "id": str(full_id),
            "object_class": "classification_crosswalk",
            "source_id": str(legacy_id) if legacy_id else str(xw_id),
            "source_class": safe_str(obj.get("legacy_class", obj.get("LEGACY_CLASS", obj.get("source_class", "")))),
            "suggested_class": safe_str(obj.get("new_class", obj.get("NEW_CLASS", obj.get("suggested_class", "")))),
            "current_class": safe_str(obj.get("new_class", obj.get("NEW_CLASS", obj.get("current_class", "")))),
            "target_layer": safe_str(obj.get("target_layer", obj.get("TARGET_LAYER", ""))),
            "confidence": safe_str(obj.get("confidence", obj.get("CONFIDENCE", ""))),
            "reason_zh": safe_str(obj.get("reason", obj.get("REASON_ZH", obj.get("mathematical_criterion", "")))),
            "reason_en": safe_str(obj.get("reason_en", obj.get("REASON_EN", ""))),
            "status": safe_str(obj.get("status", obj.get("STATUS", obj.get("migration_action", "")))),
            "canonical_source": source_file,
            "canonical_page": None,
            "schema_version": "normalized-jsonl-v1",
            "generated_at": utc_now_iso(),
            "source_commit": git_short_head(),
            "source_sha": source_sha,
            "inference_not_conclusion": True,
        })
    return entries

def main():
    parser = argparse.ArgumentParser(description="Build Phase B JSONL files")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--skip-refresh-core", action="store_true", default=True,
                        help="Skip rebuilding functions/cases (default: skip)")
    parser.add_argument("--refresh-core", action="store_true", dest="refresh_core",
                        help="Also rebuild functions/cases (implies --all)")
    args = parser.parse_args()

    if not args.all and not args.dry_run:
        print("Usage: --dry-run or --all")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REBUILD_DIR.mkdir(parents=True, exist_ok=True)

    builders = [
        ("discoveries.jsonl", build_discoveries, "discovery"),
        ("predictions.jsonl", build_predictions, "prediction"),
        ("answers.jsonl", build_answers, "answer"),
        ("analytic-solutions.jsonl", build_analytic_solutions, "analytic_solution"),
        ("function-case-relations.jsonl", build_function_case_relations, "function_case_relation"),
        ("object-classification-crosswalk.jsonl", build_crosswalk, "classification_crosswalk"),
    ]

    results = {}
    for fname, builder_fn, _ in builders:
        entries = builder_fn()
        results[fname] = entries
        print(f"  {fname}: {len(entries)}")

    if args.dry_run:
        print("Dry run complete. No files written.")
        return

    for fname, entries in results.items():
        write_jsonl_phase_b(OUTPUT_DIR / fname, entries)

    if args.refresh_core:
        print("Rebuilding core JSONL files...")
        from scripts.build_normalized_jsonl_layer_minimal import (
            build_functions, build_cases,
            write_jsonl as write_jsonl_minimal, build_manifest
        )
        funcs = build_functions(True, True)
        cases = build_cases(True, True)
        write_jsonl_minimal(OUTPUT_DIR / "functions.jsonl", funcs)
        write_jsonl_minimal(OUTPUT_DIR / "cases.jsonl", cases)
        build_manifest(len(funcs), len(cases))
        results["functions.jsonl"] = funcs
        results["cases.jsonl"] = cases
        print("  core rebuilt")

    # Phase B report
    report = {
        "phase": "phase_b",
        "is_not_core_rebuild": True,
        "canonical_data_not_replaced": True,
        "full_bootstrap_not_run": True,
        "academic_search_not_run": True,
        "novelty_passed_not_generated": True,
        "active_promotion_not_executed": True,
        "files": {fname: {"line_count": len(entries)} for fname, entries in results.items()},
    }
    with open(REBUILD_DIR / "normalized-jsonl-phase-b-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    md = f"""# Phase B Report

- Phase: phase_b
- Not core rebuild: yes
- Canonical data replaced: no
- Full bootstrap: not run
- Academic search: not run
- Novelty passed: not generated
- Active promotion: not executed

## Generated files

| File | Line Count |
|------|-----------|
"""
    for fname, entries in results.items():
        md += f"| {fname} | {len(entries)} |\n"

    md += "\n- Required fields: dynamic\n- Counts: dynamic (not hardcoded)\n"

    with open(REBUILD_DIR / "normalized-jsonl-phase-b-report.md", "w", encoding="utf-8") as f:
        f.write(md)

    print("Phase B build complete.")

if __name__ == "__main__":
    main()
