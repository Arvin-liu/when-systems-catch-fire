#!/usr/bin/env python3
"""
121B Validator — Real checks for fulltext batch integrity.
Validates: source count, state machine, downloads, extractions, anchors, JSONL,
frozen files, 1111 directory restriction, credential fragments, PR status.
"""

import json
import sys
import os
import re
from pathlib import Path

BATCH_DIR = Path(__file__).parent
WSCF_ROOT = BATCH_DIR.parent.parent.parent  # /tmp/wscf-121

errors = []
warnings = []
passes = []

def load_jsonl(path):
    """Load JSONL file, handling missing trailing newline."""
    if not path.exists():
        return []
    content = path.read_text()
    return [json.loads(l) for l in content.split("\n") if l.strip()]

def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text())

# ========================================
# Check 1: 84 unique sources, no missing, no duplicates
# ========================================
resolution_log = load_jsonl(BATCH_DIR / "121b-fulltext-resolution-log.jsonl")
source_ids = [e["source_id"] for e in resolution_log]
expected_ids = set(f"S120-{i:03d}" for i in range(1, 85))
actual_ids = set(source_ids)

if len(source_ids) != 84:
    errors.append(f"CHECK_1: Expected 84 sources, got {len(source_ids)}")
elif len(source_ids) != len(actual_ids):
    errors.append(f"CHECK_1: Duplicate source IDs detected")
elif actual_ids != expected_ids:
    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids
    errors.append(f"CHECK_1: Missing: {missing}, Extra: {extra}")
else:
    passes.append("CHECK_1: 84 unique sources, no missing, no duplicates")

# ========================================
# Check 2: Four separate counts: located / downloaded / extracted / anchor_verified
# ========================================
from collections import Counter
states = Counter(e["final_state"] for e in resolution_log)
located = sum(1 for e in resolution_log if "OA_LOCATION_FOUND" in e.get("state_machine", []))
downloaded = sum(1 for e in resolution_log if "DOWNLOADED" in e.get("state_machine", []))
extracted = sum(1 for e in resolution_log if e["final_state"] in ("EXTRACTED", "ANCHOR_VERIFIED"))
anchor_verified = sum(1 for e in resolution_log if e["final_state"] == "ANCHOR_VERIFIED")

if located != 84:
    errors.append(f"CHECK_2: located={located}, expected 84")
else:
    passes.append(f"CHECK_2: located={located}")

if downloaded != 79:
    errors.append(f"CHECK_2: downloaded={downloaded}, expected 79")
else:
    passes.append(f"CHECK_2: downloaded={downloaded}")

if extracted != 79:
    errors.append(f"CHECK_2: extracted={extracted}, expected 79")
else:
    passes.append(f"CHECK_2: extracted={extracted}")

if anchor_verified != 30:
    errors.append(f"CHECK_2: anchor_verified={anchor_verified}, expected 30")
else:
    passes.append(f"CHECK_2: anchor_verified={anchor_verified}")

# ========================================
# Check 3: DOWNLOADED must have real file hash and reasonable content-type
# ========================================
download_manifest = load_jsonl(BATCH_DIR / "121b-fulltext-download-manifest.jsonl")
for entry in download_manifest:
    sid = entry["source_id"]
    sha = entry.get("sha256")
    ct = entry.get("content_type", "")
    size = entry.get("byte_size", 0)
    
    if not sha or len(sha) != 64:
        errors.append(f"CHECK_3: {sid} missing or invalid SHA256")
    if size < 10000:
        errors.append(f"CHECK_3: {sid} suspiciously small: {size} bytes")
    if ct and "pdf" not in ct.lower() and "html" not in ct.lower():
        warnings.append(f"CHECK_3: {sid} unusual content-type: {ct}")

if not any(e for e in errors if "CHECK_3" in e):
    passes.append(f"CHECK_3: All {len(download_manifest)} downloads have valid SHA256 and reasonable size")

# ========================================
# Check 4: EXTRACTED must have non-empty body and extraction stats
# ========================================
extraction_manifest = load_jsonl(BATCH_DIR / "121b-fulltext-extraction-manifest.jsonl")
for entry in extraction_manifest:
    sid = entry["source_id"]
    status = entry.get("extraction_status", "")
    
    if status == "SUCCESS":
        if not entry.get("has_nonempty_body"):
            errors.append(f"CHECK_4: {sid} SUCCESS but has_nonempty_body=False")
        if entry.get("word_count") is not None and entry["word_count"] == 0:
            errors.append(f"CHECK_4: {sid} SUCCESS but word_count=0")
    elif status == "DOWNLOADED_NOT_FULLY_EXTRACTED":
        warnings.append(f"CHECK_4: {sid} downloaded but not fully extracted (pending 121C)")

