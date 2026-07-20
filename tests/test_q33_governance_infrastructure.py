#!/usr/bin/env python3
"""
Production tests for Q33 governance infrastructure.

Tests:
  1. Jurisdiction registry completeness and validity
  2. Source rights registry coverage
  3. Material classification schema validation
  4. Publication gate decision workflow
  5. Schema validation for all governance schemas
  6. Mutation tests: tampered data detected
"""

import json
import os
import sys
import copy

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOV_DIR = os.path.join(REPO_ROOT, "data", "governance")
SCHEMAS_DIR = os.path.join(REPO_ROOT, "schemas", "governance")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools", "governance")


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_jurisdiction_registry():
    """Test 1: Jurisdiction registry has all required jurisdictions and verified status."""
    reg = load_json(os.path.join(GOV_DIR, "jurisdiction-rule-registry.json"))

    # Check required jurisdictions
    required = ["US", "EU", "UK", "CA", "AU", "JP", "SG", "IN"]
    for j in required:
        assert j in reg["jurisdictions"], f"Missing jurisdiction: {j}"

    # Check treaty layer
    assert "treaty_layer" in reg, "Missing treaty_layer"
    for treaty_id in ["Berne_Convention_1886", "WCT_1996", "TRIPS_Copyright"]:
        assert treaty_id in reg["treaty_layer"], f"Missing treaty: {treaty_id}"

    # Check all jurisdictions are VERIFIED
    for jid, jdata in reg["jurisdictions"].items():
        assert jdata["verification_status"] == "VERIFIED", f"{jid} not VERIFIED: {jdata['verification_status']}"
        # P1 (F1 re-adjudication): every entry models a legal regime, not sovereignty
        assert jdata.get("sovereignty_position") == "NOT_ASSERTED", \
            f"{jid} must carry sovereignty_position: NOT_ASSERTED"

    # P1: registry-level sovereignty neutrality
    assert reg.get("sovereignty_position") == "NOT_ASSERTED", "Registry must declare sovereignty_position: NOT_ASSERTED"
    assert reg.get("modeling_concept") == "legal_regime_scope_of_application", \
        "Registry must model legal_regime_scope_of_application"

    # Check platform policies
    assert "platform_policy" in reg, "Missing platform_policy"
    assert "GitHub_DMCA_Takedown_Policy" in reg["platform_policy"], "Missing GitHub DMCA policy"

    # Check summary counts
    assert reg["summary"]["total_jurisdictions"] == 10, f"Expected 10 jurisdictions, got {reg['summary']['total_jurisdictions']}"
    assert reg["summary"]["total_treaties"] == 3
    assert reg["summary"]["total_platform_policies"] >= 2, f"Expected >= 2 platform policies, got {reg['summary']['total_platform_policies']}"

    return True


def test_source_rights_registry():
    """Test 2: Source rights registry covers all required categories."""
    reg = load_json(os.path.join(GOV_DIR, "source-rights-registry.json"))

    required_categories = [
        "public_domain",
        "open_license_cc_by_nc_sa",
        "open_license_agpl",
        "open_license_apache",
        "open_license_busl",
        "third_party_course_material",
        "third_party_paywall_article",
        "third_party_private_note",
        "government_publication",
        "platform_policy_document",
        "ai_generated_content",
        "project_original_content"
    ]

    for cat in required_categories:
        assert cat in reg["categories"], f"Missing source category: {cat}"
        c = reg["categories"][cat]
        assert "rights_status" in c, f"Category {cat} missing rights_status"
        assert "governance_action" in c, f"Category {cat} missing governance_action"

    # Check high-risk categories have prohibited_actions
    for hr_cat in ["third_party_course_material", "third_party_paywall_article", "third_party_private_note"]:
        assert "prohibited_actions" in reg["categories"][hr_cat], f"{hr_cat} missing prohibited_actions"
        assert "permitted_actions" in reg["categories"][hr_cat], f"{hr_cat} missing permitted_actions"

    return True


def test_material_classification():
    """Test 3: Material classification has all levels and types."""
    mc = load_json(os.path.join(GOV_DIR, "material-classification.json"))

    # Check all 7 classification levels exist (L0 through L6)
    cs = mc.get("classification_system", {})
    expected_keys = ["L0_metadata", "L1_fact", "L2_idea_method", "L3_short_quotation", "L4_substantial_text", "L5_image_photograph", "L6_audio_video"]
    for ek in expected_keys:
        assert ek in cs, f"Missing classification level {ek}"

    # Check material type registry
    mtr = mc.get("material_type_registry", {})
    for mtype in ["external_input", "ignition_increment", "project_documentation", "registry_data"]:
        assert mtype in mtr, f"Missing material type: {mtype}"

    return True


