#!/usr/bin/env python3
"""Build a read-only identity-card projection from the Current registry and optional candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
REPO_ROOT = ROOT.parent
REGISTRY_REL = "ignition/data/operations/ignition-operation-capability-registry-r1.json"
CANDIDATES_REL = "ignition/data/operations/toolbox-candidate-cards-r0.json"
CARDS_REL = "ignition/data/operations/toolbox-identity-cards-r0.json"
HUMAN_REL = "ignition/TOOLBOX.md"
REGISTRY_PATH = REPO_ROOT / REGISTRY_REL
CANDIDATES_PATH = REPO_ROOT / CANDIDATES_REL


class IdentityCardError(ValueError):
    """Raised when a source registry or candidate card is incomplete or stale."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IdentityCardError(f"cannot load {path}: {exc}") from exc


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def file_blob_sha1(path: str) -> str:
    source = REPO_ROOT / path
    if not source.is_file():
        raise IdentityCardError(f"source path is missing: {path}")
    if source.is_symlink():
        raise IdentityCardError(f"source path must not be a symlink: {path}")
    return git_blob_sha1(source.read_bytes())


def source_ref_digest(path: str) -> dict[str, Any]:
    source = REPO_ROOT / path.rstrip("/")
    if not source.exists():
        raise IdentityCardError(f"source reference is missing: {path}")
    if source.is_symlink():
        raise IdentityCardError(f"source reference must not be a symlink: {path}")
    if source.is_file():
        return {"path": path, "hash_kind": "GIT_BLOB_SHA1", "sha1": git_blob_sha1(source.read_bytes())}
    entries = []
    for item in sorted(source.rglob("*")):
        if item.is_symlink():
            raise IdentityCardError(f"source tree contains a symlink: {item.relative_to(REPO_ROOT)}")
        if item.is_file():
            entries.append({
                "path": item.relative_to(REPO_ROOT).as_posix(),
                "sha256": hashlib.sha256(item.read_bytes()).hexdigest(),
            })
    payload = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"path": path, "hash_kind": "SHA256_FILE_TREE_R0", "sha256": hashlib.sha256(payload).hexdigest(), "file_count": len(entries)}


