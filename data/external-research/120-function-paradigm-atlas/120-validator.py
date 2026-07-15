#!/usr/bin/env python3
"""120-validator.py — Validates all IGNITION-120 output files against thresholds.

Exit code 0 = all pass, non-zero = failure.
"""

import json
import os
import sys

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")

OUTPUT_DIR = "data/external-research/120-function-paradigm-atlas"
REPORT_DIR = "reports/external-research"

errors = []
warnings = []

def load_jsonl(path):
    """Load JSONL file, return list of dicts."""
    records = []
    full_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(full_path):
        errors.append(f"MISSING FILE: {path}")
        return records
    with open(full_path) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                errors.append(f"JSON PARSE ERROR in {path} line {i}: {e}")
    return records

def load_json(path):
    """Load JSON file."""
    full_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(full_path):
        errors.append(f"MISSING FILE: {path}")
        return None
    with open(full_path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"JSON PARSE ERROR in {path}: {e}")
            return None

def check_file_exists(path):
    """Check that a file exists."""
    full_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(full_path):
        errors.append(f"MISSING FILE: {path}")
        return False
    return True

def check_no_api_key_leak(path):
    """Check that no API keys are present in file."""
    full_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(full_path):
        return
    with open(full_path) as f:
        content = f.read()
    # Check for common API key patterns
    import re
    patterns = [
        r'as_sk_[a-zA-Z0-9]{10,}',  # anysearch API key
        r'sk-[a-zA-Z0-9]{20,}',     # OpenAI-style key
        r'ghp_[a-zA-Z0-9]{20,}',    # GitHub PAT
        r'Bearer\s+[a-zA-Z0-9_\-]{20,}',  # Bearer tokens
    ]
    for pattern in patterns:
        matches = re.findall(pattern, content)
        if matches:
            errors.append(f"API KEY LEAK in {path}: found pattern {pattern}")

# ============================================================
# VALIDATION CHECKS
# ============================================================

print("=" * 60)
print("IGNITION-120 Validator")
print("=" * 60)

# 1. Check all required output files exist
print("\n[1] Checking required output files...")
required_files = [
    f"{OUTPUT_DIR}/120-baseline-manifest.json",
    f"{OUTPUT_DIR}/120-provider-and-tool-audit.md",
    f"{OUTPUT_DIR}/120-function-source-registry.jsonl",
    f"{OUTPUT_DIR}/120-function-paradigm-cards.jsonl",
    f"{OUTPUT_DIR}/120-source-family-coverage.json",
    f"{OUTPUT_DIR}/120-fulltext-evidence-cards.jsonl",
    f"{OUTPUT_DIR}/120-internal-function-asset-inventory.jsonl",
    f"{OUTPUT_DIR}/120-existing-gap-overlap-matrix.jsonl",
    f"{OUTPUT_DIR}/120-gap-015-020-adjudications.jsonl",
    f"{OUTPUT_DIR}/120-function-os-candidate-overlay.json",
    f"{OUTPUT_DIR}/120-function-equivalence-state-axis.json",
    f"{OUTPUT_DIR}/120-forbidden-wording.jsonl",
    f"{OUTPUT_DIR}/120-followup-queue-121-126.jsonl",
    f"{OUTPUT_DIR}/120-run-state.json",
    f"{OUTPUT_DIR}/120-validator.py",
    f"{REPORT_DIR}/120-function-paradigm-atlas-report.md",
    f"{REPORT_DIR}/120-function-os-architecture-candidate-report.md",
    f"{REPORT_DIR}/120-source-quality-and-template-risk-audit.md",
]

for f_path in required_files:
    check_file_exists(f_path)
    
# Need to create the provider audit and reports first
print(f"  Required files: {len(required_files)}, errors so far: {len(errors)}")

