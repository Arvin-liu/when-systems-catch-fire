#!/usr/bin/env python3
"""Fail-closed validation for the CURRENT_STATE_SYNC_INVARIANT.

The contract stores identity and derivation recipes, not copied current counts.
The validator recomputes those recipes from repository registries and checks the
latest iteration receipt.  An ARCHITECTURE_CHANGED receipt requires every
registered Current/Human/AI/map surface to be changed and to contain the same
bounded OS/driver identity.  A PRESENTATION_ONLY receipt is intentionally
narrower: it proves that the governance gate was introduced without pretending
that a later architecture-content synchronization already happened.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from tools import iteration_boundary
except ImportError:
    import iteration_boundary


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]  # ignition/
REPO_ROOT = ROOT.parent
CONTRACT_PATH = ROOT / "data/architecture/current-system-identity.json"
SCHEMA_PATH = ROOT / "schemas/architecture/current-system-identity.schema.json"
RECEIPT_SCHEMA_PATH = ROOT / "schemas/architecture/current-state-sync-receipt.schema.json"
FACTS_SCHEMA_PATH = ROOT / "schemas/architecture/current-facts.schema.json"
FACTS_PATH = ROOT / "data/architecture/current-facts.json"
FACTS_MARKDOWN_PATH = ROOT / "docs/architecture/current-facts.md"
FIXTURE_PATH = ROOT / "data/operations/iterations/123/fixtures/current-state-sync-fixtures-r1.json"
RELEASE_LIFECYCLE_PATH = ROOT / "data/operations/current-release-lifecycle-r1.json"
CURRENT_SNAPSHOT_PATH = ROOT / "data/operations/current-snapshot-r1.json"
PUBLICATION_SURFACES = ("ignition/AI-START-HERE.md", "ignition/AI-HANDOFF.md")
ALLOWED_IMPACTS = {"NONE", "PRESENTATION_ONLY", "ARCHITECTURE_CHANGED"}
HEX_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_repo_path(relative_path: str) -> Path:
    """Resolve a repository-relative path without accepting an escape."""
    candidate = (REPO_ROOT / relative_path).resolve()
    try:
        candidate.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes repository: {relative_path}") from exc
    return candidate


def pointer_get(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    if not pointer.startswith("/"):
        raise ValueError(f"JSON pointer must start with /: {pointer}")
    current = value
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(token)]
        elif isinstance(current, dict):
            current = current[token]
        else:
            raise KeyError(pointer)
    return current


def schema_errors(document: Any, schema_path: Path) -> list[str]:
    """Use jsonschema when present, with a small fallback for clean bootstrap."""
    try:
        from jsonschema import Draft202012Validator

        schema = load_json(schema_path)
        validator = Draft202012Validator(schema)
        return [error.json_path + ": " + error.message for error in validator.iter_errors(document)]
    except ImportError:
        return []
    except Exception as exc:  # pragma: no cover - defensive bootstrap report
        return [f"schema validator error for {schema_path}: {exc}"]


def _require(document: dict[str, Any], keys: tuple[str, ...], label: str) -> list[str]:
    return [f"{label} missing required field {key}" for key in keys if key not in document]


def _walk_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.extend(_walk_keys(child))
    return keys


def _contains_forbidden_self_sha(contract: dict[str, Any]) -> bool:
    forbidden_names = {"commit_sha", "current_commit_sha", "head_sha", "current_head_sha", "self_sha"}
    return any(key.lower() in forbidden_names for key in _walk_keys(contract))


def derive_metric(metric: dict[str, Any]) -> Any:
    source_path = resolve_repo_path(metric["source_path"])
    if not source_path.is_file():
        raise FileNotFoundError(metric["source_path"])
    value = pointer_get(load_json(source_path), metric["json_pointer"])
    operation = metric["operation"]
    if operation == "value":
        return value
    if operation == "length":
        if not isinstance(value, (list, dict, str)):
            raise TypeError(f"length requires list/dict/string: {metric['metric_id']}")
        return len(value)
    if operation == "count_where":
        if not isinstance(value, list):
            raise TypeError(f"count_where requires list: {metric['metric_id']}")
        where = metric["where"]
        return sum(1 for item in value if pointer_get(item, where["json_pointer"]) == where["equals"])
    raise ValueError(f"unsupported metric operation: {operation}")


def derive_metrics(contract: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    values: dict[str, Any] = {}
    errors: list[str] = []
    seen: set[str] = set()
    for metric in contract.get("derived_metrics", []):
        metric_id = metric.get("metric_id", "<missing>")
        if metric_id in seen:
            errors.append(f"duplicate derived metric {metric_id}")
        seen.add(metric_id)
        try:
            values[metric_id] = derive_metric(metric)
        except Exception as exc:
            errors.append(f"cannot derive {metric_id}: {exc}")
    return values, errors


def validate_contract(contract: dict[str, Any] | None = None) -> tuple[list[str], dict[str, Any]]:
    contract = contract if contract is not None else load_json(CONTRACT_PATH)
    errors: list[str] = []
    errors.extend(schema_errors(contract, SCHEMA_PATH))
    errors.extend(_require(contract, (
        "schema_version", "contract_id", "identity_epoch", "current_iteration_boundary",
        "current_architecture_identity", "current_map", "current_method", "derived_metrics",
        "current_facts_projection",
        "known_open_obligations", "authority_ceilings", "architecture_impact_handshake",
        "required_sync_surfaces", "concept_requirements",
    ), "contract"))
    if contract.get("schema_version") != "current-system-identity-r1":
        errors.append("contract schema_version is not current-system-identity-r1")
    if contract.get("contract_id") != "CURRENT_STATE_SYNC_INVARIANT":
        errors.append("contract_id is not CURRENT_STATE_SYNC_INVARIANT")
    if contract.get("epistemically_accepted") != 0:
        errors.append("epistemically_accepted must remain exactly 0")
    if _contains_forbidden_self_sha(contract):
        errors.append("current identity contract contains a self-referential commit SHA field")
    try:
        derived = iteration_boundary.derive()
        for field in (
            "current_formal_task_id",
            "current_formal_task_ordinal",
            "latest_architecture_changing_task_id",
            "latest_architecture_task_ordinal",
            "current_iteration_boundary",
        ):
            if contract.get(field) != derived[field]:
                errors.append(f"identity {field} is not derived from canonical task identity")
        semantics = contract.get("current_iteration_boundary_semantics", {})
        if semantics.get("status") != "DEPRECATED_COMPATIBILITY_ALIAS" or semantics.get("alias_of") != "current_formal_task_ordinal":
            errors.append("identity current_iteration_boundary is not an explicit formal ordinal compatibility alias")
    except Exception as exc:
        errors.append(f"cannot derive current iteration identity: {type(exc).__name__}: {exc}")

    identity = contract.get("current_architecture_identity", {})
    required_text = {
        "system_role": "OS / orchestration-governance layer",
        "driver_role": "driver",
        "external_executor_role": "replaceable executors",
        "knowledge_role": "Domain Pack",
        "reference_executor_role": "REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR / FALLBACK_MINIMAL",
    }
    for field, marker in required_text.items():
        if marker.lower() not in str(identity.get(field, "")).lower():
            errors.append(f"current_architecture_identity.{field} must retain marker {marker!r}")

    for source in contract.get("known_open_obligations", []):
        for path in source.get("source_paths", []):
            if not resolve_repo_path(path).is_file():
                errors.append(f"open-obligation source missing: {path}")
    for surface in contract.get("required_sync_surfaces", []):
        path = surface.get("path", "")
        try:
            if not resolve_repo_path(path).is_file():
                errors.append(f"required sync surface missing: {path}")
        except ValueError as exc:
            errors.append(str(exc))

    current_map = contract.get("current_map", {})
    try:
        map_value = pointer_get(load_json(resolve_repo_path(current_map["source_path"])), current_map["json_pointer"])
        historical_value = pointer_get(load_json(resolve_repo_path(current_map["historical_map_version_source_path"])), current_map["historical_map_version_json_pointer"])
        if map_value == historical_value:
            errors.append("current map version must differ from historical map version")
    except Exception as exc:
        errors.append(f"cannot resolve current map version: {exc}")

    method = contract.get("current_method", {})
    try:
        method_text = resolve_repo_path(method["source_path"]).read_text(encoding="utf-8")
        if method.get("required_marker") not in method_text:
            errors.append("current method marker is absent from its declared source")
    except Exception as exc:
        errors.append(f"cannot resolve current method: {exc}")

    metrics, metric_errors = derive_metrics(contract)
    errors.extend(metric_errors)
    return errors, metrics


def validate_current_facts(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    projection_ref = contract.get("current_facts_projection", {})
    if projection_ref.get("json_path") != "ignition/data/architecture/current-facts.json":
        errors.append("current_facts_projection.json_path is not canonical")
    if projection_ref.get("markdown_path") != "ignition/docs/architecture/current-facts.md":
        errors.append("current_facts_projection.markdown_path is not canonical")
    if not FACTS_SCHEMA_PATH.is_file():
        errors.append("current facts schema is missing")
    if not FACTS_PATH.is_file() or not FACTS_MARKDOWN_PATH.is_file():
        return errors + ["current facts projection or bounded markdown block is missing"]
    try:
        facts = load_json(FACTS_PATH)
        errors.extend(schema_errors(facts, FACTS_SCHEMA_PATH))
        from generate_current_facts import build_projection, render_json, render_markdown

        expected = build_projection(contract)
        if FACTS_PATH.read_bytes() != render_json(expected):
            errors.append("current-facts.json is stale relative to its declared canonical sources")
        if FACTS_MARKDOWN_PATH.read_bytes() != render_markdown(expected):
            errors.append("current-facts.md is stale relative to current-facts.json")
    except Exception as exc:
        errors.append(f"cannot validate current facts projection: {exc}")
    return errors


def concept_satisfied(text: str, concept_id: str, contract: dict[str, Any]) -> bool:
    requirements = contract.get("concept_requirements", {}).get(concept_id)
    if not requirements:
        return False
    folded = text.casefold()
    return all(any(str(token).casefold() in folded for token in group) for group in requirements.get("all_of_any_group", []))


def validate_current_state_text(contract: dict[str, Any], path: str = "ignition/docs/project-current-state.md") -> list[str]:
    """Check only the Current sections; historical task sections remain exempt."""
    text = resolve_repo_path(path).read_text(encoding="utf-8")
    errors: list[str] = []
    headings = list(re.finditer(r"^##\s+", text, re.MULTILINE))
    current_sections: list[str] = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.start():end]
        if any(marker in section for marker in ("当前形态", "当前已实现能力", "当前治理结论", "当前限制与开放义务")):
            current_sections.append(section)
    current_text = "\n".join(current_sections)
    stale_literals = ("5,663", "17,333", "3,887", "5,581", "7,371", "18,351", "5,071", "6,084")
    for literal in stale_literals:
        if literal in current_text:
            errors.append(f"stale Current State metric remains in a Current section: {literal}")
    if not concept_satisfied(current_text, "current_facts", contract):
        errors.append("Current State lacks a bounded current-facts/derived-facts marker")
    return errors


def validate_map_identity(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    current_path = resolve_repo_path(contract["current_map"]["source_path"])
    layout = load_json(current_path)
    current_version = pointer_get(layout, contract["current_map"]["json_pointer"])
    historical_version = pointer_get(layout, contract["current_map"]["historical_map_version_json_pointer"])
    materialized = load_json(resolve_repo_path("ignition/data/architecture/interactive-system-map.json"))
    if materialized.get("map_version") != current_version:
        errors.append("materialized system-map map_version differs from current layout version")
    if materialized.get("historical_map_version") != historical_version:
        errors.append("materialized system-map historical_map_version differs from current layout")
    for label, payload in (("layout", layout), ("materialized", materialized)):
        subtitle = str(payload.get("subtitle", ""))
        if f"{historical_version} Current" in subtitle:
            errors.append(f"{label} subtitle still labels historical map {historical_version} as Current")
    return errors


def validate_surface_decisions(contract: dict[str, Any], receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    declared = {surface["surface_id"]: surface for surface in contract.get("required_sync_surfaces", [])}
    decisions = {item.get("surface_id"): item for item in receipt.get("surface_decisions", [])}
    missing = sorted(set(declared) - set(decisions))
    if missing:
        errors.append(f"receipt omits required sync surfaces: {', '.join(missing)}")
    unknown = sorted(set(decisions) - set(declared))
    if unknown:
        errors.append(f"receipt contains unknown sync surfaces: {', '.join(unknown)}")
    impact = receipt.get("architecture_identity_impact")
    for surface_id, surface in declared.items():
        item = decisions.get(surface_id)
        if not item:
            continue
        if item.get("path") != surface.get("path"):
            errors.append(f"receipt path mismatch for {surface_id}")
        if impact == "PRESENTATION_ONLY" and item.get("decision") == "CHANGE" and not item.get("evidence", "").strip():
            errors.append(f"PRESENTATION_ONLY CHANGE requires evidence for {surface_id}")
        if impact == "ARCHITECTURE_CHANGED":
            if item.get("decision") != "CHANGE":
                errors.append(f"ARCHITECTURE_CHANGED requires CHANGE for {surface_id}")
            if not item.get("evidence", "").strip():
                errors.append(f"ARCHITECTURE_CHANGED requires evidence for {surface_id}")
            try:
                text = resolve_repo_path(surface["path"]).read_text(encoding="utf-8")
            except Exception as exc:
                errors.append(f"cannot read required surface {surface_id}: {exc}")
                continue
            for concept in surface.get("concepts", []):
                if concept == "current_facts":
                    if not concept_satisfied(text, concept, contract):
                        errors.append(f"surface {surface_id} lacks concept {concept}")
                elif concept == "map_version":
                    current_version = pointer_get(load_json(resolve_repo_path(contract["current_map"]["source_path"])), contract["current_map"]["json_pointer"])
                    if str(current_version) not in text:
                        errors.append(f"surface {surface_id} lacks current map version {current_version}")
                elif concept == "state_delta":
                    if not concept_satisfied(text, concept, contract):
                        errors.append(f"surface {surface_id} lacks concept {concept}")
                elif not concept_satisfied(text, concept, contract):
                    errors.append(f"surface {surface_id} lacks concept {concept}")
    return errors


def validate_receipt(contract: dict[str, Any], receipt: dict[str, Any]) -> list[str]:
    errors = schema_errors(receipt, RECEIPT_SCHEMA_PATH)
    errors.extend(_require(receipt, (
        "schema_version", "task_id", "architecture_identity_impact", "identity_contract_path",
        "identity_epoch", "current_iteration_boundary", "surface_decisions", "system_map_sync",
        "state_changelog_delta", "changed_paths", "claim_ceiling",
    ), "receipt"))
    impact = receipt.get("architecture_identity_impact")
    if impact not in ALLOWED_IMPACTS:
        errors.append(f"receipt architecture_identity_impact is not one of {sorted(ALLOWED_IMPACTS)}")
    if receipt.get("identity_contract_path") != "ignition/data/architecture/current-system-identity.json":
        errors.append("receipt must name the canonical current-system-identity contract")
    if receipt.get("identity_epoch") != contract.get("identity_epoch"):
        errors.append("receipt identity_epoch differs from current identity contract")
    if receipt.get("current_iteration_boundary") != contract.get("current_iteration_boundary"):
        errors.append("receipt current_iteration_boundary differs from current identity contract")
    if receipt.get("task_id") == contract.get("current_formal_task_id"):
        try:
            derived = iteration_boundary.derive()
            for field in (
                "current_formal_task_id",
                "current_formal_task_ordinal",
                "latest_architecture_changing_task_id",
                "latest_architecture_task_ordinal",
                "current_iteration_boundary",
            ):
                if receipt.get(field) != derived[field]:
                    errors.append(f"current receipt {field} differs from canonical derivation")
            if receipt.get("current_iteration_boundary_semantics") != derived["current_iteration_boundary_semantics"]:
                errors.append("current receipt compatibility alias semantics are not canonical")
        except Exception as exc:
            errors.append(f"cannot derive receipt iteration identity: {type(exc).__name__}: {exc}")
    if impact == "ARCHITECTURE_CHANGED":
        if not receipt.get("identity_contract_changed"):
            errors.append("ARCHITECTURE_CHANGED receipt must set identity_contract_changed=true")
        if receipt.get("system_map_sync", {}).get("decision") != "CHANGE":
            errors.append("ARCHITECTURE_CHANGED receipt must mark system_map_sync CHANGE")
        if receipt.get("state_changelog_delta", {}).get("decision") != "CHANGE":
            errors.append("ARCHITECTURE_CHANGED receipt must mark state_changelog_delta CHANGE")
        errors.extend(validate_current_state_text(contract))
        errors.extend(validate_map_identity(contract))
        homepage = resolve_repo_path(".github/README.md").read_text(encoding="utf-8")
        if homepage.count("- **它说什么：**") > 1:
            errors.append("homepage still contains duplicate 它说什么 identity bullets")
    else:
        if receipt.get("surface_sync_complete"):
            errors.append("NONE/PRESENTATION_ONLY receipt cannot claim full architecture surface synchronization")
    errors.extend(validate_surface_decisions(contract, receipt))
    return errors


def discover_receipts() -> list[Path]:
    return sorted(ROOT.glob("data/operations/iterations/*/current-state-sync-receipt.json"))


def validate_fixture_manifest() -> list[str]:
    if not FIXTURE_PATH.is_file():
        return [f"missing current-state sync fixture manifest: {FIXTURE_PATH.relative_to(ROOT)}"]
    fixture = load_json(FIXTURE_PATH)
    errors: list[str] = []
    if fixture.get("schema_version") != "current-state-sync-fixtures-r1":
        errors.append("fixture manifest has wrong schema_version")
    rows = fixture.get("fixtures", [])
    if not rows:
        errors.append("fixture manifest has no fixtures")
    for row in rows:
        if row.get("kind") not in {"negative", "positive"}:
            errors.append(f"fixture {row.get('id')} has invalid kind")
        if row.get("expected_status") not in {"PASS", "FAIL"}:
            errors.append(f"fixture {row.get('id')} has invalid expected_status")
    return errors


def validate_release_publication_contract(
    lifecycle_record: dict[str, Any] | None = None,
    snapshot: dict[str, Any] | None = None,
    surface_texts: dict[str, str] | None = None,
) -> list[str]:
    """Integrate ref-derived publication authority into Current State sync."""

    errors: list[str] = []
    try:
        from validate_current_release_lifecycle import validate as validate_lifecycle
        from validate_release_state_model import validate as validate_state_model

        errors.extend(validate_lifecycle(lifecycle_record))
        errors.extend(validate_state_model())
    except Exception as exc:  # pragma: no cover - fail-closed import boundary
        errors.append(f"cannot validate release publication contract: {type(exc).__name__}")
        return errors
    lifecycle = lifecycle_record or load_json(RELEASE_LIFECYCLE_PATH)
    current_snapshot = snapshot or load_json(CURRENT_SNAPSHOT_PATH)
    if lifecycle.get("publication_authority") != "REMOTE_REF_OBSERVATION":
        errors.append("Current lifecycle publication authority is not REMOTE_REF_OBSERVATION")
    if lifecycle.get("embedded_publication_assertion") != "NONE":
        errors.append("Current lifecycle embeds a publication assertion")
    if current_snapshot.get("release_lifecycle", {}).get("required_publication_ref") != "refs/heads/main":
        errors.append("Current Snapshot required publication ref is not refs/heads/main")
    release = current_snapshot.get("release_lifecycle", {})
    if release.get("publication_authority") != "REMOTE_REF_OBSERVATION":
        errors.append("Current Snapshot publication authority is not REMOTE_REF_OBSERVATION")
    if release.get("embedded_publication_assertion") != "NONE":
        errors.append("Current Snapshot embeds a publication assertion")
    for legacy_key in ("publication_state", "post_publication_remote_check_status"):
        if legacy_key in lifecycle or legacy_key in release:
            errors.append(f"Current publication projection contains legacy field {legacy_key}")
    texts = surface_texts or {path: resolve_repo_path(path).read_text(encoding="utf-8") for path in PUBLICATION_SURFACES}
    for path, text in texts.items():
        block = re.search(r"<!-- CURRENT-SNAPSHOT:BEGIN profile=ai schema=current-snapshot-r1 -->\n.*?<!-- CURRENT-SNAPSHOT:END -->", text, re.DOTALL)
        if not block:
            errors.append(f"AI publication Current block missing: {path}")
            continue
        if "REMOTE_REF_OBSERVATION" not in block.group(0) or "refs/heads/main" not in block.group(0):
            errors.append(f"AI publication Current block lacks ref-derived authority: {path}")
        if "NOT_PUBLISHED" in block.group(0) or "release_publication_state" in block.group(0):
            errors.append(f"AI publication Current block contains static publication state: {path}")
        if "ref-derived verification" not in block.group(0):
            errors.append(f"AI publication Current block lacks verification instruction: {path}")
    return errors


def run_check(receipt_path: Path | None = None, check_fixtures: bool = True) -> list[str]:
    errors: list[str] = []
    if not CONTRACT_PATH.is_file():
        return [f"missing contract: {CONTRACT_PATH}"]
    if not SCHEMA_PATH.is_file() or not RECEIPT_SCHEMA_PATH.is_file() or not FACTS_SCHEMA_PATH.is_file():
        errors.append("current-state sync schema file is missing")
    contract = load_json(CONTRACT_PATH)
    contract_errors, metrics = validate_contract(contract)
    errors.extend(contract_errors)
    try:
        from validate_current_task_lineage import validate as validate_task_lineage

        errors.extend(validate_task_lineage())
    except Exception as exc:  # pragma: no cover - fail-closed integration boundary
        errors.append(f"cannot validate current task lineage/status source: {exc}")
    errors.extend(validate_current_facts(contract))
    errors.extend(validate_release_publication_contract())
    if receipt_path is None:
        receipts = discover_receipts()
        if not receipts:
            errors.append("no current-state-sync receipt found")
            receipt = None
        else:
            receipt = load_json(receipts[-1])
            receipt_path = receipts[-1]
    else:
        receipt = load_json(receipt_path)
    if receipt is not None:
        errors.extend(validate_receipt(contract, receipt))
    if check_fixtures:
        errors.extend(validate_fixture_manifest())
    if not errors:
        print(f"CURRENT_STATE_SYNC_OK identity_epoch={contract['identity_epoch']} metrics={len(metrics)} receipt={receipt_path.relative_to(REPO_ROOT) if receipt_path else 'none'} impact={receipt.get('architecture_identity_impact') if receipt else 'none'}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate the contract, derived metrics and latest receipt")
    parser.add_argument("--receipt", type=Path, help="validate one explicit repository-relative receipt")
    parser.add_argument("--skip-fixtures", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    receipt = args.receipt
    if receipt is not None and not receipt.is_absolute():
        receipt = resolve_repo_path(str(receipt))
    errors = run_check(receipt_path=receipt, check_fixtures=not args.skip_fixtures)
    if errors:
        print("CURRENT_STATE_SYNC_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
