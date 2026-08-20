#!/usr/bin/env python3
"""Generate the deterministic, non-authoritative Structural Governance Surface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "data/epistemic-governance/transition-grammar-r0.json"
CONTRACT = ROOT / "data/epistemic-governance/soft-governance-non-authority-invariant-r0.json"
IDENTITY = ROOT / "data/architecture/current-system-identity.json"
SCHEMA = ROOT / "schemas/epistemic-governance/structural-surface-r0.schema.json"
DEFAULT_JSON = ROOT / "data/epistemic-governance/structural-surface-r0.json"
DEFAULT_MD = ROOT / "docs/architecture/structural-governance-surface.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_surface(grammar: dict, contract: dict, identity: dict) -> dict:
    items = []
    for rule in sorted(grammar["rules"], key=lambda item: item["stable_id"]):
        items.append({
            "stable_id": rule["stable_id"],
            "domain": rule["domain"],
            "label": rule["human_label"],
            "relation": {
                "antecedent": rule["antecedent"],
                "candidate_transition": rule["candidate_transition"]
            },
            "blocked_transitions": sorted(rule["forbidden_inference"]),
            "needed_for_stronger_transition": sorted(rule["required_gate_or_evidence"]),
            "licensed_weaker_conclusion": rule["allowed_weaker_conclusion"],
            "unknown_behavior": rule["unknown_retention_rule"],
            "status": rule["status"]
        })
    return {
        "schema_version": "structural-surface-r0",
        "surface_id": "STRUCTURAL_GOVERNANCE_SURFACE_R0",
        "projection_type": "ORIGINAL_STRUCTURE",
        "surface_role": "ADVISORY_READING_SURFACE_NOT_PROMPT",
        "generated_from": {
            "transition_grammar": "ignition/data/epistemic-governance/transition-grammar-r0.json",
            "non_authority_contract": "ignition/data/epistemic-governance/soft-governance-non-authority-invariant-r0.json",
            "current_identity": "ignition/data/architecture/current-system-identity.json"
        },
        "authority_ceiling": contract["contract_text"] + " Current State remains " + identity["current_state_status"] + " and EPISTEMICALLY_ACCEPTED=0.",
        "current_state": {
            "status": identity["current_state_status"],
            "epistemically_accepted": identity["epistemically_accepted"]
        },
        "items": items
    }


def validate_surface(surface: dict, schema: dict) -> list[str]:
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(surface)]
    ids = [item.get("stable_id") for item in surface.get("items", [])]
    if len(ids) != len(set(ids)):
        errors.append("surface item IDs must be unique")
    if "not" not in surface.get("authority_ceiling", "").casefold() and "不能" not in surface.get("authority_ceiling", ""):
        errors.append("surface authority ceiling is missing a negative boundary")
    return sorted(set(errors))


def render_markdown(surface: dict) -> str:
    lines = [
        "# Structural Governance Surface",
        "",
        "这是一张由 canonical transition grammar 投影出的关系表，不是提示词、命令、",
        "权限清单或真值层。它把“当前状态 → 可以说到哪里 → 缺什么才能更强”并排呈现，",
        "让人和模型都能看到边界，但不能凭阅读它获得任何 hard authority。",
        "",
        "## 先读这里",
        "",
        "如果证据只支持一个局部工程结论，表面不会把它自动变成外部真值；如果证据",
        "缺口没有补上，未知可以保持未知；如果状态已撤回或隔离，改标题也不会让它",
        "回弹。下面每行是一个可回链关系，不是对读者或模型的行为授权。",
        "",
        "## Relations",
        "",
        "| 关系 | 当前前件 | 允许的局部转移 | 被阻断的越级 | 更强转移所需 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in surface["items"]:
        relation = item["relation"]
        blocked = "；".join(item["blocked_transitions"])
        needed = "；".join(item["needed_for_stronger_transition"])
        lines.append(f"| `{item['stable_id']}` | {relation['antecedent']} | {relation['candidate_transition']} | {blocked} | {needed} |")
    lines.extend([
        "",
        "## Hard versus soft",
        "",
        "Hard governance（permission、validator、state machine、K13、Claim Ceiling、Owner gate）",
        "决定能不能做、能不能晋级。这个表面属于 soft structural governance：它至多",
        "影响模型默认怎样判断和表达。`esi_score`、`soft_context_exposure`、风格相似度",
        "或阅读记录都不能授权、改真值、升级 M/E、扩大 claim ceiling、代替 Owner 或",
        "放行安全副作用。",
        "",
        "## Projection boundary",
        "",
        f"Generated from `{surface['generated_from']['transition_grammar']}`, `{surface['generated_from']['non_authority_contract']}` and `{surface['generated_from']['current_identity']}`.",
        "Current State 的工程状态仍为 `CURRENT_WITH_OPEN_OBLIGATIONS`，",
        "`EPISTEMICALLY_ACCEPTED=0`。本页不证明 ESI 已成立，也不包含私人观察原文。",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    surface = build_surface(load(GRAMMAR), load(CONTRACT), load(IDENTITY))
    errors = validate_surface(surface, load(SCHEMA))
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    json_bytes = (json.dumps(surface, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    markdown_bytes = render_markdown(surface).encode("utf-8")
    if args.check:
        if args.json_output.read_bytes() != json_bytes:
            print("FAIL: structural-surface JSON is not deterministic/current")
            return 1
        if args.markdown_output.read_bytes() != markdown_bytes:
            print("FAIL: structural-surface Markdown is not deterministic/current")
            return 1
        print(f"STRUCTURAL_SURFACE_DERIVED_OK items={len(surface['items'])} projection=ORIGINAL_STRUCTURE")
        return 0
    if not args.write:
        print(json.dumps(surface, ensure_ascii=False, indent=2))
        return 0
    args.json_output.write_bytes(json_bytes)
    args.markdown_output.write_bytes(markdown_bytes)
    print(f"STRUCTURAL_SURFACE_WRITTEN items={len(surface['items'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
