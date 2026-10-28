#!/usr/bin/env python3
"""Build the Task 119 boundary manifest from the live component registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/operations/project-components.json"
OUTPUT = ROOT / "data/architecture/agentization-boundary-r0.json"

ROLES = [
    "GENERIC_KERNEL",
    "AGENT_RUNTIME",
    "KNOWLEDGE_DOMAIN",
    "DOMAIN_PACK",
    "HUMAN_PUBLICATION",
    "PLATFORM_TOOLING",
    "HISTORICAL_OR_LEGACY",
]

GENERIC_IDS = {
    "owner_human",
    "charter",
    "charter_system_r1",
    "epistemic_governance_kernel",
    "agentization_boundary_r0",
    "agent_kernel_r0",
    "agent_profile_r0",
    "domain_pack_contract",
    "no_truth_upgrade",
    "no_totality_proof",
}
RUNTIME_IDS = {
    "agent_runtime_r0",
    "runtime_environment",
    "runtime_memory_loop",
}
PACK_IDS = {
    "knowledge_domain_pack",
    "research_pack_reos_light",
    "writing_pack",
    "maintenance_pack",
    "nonknowledge_pilot",
}
ADDED_R0_IDS = {
    "agentization_boundary_r0",
    "agent_kernel_r0",
    "agent_runtime_r0",
    "agent_profile_r0",
    "runtime_environment",
    "runtime_memory_loop",
    "domain_pack_contract",
    "nonknowledge_pilot",
}


def classify(component: dict) -> tuple[str, list[str], str, str, str]:
    cid = component["component_id"]
    ctype = component["component_type"]
    lifecycle = component["lifecycle"]["status"]
    if lifecycle == "historical" or ctype == "historical_asset":
        primary = "HISTORICAL_OR_LEGACY"
    elif cid in GENERIC_IDS:
        primary = "GENERIC_KERNEL"
    elif cid in RUNTIME_IDS:
        primary = "AGENT_RUNTIME"
    elif cid in PACK_IDS:
        primary = "DOMAIN_PACK"
    elif ctype == "foundation_core" or ctype == "architecture_layer":
        primary = "KNOWLEDGE_DOMAIN"
    elif ctype in {"cross_layer_control_plane", "model_projection", "feedback_interface"}:
        primary = "DOMAIN_PACK"
    elif ctype == "publication_chain" or ctype == "front_door":
        primary = "HUMAN_PUBLICATION"
    elif ctype == "interpretation_boundary":
        primary = "GENERIC_KERNEL"
    elif ctype == "governance_constraint":
        primary = "GENERIC_KERNEL"
    else:
        primary = "PLATFORM_TOOLING"

    secondary: list[str] = []
    if primary == "KNOWLEDGE_DOMAIN" and ctype in {"architecture_layer", "foundation_core"}:
        secondary.append("DOMAIN_PACK")
    if primary == "DOMAIN_PACK" and cid in {"knowledge_domain_pack", "research_pack_reos_light", "writing_pack"}:
        secondary.append("AGENT_RUNTIME")
    if primary == "HUMAN_PUBLICATION" and cid in {"owner_human", "readme", "current_state", "ai_guide"}:
        secondary.append("GENERIC_KERNEL")
    if primary == "GENERIC_KERNEL" and ctype == "governance_constraint":
        secondary.append("PLATFORM_TOOLING")

    if primary == "GENERIC_KERNEL":
        domain, direction = "domain_neutral", "OWNS_GENERIC_CONTRACT"
    elif primary == "AGENT_RUNTIME":
        domain, direction = "domain_neutral", "CONSUMES_GENERIC_CONTRACT"
    elif primary == "KNOWLEDGE_DOMAIN":
        domain, direction = "knowledge", "CONSUMES_GENERIC_CONTRACT"
    elif primary == "DOMAIN_PACK":
        domain = "research" if "research" in cid or cid in {"q12", "q13", "q14"} else ("writing" if "writing" in cid or cid in {"zhiyuan_method", "accepted_work"} else "knowledge")
        direction = "CONSUMES_GENERIC_CONTRACT"
    elif primary == "HUMAN_PUBLICATION":
        domain, direction = "publication", "CONSUMES_DOMAIN_OUTPUT"
    elif primary == "HISTORICAL_OR_LEGACY":
        domain, direction = "historical", "NO_CURRENT_DEPENDENCY"
    else:
        domain, direction = "platform", "SUPPORTS_MULTIPLE_COMPONENTS"

    if cid in ADDED_R0_IDS:
        disposition = "ADD_R0_COMPONENT"
    elif cid in {"knowledge_domain_pack", "research_pack_reos_light", "writing_pack", "maintenance_pack", "nonknowledge_pilot"}:
        disposition = "REF_ONLY_NO_MOVE"
    elif primary == "HISTORICAL_OR_LEGACY":
        disposition = "HISTORICAL_NO_MOVE"
    else:
        disposition = "KEEP_CURRENT_PATH_R0"
    reason = {
        "GENERIC_KERNEL": "keeps a domain-neutral authority, boundary or non-escalation contract; it does not own domain semantics",
        "AGENT_RUNTIME": "owns the provider-neutral execution loop while delegating domain work to packs",
        "KNOWLEDGE_DOMAIN": "contains knowledge-specific objects, evidence, formal semantics or their existing governance",
        "DOMAIN_PACK": "is an optional bounded capability/feedback pack consumed by the runtime",
        "HUMAN_PUBLICATION": "is an owner-facing or reader-facing expression and navigation surface",
        "PLATFORM_TOOLING": "supports repository generation, validation or synchronization without being domain authority",
        "HISTORICAL_OR_LEGACY": "is retained for provenance or historical compatibility and does not define the current runtime",
    }[primary]
    return primary, secondary, domain, direction, reason


def build() -> dict:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    records = []
    for component in registry["components"]:
        primary, secondary, domain, direction, reason = classify(component)
        paths = component.get("path_patterns") or [component["canonical_target"]]
        cid = component["component_id"]
        disposition = "KEEP_CURRENT_PATH_R0"
        if cid in ADDED_R0_IDS:
            disposition = "ADD_R0_COMPONENT"
        elif cid in {"knowledge_domain_pack", "research_pack_reos_light", "writing_pack", "maintenance_pack", "nonknowledge_pilot"}:
            disposition = "REF_ONLY_NO_MOVE"
        elif primary == "HISTORICAL_OR_LEGACY":
            disposition = "HISTORICAL_NO_MOVE"
        records.append(
            {
                "component_id": cid,
                "current_path": paths[0],
                "canonical_ref": component["canonical_target"],
                "primary_role": primary,
                "secondary_roles": secondary,
                "domain_binding": domain,
                "kernel_dependency_direction": direction,
                "current_move_disposition": disposition,
                "reason": reason,
            }
        )
    # Keep the disposition expression above explicit in the emitted contract;
    # the registry remains the source of component identity and count.
    for record in records:
        if record["component_id"] in ADDED_R0_IDS:
            record["reason"] += "; newly added R0 boundary asset, no existing domain tree was moved"
        elif record["component_id"] in {"knowledge_domain_pack", "research_pack_reos_light", "writing_pack", "maintenance_pack", "nonknowledge_pilot"}:
            record["reason"] += "; adapter/reference only in R0, existing source tree remains in place"
    return {
        "manifest_version": "R0",
        "task_id": "IGNITION-20260815-119",
        "baseline": {
            "repository": "Arvin-liu/when-systems-catch-fire",
            "main_sha": "4f4358ef09d1871a48d7e32575a63453130b333c",
            "registry_ref": "data/operations/project-components.json",
        },
        "role_vocabulary": ROLES,
        "components": records,
        "physical_migration": {
            "performed": False,
            "scope": "new boundary/runtime contracts and pilots only",
            "residual": [
                "Foundation, Evidence, REOS, writing and publication trees remain at their current paths",
                "future physical pack extraction requires a separately authorized task",
            ],
        },
        "invariants": [
            "Kernel does not import a domain pack",
            "Runtime does not require a provider or model brand",
            "Permission is checked before every action and unknown capability fails closed",
            "Checkpoint/resume does not upgrade a blocked or failed validation state",
            "KERNEL_NON_ESCALATION blocks lifecycle, executor selection, generic permission, checkpoint/resume, Owner acceptance and Kernel definition upgrades",
            "K13_ASSERTION_NON_ESCALATION remains the knowledge-specific assertion projection",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
            raise SystemExit("agentization boundary manifest is stale; run the generator")
        print(f"AGENTIZATION_BOUNDARY_DERIVED_OK components={len(build()['components'])}")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
