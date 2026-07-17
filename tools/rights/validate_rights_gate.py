#!/usr/bin/env python3
"""
LAB-Q33 Publication Gate Validator
LAB / SPECULATIVE / NON-AUTHORITATIVE / NOT CURRENT / NOT MERGE-AUTHORIZED

Validates that:
1. All rights registries conform to schema
2. No external content has been committed to the repository
3. Publication decisions form a consistent chain
4. All entries have claim_ceiling set
5. content_in_repo is false for non-project-generated sources
"""

import json
import sys
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "rights"
SCHEMA_DIR = ROOT / "schemas" / "rights"

VALID_REGISTRY_TYPES = {
    "jurisdiction", "legal_rule", "source_rights", "derivation_ledger",
    "publication_decision", "rights_risk_assessment", "third_party_notice",
    "historical_exposure", "takedown_response", "contributor_rights_attestation"
}

VALID_STATUSES = {
    "pending_review", "assessed", "risk_projected",
    "blocked", "allowed_with_conditions", "escalated"
}

VALID_SOURCE_TYPES = {
    "academic_paper", "book", "course_material", "blog_post",
    "open_source_code", "public_domain", "proprietary",
    "synthetic", "project_generated", "unknown"
}

VALID_RISK_LEVELS = {"low", "medium", "high", "critical", "unknown"}

VALID_CLAIM_CEILINGS = {
    "conservative_risk_projection", "metadata_only",
    "no_legal_advice", "no_license_grant"
}


class GateResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def ok(self, msg):
        self.passed.append(msg)

    def fail(self, msg):
        self.failed.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    @property
    def is_pass(self):
        return len(self.failed) == 0

    def report(self):
        lines = []
        for p in self.passed:
            lines.append(f"  [PASS] {p}")
        for f in self.failed:
            lines.append(f"  [FAIL] {f}")
        for w in self.warnings:
            lines.append(f"  [WARN] {w}")
        status = "PASS" if self.is_pass else "FAIL"
        lines.insert(0, f"Publication Gate: {status} ({len(self.passed)} pass, {len(self.failed)} fail, {len(self.warnings)} warn)")
        return "\n".join(lines)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_registry_structure(doc, path):
    """Validate basic registry structure."""
    result = GateResult()
    name = path.name

    if "registry_type" not in doc:
        result.fail(f"{name}: missing registry_type")
        return result

    if doc["registry_type"] not in VALID_REGISTRY_TYPES:
        result.fail(f"{name}: unknown registry_type '{doc['registry_type']}'")
        return result

    if "version" not in doc:
        result.fail(f"{name}: missing version")

    if "entries" not in doc:
        result.fail(f"{name}: missing entries array")
        return result

    result.ok(f"{name}: valid structure ({doc['registry_type']}, v{doc['version']}, {len(doc['entries'])} entries)")
    return result


def validate_entries(doc, path):
    """Validate individual entries."""
    result = GateResult()
    name = path.name

    for i, entry in enumerate(doc.get("entries", [])):
        eid = entry.get("id", f"index_{i}")

        # Required fields
        for field in ["id", "created_at", "status"]:
            if field not in entry:
                result.fail(f"{name}[{eid}]: missing required field '{field}'")

        # Status validation
        status = entry.get("status")
        if status and status not in VALID_STATUSES:
            result.fail(f"{name}[{eid}]: invalid status '{status}'")

        # Source type validation
        st = entry.get("source_type")
        if st and st not in VALID_SOURCE_TYPES:
            result.fail(f"{name}[{eid}]: invalid source_type '{st}'")

        # Risk level validation
        rl = entry.get("risk_level")
        if rl and rl not in VALID_RISK_LEVELS:
            result.fail(f"{name}[{eid}]: invalid risk_level '{rl}'")

        # Claim ceiling validation
        cc = entry.get("claim_ceiling")
        if cc and cc not in VALID_CLAIM_CEILINGS:
            result.fail(f"{name}[{eid}]: invalid claim_ceiling '{cc}'")

        # Content-in-repo gate: non-project-generated must not have content_in_repo=True
        if st and st not in ("project_generated", "synthetic", "public_domain"):
            if entry.get("content_in_repo") is True:
                result.fail(f"{name}[{eid}]: external source_type '{st}' has content_in_repo=true")

        # publication_allowed=false entries should not have content_in_repo=true
        if entry.get("publication_allowed") is False and entry.get("content_in_repo") is True:
            result.fail(f"{name}[{eid}]: publication_allowed=false but content_in_repo=true")

        # Every entry must have a claim_ceiling
        if "claim_ceiling" not in entry:
            result.warn(f"{name}[{eid}]: no claim_ceiling set")

    if not result.failed:
        result.ok(f"{name}: all {len(doc.get('entries', []))} entries valid")
    return result


