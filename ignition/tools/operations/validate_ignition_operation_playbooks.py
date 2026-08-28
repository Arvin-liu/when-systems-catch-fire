#!/usr/bin/env python3
"""Validate registry-derived operation playbooks and their generated human view."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
REPO_ROOT = ROOT.parent
PLAYBOOKS_PATH = ROOT / "data/operations/ignition-operation-playbooks-r1.json"
REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/ignition-operation-playbooks-r1.schema.json"
HUMAN_VIEW_PATH = ROOT / "docs/operations/ignition-operation-playbooks-r1.md"

CORE_CURRENT_READS = (
    "ignition/OPERATING-METHOD.md",
    "ignition/AI-START-HERE.md",
    "ignition/data/architecture/current-facts.json",
    "ignition/data/operations/current-snapshot-r1.json",
    "ignition/data/operations/ignition-operation-capability-registry-r1.json",
    "ignition/data/operations/ignition-run-output-contract-r1.json",
)
CALLABLE_STATUSES = {"CURRENT", "CURRENT_BOUNDED"}
CALLABLE_AI = {"PUBLIC", "PUBLIC_BOUNDED"}
CATEGORY_IDS = (
    "knowledge_navigation_retrieval",
    "object_analysis_collision",
    "source_evidence_research",
    "function_claim_governance",
    "mechanism_model_mapping",
    "synthesis_open_question_generation",
    "writing_publication_transformation",
    "translation_language_thought",
    "validation_audit",
    "repository_maintenance_self_iteration",
    "executor_orchestration",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_callable(row: dict[str, Any]) -> bool:
    return row["current_status"] in CALLABLE_STATUSES and row["ai_callability"] in CALLABLE_AI


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _registry_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["operation_id"]: row for row in registry["operations"]}


def validate(document: dict[str, Any] | None = None, *, check_human_view: bool = True) -> list[str]:
    playbooks = document if document is not None else load_json(PLAYBOOKS_PATH)
    errors = [
        f"{error.json_path}: {error.message}"
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(playbooks)
    ]
    if errors:
        return errors
    registry = load_json(REGISTRY_PATH)
    operations = _registry_map(registry)
    expected_callable = sorted(operation_id for operation_id, row in operations.items() if _is_callable(row))
    expected_excluded = sorted(set(operations) - set(expected_callable))

    actual_playbooks = [row["operation_id"] for row in playbooks["playbooks"]]
    if actual_playbooks != sorted(actual_playbooks):
        errors.append("playbooks must be sorted by operation_id")
    if len(actual_playbooks) != len(set(actual_playbooks)):
        errors.append("playbook operation IDs must be unique")
    if actual_playbooks != expected_callable:
        errors.append(f"callable playbook coverage mismatch expected={expected_callable} actual={actual_playbooks}")

    actual_excluded = [row["operation_id"] for row in playbooks["excluded_status_only"]]
    if actual_excluded != sorted(actual_excluded):
        errors.append("status-only exclusions must be sorted by operation_id")
    if len(actual_excluded) != len(set(actual_excluded)):
        errors.append("status-only exclusion operation IDs must be unique")
    if actual_excluded != expected_excluded:
        errors.append(f"status-only exclusion coverage mismatch expected={expected_excluded} actual={actual_excluded}")
    for exclusion in playbooks["excluded_status_only"]:
        row = operations.get(exclusion["operation_id"])
        if row and _is_callable(row):
            errors.append(f"{exclusion['operation_id']}: callable operation cannot be status-only excluded")
        if row and row["ai_callability"] != "STATUS_ONLY":
            errors.append(f"{exclusion['operation_id']}: excluded operation must remain STATUS_ONLY")
        if row and row["current_status"] not in exclusion["reason"]:
            errors.append(f"{exclusion['operation_id']}: exclusion reason must name actual status {row['current_status']}")

    category_ids = [row["category_id"] for row in playbooks["category_audit"]]
    if category_ids != list(CATEGORY_IDS):
        errors.append("category audit must contain the eleven required categories in canonical order")
    for category in playbooks["category_audit"]:
        unknown = sorted(set(category["operation_ids"]) - set(operations))
        if unknown:
            errors.append(f"{category['category_id']}: unknown operation IDs {unknown}")
            continue
        rows = [operations[operation_id] for operation_id in category["operation_ids"]]
        status = category["coverage_status"]
        if status == "NO_DEDICATED_CURRENT_OPERATION" and rows:
            errors.append(f"{category['category_id']}: no-dedicated status cannot list operations")
        if status in {"COVERED_CURRENT", "COVERED_BOUNDED", "PARTIAL_BOUNDED"}:
            if not rows or not all(_is_callable(row) for row in rows):
                errors.append(f"{category['category_id']}: callable coverage status must list only callable operations")
        if status == "COVERED_CURRENT" and not any(row["current_status"] == "CURRENT" for row in rows):
            errors.append(f"{category['category_id']}: COVERED_CURRENT requires a CURRENT operation")
        if status == "STATUS_ONLY_NOT_CALLABLE" and (not rows or any(_is_callable(row) for row in rows)):
            errors.append(f"{category['category_id']}: status-only category must list only non-callable operations")

    executor = next(row for row in playbooks["category_audit"] if row["category_id"] == "executor_orchestration")
    if executor["coverage_status"] != "STATUS_ONLY_NOT_CALLABLE":
        errors.append("executor/orchestration must remain status-only and not callable")
    if set(executor["operation_ids"]) != {"executor.reference_conformance", "external.live_invocation"}:
        errors.append("executor/orchestration audit differs from Current executor boundary entries")

    for playbook in playbooks["playbooks"]:
        operation_id = playbook["operation_id"]
        operation = operations.get(operation_id)
        if operation is None:
            errors.append(f"{operation_id}: playbook operation is not registered")
            continue
        if not _is_callable(operation):
            errors.append(f"{operation_id}: playbook exists for a non-callable operation")
        if operation["default_execution_mode"] == "READ_ONLY_RUN":
            if operation["repository_mutation_permission"] != "FORBIDDEN" or operation["external_action_permission"] != "FORBIDDEN":
                errors.append(f"{operation_id}: read-only playbook registry permissions are inconsistent")
        for field in ("common_natural_language_intents", "execution_steps", "stop_conditions", "prohibitions"):
            if not playbook[field] or any(not value.strip() for value in playbook[field]):
                errors.append(f"{operation_id}: {field} must contain nonblank entries")

    if playbooks["lifecycle"]["current_on_main"]:
        errors.append("Task148 candidate playbooks cannot claim Current on main")
    if check_human_view:
        expected = render_markdown(playbooks, registry)
        if not HUMAN_VIEW_PATH.is_file() or HUMAN_VIEW_PATH.read_text(encoding="utf-8") != expected:
            errors.append("generated operation playbook human view is missing or out of date")
    return errors


def _bullets(values: list[str]) -> list[str]:
    return [f"- {value}" for value in values]


def render_markdown(playbooks: dict[str, Any], registry: dict[str, Any]) -> str:
    operations = _registry_map(registry)
    lines = [
        "# 点火 Operation-specific Playbooks R1",
        "",
        "> Generated human view. Canonical authored playbook source: `ignition/data/operations/ignition-operation-playbooks-r1.json`; capability fields are projected from `ignition/data/operations/ignition-operation-capability-registry-r1.json`. Both are Task148 branch candidates and are not Current on `main`.",
        "",
        "## 选择规则",
        "",
        "Only operations whose registry status is `CURRENT` or `CURRENT_BOUNDED` and whose AI callability is `PUBLIC` or `PUBLIC_BOUNDED` receive a callable playbook. Required inputs, outputs, status, mode, read set, authorities, validators and claim ceiling below are derived from the registry rather than copied as a second truth source.",
        "",
        "## 类别覆盖审计",
        "",
        "| Category | Coverage | Operation IDs | Boundary |",
        "|---|---|---|---|",
    ]
    for row in playbooks["category_audit"]:
        operation_ids = ", ".join(f"`{value}`" for value in row["operation_ids"]) or "—"
        lines.append(f"| `{row['category_id']}` | `{row['coverage_status']}` | {operation_ids} | {row['rationale']} |")
    lines.extend([
        "",
        "## 非可调用状态项",
        "",
        "| Operation | Current status | Allowed output | Reason |",
        "|---|---|---|---|",
    ])
    for row in playbooks["excluded_status_only"]:
        operation = operations[row["operation_id"]]
        lines.append(f"| `{row['operation_id']}` | `{operation['current_status']}` | `{row['allowed_output']}` | {row['reason']} |")
    lines.extend(["", "## 可调用 Playbooks", ""])
    for authored in playbooks["playbooks"]:
        operation = operations[authored["operation_id"]]
        name = operation["public_name"]
        authority_paths = _dedupe(
            [source["path"] for source in operation["authoritative_sources"]]
            + operation["applicable_governance"]
        )
        expansion_paths = _dedupe(
            [source["path"] for source in operation["authoritative_sources"]]
            + operation["applicable_governance"]
            + [check["path"] for check in operation["validation_checks"]]
        )
        lines.extend([
            f"### `{authored['operation_id']}` — {name['zh']} / {name['en']}",
            "",
            f"- Registry status: `{operation['current_status']}`",
            f"- Run mode: `{operation['default_execution_mode']}`",
            f"- Repository permission: `{operation['repository_mutation_permission']}`",
            f"- External-action permission: `{operation['external_action_permission']}`",
            "",
            "用户常见意图：",
            "",
            *_bullets(authored["common_natural_language_intents"]),
            "",
            "输入（registry-derived）：",
            "",
            *_bullets([f"`{value}`" for value in operation["accepted_input_types"]]),
            "",
            "最小 Current read set：",
            "",
            "- Core lifecycle reads: " + ", ".join(f"`{value}`" for value in CORE_CURRENT_READS),
            "- Operation-specific required reads: " + ", ".join(f"`{value}`" for value in operation["required_current_reads"]),
            "- Expand with declared authority/governance/validator paths: " + ", ".join(f"`{value}`" for value in expansion_paths),
            "",
            "执行步骤：",
            "",
            *_bullets(authored["execution_steps"]),
            "",
            "必须检查的 authority：",
            "",
            *_bullets([f"`{value}`" for value in authority_paths]),
            "",
            "允许的最大输出：",
            "",
            *_bullets([f"`{value}`" for value in operation["output_types"]]),
            f"- Claim ceiling: {operation['claim_ceiling']}",
            "",
            "Stop conditions：",
            "",
            *_bullets(authored["stop_conditions"]),
            "",
            "不得做什么：",
            "",
            *_bullets(authored["prohibitions"]),
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    args = parser.parse_args()
    playbooks = load_json(PLAYBOOKS_PATH)
    registry = load_json(REGISTRY_PATH)
    errors = validate(playbooks, check_human_view=args.check)
    if errors:
        print("IGNITION_OPERATION_PLAYBOOKS_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    if args.write:
        HUMAN_VIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
        HUMAN_VIEW_PATH.write_text(render_markdown(playbooks, registry), encoding="utf-8")
        print(f"IGNITION_OPERATION_PLAYBOOKS_RENDERED path={HUMAN_VIEW_PATH.relative_to(REPO_ROOT)}")
        return 0
    print(
        "IGNITION_OPERATION_PLAYBOOKS_OK "
        f"playbooks={len(playbooks['playbooks'])} "
        f"excluded={len(playbooks['excluded_status_only'])} "
        f"categories={len(playbooks['category_audit'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
