#!/usr/bin/env python3
"""
083 Validator: verify 082 audit assets, quality windows, correction queue,
escalation routing, max queue, and status integrity.
"""
import json
import sys
from pathlib import Path

FIRE_ROOT = Path("/Users/zhiyuan/Agent 工作区/when-systems-catch-fire-083")

def load_jsonl(path):
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

errors = []
warnings = []

def check(condition, msg, is_error=True):
    if not condition:
        if is_error:
            errors.append(msg)
        else:
            warnings.append(msg)
        print(f"  {'❌ ERROR' if is_error else '⚠️  WARN'}: {msg}")
    else:
        print(f"  ✅ {msg}")

print("=== 083 Validator ===\n")

# 1. 082 audit files exist
print("1. 082 audit files:")
audit_files = [
    "data/foundation/audits/082-structure-audit.json",
    "data/foundation/audits/082-template-clusters.jsonl",
    "data/foundation/audits/082-sample-manifest.jsonl",
    "data/foundation/audits/082-sample-adjudications.jsonl",
    "data/foundation/work-queues/082-correction-queue.jsonl",
    "data/foundation/work-queues/082-escalation-routing.jsonl",
]
for f in audit_files:
    check((FIRE_ROOT / f).exists(), f"{f} exists")

# 2. Quality windows
print("\n2. Quality windows:")
quality = load_jsonl(FIRE_ROOT / "data/foundation/adjudications/080-quality-audits.jsonl")
check(len(quality) == 6, f"Exactly 6 windows (got {len(quality)})")
for w in quality:
    check(w['record_count'] > 0, f"{w['window_id']} non-empty ({w['record_count']} records)")
    check(len(w.get('semantic_sample', [])) >= 10, f"{w['window_id']} has >= 10 samples")
check(sum(w['record_count'] for w in quality) == 617, f"Total records = 617 (got {sum(w['record_count'] for w in quality)})")

# 3. Correction queue
print("\n3. Correction queue:")
corr = load_jsonl(FIRE_ROOT / "data/foundation/work-queues/082-correction-queue.jsonl")
check(len(corr) > 0, f"Correction queue non-empty ({len(corr)} records)")

# 4. Escalation routing
print("\n4. Escalation routing:")
routing = load_jsonl(FIRE_ROOT / "data/foundation/work-queues/082-escalation-routing.jsonl")
check(len(routing) == 506, f"Routing total = 506 (got {len(routing)})")
routing_counts = {}
for r in routing:
    rt = r['routing']
    routing_counts[rt] = routing_counts.get(rt, 0) + 1
check(set(routing_counts.keys()) <= {'MAX_REQUIRED', 'GLM_HIGH_CAN_RESOLVE', 'NO_ESCALATION_NEEDED'}, 
      f"Routing categories valid: {routing_counts}")
check(sum(routing_counts.values()) == 506, f"Routing sum = 506")

# 5. Adjudications ID/anchor check
print("\n5. Adjudications integrity:")
adjs = load_jsonl(FIRE_ROOT / "data/foundation/adjudications/080-source-text-adjudications.jsonl")
ids = [a.get('stable_id') for a in adjs]
check(len(ids) == len(set(ids)), f"stable_id unique ({len(ids)} total, {len(set(ids))} unique)")
check(all(a.get('source_files_read') for a in adjs), "All have source_files_read")

# 6. Legacy tables unchanged (compare 083 HEAD against 081 head, not main)
print("\n6. Legacy tables:")
import subprocess
# Compare against 081 head (base of 083 branch), not main
result = subprocess.run(['git', 'diff', '--name-only', 'f0862cc0a827a94e930b78a269c8fdc8a5c5c019', 'HEAD'], 
                       capture_output=True, text=True, cwd=str(FIRE_ROOT))
changed = result.stdout.strip().split('\n') if result.stdout.strip() else []
# Only check actual legacy table files (the two DOCX tables), not legacy mappings/migrations
legacy_table_patterns = ['统一函数总表', '统一案例总表', '统一函数总表.docx', '统一案例总表.docx']
legacy_changed = [f for f in changed if any(p in f for p in legacy_table_patterns)]
check(len(legacy_changed) == 0, f"Legacy two tables unchanged (changed: {legacy_changed})")
print(f"  (083 changes vs 081 head: {len(changed)} files)")

# 7. Max queue if exists
max_queue_path = FIRE_ROOT / "data/foundation/escalations/083-max-adjudication-queue.jsonl"
if max_queue_path.exists():
    print("\n7. Max queue:")
    max_q = load_jsonl(max_queue_path)
    check(len(max_q) > 0, f"Max queue non-empty ({len(max_q)} records)")
    required_fields = ['stable_id', 'legacy_path', 'controlled_proposition', 'strong_assertion_type',
                      'precise_dispute', 'current_formalization', 'known_evidence', 
                      'hidden_premises', 'closed_questions', 'verdict_options', 
                      'landing_modifications', 'dependencies', 'risk_level']
    for item in max_q:
        for rf in required_fields:
            check(rf in item, f"Max queue item {item.get('stable_id', '?')} has field '{rf}'", is_error=False)

# 8. Status axis check
print("\n8. Status axis:")
review_queue = load_jsonl(FIRE_ROOT / "data/foundation/work-queues/080-semantic-review-queue.jsonl")
bad_statuses = [r for r in review_queue if r.get('status') == 'COMPLETED_ACCEPTED']
check(len(bad_statuses) == 0, f"No 'COMPLETED_ACCEPTED' remaining ({len(bad_statuses)} found)")

# Summary
print(f"\n=== Summary ===")
print(f"Errors: {len(errors)}")
print(f"Warnings: {len(warnings)}")
if errors:
    print("\n❌ VALIDATION FAILED")
    sys.exit(1)
else:
    print("\n✅ VALIDATION PASSED")
    sys.exit(0)