# 2. Check source registry
print("\n[2] Checking source registry...")
sources = load_jsonl(f"{OUTPUT_DIR}/120-function-source-registry.jsonl")
if len(sources) < 80:
    errors.append(f"SOURCE COUNT: expected ≥80, got {len(sources)}")
else:
    print(f"  ✓ {len(sources)} sources (≥80 required)")

# Check unique IDs
source_ids = [s.get("source_id") for s in sources]
if len(source_ids) != len(set(source_ids)):
    errors.append("DUPLICATE source_id found in registry")
else:
    print(f"  ✓ All {len(source_ids)} source IDs are unique")

# 3. Check source family coverage
print("\n[3] Checking source family coverage...")
coverage = load_json(f"{OUTPUT_DIR}/120-source-family-coverage.json")
if coverage:
    for fam_key in sorted(coverage.keys()):
        fam_data = coverage[fam_key]
        if fam_data["count"] < 5:
            errors.append(f"Family {fam_key} has only {fam_data['count']} sources (≥5 required)")
        else:
            print(f"  ✓ {fam_key} ({fam_data['name']}): {fam_data['count']} sources")

# 4. Check paradigm cards
print("\n[4] Checking paradigm cards...")
cards = load_jsonl(f"{OUTPUT_DIR}/120-function-paradigm-cards.jsonl")
if len(cards) != len(sources):
    errors.append(f"PARADIGM CARD COUNT: expected {len(sources)}, got {len(cards)}")
else:
    print(f"  ✓ {len(cards)} paradigm cards match source count")

# Check required fields
required_card_fields = [
    "source_id", "title", "evidence_tier", "function_definition",
    "function_order", "input_domain", "output_domain", "carrier_type",
    "specification_language", "compiler_or_generator", "interpreter_or_runtime",
    "state_and_side_effects", "uncertainty_model", "composition_rule",
    "equivalence_criterion", "validation_regime", "execution_trace",
    "failure_boundary", "version_and_provenance",
    "what_the_paper_supports", "what_the_paper_does_not_support",
    "ignition_projection", "architectural_gap_exposed",
    "overlap_with_existing_gap_001_014", "claim_support_status"
]
for card in cards:
    for field in required_card_fields:
        if field not in card:
            errors.append(f"MISSING FIELD '{field}' in paradigm card {card.get('source_id', 'UNKNOWN')}")
            break

# 5. Check evidence tiers
print("\n[5] Checking evidence tier distribution...")
tier_counts = {}
for card in cards:
    t = card.get("evidence_tier", "MISSING")
    tier_counts[t] = tier_counts.get(t, 0) + 1
print(f"  Tier distribution: {tier_counts}")

# Check no tier exceeds allowed
if "CLAIM_SUPPORT_CONFIRMED" in tier_counts:
    errors.append(f"CLAIM_SUPPORT_CONFIRMED should be 0 (no fulltext read), got {tier_counts['CLAIM_SUPPORT_CONFIRMED']}")

# 6. Check internal asset inventory
print("\n[6] Checking internal function asset inventory...")
assets = load_jsonl(f"{OUTPUT_DIR}/120-internal-function-asset-inventory.jsonl")
if len(assets) < 30:
    errors.append(f"INTERNAL ASSETS: expected ≥30, got {len(assets)}")
else:
    print(f"  ✓ {len(assets)} internal assets (≥30 required)")

# 7. Check gap adjudications
print("\n[7] Checking GAP-015 to GAP-020 adjudications...")
gaps = load_jsonl(f"{OUTPUT_DIR}/120-gap-015-020-adjudications.jsonl")
if len(gaps) < 6:
    errors.append(f"GAP ADJUDICATIONS: expected ≥6, got {len(gaps)}")
else:
    print(f"  ✓ {len(gaps)} gap adjudications")

