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


def sustainability_economics_map() -> dict:
    nodes = [
        node("maintainer_judgment", "Maintainer judgment and Charter responsibility", "docs/governance/life-community-value-charter.md", "docs/governance/life-community-value-charter.md", "GENESIS", "Closest to maintainer sustainability and affected subjects", ["maintainer"], "maintainer", "Cannot be outsourced without losing accountability.", "preserve", "Normative judgment and refusal rights must stay accountable."),
        node("ai_quota", "AI quota and model access", "SUSTAINABILITY.md", "SUSTAINABILITY.md", "PRODUCT_RENTAL", "High for execution speed", ["maintainer", "sponsors"], "maintainer", "Provider availability and cost can change.", "rent", "Rent model access; do not make provider output a truth source."),
        node("ci_compute", "CI compute", ".github/workflows", ".github/workflows/foundation-validation.yml", "COMMODITY_UTILITY", "High for validation repeatability", ["maintainer", "GitHub Actions"], "maintainer", "CI pass is workflow evidence only.", "rent", "Use commodity CI while retaining claim boundaries."),
        node("foundation_validators", "Foundation validators", "tools/foundation", "tools/foundation/validate_foundation.py", "CUSTOM_BUILT", "High for publication safety", ["maintainer"], "maintainer", "Validator scope is repository-specific.", "automate", "Automate repeat checks to reduce maintenance load."),
        node("commercial_license", "Commercial license and reciprocity path", "LICENSES/COMMERCIAL-TERMS.md", "LICENSES/COMMERCIAL-TERMS.md", "CUSTOM_BUILT", "High for commercial users and maintainer sustainability", ["commercial users", "maintainer"], "maintainer", "Real-world uptake unknown.", "standardize", "Standardize terms while preserving case-by-case refusal and reciprocity review."),
        node("sponsorship", "Sponsorship and sustainability funding", "SUSTAINABILITY.md", "SUSTAINABILITY.md", "GENESIS", "High for maintainer life and project continuity", ["sponsors", "maintainer"], "maintainer", "Funding is not guaranteed and must not buy truth claims.", "co_build", "Seek support without governance capture."),
        node("storage_network", "Storage, network, and repository hosting", "GitHub repository", "README.md", "COMMODITY_UTILITY", "Medium-high for access and collaboration", ["maintainer", "platform"], "maintainer", "Platform terms and availability can change.", "rent", "Use commodity hosting while keeping exportable repository state.")
    ]
    edges = [
        edge("econ_judgment_license", "maintainer_judgment", "commercial_license", "control_flow", "docs/governance/life-community-value-charter.md"),
        edge("econ_sponsor_quota", "sponsorship", "ai_quota", "value_flow", "SUSTAINABILITY.md"),
        edge("econ_sponsor_ci", "sponsorship", "ci_compute", "value_flow", "SUSTAINABILITY.md"),
        edge("econ_ai_validators", "ai_quota", "foundation_validators", "information_flow", "tools/foundation/validate_foundation.py"),
        edge("econ_ci_validators", "ci_compute", "foundation_validators", "evidence_flow", ".github/workflows/foundation-validation.yml"),
        edge("econ_hosting_license", "storage_network", "commercial_license", "dependency", "README.md")
    ]
    return {
        "id": "map-maintainer-sustainability-economics",
        "map_type": "WARDLEY_STYLE_EVOLUTION",
        "as_of_commit": AS_OF_COMMIT,
        "observer_or_decision_owner": "maintainer deciding what to keep, rent, automate, standardize, or fund",
        "decision_question": "Which costs and responsibilities must be retained, automated, rented, standardized, or covered by sponsorship?",
        "value_recipient_or_affected_subject": "maintainer, noncommercial users, commercial users, and affected subjects",
        "layout_semantics": {
            "x_axis": "evolution stage from genesis to commodity utility",
            "y_axis": "visibility to maintainer sustainability and project continuity",
            "visual_boundary": "rightward movement is not moral progress or inevitable commodification"
        },
        "data_sources": ["SUSTAINABILITY.md", "LICENSES/COMMERCIAL-TERMS.md", ".github/workflows", "tools/foundation", "docs/governance/life-community-value-charter.md"],
        "generation_method": "Deterministic static projection from declared sustainability, license, validation, CI, and charter surfaces.",
        "claim_ceiling": "derived_resource_navigation_view",
        "update_triggers": ["license scope change", "sponsorship policy change", "CI cost change", "model access change", "Charter Gate change"],
        "nodes": nodes,
        "edges": edges,
        "projections": [
            {
                "id": "projection-sustainability-static-v1",
                "input_sources": ["SUSTAINABILITY.md", "LICENSES/COMMERCIAL-TERMS.md", ".github/workflows", "tools/foundation"],
                "projection_rule": "Map declared cost-bearing surfaces and reusable infrastructure into Wardley-style evolution stages with sourcing decisions.",
                "deterministic": True,
                "reviewer": "Codex main session",
                "uncertainty": "Does not predict actual sponsor or commercial behavior."
            }
        ],
        "unmapped_residue": [
            {
                "id": "residue-real-funding-response",
                "description": "Actual willingness of sponsors or commercial users to cover costs.",
                "reason": "Requires real-world response beyond repository artifacts.",
                "next_condition": "Record signed sponsorship, commercial license, or refusal evidence."
            }
        ]
    }


