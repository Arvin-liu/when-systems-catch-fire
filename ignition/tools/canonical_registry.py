#!/usr/bin/env python3
"""Canonical registry shared by 022 tools: field definitions, gate registry, legacy map."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

# ---- canonical field registry (canonical/data/canonical-field-registry.json) ----
CANONICAL_FIELDS: dict[str, dict[str, Any]] = {}
for _f in [
    "protocol_id", "title_zh", "title_en", "stable_slug", "source_status", "structure_status",
    "machine_validation_status", "semantic_review_status", "governance_status",
    "definition_original", "definition_normative", "normative_type", "constrained_object",
    "trigger_conditions", "constraint_result", "scope", "applicable_system_levels", "exclusions",
    "invalid_conditions", "termination_conditions", "neighbor_protocols", "boundary_with_neighbors",
    "conflict_resolution", "priority_rule", "circular_definition_check", "psi0_mapping",
    "p_meta_relation", "function_layer_relation", "case_layer_relation", "positive_evidence",
    "boundary_evidence", "source_references", "assertion_level", "document_path", "index_entry",
    "machine_record_path", "gate_results", "review", "blocking_issues", "soft_warnings",
    "provenance", "version_metadata",
]:
    CANONICAL_FIELDS[_f] = {"field_name": _f, "zh": _f, "type": "any", "required": True,
                            "allowed": None, "semantics": "", "source": "canonical",
                            "auto_derivable": False, "derivation_marker": None,
                            "missing_judgement": "PENDING", "hard_gate": True,
                            "needs_human_review": True, "legacy_map": [], "info_loss_risk": "low"}

# ---- legacy -> canonical field map ----
LEGACY_MAP: dict[str, list[str]] = {
    "protocol_id": ["id"],
    "title_zh": ["name_zh"],
    "title_en": ["name_en"],
    "stable_slug": ["stable_slug"],
    "source_status": ["status", "current_status"],
    "definition_original": ["definition"],
    "definition_normative": ["definition_normative", "definition_normative_draft"],
    "normative_type": ["normative_type"],
    "constrained_object": ["constrained_object"],
    "trigger_conditions": ["trigger_conditions"],
    "constraint_result": ["constraint_result", "role_in_P_meta"],
    "scope": ["scope", "dimension"],
    "applicable_system_levels": ["applicable_system_levels"],
    "exclusions": ["exclusions"],
    "invalid_conditions": ["invalid_conditions"],
    "termination_conditions": ["termination_conditions"],
    "neighbor_protocols": ["neighbor_protocols", "examples"],
    "boundary_with_neighbors": ["boundary_with_neighbors"],
    "conflict_resolution": ["conflict_resolution"],
    "priority_rule": ["priority_rule"],
    "circular_definition_check": ["circular_definition_check", "relation_to_Psi0"],
    "psi0_mapping": ["psi0_mapping", "relation_to_Psi0"],
    "p_meta_relation": ["p_meta_relation", "role_in_P_meta"],
    "function_layer_relation": ["function_layer_relation"],
    "case_layer_relation": ["case_layer_relation"],
    "positive_evidence": ["positive_evidence", "examples"],
    "boundary_evidence": ["boundary_evidence", "boundaries"],
    "source_references": ["source_references", "source_files"],
    "assertion_level": ["assertion_level"],
    "document_path": ["document_path"],
    "index_entry": ["index_entry"],
    "machine_record_path": ["machine_record_path"],
    "review": ["review"],
    # fields that have NO legacy source → must be authored (canonical-only)
    "stable_slug": ["stable_slug"],
    "structure_status": ["structure_status"],
    "machine_validation_status": ["machine_validation_status"],
    "semantic_review_status": ["semantic_review_status"],
    "governance_status": ["governance_status"],
    "definition_normative": ["definition_normative"],
    "gate_results": ["gate_results"],
    "blocking_issues": ["blocking_issues"],
    "soft_warnings": ["soft_warnings"],
    "provenance": ["provenance"],
    "version_metadata": ["version_metadata"],
}

# ---- gate registry (canonical/data/gate-registry.json) ----
GATE_REGISTRY: dict[str, dict[str, Any]] = {}
for gid in [f"G{n:02d}" for n in range(1, 36)] + [f"S{n:02d}" for n in range(1, 9)]:
    GATE_REGISTRY[gid] = {
        "gate_id": gid, "name": gid, "type": "hard", "mode": "semi_automatic",
        "blocks_structure_status": False, "blocks_content_machine_eligible": True,
        "blocks_ratification_ready": True, "blocks_formal_protocol": True,
        "pass": "evidence sufficient", "fail": "evidence clearly not satisfied",
        "pending": "evidence insufficient", "not_found": "required source/field missing",
        "not_applicable": "explicitly allowed by gate", "evidence": [],
        "auto_derivable": False,
    }
# governance gates (do NOT block machine_eligible)
for gid in ["G33", "G34", "G35"]:
    GATE_REGISTRY[gid]["type"] = "governance"
    GATE_REGISTRY[gid]["blocks_content_machine_eligible"] = False
    GATE_REGISTRY[gid]["blocks_ratification_ready"] = True
    GATE_REGISTRY[gid]["blocks_formal_protocol"] = True
# known manual gates
for gid in ["G07", "G10", "G13", "G20", "G22", "G23", "G33"]:
    GATE_REGISTRY[gid]["mode"] = "manual" if gid == "G33" else "semi_automatic"
    GATE_REGISTRY[gid]["auto_derivable"] = False
for sid in [f"S{n:02d}" for n in range(1, 9)]:
    GATE_REGISTRY[sid]["type"] = "soft"
    GATE_REGISTRY[sid]["blocks_content_machine_eligible"] = False
    GATE_REGISTRY[sid]["blocks_ratification_ready"] = False
    GATE_REGISTRY[sid]["blocks_formal_protocol"] = False


def load_gate_registry() -> dict:
    return GATE_REGISTRY


def load_legacy_map() -> dict:
    return LEGACY_MAP


def write_registries():
    (ROOT / "canonical/data/canonical-field-registry.json").write_text(
        json.dumps(CANONICAL_FIELDS, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "canonical/data/gate-registry.json").write_text(
        json.dumps(GATE_REGISTRY, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "canonical/mappings/legacy-to-canonical-field-map.json").write_text(
        json.dumps(LEGACY_MAP, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    write_registries()
    print("registries written")