# Check each gap has required fields
for gap in gaps:
    gap_id = gap.get("gap_id", "UNKNOWN")
    if gap.get("source_count_fulltext_reviewed", 0) > 0:
        errors.append(f"{gap_id} claims FULLTEXT_REVIEWED but none were performed")
    if gap.get("adjudication") not in [
        "GAP_PROMOTED", "FIELD_ENHANCEMENT_ONLY", "DOCUMENTATION_ONLY",
        "RESEARCH_CANDIDATE_INSUFFICIENT_EVIDENCE", "OVERLAPS_EXISTING_GAP", "REJECTED"
    ]:
        errors.append(f"{gap_id} has invalid adjudication: {gap.get('adjudication')}")
    print(f"  {gap_id}: {gap.get('adjudication', 'UNKNOWN')}")

# 8. Check Function OS candidate
print("\n[8] Checking Function OS candidate overlay...")
fos = load_json(f"{OUTPUT_DIR}/120-function-os-candidate-overlay.json")
if fos:
    required_nodes = [
        "1_FunctionSpec", "2_Representation", "3_Compiler", "4_Artifact",
        "5_Interpreter", "6_ExecutionTrace", "7_Validator",
        "8_ComposerRouter", "9_VersionedRegistry"
    ]
    for node in required_nodes:
        if node not in fos.get("nodes", {}):
            errors.append(f"MISSING Function OS node: {node}")
    print(f"  ✓ {len(fos.get('nodes', {}))} nodes present")

# 9. Check equivalence axis
print("\n[9] Checking equivalence state axis...")
eq_axis = load_json(f"{OUTPUT_DIR}/120-function-equivalence-state-axis.json")
if eq_axis:
    required_states = [
        "SYNTACTIC_MATCH", "SPECIFICATION_MATCH", "FINITE_TEST_BEHAVIOR_MATCH",
        "DISTRIBUTIONAL_APPROXIMATION", "OBSERVATIONAL_EQUIVALENCE",
        "FORMAL_SEMANTIC_EQUIVALENCE", "EMPIRICAL_PERFORMANCE_SIMILARITY",
        "NOT_COMPARABLE"
    ]
    for state in required_states:
        if state not in eq_axis.get("states", {}):
            errors.append(f"MISSING equivalence state: {state}")
    print(f"  ✓ {len(eq_axis.get('states', {}))} equivalence states")

# 10. Check forbidden wording
print("\n[10] Checking forbidden wording...")
forbidden = load_jsonl(f"{OUTPUT_DIR}/120-forbidden-wording.jsonl")
if len(forbidden) < 10:
    warnings.append(f"Only {len(forbidden)} forbidden phrases (≥10 recommended)")
print(f"  ✓ {len(forbidden)} forbidden phrases")

# 11. Check followup queue
print("\n[11] Checking followup queue...")
followups = load_jsonl(f"{OUTPUT_DIR}/120-followup-queue-121-126.jsonl")
if len(followups) < 6:
    errors.append(f"FOLLOWUP QUEUE: expected ≥6, got {len(followups)}")
else:
    print(f"  ✓ {len(followups)} followup tasks (121-126)")

# 12. Check baseline manifest
print("\n[12] Checking baseline manifest...")
manifest = load_json(f"{OUTPUT_DIR}/120-baseline-manifest.json")
if manifest:
    # Check 085 frozen v1 hash
    frozen_hash = manifest.get("baseline_hashes", {}).get("085_frozen_v1", {}).get("sha256", "")
    expected_hash = "7d79f30a5eacb7f12c7ca9594c711000e030f7e12a61a9e609dbe75dac532a03"
    if frozen_hash != expected_hash:
        errors.append(f"085 FROZEN V1 HASH MISMATCH: expected {expected_hash}, got {frozen_hash}")
    else:
        print(f"  ✓ 085 frozen v1 hash matches expected value")
    
    # Check Ψ₀ hash
    psi0_hash = manifest.get("baseline_hashes", {}).get("psi0_definition", {}).get("sha256", "")
    expected_psi0 = "b90235ae9beb3b98458e0075345f3d3c53eaefe72035609bdea17385a3c1fd56"
    if psi0_hash != expected_psi0:
        errors.append(f"Ψ₀ HASH MISMATCH: expected {expected_psi0}, got {psi0_hash}")
    else:
        print(f"  ✓ Ψ₀ hash matches expected value")

