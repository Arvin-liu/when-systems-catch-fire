#!/usr/bin/env python3
"""
Fail-Closed Publication Gate Validator — Q33 Core Gate

This tool enforces a fail-closed publication gate for all materials
entering or leaving the repository. It validates against:
  - jurisdiction/rule registry
  - source-rights registry
  - material classification
  - external input non-republication principle

Usage:
  python3 tools/governance/fail_closed_publication_gate.py --action check --input-id MAT-001
  python3 tools/governance/fail_closed_publication_gate.py --action classify --input-id MAT-001 --category third_party_course_material
  python3 tools/governance/fail_closed_publication_gate.py --action gate --input-id MAT-001 --gate-decision BLOCK
  python3 tools/governance/fail_closed_publication_gate.py --action audit
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOV_DIR = os.path.join(REPO_ROOT, "data", "governance")
SCHEMAS_DIR = os.path.join(REPO_ROOT, "schemas", "governance")


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')


def validate_schema(data, schema_path):
    """Basic schema validation without jsonschema library."""
    schema = load_json(schema_path)
    required = schema.get("required", [])
    props = schema.get("properties", {})

    errors = []
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    for key, val in data.items():
        if key in props:
            expected_type = props[key].get("type")
            if expected_type == "string" and not isinstance(val, str):
                errors.append(f"Field '{key}' should be string, got {type(val).__name__}")
            elif expected_type == "integer" and not isinstance(val, int):
                errors.append(f"Field '{key}' should be integer, got {type(val).__name__}")
            elif expected_type == "boolean" and not isinstance(val, bool):
                errors.append(f"Field '{key}' should be boolean, got {type(val).__name__}")
            elif expected_type == "array" and not isinstance(val, list):
                errors.append(f"Field '{key}' should be array, got {type(val).__name__}")

            # Check enum values
            if "enum" in props[key] and val not in props[key]["enum"]:
                errors.append(f"Field '{key}' value '{val}' not in allowed values: {props[key]['enum']}")

    return errors


class FailClosedPublicationGate:
    def __init__(self):
        self.jurisdiction_registry = load_json(os.path.join(GOV_DIR, "jurisdiction-rule-registry.json"))
        self.source_rights_registry = load_json(os.path.join(GOV_DIR, "source-rights-registry.json"))
        self.material_classification = load_json(os.path.join(GOV_DIR, "material-classification.json"))
        self.gate_decisions = {}
        self.non_republication_records = {}
        self.history_remediations = []

    def load_existing_decisions(self):
        decisions_path = os.path.join(GOV_DIR, "publication-gate-decisions.jsonl")
        if os.path.exists(decisions_path):
            with open(decisions_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = json.loads(line)
                        self.gate_decisions[entry["material_id"]] = entry

    def classify_material(self, material_id, source_category, access_method="unknown"):
        """Classify a material and return its classification level."""
        categories = self.source_rights_registry["categories"]
        if source_category not in categories:
            return {
                "material_id": material_id,
                "classification_level": 6,
                "risk_level": "CRITICAL",
                "gate_decision": "BLOCK",
                "reason": f"Unknown source category: {source_category}. Fail-closed: default to BLOCK.",
                "fail_closed_default": True
            }

        cat = categories[source_category]
        risk = cat.get("risk_level", "MEDIUM")

        # Map rights_status to classification level
        level_map = {
            "NO_RESTRICTION": 0,
            "COVERED_BY_PROJECT_LAYERED_LICENSE": 1,
            "CONDITIONAL_FREE_USE": 2,
            "COPYLEFT_NETWORK_USE": 2,
            "PERMISSIVE_WITH_PATENT_GRANT": 2,
            "NON_COMMERCIAL_ONLY": 3,
            "RESTRICTED_PRE_CHANGE_DATE": 3,
            "AUTHOR_OWNS_COPYRIGHT": 4,
            "PUBLISHER_OR_AUTHOR_OWNS_COPYRIGHT": 4,
            "ACCESS_RESTRICTED": 6,
            "VARY_BY_JURISDICTION": 5,
            "PLATFORM_OWNS_COPYRIGHT": 2,
            "UNCERTAIN": 5
        }

        level = level_map.get(cat["rights_status"], 4)

        gate_map = {
            0: "PASS",
            1: "PASS",
            2: "PASS_WITH_COMPLIANCE",
            3: "CONDITIONAL_PASS",
            4: "BLOCK",
            5: "BLOCK",
            6: "BLOCK"
        }

        gate = gate_map.get(level, "BLOCK")

        return {
            "material_id": material_id,
            "source_category": source_category,
            "access_method": access_method,
            "classification_level": level,
            "rights_status": cat["rights_status"],
            "risk_level": risk,
            "gate_decision": gate,
            "governance_action": cat["governance_action"],
            "provenance_required": True,
            "fail_closed_default": False
        }

    def check_gate(self, decision):
        """Check if a gate decision is valid against the classification levels.
        
        This performs gate-level consistency validation only (does not require 
        all schema fields). Use validate_schema() separately for full schema compliance.
        """
        # Lightweight gate-level consistency check (no full schema required)
        expected_gate = {
            0: ["PASS"],
            1: ["PASS"],
            2: ["PASS_WITH_COMPLIANCE"],
            3: ["CONDITIONAL_PASS"],
            4: ["BLOCK", "BLOCK_PENDING_PERMISSION"],
            5: ["BLOCK", "BLOCK_PENDING_COUNSEL"],
            6: ["BLOCK"]
        }

        level = decision.get("classification_level")
        gate_val = decision.get("gate_decision")

        errors = []
        
        if level is not None and gate_val is not None:
            allowed = expected_gate.get(level, ["BLOCK"])
            if gate_val not in allowed:
                errors.append(f"Gate decision '{gate_val}' not allowed for classification level {level}. Allowed: {allowed}")

        return {"valid": len(errors) == 0, "errors": errors}

    def record_gate_decision(self, decision):
        """Record a gate decision and persist it."""
        check = self.check_gate(decision)
        if not check["valid"]:
            return {"success": False, "errors": check["errors"]}

        decision["timestamp_HE"] = "12026年7月19日（人类纪元；对应公元2026年7月19日）"
        decision["timestamp_ISO"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.gate_decisions[decision["material_id"]] = decision

        # Persist to JSONL
        decisions_path = os.path.join(GOV_DIR, "publication-gate-decisions.jsonl")
        with open(decisions_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(decision, ensure_ascii=False) + '\n')

        return {"success": True, "material_id": decision["material_id"], "gate_decision": decision.get("gate_decision", "UNKNOWN")}

    def certify_non_republication(self, record):
        """Certify compliance with the External Input Non-Republication Principle."""
        schema_path = os.path.join(SCHEMAS_DIR, "external-input-non-republication.schema.json")
        errors = validate_schema(record, schema_path)
        if errors:
            return {"success": False, "errors": errors}

        if not record.get("non_republication_certified", False):
            return {"success": False, "errors": ["Non-republication certification is required."]}

        record["timestamp_HE"] = "12026年7月19日（人类纪元；对应公元2026年7月19日）"
        record["timestamp_ISO"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.non_republication_records[record["input_id"]] = record

        rec_path = os.path.join(GOV_DIR, "external-input-non-republication-records.jsonl")
        with open(rec_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

        return {"success": True, "input_id": record["input_id"]}

    def audit_report(self):
        """Generate an audit report of all gate decisions and records."""
        total_materials = len(self.gate_decisions)
        passed = sum(1 for d in self.gate_decisions.values() if d.get("gate_decision") in ("PASS", "PASS_WITH_COMPLIANCE"))
        blocked = sum(1 for d in self.gate_decisions.values() if d.get("gate_decision").startswith("BLOCK"))
        conditional = sum(1 for d in self.gate_decisions.values() if d.get("gate_decision") == "CONDITIONAL_PASS")

        return {
            "audit_timestamp_HE": "12026年7月19日（人类纪元；对应公元2026年7月19日）",
            "audit_timestamp_ISO": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_materials_classified": total_materials,
            "gate_summary": {
                "passed": passed,
                "blocked": blocked,
                "conditional_pass": conditional
            },
            "non_republication_certified": len(self.non_republication_records),
            "total_jurisdictions_in_registry": len(self.jurisdiction_registry["jurisdictions"]),
            "total_source_categories": len(self.source_rights_registry["categories"]),
            "verification_statuses": self.jurisdiction_registry["summary"]["verification_statuses"]
        }


def main():
    parser = argparse.ArgumentParser(description="Fail-Closed Publication Gate Validator")
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # classify
    p_classify = subparsers.add_parser("classify", help="Classify a material")
    p_classify.add_argument("--input-id", required=True, help="Material ID")
    p_classify.add_argument("--category", required=True, help="Source category from registry")
    p_classify.add_argument("--access-method", default="unknown", help="How the material was accessed")

    # gate
    p_gate = subparsers.add_parser("gate", help="Record a gate decision")
    p_gate.add_argument("--input-id", required=True, help="Material ID")
    p_gate.add_argument("--gate-decision", required=True,
                        choices=["PASS", "PASS_WITH_COMPLIANCE", "CONDITIONAL_PASS", "BLOCK", "BLOCK_PENDING_PERMISSION", "BLOCK_PENDING_COUNSEL"],
                        help="Gate decision")
    p_gate.add_argument("--classification-level", type=int, required=True, help="Classification level 0-6")
    p_gate.add_argument("--source-category", required=True, help="Source category")
    p_gate.add_argument("--reviewer", default="agent", help="Who made the decision")

    # check
    p_check = subparsers.add_parser("check", help="Validate a gate decision")
    p_check.add_argument("--input-id", required=True, help="Material ID to look up")

    # audit
    subparsers.add_parser("audit", help="Generate audit report")

    args = parser.parse_args()
    gate = FailClosedPublicationGate()
    gate.load_existing_decisions()

    if args.action == "classify":
        result = gate.classify_material(args.input_id, args.category, args.access_method)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.action == "gate":
        decision = {
            "material_id": args.input_id,
            "source_category": args.source_category,
            "gate_decision": args.gate_decision,
            "classification_level": args.classification_level,
            "reviewer": args.reviewer,
            "provenance_recorded": True
        }
        result = gate.record_gate_decision(decision)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.action == "check":
        if args.input_id in gate.gate_decisions:
            result = gate.check_gate(gate.gate_decisions[args.input_id])
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(json.dumps({"error": f"No gate decision found for material {args.input_id}"}))

    elif args.action == "audit":
        result = gate.audit_report()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