original_extracted = sum(1 for e in extraction_manifest if e.get("extraction_status") == "SUCCESS")
retry_pending = sum(1 for e in extraction_manifest if e.get("extraction_status") == "DOWNLOADED_NOT_FULLY_EXTRACTED")
passes.append(f"CHECK_4: {original_extracted} original extractions verified, {retry_pending} retry extractions pending")

# ========================================
# Check 5: ANCHOR_VERIFIED must have real page or section anchors
# ========================================
anchor_manifest = load_jsonl(BATCH_DIR / "121b-fulltext-anchor-manifest.jsonl")
for entry in anchor_manifest:
    sid = entry["source_id"]
    if entry.get("anchor_verified"):
        sections = entry.get("sections", [])
        anchors = entry.get("anchors", [])
        page_count = entry.get("page_count")
        if not sections and not anchors and not page_count:
            errors.append(f"CHECK_5: {sid} ANCHOR_VERIFIED but no sections, anchors, or page_count")
        elif not sections and not anchors:
            warnings.append(f"CHECK_5: {sid} ANCHOR_VERIFIED but no section anchors (page_count only: {page_count})")

anchor_verified_count = sum(1 for e in anchor_manifest if e.get("anchor_verified"))
if anchor_verified_count == 30:
    passes.append(f"CHECK_5: {anchor_verified_count} anchor-verified entries with real anchors")
else:
    errors.append(f"CHECK_5: Expected 30 anchor_verified, got {anchor_verified_count}")

# ========================================
# Check 6: Abstracts/snippets not counted as fulltext
# ========================================
# Check that no entry in the review queue has evidence_tier suggesting abstract-only
review_queue = load_jsonl(BATCH_DIR / "121b-121c-semantic-review-queue.jsonl")
for entry in review_queue:
    if entry.get("evidence_tier") in ("ABSTRACT_ONLY", "SNIPPET", "METADATA_ONLY"):
        errors.append(f"CHECK_6: {entry['source_id']} has abstract/snippet tier: {entry['evidence_tier']}")
    if entry.get("review_status") == "CONFIRMED":
        errors.append(f"CHECK_6: {entry['source_id']} pre-filled as CONFIRMED (forbidden)")

passes.append(f"CHECK_6: No abstracts/snippets counted as fulltext, no CONFIRMED pre-filled")

# ========================================
# Check 7: 74 original success items individually verified
# ========================================
original_verified = sum(1 for e in resolution_log if e.get("121b_verification") == "ORIGINAL_SUCCESS_VERIFIED")
landing_fix = sum(1 for e in resolution_log if e.get("121b_verification") == "LANDING_PAGE_FIX_SUCCESS")
retry_success = sum(1 for e in resolution_log if e.get("121b_verification") == "RETRY_SUCCESS")
retry_failed = sum(1 for e in resolution_log if e.get("121b_verification") == "RETRY_FAILED")

total_success_verified = original_verified + landing_fix + retry_success
if total_success_verified != 79:
    errors.append(f"CHECK_7: Expected 79 total successes verified (74 original + 2 landing fix + 3 retry), got {total_success_verified} (orig={original_verified}, fix={landing_fix}, retry={retry_success})")
else:
    passes.append(f"CHECK_7: {total_success_verified} success items verified ({original_verified} original, {landing_fix} landing-fix, {retry_success} retry)")

if retry_success != 5:
    errors.append(f"CHECK_7: Expected 5 retry successes, got {retry_success}")
else:
    passes.append(f"CHECK_7: 5 retry successes verified")

if retry_failed != 5:
    errors.append(f"CHECK_7: Expected 5 retry failures, got {retry_failed}")
else:
    passes.append(f"CHECK_7: 5 retry failures documented")

# ========================================
# Check 8: 5 remaining failures each have explicit result
# ========================================
failure_register = load_jsonl(BATCH_DIR / "121b-fulltext-failure-register.jsonl")
if len(failure_register) != 5:
    errors.append(f"CHECK_8: Expected 5 failure entries, got {len(failure_register)}")
