#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""121A Night Recovery Validator

Validates all 121A artifacts meet minimum requirements.
Exits non-zero on failure.
"""

import json
import sys
import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent.parent  # repo root (data/external-research/121A-night-recovery/ -> repo root)
DIR_121A = BASE / "data" / "external-research" / "121A-night-recovery"
DIR_121 = BASE / "data" / "external-research" / "121-fulltext-resolver"

errors = []
warnings = []

def error(msg):
    errors.append(msg)
    print(f"  ❌ FAIL: {msg}")

def warn(msg):
    warnings.append(msg)
    print(f"  ⚠️  WARN: {msg}")

def ok(msg):
    print(f"  ✅ PASS: {msg}")

def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        error(f"Cannot parse JSON: {path} — {e}")
        return None

def load_jsonl(path):
    lines = []
    for i, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            lines.append(json.loads(line))
        except:
            error(f"Invalid JSONL line {i} in {path}")
    return lines

print("=" * 60)
print("121A Night Recovery Validator")
print("=" * 60)

# 1. All required 121A files exist
print("\n--- Check 1: Required 121A files ---")
required_files = [
    "121A-workspace-snapshot-manifest.json",
    "121A-kimi-output-inventory.jsonl",
    "121A-stage-completion-matrix.json",
    "121A-jsonl-format-audit.json",
    "121A-repair-register.jsonl",
    "121A-openalex-tool-provenance.json",
    "121A-openalex-smoke-test.json",
    "121A-program-as-weights-fetch-smoke-test.json",
    "121A-credential-hygiene-audit.json",
    "121A-run-state.json",
    "121A-resume-plan-121B-121C.md",
    "121A-validator.py",
]
for f in required_files:
    p = DIR_121A / f
    if p.exists():
        ok(f"{f} exists")
    else:
        error(f"Missing: {f}")

report_path = BASE / "reports" / "external-research" / "121A-night-recovery-report.md"
if report_path.exists():
    ok("121A-night-recovery-report.md exists")
else:
    error("Missing: reports/external-research/121A-night-recovery-report.md")

# 2. All JSON/JSONL parse correctly
print("\n--- Check 2: JSON/JSONL validity ---")
for f in required_files:
    if f.endswith(".json"):
        p = DIR_121A / f
        if p.exists():
            if load_json(p) is not None:
                ok(f"{f} valid JSON")
    elif f.endswith(".jsonl"):
        p = DIR_121A / f
        if p.exists():
            lines = load_jsonl(p)
            if lines:
                ok(f"{f} valid JSONL ({len(lines)} lines)")

# 3. All 121 JSONL files are valid
print("\n--- Check 3: 121 JSONL files ---")
jsonl_files = list(DIR_121.glob("*.jsonl"))
for jf in jsonl_files:
    lines = load_jsonl(jf)
    if lines:
        ok(f"{jf.name}: {len(lines)} valid lines")

# 4. Counts from files
print("\n--- Check 4: Counts from files ---")
evidence_cards = load_jsonl(DIR_121 / "121-fulltext-evidence-cards.jsonl")
if evidence_cards:
    ok(f"Evidence cards: {len(evidence_cards)}")
    if len(evidence_cards) >= 20:
        ok("Evidence cards ≥ 20 (CP4 minimum)")
    else:
        error(f"Evidence cards < 20: {len(evidence_cards)}")

gaps = load_jsonl(DIR_121 / "121-gap-015-020-readjudications.jsonl")
if gaps:
    ok(f"GAP readjudications: {len(gaps)}")
    if len(gaps) == 6:
        ok("GAP-015 to GAP-020 all readjudicated")
    else:
        error(f"Expected 6 GAPs, got {len(gaps)}")

source_registry = load_jsonl(DIR_121 / "121-fulltext-source-registry.jsonl")
if source_registry:
    ok(f"Source registry: {len(source_registry)} sources")

failures = load_jsonl(DIR_121 / "121-fulltext-failure-register.jsonl")
if failures:
    ok(f"Failure register: {len(failures)} failures")

# 5. OpenAlex provenance
print("\n--- Check 5: OpenAlex provenance ---")
prov = load_json(DIR_121A / "121A-openalex-tool-provenance.json")
if prov:
    if prov.get("source_commit", "").startswith("5d33b72"):
        ok(f"OpenAlex source commit: {prov['source_commit']}")
    else:
        error(f"OpenAlex source commit mismatch: {prov.get('source_commit')}")
    if prov.get("sha256"):
        ok(f"OpenAlex SHA256: {prov['sha256'][:16]}...")
    else:
        error("OpenAlex SHA256 missing")

# 6. Credential hygiene
print("\n--- Check 6: Credential hygiene ---")
cred = load_json(DIR_121A / "121A-credential-hygiene-audit.json")
if cred:
    if cred.get("credential_values_found") == 0:
        ok("0 credential values found")
    else:
        error(f"Credential values found: {cred.get('credential_values_found')}")
    if cred.get("authorization_headers_found") == 0:
        ok("0 Authorization headers found")
    else:
        error(f"Authorization headers found: {cred.get('authorization_headers_found')}")
    if cred.get("env_file_content_leaked") == 0:
        ok("0 .env content leaks")
    else:
        error(f".env content leaked: {cred.get('env_file_content_leaked')}")

# 7. Redlines
print("\n--- Check 7: Redlines ---")
manifest = load_json(DIR_121A / "121A-workspace-snapshot-manifest.json")
if manifest:
    if manifest.get("psi0_modified") is False:
        ok("Ψ₀ not modified")
    else:
        error("Ψ₀ modified!")
    if manifest.get("frozen_v1_085_modified") is False:
        ok("085 frozen v1 not modified")
    else:
        error("085 frozen v1 modified!")
    if manifest.get("function_table_modified") is False:
        ok("Function table not modified")
    else:
        error("Function table modified!")
    if manifest.get("case_table_modified") is False:
        ok("Case table not modified")
    else:
        error("Case table modified!")

# 8. Program-as-Weights fetch evidence
print("\n--- Check 8: Program-as-Weights fetch ---")
paw = load_json(DIR_121A / "121A-program-as-weights-fetch-smoke-test.json")
if paw:
    if paw.get("html_fetch", {}).get("http_status") == 200:
        ok(f"HTML fetch: 200, {paw['html_fetch']['content_length_bytes']} bytes")
    else:
        error("HTML fetch failed")
    if paw.get("pdf_fetch", {}).get("http_status") == 200:
        ok(f"PDF fetch: 200, {paw['pdf_fetch']['content_length_bytes']} bytes")
    else:
        error("PDF fetch failed")
    if paw.get("text_extraction", {}).get("extraction_successful"):
        ok(f"Text extraction: {paw['text_extraction']['word_count']} words")
    else:
        error("Text extraction failed")
    if paw.get("semantic_review_status") == "FULLTEXT_FETCH_AND_EXTRACTION_VERIFIED_PENDING_SEMANTIC_REVIEW":
        ok("Status: FETCH_VERIFIED_PENDING_SEMANTIC_REVIEW (not FULLTEXT_REVIEWED)")
    else:
        error(f"Unexpected status: {paw.get('semantic_review_status')}")

# 9. OpenAlex smoke test
print("\n--- Check 9: OpenAlex smoke test ---")
smoke = load_json(DIR_121A / "121A-openalex-smoke-test.json")
if smoke:
    if smoke.get("overall_status") == "ALL_TESTS_PASS":
        ok("All OpenAlex smoke tests pass")
    else:
        error(f"OpenAlex smoke test: {smoke.get('overall_status')}")
    if smoke.get("oa_url_not_counted_as_fulltext_reviewed"):
        ok("oa_url not counted as FULLTEXT_REVIEWED")

# 10. No large PDF/cache files in git diff
print("\n--- Check 10: Git diff cleanliness ---")
# Check that .cache/ is in .gitignore
gitignore = (BASE / ".gitignore").read_text()
if ".cache/fulltext/" in gitignore:
    ok(".cache/fulltext/ in .gitignore")
else:
    warn(".cache/fulltext/ not in .gitignore")

# Summary
print("\n" + "=" * 60)
print(f"SUMMARY: {len(errors)} errors, {len(warnings)} warnings")
if errors:
    print("STATUS: FAIL")
    sys.exit(1)
else:
    print("STATUS: PASS")
    sys.exit(0)
