#!/usr/bin/env python3
"""
Migrate existing function-case links from data/functions/items/*.json and data/cases/items/*.json
into data/relations/function-case-relations.jsonl.

Usage:
    python3 scripts/migrate_function_case_relations.py --dry-run
    python3 scripts/migrate_function_case_relations.py
    python3 scripts/migrate_function_case_relations.py --check
"""

import argparse
import glob
import json
import os
import sys
from datetime import date, datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Default values that MUST be set on every record
DEFAULTS = {
    "entailment_status": "non_entailing",
    "is_definitive": False,
    "is_unique_explanation": False,
    "is_bidirectional_proof": False,
    "inference_note": {
        "zh": "这是推论关系，不是定论关系。",
        "en": "This is an inferential relation, not a definitive entailment."
    },
    "evidence_scope": {"zh": "", "en": ""},
    "limitations": {"zh": "", "en": ""},
    "counterexamples": [],
    "confidence": "low",
    "source_refs": [],
    "legacy_relation_migrated": True
}


def load_existing_records(path):
    """Load existing relations from jsonl, return dict keyed by (function_id, case_id)."""
    records = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    key = (rec.get("function_id", ""), rec.get("case_id", ""))
                    if key[0] and key[1]:
                        records[key] = rec
                except json.JSONDecodeError:
                    continue
    return records


def get_next_id(existing_records):
    """Return the next available FCR-XXXX id number."""
    max_n = 0
    for rec in existing_records.values():
        rid = rec.get("id", "")
        if rid.startswith("FCR-"):
            try:
                n = int(rid[4:])
                if n > max_n:
                    max_n = n
            except ValueError:
                pass
    return max_n + 1


def migrate(dry_run=False):
    relations_path = os.path.join(BASE_DIR, "data", "relations", "function-case-relations.jsonl")
    json_path = os.path.join(BASE_DIR, "data", "relations", "function-case-relations.json")
    index_path = os.path.join(BASE_DIR, "data", "relations", "function-case-relations-index.md")

    existing = load_existing_records(relations_path)
    next_id = get_next_id(existing)

    new_records = []
    migrated_count = 0
    seen_keys = set()

    # Scan function items for related_cases
    for fpath in sorted(glob.glob(os.path.join(BASE_DIR, "data", "functions", "items", "*.json"))):
        with open(fpath, "r", encoding="utf-8") as f:
            func = json.load(f)
        func_id = func.get("normalized_id", func.get("id", ""))
        if not func_id:
            continue
        for case_id in func.get("related_cases", []):
            key = (func_id, case_id)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            if key not in existing:
                rec = {
                    "id": f"FCR-{next_id:04d}",
                    "function_id": func_id,
                    "case_id": case_id,
                    "relation_type": "current_mapping",
                    "direction": "bidirectional_non_entailing",
                    "epistemic_status": "current_mapping",
                }
                rec.update(DEFAULTS)
                rec["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d")
                new_records.append(rec)
                next_id += 1
            else:
                # Update existing to ensure defaults
                existing[key].update(DEFAULTS)
                existing[key]["legacy_relation_migrated"] = True
                existing[key]["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d")
                migrated_count += 1

    # Scan case items for related_functions
    for fpath in sorted(glob.glob(os.path.join(BASE_DIR, "data", "cases", "items", "C-*.json"))):
        with open(fpath, "r", encoding="utf-8") as f:
            case = json.load(f)
        case_id = case.get("case_id", case.get("id", ""))
        if not case_id:
            continue
        for func_id in case.get("related_functions", []):
            key = (func_id, case_id)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            if key not in existing:
                rec = {
                    "id": f"FCR-{next_id:04d}",
                    "function_id": func_id,
                    "case_id": case_id,
                    "relation_type": "current_mapping",
                    "direction": "bidirectional_non_entailing",
                    "epistemic_status": "current_mapping",
                }
                rec.update(DEFAULTS)
                rec["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d")
                new_records.append(rec)
                next_id += 1
            else:
                existing[key].update(DEFAULTS)
                existing[key]["legacy_relation_migrated"] = True
                existing[key]["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d")
                migrated_count += 1

    if dry_run:
        print(f"DRY RUN — would create {len(new_records)} new relation records")
        print(f"DRY RUN — would update {migrated_count} existing records with defaults")
        if new_records:
            print("\nNew records (first 10):")
            for r in new_records[:10]:
                print(f"  {r['id']}: {r['function_id']} <-> {r['case_id']}")
        return {
            "new_records": len(new_records),
            "migrated_records": migrated_count,
            "total_existing": len(existing),
            "status": "dry_run",
        }

    # Write jsonl
    all_records = {}
    for rec in existing.values():
        all_records[(rec["function_id"], rec["case_id"])] = rec
    for rec in new_records:
        key = (rec["function_id"], rec["case_id"])
        all_records[key] = rec

    with open(relations_path, "w", encoding="utf-8") as f:
        for rec in sorted(all_records.values(), key=lambda r: r.get("id", "")):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Write json
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(all_records),
            "items": sorted(all_records.values(), key=lambda r: r.get("id", ""))
        }, f, ensure_ascii=False, indent=2)

    # Write index
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Function-Case Relations Index\n\n")
        f.write("All function-case relations are inferential, not definitive.\n\n")
        f.write("| ID | Function | Case | Type | Epistemic Status | Entailment Status | Confidence |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for rec in sorted(all_records.values(), key=lambda r: r.get("id", "")):
            f.write(f"| {rec['id']} | {rec['function_id']} | {rec['case_id']} | "
                    f"{rec['relation_type']} | {rec['epistemic_status']} | "
                    f"{rec['entailment_status']} | {rec['confidence']} |\n")

    print(f"MIGRATED: {migrated_count} existing records updated")
    print(f"CREATED: {len(new_records)} new relation records")
    print(f"TOTAL: {len(all_records)} function-case relation records")

    return {
        "new_records": len(new_records),
        "migrated_records": migrated_count,
        "total_relations": len(all_records),
        "status": "completed",
    }


def check():
    relations_path = os.path.join(BASE_DIR, "data", "relations", "function-case-relations.jsonl")
    if not os.path.exists(relations_path):
        print(f"CHECK FAIL: {relations_path} not found")
        return False

    errors = []
    with open(relations_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {i}: JSON parse error: {e}")
                continue

            if rec.get("entailment_status") != "non_entailing":
                errors.append(f"{rec.get('id', 'unknown')}: entailment_status is not non_entailing")
            if rec.get("is_definitive") is not False:
                errors.append(f"{rec.get('id', 'unknown')}: is_definitive is not false")
            if rec.get("is_unique_explanation") is not False:
                errors.append(f"{rec.get('id', 'unknown')}: is_unique_explanation is not false")
            if rec.get("is_bidirectional_proof") is not False:
                errors.append(f"{rec.get('id', 'unknown')}: is_bidirectional_proof is not false")

    if errors:
        print(f"CHECK FAIL: {len(errors)} errors found")
        for e in errors[:20]:
            print(f"  - {e}")
        return False

    print(f"CHECK PASS: all relation records are non_entailing")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate function-case relations")
    parser.add_argument("--dry-run", action="store_true", help="Dry run only")
    parser.add_argument("--check", action="store_true", help="Check existing relations")
    args = parser.parse_args()

    if args.check:
        ok = check()
        sys.exit(0 if ok else 1)
    elif args.dry_run:
        result = migrate(dry_run=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = migrate(dry_run=False)
        print(json.dumps(result, ensure_ascii=False, indent=2))