def build_cards() -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    candidates = load_json(CANDIDATES_PATH)
    registry_blob = git_blob_sha1(REGISTRY_PATH.read_bytes())
    if candidates.get("source_registry_path") != REGISTRY_REL:
        raise IdentityCardError("candidate cards point at a different Current registry")
    if candidates.get("source_registry_blob_sha1") != registry_blob:
        raise IdentityCardError("candidate cards are stale against the Current registry blob")

    manifests: dict[str, dict[str, Any]] = {}
    for manifest_path in registry["coverage"]["pack_manifest_paths"]:
        manifest = load_json(REPO_ROOT / manifest_path)
        manifests[manifest["pack_id"]] = manifest

    cards: list[dict[str, Any]] = []
    for operation in registry["operations"]:
        binding = operation["pack_binding"]
        manifest = manifests.get(binding["pack_id"]) if binding else None
        dependencies = [source["path"] for source in operation["authoritative_sources"]]
        dependencies.extend(operation["required_current_reads"])
        dependencies.extend(operation["applicable_governance"])
        dependencies.extend(check["path"] for check in operation["validation_checks"])
        if binding:
            dependencies.append(binding["manifest_path"])
        comparison_refs = sorted({
            REGISTRY_REL,
            *(source["path"] for source in operation["authoritative_sources"]),
            *(check["path"] for check in operation["validation_checks"]),
        })
        disposition_status = (
            "ACTIVE"
            if operation["current_status"] in {"CURRENT", "CURRENT_BOUNDED"} and operation["ai_callability"] != "STATUS_ONLY"
            else "ROUTER_EXCLUDED"
        )
        cards.append({
            "tool_id": operation["operation_id"],
            "card_kind": "CURRENT_OPERATION_REGISTRY_PROJECTION",
            "availability": "REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE",
            "lifecycle": operation["current_status"],
            "name": operation["public_name"],
            "can_do": operation["description"],
            "good_for": {
                "accepted_inputs": operation["accepted_input_types"],
                "declared_outputs": operation["output_types"],
                "operation_class": operation["operation_class"],
            },
            "cannot_do": operation["known_limits"],
            "only_if": [
                f"Current status is {operation['current_status']} and callability is {operation['ai_callability']}.",
                *operation["required_current_reads"],
            ],
            "counterindicated_when": [
                f"The request requires a mode other than {operation['default_execution_mode']}.",
                "A required Current authority or declared source is unavailable.",
            ],
            "accepted_input_types": operation["accepted_input_types"],
            "output_types": operation["output_types"],
            "permission": {
                "ai_callability": operation["ai_callability"],
                "execution_mode": operation["default_execution_mode"],
                "repository_mutation": operation["repository_mutation_permission"],
                "external_action": operation["external_action_permission"],
                "explicit_owner_authorization_required": operation["explicit_owner_authorization_required"],
            },
            "side_effects": {
                "repository_mutation_permission": operation["repository_mutation_permission"],
                "external_action_permission": operation["external_action_permission"],
            },
            "dependencies": sorted(set(dependencies)),
            "version": manifest["version"] if manifest else "UNKNOWN_NOT_DECLARED_BY_OPERATION_REGISTRY",
            "runtime_dependencies": manifest.get("optional_dependencies", []) if manifest else [],
            "estimated_cost": {"status": "UNKNOWN", "basis": "No comparable per-operation cost evidence is declared."},
            "alternatives": {"status": "NOT_MAPPED_IN_CURRENT_REGISTRY", "tool_ids": []},
            "replacement_candidates": [],
            "unique_remaining_use_cases": [],
            "comparison_evidence": {
                "status": "COMPARISON_UNKNOWN",
                "scope": "The Current operation projection contains no paired same-task outcome comparison; this card does not infer uniqueness, redundancy, or replacement value.",
                "compared_tool_ids": [],
                "evidence_refs": comparison_refs,
                "findings": ["Current lifecycle and callability remain sourced from the authoritative operation registry; no replacement or retirement decision is inferred."],
            },
            "deprecation_or_retirement_status": {
                "status": disposition_status,
                "basis": f"Preserve registry status {operation['current_status']} and callability {operation['ai_callability']}; no comparative retirement decision is recorded.",
            },
            "migration_and_rollback": {
                "migration_notes": ["Do not replace this Current operation from discovery-card similarity alone; compare the same task, permission, environment, and output contract first."],
                "rollback_steps": ["Apply any lifecycle change through the canonical operation registry and its governed dependent projections; restore the prior registry entry if the replacement regresses."],
            },
            "fallback": "Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.",
            "evidence": {
                "level": "DECLARATION_ONLY",
                "registry_path": REGISTRY_REL,
                "registry_blob_sha1": registry_blob,
                "source_refs": [
                    {"path": source["path"], "role": source["role"], "blob_sha1": file_blob_sha1(source["path"])}
                    for source in operation["authoritative_sources"]
                ],
                "validation_refs": [check["path"] for check in operation["validation_checks"]],
                "claim_ceiling": operation["claim_ceiling"],
            },
            "router_selectable_by_default": operation["current_status"] in {"CURRENT", "CURRENT_BOUNDED"} and operation["ai_callability"] != "STATUS_ONLY",
        })

    if not isinstance(candidates.get("candidates"), list):
        raise IdentityCardError("candidate card source must contain candidates")
    for candidate in candidates["candidates"]:
        if candidate.get("availability") != "EXPERIMENTAL_AVAILABLE":
            raise IdentityCardError(f"candidate is not marked experimental-available: {candidate.get('tool_id')}")
        if candidate.get("router_selectable_by_default") is not False:
            raise IdentityCardError(f"candidate must default off: {candidate.get('tool_id')}")
        source_path = candidate.get("source_path")
        source_blob = file_blob_sha1(source_path)
        source_refs = [source_ref_digest(reference["path"]) for reference in candidate.get("source_refs", [])]
        comparison_evidence = candidate.get("comparison_evidence", {
            "status": "COMPARISON_UNKNOWN",
            "scope": "No same-task comparative assessment is declared in this legacy candidate card.",
            "compared_tool_ids": [],
            "evidence_refs": [],
            "findings": ["Replacement value and remaining unique use cases are unknown; preserve uncertainty."],
        })
        retirement_status = candidate.get("deprecation_or_retirement_status", {
            "status": "COMPARISON_UNKNOWN",
            "basis": "No comparative evidence is declared in this legacy candidate card.",
        })
        migration_and_rollback = candidate.get("migration_and_rollback", {
            "migration_notes": ["Do not infer replacement from name or capability similarity; compare the same task and contract first."],
            "rollback_steps": ["Retain the previous candidate source and card until a reviewed comparison supports migration."],
        })
        cards.append({
            **candidate,
            "replacement_candidates": candidate.get("replacement_candidates", []),
            "unique_remaining_use_cases": candidate.get("unique_remaining_use_cases", []),
            "comparison_evidence": comparison_evidence,
            "deprecation_or_retirement_status": retirement_status,
            "migration_and_rollback": migration_and_rollback,
            "card_kind": "OPTIONAL_EXPERIMENTAL_TOOL",
            "source_blob_sha1": source_blob,
            "source_refs_with_hashes": source_refs,
            "candidate_catalog_path": CANDIDATES_REL,
            "candidate_catalog_blob_sha1": git_blob_sha1(CANDIDATES_PATH.read_bytes()),
            "current_registry_path": REGISTRY_REL,
            "current_registry_blob_sha1": registry_blob,
        })

    cards.sort(key=lambda card: card["tool_id"])
    return {
        "schema_version": "toolbox-identity-cards-r0",
        "authority_boundary": "GENERATED_DISCOVERY_PROJECTION; CURRENT_OPERATION_REGISTRY_AND_PINNED_CANDIDATE_CARDS_REMAIN_THE_SOURCES",
        "current_registry": {"path": REGISTRY_REL, "blob_sha1": registry_blob, "operation_count": len(registry["operations"])},
        "candidate_cards": {"path": CANDIDATES_REL, "blob_sha1": git_blob_sha1(CANDIDATES_PATH.read_bytes()), "candidate_count": len(candidates["candidates"])},
        "cards": cards,
        "card_count": len(cards),
        "claim_ceiling": "Discovery metadata only; registry declarations and experimental availability do not imply that a task should invoke a tool, that an operation ran, or that any result is true.",
    }


