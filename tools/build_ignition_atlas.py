#!/usr/bin/env python3
"""Build deterministic Ignition Atlas projections from repository artifacts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AS_OF_COMMIT = "5297fe6c4c3aa36519b2e0a4d751be43dee09441"


def node(node_id: str, label: str, object_ref: str, source: str, maturity: str, value: str, cost: list[str], maintainer: str, uncertainty: str, decision: str, reason: str) -> dict:
    return {
        "id": node_id,
        "label": label,
        "object_ref": object_ref,
        "source_refs": [source],
        "maturity": maturity,
        "value_visibility": value,
        "cost_bearers": cost,
        "maintainer": maintainer,
        "uncertainty": uncertainty,
        "sourcing_decision": {
            "decision": decision,
            "reason": reason,
            "affordable_loss": "Decision must remain reversible or bounded unless a later map raises the threshold.",
            "charter_constraint": "Outsourcing or automation cannot transfer value judgment, privacy risk, or Charter Gate duty.",
            "responsibility_retained": True
        },
        "evolution_record": {
            "stage": maturity,
            "basis": f"Projected from {source} for this map only.",
            "not_natural_law": True
        }
    }


def edge(edge_id: str, src: str, dst: str, edge_type: str, source: str, uncertainty: str = "Derived from declared architecture relation.") -> dict:
    return {
        "id": edge_id,
        "from": src,
        "to": dst,
        "edge_type": edge_type,
        "source_refs": [source],
        "uncertainty": uncertainty,
        "not_causality": True
    }


def structural_architecture_map() -> dict:
    nodes = [
        node("charter_gate", "Charter Gate", "docs/governance/life-community-value-charter.md", "docs/governance/life-community-value-charter.md", "CUSTOM_BUILT", "High for affected subjects and maintainer", ["maintainer", "affected subjects"], "maintainer", "Normative boundary, not factual proof.", "preserve", "Must remain project-specific and auditable."),
        node("l0_sources", "L0 Sources and Evidence", "ARCHITECTURE.md#L0", "ARCHITECTURE.md", "CUSTOM_BUILT", "High for evidence traceability", ["maintainer", "reviewers"], "maintainer", "Coverage remains incomplete for some content.", "preserve", "Source separation is core to non-overclaiming."),
        node("l1_claims", "L1 Controlled Claims", "data/foundation/claims/claims.jsonl", "data/foundation/claims/claims.jsonl", "CUSTOM_BUILT", "High for claim discipline", ["maintainer"], "maintainer", "Claim status axes must not auto-upgrade.", "automate", "Validation can be automated while judgment remains retained."),
        node("l2_objects", "L2 Formal Objects", "data/foundation/formal-objects/objects.jsonl", "data/foundation/formal-objects/objects.jsonl", "CUSTOM_BUILT", "Medium-high for formalization", ["maintainer"], "maintainer", "Object typing depends on source adjudication.", "automate", "Schema validation can reduce manual burden."),
        node("l3_arguments", "L3 Logical Arguments", "data/foundation/arguments/arguments.jsonl", "data/foundation/arguments/arguments.jsonl", "CUSTOM_BUILT", "Medium for inferential trace", ["maintainer"], "maintainer", "Argument quality remains source-dependent.", "preserve", "Argument separation should not be outsourced as truth judgment."),
        node("l4_proofs", "L4 Proofs and Models", "formal/lean/Foundation.lean", "formal/lean/Foundation.lean", "PRODUCT_RENTAL", "Medium for machine-checkable fragments", ["maintainer", "CI"], "maintainer", "Only scoped proofs are covered.", "rent", "Use public proof tooling while retaining proof-scope claims."),
        node("l5_validation", "L5 Validation", "tools/foundation/validate_foundation.py", "tools/foundation/validate_foundation.py", "CUSTOM_BUILT", "High for safe publication", ["maintainer", "CI"], "maintainer", "CI pass is workflow evidence only.", "automate", "Automation reduces repeated validation cost."),
        node("l6_publication", "L6 Publication", "README.md / reports", "ARCHITECTURE.md", "CUSTOM_BUILT", "High for readers", ["maintainer", "readers"], "maintainer", "Publication cannot create lower-layer truth.", "preserve", "Narrative claims need retained judgment."),
        node("function_os", "Function OS", "function-os-candidate/v0.2", "function-os-candidate/v0.2", "CUSTOM_BUILT", "Medium-high for execution", ["maintainer", "CI"], "maintainer", "Execution capability is not worthiness.", "automate", "Tests and packaging can be automated."),
        node("q12_dual_loop", "Q12 Dual Loop", "docs/architecture/effectual-action-plane.md", "docs/architecture/effectual-action-plane.md", "GENESIS", "Medium for action and interpretation discipline", ["maintainer"], "maintainer", "Real future effect is pending.", "preserve", "Keep as reviewable overlay."),
        node("q13_controls", "Q13 Attention/Distribution/Compression Controls", "docs/architecture/attention-attractor-control-plane.md", "docs/architecture/attention-attractor-control-plane.md", "GENESIS", "Medium for avoiding loops and pseudo-compression", ["maintainer"], "maintainer", "Real future effect is pending.", "preserve", "Keep as Draft overlay until review.")
    ]
    edges = [
        edge("e_charter_l0", "charter_gate", "l0_sources", "control_flow", "ARCHITECTURE.md"),
        edge("e_l0_l1", "l0_sources", "l1_claims", "evidence_flow", "ARCHITECTURE.md"),
        edge("e_l1_l2", "l1_claims", "l2_objects", "information_flow", "ARCHITECTURE.md"),
        edge("e_l2_l3", "l2_objects", "l3_arguments", "dependency", "ARCHITECTURE.md"),
        edge("e_l3_l4", "l3_arguments", "l4_proofs", "dependency", "ARCHITECTURE.md"),
        edge("e_l4_l5", "l4_proofs", "l5_validation", "evidence_flow", "ARCHITECTURE.md"),
        edge("e_l5_l6", "l5_validation", "l6_publication", "control_flow", "ARCHITECTURE.md"),
        edge("e_function_validation", "function_os", "l5_validation", "evidence_flow", ".github/workflows/function-os-ci.yml"),
        edge("e_q12_execution", "q12_dual_loop", "function_os", "control_flow", "ARCHITECTURE.md"),
        edge("e_q13_q12", "q13_controls", "q12_dual_loop", "control_flow", "ARCHITECTURE.md")
    ]
    return {
        "id": "map-epistemic-architecture",
        "map_type": "STRUCTURAL_LANDSCAPE",
        "as_of_commit": AS_OF_COMMIT,
        "observer_or_decision_owner": "maintainer and reviewer deciding how claims can move toward publication",
        "decision_question": "Which architecture surfaces constrain evidence, execution, validation, and publication?",
        "value_recipient_or_affected_subject": "readers, maintainers, and subjects affected by claims",
        "layout_semantics": {
            "x_axis": "layer or overlay sequence from source to publication",
            "y_axis": "normative/control/evidence dependency, not visual proof",
            "visual_boundary": "visual adjacency does not imply isomorphism or causality"
        },
        "data_sources": ["ARCHITECTURE.md", "data/foundation/project-state.json", "docs/architecture/*.md", "function-os-candidate/v0.2"],
        "generation_method": "Deterministic projection from declared architecture sections and known overlay files.",
        "claim_ceiling": "derived_navigation_view",
        "update_triggers": ["architecture file changes", "new overlay", "validator or CI boundary change", "Charter Gate change"],
        "nodes": nodes,
        "edges": edges,
        "projections": [
            {
                "id": "projection-architecture-static-v1",
                "input_sources": ["ARCHITECTURE.md", "data/foundation/project-state.json", "docs/architecture/*.md"],
                "projection_rule": "Map declared layers and overlays into nodes; map stated arrows into typed edges; preserve source refs and uncertainty.",
                "deterministic": True,
                "reviewer": "Codex main session",
                "uncertainty": "Does not infer hidden dependencies beyond declared architecture."
            }
        ],
        "unmapped_residue": [
            {
                "id": "residue-architecture-real-world-effect",
                "description": "Whether Q12/Q13 controls improve future reasoning behavior.",
                "reason": "Requires later use and external feedback.",
                "next_condition": "Compare future PRs and reviews after controls are used."
            }
        ]
    }


def build_atlas() -> dict:
    return {
        "atlas_spec": {
            "id": "ignition-atlas-121q14",
            "version": "121Q14-draft",
            "as_of_commit": AS_OF_COMMIT,
            "purpose": "Versioned derived maps for navigation and resource decisions.",
            "canonical_truth_source": "Repository registries, matrices, schemas, tests, and source artifacts remain authoritative.",
            "permanent_total_map": False
        },
        "maps": [structural_architecture_map()]
    }


def main() -> int:
    out_dir = ROOT / "data/atlas/generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    atlas = build_atlas()
    target = out_dir / "ignition-atlas-121q14.json"
    target.write_text(json.dumps(atlas, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