def validate_no_external_content(doc, path):
    """Ensure no external copyrighted content is in the repo."""
    result = GateResult()
    name = path.name

    for entry in doc.get("entries", []):
        eid = entry.get("id", "?")
        st = entry.get("source_type", "unknown")
        in_repo = entry.get("content_in_repo", False)

        if st in ("proprietary", "course_material", "book", "academic_paper"):
            if in_repo:
                result.fail(f"{name}[{eid}]: {st} content marked as in-repo - COPYRIGHT RISK")

    if not result.failed:
        result.ok(f"{name}: no external content in repo")
    return result


def validate_derivation_chain(doc, path):
    """Validate derivation ledger entries."""
    result = GateResult()
    name = path.name

    for entry in doc.get("entries", []):
        eid = entry.get("id", "?")
        chain = entry.get("derivation_chain", [])
        for j, link in enumerate(chain):
            if "source_id" not in link:
                result.fail(f"{name}[{eid}].chain[{j}]: missing source_id")
            if "relation" not in link:
                result.fail(f"{name}[{eid}].chain[{j}]: missing relation")

    if not result.failed:
        result.ok(f"{name}: derivation chains valid")
    return result


def validate_publication_decisions(doc, path):
    """Validate publication decision consistency."""
    result = GateResult()
    name = path.name

    for entry in doc.get("entries", []):
        eid = entry.get("id", "?")
        if entry.get("publication_allowed") is True:
            conditions = entry.get("conditions", [])
            if not conditions:
                result.warn(f"{name}[{eid}]: allowed publication but no conditions specified")

    if not result.failed:
        result.ok(f"{name}: publication decisions consistent")
    return result


def validate_all():
    """Run all publication gate validations."""
    total = GateResult()

    if not DATA_DIR.exists():
        total.fail(f"Rights data directory not found: {DATA_DIR}")
        return total

    registry_files = sorted(DATA_DIR.glob("*.json"))
    if not registry_files:
        total.fail("No rights registry files found")
        return total

    for rf in registry_files:
        try:
            doc = load_json(rf)
        except (json.JSONDecodeError, OSError) as e:
            total.fail(f"{rf.name}: cannot load JSON: {e}")
            continue

        r1 = validate_registry_structure(doc, rf)
        r2 = validate_entries(doc, rf)
        r3 = validate_no_external_content(doc, rf)

        total.passed.extend(r1.passed + r2.passed + r3.passed)
        total.failed.extend(r1.failed + r2.failed + r3.failed)
        total.warnings.extend(r1.warnings + r2.warnings + r3.warnings)

        if doc.get("registry_type") == "derivation_ledger":
            r4 = validate_derivation_chain(doc, rf)
            total.passed.extend(r4.passed)
            total.failed.extend(r4.failed)
            total.warnings.extend(r4.warnings)

        if doc.get("registry_type") == "publication_decision":
            r5 = validate_publication_decisions(doc, rf)
            total.passed.extend(r5.passed)
            total.failed.extend(r5.failed)
            total.warnings.extend(r5.warnings)

    return total


if __name__ == "__main__":
    result = validate_all()
    print(result.report())
    sys.exit(0 if result.is_pass else 1)