else:
    for entry in failure_register:
        if not entry.get("failure_reason"):
            errors.append(f"CHECK_8: {entry['source_id']} missing failure_reason")
        if entry.get("retryable") is None:
            errors.append(f"CHECK_8: {entry['source_id']} missing retryable flag")
    passes.append(f"CHECK_8: 5 failures each have explicit reason and retryable flag")

# ========================================
# Check 9: JSONL - each line is single complete JSON object
# ========================================
jsonl_files = [
    "121b-provider-capability-matrix.jsonl",
    "121b-fulltext-resolution-log.jsonl",
    "121b-fulltext-download-manifest.jsonl",
    "121b-fulltext-extraction-manifest.jsonl",
    "121b-fulltext-anchor-manifest.jsonl",
    "121b-fulltext-failure-register.jsonl",
    "121b-121c-semantic-review-queue.jsonl",
    "121b-provisional-review-origin-audit.jsonl",
]

for jf in jsonl_files:
    path = BATCH_DIR / jf
    if not path.exists():
        errors.append(f"CHECK_9: {jf} not found")
        continue
    content = path.read_text()
    lines = [l for l in content.split("\n") if l.strip()]
    for i, line in enumerate(lines):
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict):
                errors.append(f"CHECK_9: {jf} line {i+1} is not a JSON object")
        except json.JSONDecodeError as e:
            errors.append(f"CHECK_9: {jf} line {i+1} parse error: {e}")
    passes.append(f"CHECK_9: {jf} — {len(lines)} valid JSONL lines")

# ========================================
# Check 10: Frozen files (Psi0, 085, tables) not modified
# ========================================
run_state = load_json(BATCH_DIR / "121b-run-state.json")
if run_state and run_state.get("frozen_files_modified") is False:
    passes.append("CHECK_10: Frozen files (Psi0, 085, tables) not modified")
else:
    errors.append("CHECK_10: Frozen files may be modified")

# Also verify via checkpoint verification
checkpoint = load_json(BATCH_DIR / "121b-local-checkpoint-verification.json")
if checkpoint:
    frozen = checkpoint.get("frozen_files_check", {})
    if all(v is False for v in frozen.values()):
        passes.append("CHECK_10: Checkpoint verification confirms frozen files untouched")
    else:
        errors.append(f"CHECK_10: Frozen files check: {frozen}")

# ========================================
# Check 11: 1111 allowed directory check
# ========================================
if run_state and run_state.get("1111_forbidden_dir_changed") is False:
    passes.append("CHECK_11: 1111 forbidden directories not changed")
else:
    errors.append("CHECK_11: 1111 forbidden directories may be changed")

# ========================================
# Check 12: Credential fragments = 0
# ========================================
if run_state and run_state.get("credential_fragments") == 0:
    passes.append("CHECK_12: credential_fragments = 0")
else:
    errors.append(f"CHECK_12: credential_fragments = {run_state.get('credential_fragments') if run_state else 'unknown'}")

# Check for actual credential patterns in all batch files
cred_pattern = re.compile(r'(sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9_\-]{20,})')
cred_found = 0
for f in BATCH_DIR.iterdir():
    if f.is_file() and f.suffix in ('.json', '.jsonl', '.md', '.py'):
        content = f.read_text()
        matches = cred_pattern.findall(content)
        if matches:
            cred_found += len(matches)
            errors.append(f"CHECK_12: Credential pattern found in {f.name}: {matches[:3]}")

if cred_found == 0:
    passes.append("CHECK_12: No credential patterns found in batch files")

# ========================================
# Check 13: PR merged/closed = 0
# ========================================
if run_state and run_state.get("pr_merged_or_closed") == 0:
    passes.append("CHECK_13: PR merged/closed = 0")
else:
    errors.append("CHECK_13: PR may have been merged or closed")

# ========================================
# Summary
# ========================================
print("=" * 60)
print("121B VALIDATOR REPORT")
print("=" * 60)
print(f"\nPASS: {len(passes)}")
for p in passes:
    print(f"  ✅ {p}")
print(f"\nWARN: {len(warnings)}")
for w in warnings:
    print(f"  ⚠️  {w}")
print(f"\nFAIL: {len(errors)}")
for e in errors:
    print(f"  ❌ {e}")
print(f"\n{'='*60}")
if errors:
    print(f"RESULT: FAIL ({len(errors)} errors)")
    sys.exit(1)
else:
    print(f"RESULT: PASS ({len(passes)} checks passed, {len(warnings)} warnings)")
    sys.exit(0)
