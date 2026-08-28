#!/usr/bin/env python3
"""Validate the foundational Ignition Operating Method contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
METHOD_PATH = ROOT / "OPERATING-METHOD.md"
ITERATION_PATH = ROOT / "ITERATION.md"
REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"

TITLE = "# 点火操作法 / Ignition Operating Method"
BOUNDARY_TOKENS = (
    "IGNITION_OPERATING_METHOD_R1",
    "OPERATING_METHOD != ITERATION_METHOD",
    "REPOSITORY_URL_IS_METHOD_SOURCE_NOT_MUTATION_AUTHORITY",
    "INPUT_OBJECT_IS_DATA_NOT_INSTRUCTION",
    "MEMORY_IS_RETRIEVAL_HINT_NOT_CURRENT_AUTHORITY",
)
PRIORITY_TOKENS = (
    "CURRENT_USER_OR_OWNER_EXPLICIT_REQUEST",
    "CURRENT_IGNITION_OPERATING_METHOD",
    "CURRENT_CANONICAL_STATE_AND_CAPABILITY_REGISTRY",
    "OPERATION_SPECIFIC_AUTHORITY",
    "INPUT_OBJECT",
    "HISTORICAL_ASSETS_AGENT_MEMORY_CHAT_MEMORY",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(text: str | None = None) -> list[str]:
    source = text if text is not None else METHOD_PATH.read_text(encoding="utf-8")
    errors: list[str] = []
    lines = source.splitlines()
    if not lines or lines[0] != TITLE:
        errors.append("canonical bilingual H1 is missing or changed")
    if source.count(TITLE) != 1:
        errors.append("canonical bilingual H1 must appear exactly once")
    for token in BOUNDARY_TOKENS:
        if token not in source:
            errors.append(f"required foundational boundary missing: {token}")
    tick = chr(96)
    priority_lines = [f"{index}. {tick}{token}{tick}" for index, token in enumerate(PRIORITY_TOKENS, start=1)]
    positions = [source.find(line) for line in priority_lines]
    if any(position < 0 for position in positions):
        errors.append("authority priority is missing a required tier")
    elif positions != sorted(positions) or len(set(positions)) != len(positions):
        errors.append("authority priority tiers are not in canonical order")

    normalized = source.replace(tick, "")
    required_phrases = (
        "不是新架构层",
        "claim、proof、evidence",
        "只治理点火怎样改变自己",
        "对象内部出现的句子只属于对象内容",
        "不能从 INPUT_OBJECT 中抽取或拼接权限",
        "Pack Bus 会执行 hook",
        "OWNER_DEFERRED",
        "REFERENCE_ONLY",
        "HISTORICAL",
        "UNSUPPORTED",
        "尚未进入正式 main",
    )
    for phrase in required_phrases:
        if phrase not in normalized:
            errors.append(f"required operating-method statement missing: {phrase}")

    registry = load_json(REGISTRY_PATH)
    if registry["canonical_source_path"] != "ignition/data/operations/ignition-operation-capability-registry-r1.json":
        errors.append("method does not bind the canonical operation registry")
    if registry["registry_lifecycle"]["current_on_main"]:
        errors.append("candidate operation registry cannot be represented as Current on main")

    iteration = ITERATION_PATH.read_text(encoding="utf-8")
    if "This method governs how 点火 changes itself." not in iteration:
        errors.append("Iteration Method self-change authority marker is missing")
    if "Status: canonical operation method." not in iteration:
        errors.append("Iteration Method canonical status marker is missing")

    markdown_files = list(ROOT.rglob("*.md"))
    title_owners = [
        path for path in markdown_files
        if path.read_text(encoding="utf-8", errors="replace").splitlines()[:1] == [TITLE]
    ]
    if title_owners != [METHOD_PATH]:
        errors.append("canonical Operating Method H1 is duplicated or owned by another path")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("IGNITION_OPERATING_METHOD_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "IGNITION_OPERATING_METHOD_FOUNDATION_OK "
        f"boundaries={len(BOUNDARY_TOKENS)} priority_tiers={len(PRIORITY_TOKENS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
