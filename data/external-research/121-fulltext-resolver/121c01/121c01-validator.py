#!/usr/bin/env python3
"""121C01 Validator — verifies all 121C01 outputs."""

import json
import os
import sys

BASE = "data/external-research/121-fulltext-resolver/121c01"
checks = []
errors = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    checks.append((status, name, detail))
    if not condition:
        errors.append(f"{name}: {detail}")

def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)

# CHECK 1: Status axis reconciliation exists and has correct structure
sa = load_json(f"{BASE}/121c01-status-axis-reconciliation.json")
check("status-axis-reconciliation exists", bool(sa))
recon = sa.get("reconciliation", sa)
check("status-axis has content_access_counts", "content_access_counts" in recon)
check("status-axis has semantic_review_counts", "semantic_review_counts" in recon)
check("content_access total = 84", recon.get("content_access_counts", {}).get("LOCATED", 0) == 84)
check("downloaded = 79", recon.get("content_access_counts", {}).get("DOWNLOADED", 0) == 79)
check("extracted_full = 72", recon.get("content_access_counts", {}).get("EXTRACTED_FULL", 0) == 72)
check("extracted_partial = 7", recon.get("content_access_counts", {}).get("EXTRACTED_PARTIAL", 0) == 7)
check("anchor_verified = 30", recon.get("content_access_counts", {}).get("ANCHOR_VERIFIED", 0) == 30)
check("failed = 5", recon.get("content_access_counts", {}).get("FAILED_LEGAL_OA_NOT_FOUND", 0) == 5)
check("not_reviewed = 49", recon.get("semantic_review_counts", {}).get("NOT_REVIEWED", 0) == 49)
check("provisional = 30", recon.get("semantic_review_counts", {}).get("PROVISIONAL_NON_MAX_REVIEW", 0) == 30)

# CHECK 2: Validator warning reconciliation
warnings = load_jsonl(f"{BASE}/121c01-validator-warning-reconciliation.jsonl")
check(f"warning reconciliation has 7 entries", len(warnings) == 7)
warning_ids = [w["source_id"] for w in warnings]
expected_warning_ids = ["S120-024", "S120-032", "S120-013", "S120-023", "S120-033", "S120-056", "S120-080"]
check("warning IDs match expected", set(warning_ids) == set(expected_warning_ids))

# CHECK 3: Selected sources
selected = load_jsonl(f"{BASE}/121c01-selected-sources.jsonl")
check(f"selected sources = 10", len(selected) == 10)
selected_ids = [s["source_id"] for s in selected]
check("no duplicate source IDs", len(selected_ids) == len(set(selected_ids)))
check("S120-051 not selected", "S120-051" not in selected_ids)
check("S120-057 not selected", "S120-057" not in selected_ids)

# CHECK 4: Evidence cards
cards = load_jsonl(f"{BASE}/121c01-max-semantic-evidence-cards.jsonl")
check(f"evidence cards = 10", len(cards) == 10)
card_ids = [c["source_id"] for c in cards]
check("card IDs match selected IDs", set(card_ids) == set(selected_ids))

for c in cards:
    sid = c["source_id"]
    check(f"{sid} has sha256", bool(c.get("sha256")))
    check(f"{sid} has sections_reviewed", len(c.get("sections_reviewed", [])) >= 3)
    check(f"{sid} has page_or_section_anchors", len(c.get("page_or_section_anchors", [])) >= 3)
    check(f"{sid} has paper_core_claims", len(c.get("paper_core_claims", [])) >= 2)
    check(f"{sid} has claim_support_status", c.get("claim_support_status") in ["CONFIRMED", "PARTIAL", "NOT_SUPPORTED", "UNRESOLVED"])
    check(f"{sid} reviewer = GLM-5.2", c.get("reviewer_model") == "qclaw/pool-glm-5.2")
    check(f"{sid} reasoning = high", c.get("reviewer_reasoning_level") == "high")
    check(f"{sid} has supersedes_provisional_card_id", bool(c.get("supersedes_provisional_card_id")))
    check(f"{sid} has what_the_paper_does_not_support", len(c.get("what_the_paper_does_not_support", [])) >= 2)
    check(f"{sid} has function_os_node_impacts", bool(c.get("function_os_node_impacts")))
    check(f"{sid} has ignition_gap_impacts", bool(c.get("ignition_gap_impacts")))

# CHECK 5: Individual evidence card files exist
for sid in selected_ids:
    path = f"{BASE}/evidence-cards-max/{sid}.json"
    check(f"individual card file {sid}.json exists", os.path.exists(path))

# CHECK 6: Provisional vs Max comparison
comparisons = load_jsonl(f"{BASE}/121c01-provisional-vs-max-comparison.jsonl")
check(f"comparison entries = 10", len(comparisons) == 10)
for comp in comparisons:
    check(f"comparison {comp['source_id']} has valid comparison type",
          comp["comparison"] in ["AGREES", "NARROWS", "CORRECTS", "REJECTS", "NOT_COMPARABLE"])

