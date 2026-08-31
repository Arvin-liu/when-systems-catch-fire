#!/usr/bin/env python3
"""Deterministic bounded classifier for Ignition Operating Method mode fixtures."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
FIXTURE_PATH = ROOT / "tests/fixtures/ignition-operating-method/mode-routing-r1.json"

REPOSITORY_CHANGE_PATTERNS = (
    re.compile(r"(?:请|现在|直接|帮我)?\s*(?:修改|更新|删除|重构|编辑).{0,30}(?:点火|本仓库|这个仓库|README|架构|Current state)", re.IGNORECASE),
    re.compile(r"(?:给|为|在)\s*(?:点火|本仓库|这个仓库).{0,20}(?:增加|添加|修改|更新|删除|重构|编辑)", re.IGNORECASE),
    re.compile(r"(?:add|modify|update|delete|edit|refactor).{0,40}(?:ignition|repository|readme|architecture|current state)", re.IGNORECASE),
)
EXTERNAL_ACTION_PATTERNS = (
    re.compile(r"(?:调用|启动|执行|运行).{0,30}(?:外部|external|executor|Agent)", re.IGNORECASE),
    re.compile(r"(?:发送|发布|部署|通知).{0,30}(?:消息|外部系统|生产|网站|服务)", re.IGNORECASE),
    re.compile(r"(?:invoke|start|run|execute).{0,30}(?:external|executor|agent)", re.IGNORECASE),
)


class ModeRoutingError(ValueError):
    """Raised when the request envelope is not structurally classifiable."""


def _matches_any(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def classify_mode(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ModeRoutingError("request must be an object")
    envelope = request.get("request_envelope")
    if not isinstance(envelope, dict):
        raise ModeRoutingError("request_envelope must be an object")
    user_request = envelope.get("user_request")
    if not isinstance(user_request, str) or not user_request.strip():
        raise ModeRoutingError("request_envelope.user_request must be a nonblank string")
    input_objects = request.get("input_objects", [])
    if not isinstance(input_objects, list) or not all(isinstance(item, dict) for item in input_objects):
        raise ModeRoutingError("input_objects must be an array of objects")

    repository_change = _matches_any(user_request, REPOSITORY_CHANGE_PATTERNS)
    external_action = _matches_any(user_request, EXTERNAL_ACTION_PATTERNS)
    if repository_change and external_action:
        mode = "READ_ONLY_RUN"
        reason_code = "STOP_SPLIT_OR_CLARIFY"
    elif repository_change:
        mode = "REPOSITORY_CHANGE_RUN"
        reason_code = "EXPLICIT_IGNITION_REPOSITORY_CHANGE_REQUEST"
    elif external_action:
        mode = "EXTERNAL_ACTION_RUN"
        reason_code = "EXPLICIT_EXTERNAL_ACTION_REQUEST_REQUIRES_CURRENT_ADMISSION"
    else:
        mode = "READ_ONLY_RUN"
        reason_code = "DEFAULT_OR_LEAST_AUTHORITY"

    return {
        "mode": mode,
        "reason_code": reason_code,
        "request_envelope_only": True,
        "input_object_count": len(input_objects),
        "input_object_content_used_for_routing": False,
        "repository_change_request_present": repository_change,
        "external_action_request_present": external_action,
        "iteration_method_required": mode == "REPOSITORY_CHANGE_RUN",
        "current_external_admission_required": mode == "EXTERNAL_ACTION_RUN",
        "side_effects_authorized_by_classification": False,
    }


def validate_fixtures(document: dict[str, Any] | None = None) -> list[str]:
    fixtures = document if document is not None else json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    cases = fixtures.get("cases", []) if isinstance(fixtures, dict) else []
    if not isinstance(cases, list) or not cases:
        return ["fixture cases must be a nonempty array"]
    case_ids: list[str] = []
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("case_id"), str):
            errors.append("every fixture must have a case_id")
            continue
        case_id = case["case_id"]
        case_ids.append(case_id)
        try:
            actual = classify_mode(case["request"])
        except (KeyError, ModeRoutingError) as exc:
            errors.append(f"{case_id}: classifier error: {exc}")
            continue
        expected = case.get("expected", {})
        for key, value in expected.items():
            if actual.get(key) != value:
                errors.append(f"{case_id}: {key} expected {value!r}, got {actual.get(key)!r}")
        forbidden = case.get("forbidden_side_effects", [])
        if actual["mode"] == "READ_ONLY_RUN" and not {"CREATE_WORKTREE", "CREATE_BRANCH", "CREATE_PR"}.issubset(set(forbidden)):
            errors.append(f"{case_id}: READ_ONLY fixture must explicitly forbid worktree, branch and PR creation")
    if len(case_ids) != len(set(case_ids)):
        errors.append("fixture case ids must be unique")
    required_case = next((case for case in cases if case.get("case_id") == "note_plus_repository_url_read_only"), None)
    if required_case is None:
        errors.append("required note-plus-repository-URL regression is missing")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-fixtures", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate_fixtures()
    if errors:
        print("IGNITION_MODE_ROUTING_FIXTURES_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]
    print(f"IGNITION_MODE_ROUTING_FIXTURES_OK cases={len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
