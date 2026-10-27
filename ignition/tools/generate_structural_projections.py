#!/usr/bin/env python3
"""Generate deterministic ESI ablation and control projections."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/epistemic-governance/structural-surface-r0.json"
SCHEMA = ROOT / "schemas/epistemic-governance/structural-projections-r0.schema.json"
OUT_DIR = ROOT / "data/epistemic-governance/projections"
PROJECTION_TYPES = (
    "DELEXICALIZED_STRUCTURE",
    "TERMINOLOGY_ONLY",
    "STRUCTURE_BROKEN_CONTROL",
    "STYLE_MATCHED_CONTROL",
    "CONCISE_CAPSULE",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def delexicalize(text: str) -> str:
    replacements = (
        ("EPISTEMICALLY", "STATUS_AXIS"),
        ("epistemic", "evidence-bound"),
        ("Owner", "authorized reviewer"),
        ("Agent", "executor"),
        ("Claim Ceiling", "claim limit"),
        ("M/E", "two independent maturity axes"),
        ("K13", "non-escalation rule"),
        ("Federation", "executor interchange"),
        ("Pointfire", "the repository"),
        ("ESI", "the candidate effect"),
    )
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    return result


def terminology_tokens(surface: dict) -> list[str]:
    text = " ".join([item["label"] + " " + item["relation"]["antecedent"] for item in surface["items"]])
    candidates = ("K13", "M/E", "Claim Ceiling", "Owner", "unknown", "withdrawn", "quarantine", "evidence", "permission", "truth")
    # The terminology-only arm deliberately retains the named vocabulary even
    # when a current grammar label is delexicalized; it is a control for terms,
    # not a claim that the terms are themselves canonical relations.
    return sorted({token for token in candidates if token.casefold() in text.casefold()} | set(candidates))


def build_projection(surface: dict, projection_type: str) -> dict:
    source_items = surface["items"]
    items: list[dict] = []
    if projection_type == "DELEXICALIZED_STRUCTURE":
        for item in source_items:
            relation = item["relation"]
            body = "关系前件：" + delexicalize(relation["antecedent"]) + "；局部转移：" + delexicalize(relation["candidate_transition"])
            body += "；不能直接推出：" + "、".join(delexicalize(x) for x in item["blocked_transitions"])
            body += "；仍缺：" + "、".join(delexicalize(x) for x in item["needed_for_stronger_transition"])
            items.append({"stable_id": item["stable_id"], "body": body})
        properties = {"relation_preserved": True, "terminology_preserved": False, "style_matched": False}
        intent = "Remove named vocabulary while preserving antecedent, licensed transition, blocked transition and missing-gate relations."
    elif projection_type == "TERMINOLOGY_ONLY":
        tokens = terminology_tokens(surface)
        for index, item in enumerate(source_items):
            rotation = tokens[index % len(tokens)] if tokens else "evidence"
            items.append({"stable_id": item["stable_id"], "body": f"术语卡 {index + 1}：{rotation}；相关词汇被保留，但状态前件、允许转移和缺口关系未提供。"})
        properties = {"relation_preserved": False, "terminology_preserved": True, "style_matched": False}
        intent = "Keep recognizable governance vocabulary and matched item count, while omitting the relations that could license a transition."
    elif projection_type == "STRUCTURE_BROKEN_CONTROL":
        for index, item in enumerate(source_items):
            other = source_items[(index + 1) % len(source_items)]
            body = "关系前件：" + item["relation"]["antecedent"] + "；局部转移：" + other["relation"]["candidate_transition"]
            body += "；不能直接推出：" + "、".join(other["blocked_transitions"])
            body += "；仍缺：" + "、".join(item["needed_for_stronger_transition"])
            items.append({"stable_id": item["stable_id"], "body": body})
        properties = {"relation_preserved": False, "terminology_preserved": True, "style_matched": False}
        intent = "Match the original topic and approximate information volume while rotating transition consequences so the governing structure is broken."
    elif projection_type == "STYLE_MATCHED_CONTROL":
        for index, item in enumerate(source_items):
            items.append({"stable_id": item["stable_id"], "body": f"这里保留一种克制、分层、留有余地的表达方式（样式段 {index + 1}）。它不声明前件、跃迁许可或所需证据。"})
        properties = {"relation_preserved": False, "terminology_preserved": False, "style_matched": True}
        intent = "Match cautious prose rhythm and formatting without presenting epistemic state-transition relations."
    elif projection_type == "CONCISE_CAPSULE":
        for item in source_items:
            relation = item["relation"]
            items.append({"stable_id": item["stable_id"], "body": f"{relation['antecedent']} → {relation['candidate_transition']}; stronger claim needs: {'; '.join(item['needed_for_stronger_transition'])}."})
        properties = {"relation_preserved": True, "terminology_preserved": False, "style_matched": False}
        intent = "Provide a compact advisory capsule for experiment or cold-start reading; it is not a permission or safety contract."
    else:
        raise ValueError(f"unsupported projection type: {projection_type}")
    serialized_body = "\n".join(item["body"] for item in items)
    properties.update({"content_length_chars": len(serialized_body), "item_count": len(items)})
    return {
        "schema_version": "structural-projection-r0",
        "projection_id": "ESI-" + projection_type,
        "projection_type": projection_type,
        "source_surface": "ignition/data/epistemic-governance/structural-surface-r0.json",
        "design_intent": intent,
        "control_properties": properties,
        "items": items,
    }


def validate(projection: dict, schema: dict) -> list[str]:
    return sorted(error.message for error in Draft202012Validator(schema).iter_errors(projection))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    surface = load(SOURCE)
    schema = load(SCHEMA)
    projections = {projection_type: build_projection(surface, projection_type) for projection_type in PROJECTION_TYPES}
    errors = [f"{key}: {error}" for key, value in projections.items() for error in validate(value, schema)]
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    if args.check:
        for projection_type, value in projections.items():
            path = args.out_dir / (projection_type.lower().replace("_", "-") + ".json")
            expected = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            if not path.is_file() or path.read_bytes() != expected:
                print(f"FAIL: projection is stale or missing: {path.name}")
                return 1
        print(f"STRUCTURAL_PROJECTIONS_DERIVED_OK projections={len(projections)}")
        return 0
    if not args.write:
        print(json.dumps(projections, ensure_ascii=False, indent=2))
        return 0
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for projection_type, value in projections.items():
        path = args.out_dir / (projection_type.lower().replace("_", "-") + ".json")
        path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"STRUCTURAL_PROJECTIONS_WRITTEN projections={len(projections)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