def render_human(document: dict[str, Any]) -> str:
    lines = [
        "# Ignition Toolbox / 点火工具箱",
        "",
        "> This page is generated from the canonical Current operation registry plus the pinned optional candidate-card source. It is a discovery surface, not a permission or truth authority.",
        ">",
        "> Current operation entries are registered capabilities; the registry does not prove that every entry is a standalone executable in this environment. Experimental tools are opt-in and default off.",
        "",
        f"Current operation registry: {document['current_registry']['operation_count']} entries · `blob {document['current_registry']['blob_sha1']}`.",
        f"Optional experimental tools: {document['candidate_cards']['candidate_count']} · `blob {document['candidate_cards']['blob_sha1']}`.",
        "",
        "Machine-readable cards: [toolbox-identity-cards-r0.json](data/operations/toolbox-identity-cards-r0.json).",
        "Current operation authority: [ignition-operation-capability-registry-r1.json](data/operations/ignition-operation-capability-registry-r1.json).",
        "",
        "## Registered operations",
        "",
    ]
    for card in document["cards"]:
        if card["card_kind"] != "CURRENT_OPERATION_REGISTRY_PROJECTION":
            continue
        comparison = card["comparison_evidence"]
        disposition = card["deprecation_or_retirement_status"]
        migration = card["migration_and_rollback"]
        lines.extend([
            f"### `{card['tool_id']}` · {card['name']['zh']} / {card['name']['en']}",
            "",
            f"- State: `{card['lifecycle']}` · callability `{card['permission']['ai_callability']}` · availability `{card['availability']}`",
            f"- Can do: {card['can_do']}",
            f"- Suitable for: inputs `{', '.join(card['good_for']['accepted_inputs'])}`; declared outputs `{', '.join(card['good_for']['declared_outputs'])}`; class `{card['good_for']['operation_class']}`.",
            f"- Use only if: {'; '.join(card['only_if'])}",
            f"- Do not use when: {'; '.join(card['counterindicated_when'])}",
            f"- Inputs: {', '.join(card['accepted_input_types'])}",
            f"- Outputs: {', '.join(card['output_types'])}",
            f"- Mode and permissions: `{card['permission']['execution_mode']}`; repository `{card['permission']['repository_mutation']}`; external `{card['permission']['external_action']}`",
            f"- Side effects: repository `{card['side_effects']['repository_mutation_permission']}`; external `{card['side_effects']['external_action_permission']}`.",
            f"- Dependencies: {', '.join(card['dependencies']) or 'none declared'}; runtime `{', '.join(card['runtime_dependencies']) or 'none declared'}`; version `{card['version']}`.",
            f"- Cost: `{card['estimated_cost']['status']}` · {card['estimated_cost']['basis']}",
            f"- Alternatives: `{card['alternatives']['status']}` · {', '.join(card['alternatives']['tool_ids']) or 'none mapped'}.",
            f"- Replacement candidates: {', '.join(card['replacement_candidates']) or 'none established'}.",
            f"- Unique remaining use cases: {'; '.join(card['unique_remaining_use_cases']) or 'not established'}.",
            f"- Comparison evidence: `{comparison['status']}` · {comparison['scope']} Comparators: {', '.join(comparison['compared_tool_ids']) or 'none recorded'}; refs: {', '.join(comparison['evidence_refs'])}; findings: {'; '.join(comparison['findings'])}.",
            f"- Deprecation/retirement: `{disposition['status']}` · {disposition['basis']}",
            f"- Migration/rollback: {'; '.join(migration['migration_notes'])} / {'; '.join(migration['rollback_steps'])}.",
            f"- Fallback: {card['fallback']}",
            f"- Limits: {'; '.join(card['cannot_do'])}",
            f"- Evidence: `{card['evidence']['level']}` · registry blob `{card['evidence']['registry_blob_sha1']}` · validation `{', '.join(card['evidence']['validation_refs']) or 'none declared'}`.",
            f"- Route default: `{str(card['router_selectable_by_default']).lower()}` · claim ceiling: {card['evidence']['claim_ceiling']}",
            "",
        ])
    lines.extend(["## Optional experimental tools", ""])
    for card in document["cards"]:
        if card["card_kind"] != "OPTIONAL_EXPERIMENTAL_TOOL":
            continue
        validation_links = ", ".join(
            "[%s](%s)" % (path, path.removeprefix("ignition/"))
            for path in card["validation"]["focused_checks"]
        )
        alternatives = "; ".join(
            f"`{row['tool_id']}` ({row['relationship']}): {row['reason']}"
            for row in card["alternatives"]
        ) or "none mapped"
        source_refs = ", ".join(f"`{row['path']}` ({row['role']})" for row in card["source_refs"])
        network_hosts = ", ".join(card["permissions"].get("network_hosts", [])) or "none"
        comparison = card["comparison_evidence"]
        disposition = card["deprecation_or_retirement_status"]
        migration = card["migration_and_rollback"]
        lines.extend([
            f"### `{card['tool_id']}` · {card['display_name']['zh']} / {card['display_name']['en']}",
            "",
            f"- State: `{card['availability']}` / `{card['lifecycle']}` · version `{card['version']}` · license `{card['license']}` · maintainer `{card['maintainer']}` · source blob `{card['source_blob_sha1']}`.",
            f"- Can do: {card['description']}",
            f"- Good for: {'; '.join(card['good_for'])}",
            f"- Not for: {'; '.join(card['not_for'])}",
            f"- Use only if: {'; '.join(card['only_if'])}",
            f"- Do not use when: {'; '.join(card['counterindicated_when'])}",
            f"- Inputs → outputs: {', '.join(card['accepted_input_types'])} → {', '.join(card['output_types'])}",
            f"- Permissions: `{card['execution_mode']}` / `{card['permission_mode']}` · explicit Owner authorization required `{str(card['explicit_owner_authorization_required']).lower()}` · reads `{', '.join(card['permissions']['read_paths']) or 'none'}` · writes `{', '.join(card['permissions']['write_paths']) or 'none'}` · network `{str(card['permissions']['network']).lower()}` hosts `{network_hosts}` · secrets `{str(card['permissions']['secrets']).lower()}` · billing `{str(card['permissions']['billing']).lower()}` · external actions `{str(card['permissions']['external_actions']).lower()}.",
            f"- Side effects: {', '.join(card['side_effects']) or 'none declared'}.",
            f"- Dependencies: {', '.join(card['dependencies']) or 'none declared'}; runtime dependencies: {', '.join(card['runtime_dependencies']) or 'none declared'}.",
            f"- Cost: `{card['estimated_cost']['status']}` · {card['estimated_cost']['basis']}",
            f"- Alternatives: {alternatives}.",
            f"- Replacement candidates: {', '.join(card['replacement_candidates']) or 'none established'}.",
            f"- Unique remaining use cases: {'; '.join(card['unique_remaining_use_cases']) or 'not established'}.",
            f"- Comparison evidence: `{comparison['status']}` · {comparison['scope']} Comparators: {', '.join(comparison['compared_tool_ids']) or 'none recorded'}; refs: {', '.join(comparison['evidence_refs'])}; findings: {'; '.join(comparison['findings'])}.",
            f"- Deprecation/retirement: `{disposition['status']}` · {disposition['basis']}",
            f"- Migration/rollback: {'; '.join(migration['migration_notes'])} / {'; '.join(migration['rollback_steps'])}.",
            f"- Invocation example: `{card['entrypoint']}`",
            f"- Fallback: {card['fallback']}",
            f"- Evidence: `{card['evidence_level']}` · source refs {source_refs}; focused checks {validation_links}; negative controls: {'; '.join(card['validation']['negative_controls'])}.",
            f"- Route default: `{str(card['router_selectable_by_default']).lower()}` · conditions: {'; '.join(card['router_conditions'])}.",
            f"- Claim ceiling: {card['claim_ceiling']}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="write the deterministic JSON and Markdown projections")
    group.add_argument("--check", action="store_true", help="verify both checked-in projections are current")
    group.add_argument("--markdown", action="store_true", help="print the human directory to stdout")
    args = parser.parse_args(argv)
    try:
        document = build_cards()
    except IdentityCardError as exc:
        print(f"TOOLBOX_IDENTITY_CARDS_INVALID: {exc}", file=sys.stderr)
        return 1
    machine = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    human = render_human(document)
    machine_path = REPO_ROOT / CARDS_REL
    human_path = REPO_ROOT / HUMAN_REL
    if args.markdown:
        sys.stdout.write(human)
        return 0
    if args.check:
        if not machine_path.is_file() or machine_path.read_text(encoding="utf-8") != machine:
            print("TOOLBOX_IDENTITY_CARDS_STALE: " + CARDS_REL, file=sys.stderr)
            return 1
        if not human_path.is_file() or human_path.read_text(encoding="utf-8") != human:
            print("TOOLBOX_DIRECTORY_STALE: " + HUMAN_REL, file=sys.stderr)
            return 1
        print(f"TOOLBOX_IDENTITY_CARDS_OK current_operations={document['current_registry']['operation_count']} experimental={document['candidate_cards']['candidate_count']} cards={document['card_count']}")
        return 0
    machine_path.write_text(machine, encoding="utf-8")
    human_path.write_text(human, encoding="utf-8")
    print(f"TOOLBOX_IDENTITY_CARDS_WRITTEN current_operations={document['current_registry']['operation_count']} experimental={document['candidate_cards']['candidate_count']} cards={document['card_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