# 13. API key leak scan
print("\n[13] Scanning for API key leaks...")
all_output_files = [
    f"{OUTPUT_DIR}/120-baseline-manifest.json",
    f"{OUTPUT_DIR}/120-function-source-registry.jsonl",
    f"{OUTPUT_DIR}/120-function-paradigm-cards.jsonl",
    f"{OUTPUT_DIR}/120-source-family-coverage.json",
    f"{OUTPUT_DIR}/120-fulltext-evidence-cards.jsonl",
    f"{OUTPUT_DIR}/120-internal-function-asset-inventory.jsonl",
    f"{OUTPUT_DIR}/120-existing-gap-overlap-matrix.jsonl",
    f"{OUTPUT_DIR}/120-gap-015-020-adjudications.jsonl",
    f"{OUTPUT_DIR}/120-function-os-candidate-overlay.json",
    f"{OUTPUT_DIR}/120-function-equivalence-state-axis.json",
    f"{OUTPUT_DIR}/120-forbidden-wording.jsonl",
    f"{OUTPUT_DIR}/120-followup-queue-121-126.jsonl",
    f"{OUTPUT_DIR}/120-run-state.json",
    f"{OUTPUT_DIR}/120-provider-and-tool-audit.md",
    f"{REPORT_DIR}/120-function-paradigm-atlas-report.md",
    f"{REPORT_DIR}/120-function-os-architecture-candidate-report.md",
    f"{REPORT_DIR}/120-source-quality-and-template-risk-audit.md",
]
for f_path in all_output_files:
    check_no_api_key_leak(f_path)
print(f"  ✓ Scanned {len(all_output_files)} files for API key leaks")

# 14. Check no red lines violated
print("\n[14] Checking red line compliance...")
# Check no modifications to Ψ₀
psi0_path = os.path.join(BASE_DIR, "统一函数总表/0001-Ψ₀元函数完整数学定义.md")
import hashlib
with open(psi0_path, "rb") as f:
    actual_psi0_hash = hashlib.sha256(f.read()).hexdigest()
if actual_psi0_hash != "b90235ae9beb3b98458e0075345f3d3c53eaefe72035609bdea17385a3c1fd56":
    errors.append("Ψ₀ FILE WAS MODIFIED - red line violation!")
else:
    print(f"  ✓ Ψ₀ file unmodified")

# Check no modifications to 085 frozen v1
frozen_path = os.path.join(BASE_DIR, "data/foundation/project-state-085.json")
with open(frozen_path, "rb") as f:
    actual_frozen_hash = hashlib.sha256(f.read()).hexdigest()
if actual_frozen_hash != "7d79f30a5eacb7f12c7ca9594c711000e030f7e12a61a9e609dbe75dac532a03":
    errors.append("085 FROZEN V1 WAS MODIFIED - red line violation!")
else:
    print(f"  ✓ 085 frozen v1 unmodified")

# ============================================================
# RESULTS
# ============================================================
print("\n" + "=" * 60)
print("VALIDATION RESULTS")
print("=" * 60)
print(f"Errors: {len(errors)}")
print(f"Warnings: {len(warnings)}")

if errors:
    print("\nERRORS:")
    for e in errors:
        print(f"  ✗ {e}")

if warnings:
    print("\nWARNINGS:")
    for w in warnings:
        print(f"  ⚠ {w}")

if not errors:
    print("\n✓ ALL CHECKS PASSED")
    sys.exit(0)
else:
    print(f"\n✗ {len(errors)} ERRORS FOUND")
    sys.exit(1)