# CHECK 7: GAP evidence increment
gaps = load_jsonl(f"{BASE}/121c01-gap-015-020-evidence-increment.jsonl")
check(f"GAP entries = 6", len(gaps) == 6)
for g in gaps:
    check(f"GAP {g['gap_id']} has valid status",
          g["status"] in ["EVIDENCE_ACCUMULATING", "POSSIBLE_FIELD_ENHANCEMENT",
                          "POSSIBLE_ARCHITECTURE_CANDIDATE", "POSSIBLE_DUPLICATE_OR_SUBSET",
                          "INSUFFICIENT_EVIDENCE"])

# CHECK 8: Function OS node evidence
nodes = load_jsonl(f"{BASE}/121c01-function-os-node-evidence-increment.jsonl")
check(f"Function OS nodes = 9", len(nodes) == 9)
for n in nodes:
    check(f"node {n['node_id']} has valid status",
          n["status"] in ["NO_EVIDENCE", "WEAK_EVIDENCE", "MULTI_SOURCE_EVIDENCE",
                          "INTERNAL_USE_CASE_PRESENT", "READY_FOR_LATER_ARCHITECTURE_REVIEW"])

# CHECK 9: Batch manifest
batches = load_jsonl(f"{BASE}/121c02-121c08-batch-manifest.jsonl")
check(f"batch manifest entries = 7", len(batches) == 7)
total_remaining = sum(len(b["source_ids"]) for b in batches)
check(f"total remaining sources = 69", total_remaining == 69)

# CHECK 10: Run state
rs = load_json(f"{BASE}/121c01-run-state.json")
check("run-state exists", bool(rs))
check("run-state status", rs.get("status") == "121C01_MAX_SEMANTIC_BATCH_COMPLETE_EVIDENCE_ACCUMULATING")
check("run-state model", rs.get("reviewer_model") == "qclaw/pool-glm-5.2")
check("run-state reasoning", rs.get("reviewer_reasoning_level") == "high")
check("run-state no model switch", rs.get("model_switch") == False)
check("run-state no fallback", rs.get("fallback") == False)
check("run-state credential_fragments = 0", rs.get("credential_fragments") == 0)
check("run-state pr_merged = 0", rs.get("pr_merged_or_closed") == 0)
check("run-state frozen not modified", rs.get("frozen_files_modified") == False)

# CHECK 11: No template repetition — check that paper_core_claims are unique
all_claims = []
for c in cards:
    for claim in c.get("paper_core_claims", []):
        all_claims.append(claim)
check("no duplicate claims across cards", len(all_claims) == len(set(all_claims)))

# CHECK 12: CONFIRMED cards have section anchors
for c in cards:
    if c["claim_support_status"] == "CONFIRMED":
        check(f"{c['source_id']} CONFIRMED has >= 3 anchors",
              len(c.get("page_or_section_anchors", [])) >= 3)

# CHECK 13: Frozen files not modified (check via git)
import subprocess
result = subprocess.run(["git", "diff", "--name-only", "66c6efdf673dc486fbf10373edbcf2eab67a528c"],
                       capture_output=True, text=True, cwd="/tmp/wscf-121")
changed_files = [f for f in result.stdout.strip().split("\n") if f]
frozen_patterns = ["docs/ignition/", "data/functions/", "data/cases/", "Psi0", "085"]
for cf in changed_files:
    for fp in frozen_patterns:
        if fp in cf:
            errors.append(f"FROZEN FILE MODIFIED: {cf}")
            check(f"frozen file {cf} not modified", False)
            break

# CHECK 14: No credential fragments
import re
cred_patterns = [
    r'sk-[a-zA-Z0-9]{20}',
    r'AKIA[A-Z0-9]{16}',
    r'ghp_[a-zA-Z0-9]{36}',
]
all_files = []
for root, dirs, files in os.walk(BASE):
    for fn in files:
        if fn.endswith('.py'):
            continue  # skip python files (the validator itself)
        all_files.append(os.path.join(root, fn))
cred_found = 0
for fp in all_files:
    try:
        with open(fp) as f:
            content = f.read()
        for pat in cred_patterns:
            if re.search(pat, content):
                cred_found += 1
                errors.append(f"CREDENTIAL FRAGMENT in {fp}: pattern {pat}")
    except:
        pass
check("no credential fragments", cred_found == 0)

# CHECK 15: No PDF files in git
pdf_files = [f for f in changed_files if f.endswith('.pdf')]
check("no PDF files in git diff", len(pdf_files) == 0)

# Print report
print("=" * 60)
print("121C01 VALIDATOR REPORT")
print("=" * 60)
print()

pass_count = sum(1 for s, _, _ in checks if s == "PASS")
fail_count = sum(1 for s, _, _ in checks if s == "FAIL")
print(f"PASS: {pass_count}")
print(f"FAIL: {fail_count}")
print()

if errors:
    print("ERRORS:")
    for e in errors:
        print(f"  ❌ {e}")
    print()

print("=" * 60)
result = "PASS" if fail_count == 0 else "FAIL"
print(f"RESULT: {result} ({pass_count} checks passed, {fail_count} failed)")
sys.exit(0 if fail_count == 0 else 1)
