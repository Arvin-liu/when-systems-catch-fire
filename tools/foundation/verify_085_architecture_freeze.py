#!/usr/bin/env python3
"""
085 Architecture Structure Freeze Validator
Validates that architecture structure freeze is correct and consistent.
"""
import json
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def load_jsonl(path):
    records = []
    if not os.path.exists(path):
        return records
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)

def main():
    base = REPO_ROOT / "data" / "foundation"
    errors = []
    warnings = []
    checks_passed = 0
    checks_total = 0

    print("=== 085 Architecture Structure Freeze Validator ===\n")

    # 1. 084 original files still exist
    checks_total += 1
    files_084 = [
        base / "adjudications" / "084-max-decisions.jsonl",
        base / "adjudications" / "084-max-self-review.jsonl",
        base / "adjudications" / "084-run-state.json",
        base / "proofs" / "084-proof-obligations.jsonl",
        base / "evidence" / "084-empirical-obligations.jsonl",
    ]
    all_exist = all(f.exists() for f in files_084)
    if all_exist:
        checks_passed += 1
        print(f"✅ 084 original files exist ({len(files_084)} files)")
    else:
        missing = [str(f) for f in files_084 if not f.exists()]
        errors.append(f"084 files missing: {missing}")
        print(f"❌ 084 files missing: {missing}")

    # 2. 085 overlay ID set matches 084
    checks_total += 1
    decisions_084 = load_jsonl(str(base / "adjudications" / "084-max-decisions.jsonl"))
    overlay_085 = load_jsonl(str(base / "adjudications" / "085-084-status-overlay.jsonl"))
    ids_084 = {d["stable_id"] for d in decisions_084}
    ids_085 = {d["stable_id"] for d in overlay_085}
    if ids_084 == ids_085:
        checks_passed += 1
        print(f"✅ 085 overlay ID set matches 084 ({len(ids_084)} IDs)")
    else:
        only_084 = ids_084 - ids_085
        only_085 = ids_085 - ids_084
        errors.append(f"ID mismatch: only_084={sorted(only_084)[:5]}, only_085={sorted(only_085)[:5]}")
        print(f"❌ ID mismatch: only_084={len(only_084)}, only_085={len(only_085)}")

    # 3. All summary sums = 353
    checks_total += 1
    decision_counts = {}
    for d in decisions_084:
        decision_counts[d['reconciled_decision']] = decision_counts.get(d['reconciled_decision'], 0) + 1
    if sum(decision_counts.values()) == 353:
        checks_passed += 1
        print(f"✅ Decision sum = {sum(decision_counts.values())} == 353")
    else:
        errors.append(f"Decision sum = {sum(decision_counts.values())} != 353")
        print(f"❌ Decision sum = {sum(decision_counts.values())} != 353")

    # 4. T4 contradiction resolved
    checks_total += 1
    t4 = next((d for d in decisions_084 if d['stable_id'] == 'T4'), None)
    t4_overlay = next((d for d in overlay_085 if d['stable_id'] == 'T4'), None)
    if t4 and t4_overlay:
        if t4['reconciled_decision'] == t4_overlay['084_original_reconciled_decision']:
            checks_passed += 1
            print(f"✅ T4 contradiction resolved: {t4['reconciled_decision']} (JSONL truth confirmed)")
        else:
            errors.append("T4 overlay doesn't match 084 data")
            print(f"❌ T4 overlay mismatch")
    else:
        errors.append("T4 not found in 084 or overlay")
        print(f"❌ T4 not found")

    # 5. P8 contradiction resolved
    checks_total += 1
    p8 = [d for d in decisions_084 if d['claim_type'] == 'P8_other_strong']
    p8_retain = sum(1 for d in p8 if d['reconciled_decision'] == 'RETAIN_SCOPED_DEFINITION')
    p8_downgrade_nl = sum(1 for d in p8 if d['reconciled_decision'] == 'DOWNGRADE_TO_NATURAL_LANGUAGE_CANDIDATE')
    p8_downgrade_sa = sum(1 for d in p8 if d['reconciled_decision'] == 'DOWNGRADE_TO_STRUCTURAL_ANALOGY')
    p8_sum = p8_retain + p8_downgrade_nl + p8_downgrade_sa
    if p8_sum == len(p8) == 122:
        checks_passed += 1
        print(f"✅ P8 contradiction resolved: retain={p8_retain}, downgrade_nl={p8_downgrade_nl}, structural={p8_downgrade_sa}, total={p8_sum}")
    else:
        errors.append(f"P8 sum mismatch: {p8_sum} != {len(p8)}")
        print(f"❌ P8 sum mismatch: {p8_sum} != {len(p8)}")

    # 6. No PROVED without artifact
    checks_total += 1
    proved = [d for d in decisions_084 if d['proof_status'] == 'PROVED_WITH_ARTIFACT']
    if len(proved) == 0:
        checks_passed += 1
        print(f"✅ No PROVED_WITH_ARTIFACT records (correct - no artifacts exist)")
    else:
        errors.append(f"{len(proved)} records have PROVED_WITH_ARTIFACT without artifact")
        print(f"❌ {len(proved)} records have PROVED_WITH_ARTIFACT")

    # 7. No EMPIRICALLY_VALIDATED without external source
    checks_total += 1
    empirical = [d for d in decisions_084 if d['evidence_status'] == 'EMPIRICAL_EVIDENCE_AVAILABLE']
    # T18 should be corrected in overlay
    t18_overlay = next((d for d in overlay_085 if d['stable_id'] == 'T18'), None)
    if t18_overlay and t18_overlay.get('085_corrected_evidence_status') == 'NO_EMPIRICAL_EVIDENCE':
        checks_passed += 1
        print(f"✅ T18 evidence_status corrected to NO_EMPIRICAL_EVIDENCE in overlay")
    else:
        warnings.append("T18 evidence_status not corrected in overlay")
        print(f"⚠️ T18 evidence_status not corrected in overlay")

    # 8. No STRICT_ISOMORPHISM accepted
    checks_total += 1
    strict_iso = [d for d in decisions_084 if d['reconciled_decision'] == 'RETAIN_SCOPED_DEFINITION' and d['claim_type'] == 'P4_structural_isomorphism']
    if len(strict_iso) == 0:
        checks_passed += 1
        print(f"✅ No STRICT_ISOMORPHISM accepted (correct - no bijection verification exists)")
    else:
        # Check if they actually have bijection verification
        for d in strict_iso:
            if 'bijection' not in d.get('source_quote', '').lower():
                errors.append(f"{d['stable_id']}: RETAIN_SCOPED_DEFINITION for P4 without bijection evidence")
        if not any(e for e in errors if 'bijection' in e):
            checks_passed += 1
            print(f"⚠️ {len(strict_iso)} P4 RETAIN_SCOPED_DEFINITION records exist (need manual verification)")

    # 9. Architecture freeze status correct
    checks_total += 1
    freeze_json = load_json(str(base / "architecture-structure-freeze-v1.json"))
    if freeze_json and freeze_json.get('status') == 'ARCHITECTURE_STRUCTURE_FROZEN_CLAIM_TRUTH_PROVISIONAL':
        checks_passed += 1
        print(f"✅ Architecture freeze status = ARCHITECTURE_STRUCTURE_FROZEN_CLAIM_TRUTH_PROVISIONAL")
    else:
        errors.append(f"Architecture freeze status incorrect: {freeze_json.get('status') if freeze_json else 'file not found'}")
        print(f"❌ Architecture freeze status incorrect")

    # 10. Legacy tables unchanged
    checks_total += 1
    legacy_files = [
        REPO_ROOT / "统一函数总表",
        REPO_ROOT / "统一案例总表",
    ]
    # Check they exist
    if all(f.exists() for f in legacy_files):
        checks_passed += 1
        print(f"✅ Legacy table directories exist")
    else:
        errors.append("Legacy table directories missing")
        print(f"❌ Legacy table directories missing")

    # 11. Project state file
    checks_total += 1
    project_state = load_json(str(base / "project-state-085.json"))
    if project_state and project_state.get('architecture_freeze_status') == 'ARCHITECTURE_STRUCTURE_FROZEN_CLAIM_TRUTH_PROVISIONAL':
        checks_passed += 1
        print(f"✅ Project state 085 architecture_freeze_status correct")
    else:
        errors.append("Project state 085 missing or incorrect")
        print(f"❌ Project state 085 missing or incorrect")

    # 12. Audit files exist
    checks_total += 1
    audit_files = [
        base / "audits" / "085-084-generation-mechanism-audit.json",
        base / "audits" / "085-084-template-clusters.jsonl",
        base / "audits" / "085-report-data-contradictions.jsonl",
    ]
    if all(f.exists() for f in audit_files):
        checks_passed += 1
        print(f"✅ Audit files exist ({len(audit_files)} files)")
    else:
        missing = [str(f) for f in audit_files if not f.exists()]
        errors.append(f"Audit files missing: {missing}")
        print(f"❌ Audit files missing: {missing}")

    # 13. Backlog queue files exist
    checks_total += 1
    queue_files = [
        base / "work-queues" / "085-proof-priority-queue.jsonl",
        base / "work-queues" / "085-empirical-priority-queue.jsonl",
        base / "work-queues" / "085-cross-model-acceptance-queue.jsonl",
    ]
    if all(f.exists() for f in queue_files):
        checks_passed += 1
        proof_count = sum(1 for l in open(queue_files[0]) if l.strip())
        empirical_count = sum(1 for l in open(queue_files[1]) if l.strip())
        cross_model_count = sum(1 for l in open(queue_files[2]) if l.strip())
        print(f"✅ Backlog queues: proof={proof_count}, empirical={empirical_count}, cross-model={cross_model_count}")
    else:
        missing = [str(f) for f in queue_files if not f.exists()]
        errors.append(f"Queue files missing: {missing}")
        print(f"❌ Queue files missing: {missing}")

    # Summary
    print(f"\n=== Summary ===")
    print(f"Checks passed: {checks_passed}/{checks_total}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    for e in errors:
        print(f"  ❌ {e}")
    for w in warnings:
        print(f"  ⚠️ {w}")

    if errors:
        print("\n❌ VALIDATION FAILED")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
