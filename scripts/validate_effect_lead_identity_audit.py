#!/usr/bin/env python3
"""
校验 EFF lead 身份审查脚本。
验证审计报告的正确性和完整性。
"""

import json
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def validate_audit(report_json):
    """Validate the audit report JSON."""
    errors = []

    # Check required top-level keys
    required_keys = [
        "reviewed_total",
        "confirmed_effect_candidates",
        "likely_function_candidates",
        "likely_analytic_solution_candidates",
        "likely_discovery_candidates",
        "likely_prediction_candidates",
        "likely_answer_candidates",
        "note_or_reference_candidates",
        "malformed_or_insufficient",
        "needs_human_review",
        "likely_misnumbered_count",
        "should_keep_eff_id_count",
        "should_not_keep_eff_id_count",
        "default_accepted_as_effect",
        "migration_not_executed",
        "bootstrap_full_run_executed",
        "novelty_search_executed",
        "active_promotion_executed",
        "model_used",
        "items",
    ]

    for key in required_keys:
        if key not in report_json:
            errors.append(f"Missing required key: {key}")

    # Check non-acceptance guarantees
    if report_json.get("default_accepted_as_effect") is not False:
        errors.append("default_accepted_as_effect must be false")
    if report_json.get("migration_not_executed") is not True:
        errors.append("migration_not_executed must be true")
    if report_json.get("bootstrap_full_run_executed") is not False:
        errors.append("bootstrap_full_run_executed must be false")
    if report_json.get("novelty_search_executed") is not False:
        errors.append("novelty_search_executed must be false")
    if report_json.get("active_promotion_executed") is not False:
        errors.append("active_promotion_executed must be false")

    # Check model
    if report_json.get("model_used") != "agnes/agnes-2.0-flash":
        errors.append(f"Wrong model: {report_json.get('model_used')}")

    # Check item count
    items = report_json.get("items", [])
    if not items:
        errors.append("No items in report")
        return errors

    # Validate each item
    eff_ids_seen = set()
    for item in items:
        eid = item.get("id", "")
        if not eid.startswith("EFF-"):
            errors.append(f"Invalid EFF id: {eid}")
            continue

        if eid in eff_ids_seen:
            errors.append(f"Duplicate EFF id: {eid}")
        eff_ids_seen.add(eid)

        audit = item.get("audit_result", {})
        if not audit.get("suggested_class"):
            errors.append(f"Missing suggested_class: {eid}")

        if audit.get("confidence") not in ("high", "medium", "low"):
            errors.append(f"Invalid confidence for {eid}: {audit.get('confidence')}")

        if "mathematical_reason_zh" not in audit:
            errors.append(f"Missing mathematical_reason_zh: {eid}")
        if "mathematical_reason_en" not in audit:
            errors.append(f"Missing mathematical_reason_en: {eid}")

        if audit.get("should_migrate_now") is not False:
            errors.append(f"should_migrate_now must be false for {eid}")

        if item.get("safe_action") != "report_only":
            errors.append(f"safe_action must be report_only for {eid}")

    # Check all 36 are present
    expected_ids = {f"EFF-{i:04d}" for i in range(1, 37)}
    missing = expected_ids - eff_ids_seen
    if missing:
        errors.append(f"Missing EFF items: {missing}")
    extra = eff_ids_seen - expected_ids
    if extra:
        errors.append(f"Extra EFF items: {extra}")

    # Check count consistency
    if report_json.get("reviewed_total", 0) != len(items):
        errors.append(f"reviewed_total ({report_json.get('reviewed_total')}) != items count ({len(items)})")

    return errors


def check_files_exist():
    """Check that all expected output files exist."""
    rebuild = ROOT / "data" / "rebuild"
    required_files = [
        rebuild / "effect-leads-identity-audit-report.md",
        rebuild / "effect-leads-identity-audit-report.json",
        rebuild / "effect-leads-identity-audit.json",
        rebuild / "effect-leads-identity-audit.jsonl",
    ]
    missing = [f for f in required_files if not f.exists()]
    return missing


def main():
    parser = argparse.ArgumentParser(description="Validate EFF lead identity audit")
    parser.add_argument("--check", action="store_true", help="Run full validation")
    args = parser.parse_args()

    if not args.check:
        print("Usage: python validate_effect_lead_identity_audit.py --check")
        sys.exit(1)

    all_ok = True
    errors = []

    # 1. Check files exist
    print("=== File existence check ===")
    missing = check_files_exist()
    if missing:
        errors.extend([f"Missing file: {f.name}" for f in missing])
        print(f"  MISSING: {[f.name for f in missing]}")
        all_ok = False
    else:
        print("  All required files present")

    # 2. Validate JSON report
    print("\n=== JSON report validation ===")
    report_path = ROOT / "data" / "rebuild" / "effect-leads-identity-audit-report.json"
    if report_path.exists():
        with open(report_path, encoding="utf-8") as f:
            report = json.load(f)
        errors.extend(validate_audit(report))
        if errors:
            print("  ERRORS:")
            for e in errors[-5:]:
                print(f"    - {e}")
            all_ok = False
        else:
            print("  All validation checks passed")
            print(f"  Reviewed: {report.get('reviewed_total')}")
            print(f"  Model: {report.get('model_used')}")
            print(f"  Effects confirmed: {report.get('confirmed_effect_candidates')}")
            print(f"  Function candidates: {report.get('likely_function_candidates')}")
    else:
        errors.append("effect-leads-identity-audit-report.json not found")
        all_ok = False

    # 3. Validate JSONL
    print("\n=== JSONL validation ===")
    jsonl_path = ROOT / "data" / "rebuild" / "effect-leads-identity-audit.jsonl"
    if jsonl_path.exists():
        lines = jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        print(f"  Lines: {len(lines)}")
        if len(lines) != 36:
            errors.append(f"JSONL has {len(lines)} lines, expected 36")
            all_ok = False
    else:
        errors.append("JSONL file not found")
        all_ok = False

    # 4. Check AGENT_ENTRY.md
    print("\n=== AGENT_ENTRY.md check ===")
    agent_entry = ROOT / "AGENT_ENTRY.md"
    if agent_entry.exists():
        content = agent_entry.read_text(encoding="utf-8")
        if "效应候选身份审查规则" in content or "Effect Lead Identity Audit Rule" in content:
            print("  Effect Lead Identity Audit Rule found")
        else:
            errors.append("AGENT_ENTRY.md missing Effect Lead Identity Audit Rule")
            all_ok = False
    else:
        print("  AGENT_ENTRY.md not found (may be OK if not created)")

    # 5. Check llms.txt
    print("\n=== llms.txt check ===")
    llms_path = ROOT / "llms.txt"
    if llms_path.exists():
        content = llms_path.read_text(encoding="utf-8")
        if "Effect Lead Identity Audit" in content:
            print("  Effect Lead Identity Audit found")
        else:
            errors.append("llms.txt missing Effect Lead Identity Audit")
            all_ok = False
    else:
        print("  llms.txt not found (may be OK if not created)")

    # Final
    print(f"\n=== RESULT ===")
    if all_ok and not errors:
        print("ALL VALIDATION CHECKS PASSED")
    else:
        print(f"VALIDATION FAILED: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
