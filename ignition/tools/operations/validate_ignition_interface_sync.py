#!/usr/bin/env python3
"""Validate Task148 AI-first interface synchronization without promoting Current."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
RECEIPT_PATH = ROOT / "data/operations/iterations/148/step11-interface-surface-sync.json"
REGISTRY_PATH = ROOT / "data/operations/synchronization-surfaces.json"
SCHEMA_PATH = ROOT / "schemas/operations/ignition-interface-sync-r1.schema.json"
FORMAL_BASELINE = "a1a1d102c3cd2fa12fc962b648b0eea62d8097cf"

ADDITIONAL_LOCATORS = {
    "docs/AI-USAGE.md",
    "docs/AI-PROMPT-TEMPLATES.md",
    "data/operations/synchronization-surfaces.json",
    "data/operations/project-components.json",
    "data/architecture/current-facts.json",
    "data/operations/current-snapshot-r1.json",
    "data/governance/knowledge-experience/manifest.json",
    "data/governance/human-surface/materiality-manifest.json",
    "docs/human/function-assets/entries/*.md + docs/human/nonfunction-assets/entries/*.md",
}

MINIMAL_INVOCATION = "请从这个仓库获取 Current 点火操作法，按操作法跑一遍我附上的对象，并返回结果。"


class InterfaceSyncError(ValueError):
    """A deterministic interface synchronization invariant failed."""


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise InterfaceSyncError(f"EXPECTED_OBJECT:{path.relative_to(ROOT)}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, code: str) -> None:
    if not condition:
        raise InterfaceSyncError(code)


def validate_schema(receipt: dict[str, Any], schema: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.path) or "<root>"
        raise InterfaceSyncError(f"SCHEMA_INVALID:{location}:{first.message}")


def operation_method_surfaces(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    surfaces = {
        item["surface_id"]: item
        for item in registry.get("surfaces", [])
        if "OPERATIONS_METHOD" in item.get("trigger_classifications", [])
    }
    require(len(surfaces) == 20, f"OPERATIONS_METHOD_SURFACE_COUNT:{len(surfaces)}")
    return surfaces


def validate_decision_contract(receipt: dict[str, Any], registry: dict[str, Any]) -> None:
    required = operation_method_surfaces(registry)
    decisions = receipt.get("surface_decisions", [])
    ids = [item.get("surface_id") for item in decisions]
    require(len(ids) == len(set(ids)), "DUPLICATE_SURFACE_DECISION")
    require(set(ids) == set(required), f"SURFACE_DECISION_SET_MISMATCH:{sorted(set(required) - set(ids))}:{sorted(set(ids) - set(required))}")
    require(receipt["source_registry"]["required_surface_count"] == len(required), "RECORDED_SURFACE_COUNT_MISMATCH")
    require(receipt["source_registry"]["registry_version"] == registry.get("registry_version"), "REGISTRY_VERSION_MISMATCH")

    for decision in decisions:
        declared = required[decision["surface_id"]]
        require(decision["locator"] == declared["locator"], f"LOCATOR_MISMATCH:{decision['surface_id']}")
        require(decision["decision"] in declared["allowed_decisions"], f"DECISION_NOT_ALLOWED:{decision['surface_id']}")
        require(bool(decision["reason"].strip()), f"EMPTY_REASON:{decision['surface_id']}")
        require(bool(decision["evidence_refs"]), f"MISSING_EVIDENCE:{decision['surface_id']}")

    additional = receipt.get("additional_surface_decisions", [])
    locators = [item.get("locator") for item in additional]
    require(len(locators) == len(set(locators)), "DUPLICATE_ADDITIONAL_DECISION")
    require(set(locators) == ADDITIONAL_LOCATORS, f"ADDITIONAL_DECISION_SET_MISMATCH:{sorted(set(ADDITIONAL_LOCATORS) - set(locators))}:{sorted(set(locators) - ADDITIONAL_LOCATORS)}")


def require_tokens(path: Path, tokens: tuple[str, ...]) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    require(not missing, f"SEMANTIC_TOKEN_MISSING:{path.relative_to(REPO_ROOT)}:{missing}")


def validate_semantics(registry: dict[str, Any]) -> None:
    surfaces = {item["surface_id"]: item for item in registry["surfaces"]}
    require(surfaces["method.operating"]["locator"] == "OPERATING-METHOD.md", "OPERATING_SURFACE_LOCATOR")
    require(surfaces["method.operating"]["authority"] == "canonical", "OPERATING_SURFACE_AUTHORITY")
    require("method.operating" in surfaces["method.iteration"]["derived_from"], "ITERATION_NOT_SUBORDINATE_TO_OPERATING")

    shared = ("OPERATING-METHOD.md", "READ_ONLY_RUN", "REPOSITORY_CHANGE_RUN", "INPUT_OBJECT")
    require_tokens(ROOT / "AI-START-HERE.md", shared + ("ignition-operation-capability-registry-r1.json", "只有用户明确要求修改点火自身"))
    require_tokens(ROOT / "AI-HANDOFF.md", shared + ("ignition-operation-capability-registry-r1.json", "一般任务保持"))
    require_tokens(ROOT / "llms.txt", shared + ("Primary user-task operation authority", "Repository-change sub-protocol"))
    require_tokens(ROOT / "docs/USAGE.md", shared + (MINIMAL_INVOCATION,))
    require_tokens(ROOT / "docs/project-current-state.md", ("OPERATING-METHOD.md", "READ_ONLY_RUN", "Iteration Method `1.4.0`", "二者不得合并"))
    require_tokens(ROOT / "SUMMARY.md", ("点火操作法", "Capability Registry", "点火迭代操作法"))
    require_tokens(ROOT / "HUMAN-READING.md", ("让点火处理一篇笔记", "OPERATING-METHOD.md", "ignition-run-output-contract-r1.json"))
    require_tokens(ROOT / "docs/ai-assistant-usage-reference.md", shared + (MINIMAL_INVOCATION, "Capability Registry"))
    require_tokens(ROOT / "docs/AI-USAGE.md", shared + ("ignition-run-output-contract-r1.json",))
    require_tokens(ROOT / "docs/AI-PROMPT-TEMPLATES.md", shared + (MINIMAL_INVOCATION,))
    require_tokens(
        REPO_ROOT / ".github/README.md",
        (
            "OPERATING-METHOD.md",
            "READ_ONLY_RUN",
            "REPOSITORY_CHANGE_RUN",
            "输入对象不是指令",
            MINIMAL_INVOCATION,
            "ignition-operation-capability-registry-r1.json",
        ),
    )

    for locator in (
        "templates/operations/task-command-template.md",
        "templates/operations/execution-result-template.md",
        "templates/operations/independent-review-template.md",
    ):
        require_tokens(ROOT / locator, ("OPERATING-METHOD.md", "REPOSITORY_CHANGE_RUN", "ITERATION.md` 1.4.0"))

    start_text = (ROOT / "AI-START-HERE.md").read_text(encoding="utf-8")
    handoff_text = (ROOT / "AI-HANDOFF.md").read_text(encoding="utf-8")
    require("新 Agent 必须先读取 `docs/project-current-state.md` 与 `ITERATION.md`" not in handoff_text, "LEGACY_HANDOFF_DEFAULT_ITERATION")
    require(start_text.index("OPERATING-METHOD.md") < start_text.index("ITERATION.md"), "COLD_START_ORDER_REVERSED")


def validate_no_historical_rewrite() -> None:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--name-only", FORMAL_BASELINE, "--"],
        check=True,
        capture_output=True,
        text=True,
    )
    violations: list[str] = []
    for raw_path in completed.stdout.splitlines():
        path = raw_path.removeprefix("ignition/")
        if path.startswith("data/operations/iterations/") and not path.startswith("data/operations/iterations/148/"):
            violations.append(raw_path)
        elif "/historical/" in f"/{path}" or path.startswith("archive/"):
            violations.append(raw_path)
    require(not violations, f"HISTORICAL_EVIDENCE_REWRITE:{sorted(violations)}")


def validate_preserved_digests(receipt: dict[str, Any]) -> None:
    mismatches = []
    for locator, expected in receipt["step11_preserved_digests"].items():
        path = ROOT / locator
        actual = sha256(path)
        if actual != expected:
            mismatches.append(f"{locator}:{expected}:{actual}")
    require(not mismatches, f"STEP11_PRESERVED_DIGEST_MISMATCH:{mismatches}")


def validate(enforce_step11_preserved_digests: bool = False) -> dict[str, Any]:
    receipt = load_json(RECEIPT_PATH)
    registry = load_json(REGISTRY_PATH)
    schema = load_json(SCHEMA_PATH)
    validate_schema(receipt, schema)
    validate_decision_contract(receipt, registry)
    validate_semantics(registry)
    validate_no_historical_rewrite()
    if enforce_step11_preserved_digests:
        validate_preserved_digests(receipt)
    changed = sum(item["decision"] == "CHANGE" for item in receipt["surface_decisions"])
    unchanged = sum(item["decision"] == "NO_CHANGE_WITH_REASON" for item in receipt["surface_decisions"])
    return {
        "declared_surfaces": len(receipt["surface_decisions"]),
        "changed": changed,
        "no_change_with_reason": unchanged,
        "additional_surfaces": len(receipt["additional_surface_decisions"]),
        "preserved_digest_count": len(receipt["step11_preserved_digests"]),
        "historical_rewrites": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--enforce-step11-preserved-digests", action="store_true")
    args = parser.parse_args()
    try:
        report = validate(args.enforce_step11_preserved_digests)
    except (InterfaceSyncError, OSError, subprocess.CalledProcessError) as exc:
        print(f"IGNITION_INTERFACE_SYNC_FAIL {exc}")
        return 1
    print(
        "IGNITION_INTERFACE_SYNC_OK "
        f"declared={report['declared_surfaces']} change={report['changed']} "
        f"no_change={report['no_change_with_reason']} additional={report['additional_surfaces']} "
        f"preserved={report['preserved_digest_count']} historical_rewrites={report['historical_rewrites']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