def agent_operations_map() -> dict:
    nodes = [
        node("user_request", "User request", "conversation / 1111 command", "agent-commands", "GENESIS", "Highest for user intent", ["user", "maintainer"], "user and maintainer", "Conversation context can be incomplete.", "preserve", "Intent interpretation remains human/accountable."),
        node("command_bus", "1111 command bus", "Arvin-liu/1111", "agent-commands", "CUSTOM_BUILT", "High for cross-session continuity", ["maintainer"], "maintainer", "Command bus is metadata/control, not proof.", "preserve", "Keep lightweight and auditable."),
        node("codex_execution", "Codex execution session", "current branch work", "AI-HANDOFF.md", "PRODUCT_RENTAL", "High for implementation throughput", ["maintainer", "AI quota"], "maintainer", "Model output is not independent evidence.", "rent", "Rent execution capacity while retaining verification."),
        node("repo_artifacts", "Repository artifacts", "git commits", "data/atlas/121q14-ledger.jsonl", "CUSTOM_BUILT", "High for reviewable work", ["maintainer", "reviewers"], "maintainer", "Artifacts can still overclaim if unvalidated.", "preserve", "Commit history remains audit surface."),
        node("local_validation", "Local validation", "tools and tests", "tools/validate_attention_distribution_compression.py", "CUSTOM_BUILT", "High before push", ["maintainer", "local compute"], "maintainer", "Local pass can differ from CI.", "automate", "Automate checks while preserving failure reports."),
        node("remote_ci", "Remote CI", "GitHub Actions", ".github/workflows", "COMMODITY_UTILITY", "High for reproducibility", ["GitHub Actions", "maintainer"], "maintainer", "Workflow pass is not truth.", "rent", "Use platform CI as workflow evidence."),
        node("draft_pr", "Draft PR", "GitHub PR", "reports/atlas/121Q14-baseline-latent-map-audit.md", "COMMODITY_UTILITY", "High for external review", ["reviewers", "maintainer"], "maintainer", "Mergeability is not acceptance.", "standardize", "Keep draft until GPT verification."),
        node("receipt", "1111 result receipt", "agent-results", "agent-results", "CUSTOM_BUILT", "High for cross-thread trace", ["maintainer"], "maintainer", "Receipt records facts but does not certify legal or empirical truth.", "preserve", "Write concise independent closeout.")
    ]
    edges = [
        edge("ops_user_command", "user_request", "command_bus", "information_flow", "agent-commands"),
        edge("ops_command_execution", "command_bus", "codex_execution", "control_flow", "AI-HANDOFF.md"),
        edge("ops_execution_artifacts", "codex_execution", "repo_artifacts", "information_flow", "git commits"),
        edge("ops_artifacts_local", "repo_artifacts", "local_validation", "evidence_flow", "tools"),
        edge("ops_artifacts_ci", "repo_artifacts", "remote_ci", "evidence_flow", ".github/workflows"),
        edge("ops_artifacts_pr", "repo_artifacts", "draft_pr", "control_flow", "GitHub PR"),
        edge("ops_pr_receipt", "draft_pr", "receipt", "information_flow", "agent-results")
    ]
    return {
        "id": "map-agent-delivery-operations",
        "map_type": "WARDLEY_STYLE_EVOLUTION",
        "as_of_commit": AS_OF_COMMIT,
        "observer_or_decision_owner": "maintainer coordinating AI execution, validation, PR review, and command-bus receipt",
        "decision_question": "Which delivery steps should remain human/accountable, which can be automated, and which are rented infrastructure?",
        "value_recipient_or_affected_subject": "user, maintainer, reviewers, and future agents",
        "layout_semantics": {
            "x_axis": "evolution stage of delivery component",
            "y_axis": "visibility to successful audited delivery",
            "visual_boundary": "workflow proximity is not evidence independence"
        },
        "data_sources": ["agent-commands", "AI-HANDOFF.md", "tools", ".github/workflows", "GitHub PRs", "agent-results"],
        "generation_method": "Deterministic static projection from observed delivery workflow surfaces.",
        "claim_ceiling": "derived_operations_navigation_view",
        "update_triggers": ["new command-bus protocol", "new CI workflow", "new validation gate", "review process change"],
        "nodes": nodes,
        "edges": edges,
        "projections": [
            {
                "id": "projection-agent-ops-static-v1",
                "input_sources": ["agent-commands", "AI-HANDOFF.md", "tools", ".github/workflows"],
                "projection_rule": "Map delivery workflow steps into nodes and information/control/evidence edges.",
                "deterministic": True,
                "reviewer": "Codex main session",
                "uncertainty": "Does not measure actual human cognitive load or future agent reliability."
            }
        ],
        "unmapped_residue": [
            {
                "id": "residue-human-review-quality",
                "description": "Actual quality and independence of future human/GPT review.",
                "reason": "Requires later review behavior, not current repository topology.",
                "next_condition": "Compare review findings against PR contents and CI outcomes."
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
        "maps": [
            sustainability_economics_map(),
            structural_architecture_map(),
            agent_operations_map()
        ]
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
