#!/usr/bin/env python3
"""
084 Max Adjudication Validator
Validates 084 max adjudication decisions against schema and integrity rules.
"""
import json
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

VALID_MAIN_STATUSES = {
    "RETAIN_SCOPED_DEFINITION",
    "RETAIN_INTERNAL_ALGORITHM_OR_RULE",
    "RETAIN_PROVISIONAL_MODEL",
    "RETAIN_FORMAL_PROPOSITION_UNPROVED",
    "RETAIN_EXTERNAL_THEOREM_REFERENCE",
    "PROVED_ORIGINAL_CLAIM_WITH_ARTIFACT",
    "REFUTED_ORIGINAL_CLAIM_WITH_COUNTEREXAMPLE",
    "DOWNGRADE_TO_STRUCTURAL_ANALOGY",
    "DOWNGRADE_TO_EMPIRICAL_ASSOCIATION",
    "DOWNGRADE_TO_MECHANISM_HYPOTHESIS",
    "DOWNGRADE_TO_NATURAL_LANGUAGE_CANDIDATE",
    "REJECT_FALSE_OR_INCOHERENT",
    "DEFER_MISSING_SOURCE_OR_DOMAIN_EXPERT",
}

REQUIRED_STATUS_AXES = [
    "semantic_status", "logic_status", "formal_status",
    "proof_status", "evidence_status", "scope_status", "provenance_status"
]

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

def validate_decisions(decisions_path, queue_path, manifest_path, schema_path):
    errors = []
    warnings = []

    decisions = load_jsonl(decisions_path)
    queue = load_jsonl(queue_path)
    manifest = load_json(manifest_path)
    schema = load_json(schema_path)

    # 1. Count check
    if len(decisions) != 353:
        errors.append(f"Decision count {len(decisions)} != 353")

    # 2. ID set consistency
    decision_ids = {d["stable_id"] for d in decisions}
    queue_ids = {q["stable_id"] for q in queue}
    if decision_ids != queue_ids:
        only_dec = decision_ids - queue_ids
        only_q = queue_ids - decision_ids
        if only_dec:
            errors.append(f"IDs only in decisions: {sorted(only_dec)[:10]}")
        if only_q:
            errors.append(f"IDs only in queue: {sorted(only_q)[:10]}")

    # 3. Uniqueness
    seen = set()
    for d in decisions:
        sid = d["stable_id"]
        if sid in seen:
            errors.append(f"Duplicate stable_id: {sid}")
        seen.add(sid)

    # 4. Required fields
    required_fields = schema.get("required", [])
    for d in decisions:
        missing = [f for f in required_fields if f not in d or d[f] is None or d[f] == ""]
        if missing:
            errors.append(f"{d.get('stable_id','?')}: missing fields: {missing}")

    # 5. Main status validity
    for d in decisions:
        for field in ["primary_verdict", "reconciled_decision"]:
            val = d.get(field, "")
            if val and val not in VALID_MAIN_STATUSES:
                errors.append(f"{d['stable_id']}: invalid {field} '{val}'")

    # 6. Status axes presence
    for d in decisions:
        for axis in REQUIRED_STATUS_AXES:
            if axis not in d or not d[axis]:
                errors.append(f"{d['stable_id']}: missing {axis}")

    # 7. Source-specific rationale min 2 items
    for d in decisions:
        rationale = d.get("source_specific_rationale", [])
        if len(rationale) < 2:
            errors.append(f"{d['stable_id']}: source_specific_rationale has <2 items")

    # 8. Batch coverage
    if manifest:
        for batch in manifest["batches"]:
            batch_ids = set(batch["stable_ids"])
            dec_in_batch = {d["stable_id"] for d in decisions if d.get("batch_id") == batch["batch_id"]}
            if dec_in_batch != batch_ids:
                missing_in_batch = batch_ids - dec_in_batch
                extra_in_batch = dec_in_batch - batch_ids
                if missing_in_batch:
                    errors.append(f"{batch['batch_id']}: missing {len(missing_in_batch)} IDs")
                if extra_in_batch:
                    errors.append(f"{batch['batch_id']}: extra {len(extra_in_batch)} IDs")

    # 9. Template repetition check (simple: count identical forbidden_wording)
    forbidden_counts = {}
    for d in decisions:
        fw = tuple(sorted(d.get("forbidden_wording", [])))
        if fw:
            forbidden_counts[fw] = forbidden_counts.get(fw, 0) + 1
    for fw, count in forbidden_counts.items():
        if count > 15:
            warnings.append(f"forbidden_wording template used {count} times: {fw[:3]}")

    # 10. Primary-adversarial consistency field
    for d in decisions:
        if "primary_adversarial_consistent" not in d:
            errors.append(f"{d['stable_id']}: missing primary_adversarial_consistent")

    return errors, warnings, len(decisions)

def validate_self_review(self_review_path, decisions_path):
    errors = []
    sr = load_jsonl(self_review_path)
    dec = load_jsonl(decisions_path)
    sr_ids = {r["stable_id"] for r in sr}
    dec_ids = {d["stable_id"] for d in dec}
    if sr_ids != dec_ids:
        errors.append(f"Self-review ID mismatch: {len(sr_ids)} vs {len(dec_ids)}")
    return errors, len(sr)

def main():
    base = REPO_ROOT / "data" / "foundation"

    decisions_path = base / "adjudications" / "084-max-decisions.jsonl"
    queue_path = base / "escalations" / "083-max-adjudication-queue.jsonl"
    manifest_path = base / "escalations" / "083-max-queue-manifest.json"
    schema_path = REPO_ROOT / "schemas" / "foundation" / "max-adjudication-decision.schema.json"
    self_review_path = base / "adjudications" / "084-max-self-review.jsonl"

    print("=== 084 Max Adjudication Validator ===")
    all_errors = []
    all_warnings = []

    if not decisions_path.exists():
        print("❌ 084-max-decisions.jsonl not found")
        sys.exit(1)

    errors, warnings, dec_count = validate_decisions(
        str(decisions_path), str(queue_path), str(manifest_path), str(schema_path))
    all_errors.extend(errors)
    all_warnings.extend(warnings)

    print(f"Decisions: {dec_count}/353")

    if self_review_path.exists():
        sr_errors, sr_count = validate_self_review(str(self_review_path), str(decisions_path))
        all_errors.extend(sr_errors)
        print(f"Self-review: {sr_count}/353")
    else:
        print("Self-review: not found")

    # Proof obligations
    proof_path = base / "proofs" / "084-proof-obligations.jsonl"
    if proof_path.exists():
        proof_count = sum(1 for l in open(proof_path) if l.strip())
        print(f"Proof obligations: {proof_count}")
    else:
        print("Proof obligations: not found")

    # Evidence obligations
    evidence_path = base / "evidence" / "084-empirical-obligations.jsonl"
    if evidence_path.exists():
        ev_count = sum(1 for l in open(evidence_path) if l.strip())
        print(f"Evidence obligations: {ev_count}")
    else:
        print("Evidence obligations: not found")

    print(f"\nErrors: {len(all_errors)}")
    for e in all_errors[:20]:
        print(f"  ❌ {e}")
    if len(all_errors) > 20:
        print(f"  ... and {len(all_errors)-20} more")

    print(f"\nWarnings: {len(all_warnings)}")
    for w in all_warnings[:10]:
        print(f"  ⚠️ {w}")
    if len(all_warnings) > 10:
        print(f"  ... and {len(all_warnings)-10} more")

    if all_errors:
        print("\n❌ VALIDATION FAILED")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