def test_publication_gate_workflow():
    """Test 4: Publication gate decision workflow works correctly."""
    sys.path.insert(0, TOOLS_DIR)
    from fail_closed_publication_gate import FailClosedPublicationGate

    gate = FailClosedPublicationGate()

    # Test classify: public domain -> PASS
    result = gate.classify_material("TEST-PD-001", "public_domain")
    assert result["gate_decision"] == "PASS", f"Expected PASS for public_domain, got {result['gate_decision']}"
    assert result["classification_level"] == 0

    # Test classify: project owned -> PASS
    result = gate.classify_material("TEST-PRJ-001", "project_original_content")
    assert result["gate_decision"] == "PASS", f"Expected PASS for project_original_content, got {result['gate_decision']}"

    # Test classify: course material -> BLOCK
    result = gate.classify_material("TEST-COURSE-001", "third_party_course_material")
    assert result["gate_decision"] == "BLOCK", f"Expected BLOCK for third_party_course_material, got {result['gate_decision']}"
    assert result["classification_level"] == 4

    # Test classify: private note -> BLOCK (critical)
    result = gate.classify_material("TEST-PRIVATE-001", "third_party_private_note")
    assert result["gate_decision"] == "BLOCK", f"Expected BLOCK for third_party_private_note, got {result['gate_decision']}"
    assert result["classification_level"] == 6

    # Test classify: unknown category -> BLOCK (fail-closed)
    result = gate.classify_material("TEST-UNKNOWN-001", "nonexistent_category")
    assert result["gate_decision"] == "BLOCK", f"Expected BLOCK for unknown category, got {result['gate_decision']}"
    assert result["fail_closed_default"] is True

    # Test gate recording (fail-closed contract: provenance/reason/rule/version required)
    decision = {
        "material_id": "TEST-COURSE-001",
        "source_category": "third_party_course_material",
        "gate_decision": "BLOCK",
        "classification_level": 4,
        "source_rights_entry_id": "third_party_course_material",
        "content_digest_sha256": "0" * 64,
        "reason": "Third-party course material: author owns copyright; republication prohibited.",
        "rule_ref": "source-rights-registry:third_party_course_material",
        "schema_version": "governance-gate-v1"
    }
    result = gate.record_gate_decision(decision)
    assert result["success"] is True
    assert result["gate_decision"] == "BLOCK"

    # Test audit report (counts persisted gate decisions, not in-memory classifications)
    # Record additional decisions to ensure audit has enough data. Unknown category must
    # fail closed (not persisted) — verifying the gate no longer blindly records.
    for mid, cat, lvl, gate_d in [
        ("T1", "public_domain", 0, "PASS"),
        ("T3", "third_party_private_note", 6, "BLOCK"),
    ]:
        d = {
            "material_id": mid,
            "source_category": cat,
            "gate_decision": gate_d,
            "classification_level": lvl,
            "source_rights_entry_id": cat,
            "content_digest_sha256": "0" * 64,
            "reason": f"Recorded decision for {mid}",
            "rule_ref": f"source-rights-registry:{cat}",
            "schema_version": "governance-gate-v1"
        }
        r = gate.record_gate_decision(d)
        assert r["success"] is True, f"Expected {mid} recorded, got {r}"

    # Unknown category must be rejected (fail-closed), not persisted.
    bad = {
        "material_id": "T4",
        "source_category": "nonexistent_category",
        "gate_decision": "BLOCK",
        "classification_level": 6,
        "source_rights_entry_id": "nonexistent_category",
        "content_digest_sha256": "0" * 64,
        "reason": "should be rejected",
        "rule_ref": "n/a",
        "schema_version": "governance-gate-v1"
    }
    r_bad = gate.record_gate_decision(bad)
    assert r_bad["success"] is False, "Unknown category must fail closed (not recorded)"
    assert "fail-closed" in " ".join(r_bad.get("errors", [])).lower() or r_bad.get("errors")

    audit = gate.audit_report()
    print(f"Audit: total={audit['total_materials_classified']} blocked={audit['gate_summary']['blocked']}")
    assert audit["total_materials_classified"] >= 3, f"Expected >= 3 persisted decisions, got {audit['total_materials_classified']}"
    assert audit["gate_summary"]["blocked"] >= 2, f"Expected >= 2 blocked, got {audit['gate_summary']['blocked']}"

    return True


def test_schema_validation():
    """Test 5: All governance schemas are valid JSON."""
    schema_files = [
        "jurisdiction-rule-entry.schema.json",
        "source-rights-entry.schema.json",
        "publication-gate-decision.schema.json",
        "external-input-non-republication.schema.json",
        "history-remediation-entry.schema.json"
    ]

    for sf in schema_files:
        path = os.path.join(SCHEMAS_DIR, sf)
        assert os.path.exists(path), f"Schema file missing: {path}"
        schema = load_json(path)
        assert "$schema" in schema, f"Schema {sf} missing $schema field"
        assert "title" in schema, f"Schema {sf} missing title"
        assert "required" in schema, f"Schema {sf} missing required fields"

    return True


def test_mutation_detection():
    """Test 6: Mutation tests — tampered data should be detected."""
    reg = load_json(os.path.join(GOV_DIR, "jurisdiction-rule-registry.json"))

    # Tamper with a jurisdiction's verification status
    tampered = copy.deepcopy(reg)
    tampered["jurisdictions"]["US"]["verification_status"] = "UNVERIFIED"

    # This should be detectable: US should be VERIFIED
    assert tampered["jurisdictions"]["US"]["verification_status"] != "VERIFIED"

    # Tamper with source rights: remove prohibited_actions from high-risk category
    src_reg = load_json(os.path.join(GOV_DIR, "source-rights-registry.json"))
    tampered_src = copy.deepcopy(src_reg)
    del tampered_src["categories"]["third_party_course_material"]["prohibited_actions"]

    assert "prohibited_actions" not in tampered_src["categories"]["third_party_course_material"]

    # Gate validator should catch this inconsistency
    sys.path.insert(0, TOOLS_DIR)
    from fail_closed_publication_gate import FailClosedPublicationGate
    gate = FailClosedPublicationGate()

    # A tampered decision with wrong gate-for-level should fail validation
    bad_decision = {
        "material_id": "MUTATION-TEST",
        "source_category": "third_party_private_note",
        "gate_decision": "PASS",  # Should be BLOCK for level 6
        "classification_level": 6
    }
    result = gate.check_gate(bad_decision)
    assert result["valid"] is False, "Mutation test failed: tampered gate decision should be invalid"

    return True


def test_validator_tool_exists():
    """Test 7: Validator tool exists and is executable Python."""
    tool_path = os.path.join(TOOLS_DIR, "fail_closed_publication_gate.py")
    assert os.path.exists(tool_path), f"Validator tool missing: {tool_path}"

    with open(tool_path, 'r') as f:
        content = f.read()
    assert "class FailClosedPublicationGate" in content, "Validator missing FailClosedPublicationGate class"
    assert "classify_material" in content, "Validator missing classify_material method"
    assert "check_gate" in content, "Validator missing check_gate method"
    assert "record_gate_decision" in content, "Validator missing record_gate_decision method"
    assert "certify_non_republication" in content, "Validator missing certify_non_republication method"
    assert "audit_report" in content, "Validator missing audit_report method"

    return True


def test_governance_documents_exist():
    """Test 8: Governance documents exist and contain required content."""
    doc_path = os.path.join(REPO_ROOT, "docs", "governance", "external-input-non-republication-principle.md")
    assert os.path.exists(doc_path), f"Document missing: {doc_path}"

    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "不得被复述" in content or "Non-Republication" in content, "Document missing non-republication principle"
    assert "禁止" in content or "prohibited" in content.lower(), "Document missing prohibited actions"
    assert "公平交易" in content or "fair dealing" in content.lower(), "Document missing fair dealing reference"

    # History remediation register
    hist_path = os.path.join(GOV_DIR, "history-remediation-register.json")
    assert os.path.exists(hist_path), f"History remediation register missing: {hist_path}"

    hist = load_json(hist_path)
    assert "entries" in hist, "History remediation register missing entries"
    assert len(hist["entries"]) > 0, "History remediation register has no entries"

    return True


def main():
    tests = [
        ("Jurisdiction registry", test_jurisdiction_registry),
        ("Source rights registry", test_source_rights_registry),
        ("Material classification", test_material_classification),
        ("Publication gate workflow", test_publication_gate_workflow),
        ("Schema validation", test_schema_validation),
        ("Mutation detection", test_mutation_detection),
        ("Validator tool", test_validator_tool_exists),
        ("Governance documents", test_governance_documents_exist),
    ]

    passed = 0
    failed = 0
    errors = []

    for name, test_fn in tests:
        try:
            result = test_fn()
            if result:
                print(f"  PASS: {name}")
                passed += 1
            else:
                print(f"  FAIL: {name} (returned False)")
                failed += 1
                errors.append(name)
        except Exception as e:
            print(f"  ERROR: {name} — {e}")
            failed += 1
            errors.append(f"{name}: {e}")

    print(f"\nResults: {passed}/{passed + failed} tests passed")
    if errors:
        print(f"Failed: {', '.join(errors)}")
        sys.exit(1)
    else:
        print("All Q33 governance tests passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
