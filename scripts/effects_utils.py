#!/usr/bin/env python3
"""Helpers for the Effects layer."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from display_utils import format_bilingual_title


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_JSON = REPO_ROOT / "data/answers/new-effects.json"
OUT_DIR = REPO_ROOT / "data/effects"
DOC_DIR = REPO_ROOT / "docs/zh/effects"
ITEM_DIR = DOC_DIR / "items"
CATEGORY_DIR = DOC_DIR / "categories"

EFFECTS_JSON = OUT_DIR / "unified-effects.json"
EFFECTS_JSONL = OUT_DIR / "unified-effects.jsonl"
EFFECTS_INDEX_MD = OUT_DIR / "unified-effects-index.md"
EFFECTS_HUMAN_MD = REPO_ROOT / "EFFECTS.md"
CATEGORIES_JSON = OUT_DIR / "categories.json"
CATEGORIES_JSONL = OUT_DIR / "categories.jsonl"
CATEGORY_MAP_JSON = OUT_DIR / "category-map.json"
CATEGORY_MAP_JSONL = OUT_DIR / "category-map.jsonl"
EFFECT_TEMPLATE_MD = DOC_DIR / "EFFECT_TEMPLATE.md"


TERM_ZH = {
    "physics": "物理",
    "biology": "生物",
    "chemistry": "化学",
    "ai": "AI",
    "cognition": "认知",
    "systems": "系统",
    "society": "社会",
    "economics": "经济",
    "epistemology": "认识论",
    "medicine": "医学",
    "neuroscience": "神经科学",
    "psychology": "心理学",
    "philosophy": "哲学",
    "mathematics": "数学",
    "media": "媒介",
    "probability": "概率",
    "behavior": "行为",
    "engineering": "工程",
    "dermatology": "皮肤科",
    "epidemiology": "流行病学",
}


def read_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return default
    return json.loads(text)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, payloads: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for item in payloads:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def split_discipline(discipline: str) -> list[str]:
    return [part for part in discipline.split("-") if part]


def discipline_title(discipline: str) -> dict[str, str]:
    parts = split_discipline(discipline)
    if not parts:
        return {"zh": "未分类", "en": "Unsorted"}
    zh = "与".join(TERM_ZH.get(part, part) for part in parts)
    en = " and ".join(part.capitalize() if part != "ai" else "AI" for part in parts)
    return {"zh": zh, "en": en}


def novelty_payload(title_zh: str, conjecture_zh: str, source_refs: list[str], external_sources: list[dict]) -> dict:
    query_terms = [title_zh, conjecture_zh][:2]
    sources_checked = []
    for item in external_sources[:5]:
        if isinstance(item, dict):
            title = item.get("title")
            url = item.get("url")
            if title:
                sources_checked.append(title)
            if url:
                sources_checked.append(url)
    return {
        "status": "pending",
        "checked_at": "",
        "query_terms": query_terms,
        "sources_checked": sources_checked or source_refs[:3],
        "nearest_matches": [],
        "novelty_claim": {
            "zh": "",
            "en": "",
        },
        "reviewer_note": "Needs academic novelty review before promotion to active.",
    }


def infer_direction(text: str) -> str:
    value = text or ""
    if any(word in value for word in ["提高", "提升", "增强", "上升", "增加", "更强", "amplify", "increase", "raise"]):
        return "increase"
    if any(word in value for word in ["降低", "减少", "衰减", "减弱", "下降", "更弱", "decrease", "lower", "attenuate"]):
        return "decrease"
    if any(word in value for word in ["反转", "倒转", "inversion"]):
        return "inversion"
    if any(word in value for word in ["分岔", "bifurcation", "分离"]):
        return "bifurcation"
    if any(word in value for word in ["稳定", "stabil", "收敛"]):
        return "stabilization"
    if any(word in value for word in ["失稳", "destabil", "逃逸", "deadlock"]):
        return "destabilization"
    return "other"


def effect_from_source(src: dict) -> dict:
    effect_id = src["id"]
    title = src.get("title", {})
    conjecture = src.get("conjecture", {})
    conclusion = src.get("conclusion", {})
    formal = src.get("mathematical_formalization", {})
    derivation = src.get("mathematical_derivation", {})
    discipline = src.get("discipline", "other")
    title_zh = title.get("zh") or effect_id
    title_en = title.get("en") or title_zh
    category = discipline_title(discipline)
    source_refs = list(src.get("source_refs", []))
    external_sources = list(src.get("external_sources", []))
    signal = formal.get("math_expression") or formal.get("symbol") or ""
    trigger_conditions = [conjecture.get("zh") or "", src.get("empirical_scope", {}).get("zh") or ""]
    trigger_conditions = [item for item in trigger_conditions if item]
    related_functions = list(src.get("related_functions", []))

    return {
        "id": effect_id,
        "type": "effect",
        "status": "lead",
        "bootstrap_status": src.get("status"),
        "title": {"zh": title_zh, "en": title_en},
        "discipline": discipline,
        "categories": [discipline],
        "trigger_conditions": trigger_conditions,
        "observed_change": conclusion.get("zh") or "",
        "effect_direction": infer_direction(conclusion.get("zh", "") + " " + conjecture.get("zh", "")),
        "measurable_signal": signal,
        "related_functions": related_functions,
        "related_cases": [],
        "related_discoveries": [],
        "related_predictions": [],
        "related_analytic_solutions": [],
        "source_refs": source_refs,
        "external_sources": external_sources,
        "mathematical_formalization": formal,
        "mathematical_derivation": derivation,
        "academic_novelty": novelty_payload(title_zh, conjecture.get("zh") or "", source_refs, external_sources),
        "page": f"docs/zh/effects/items/{effect_id}.md",
        "created_at": src.get("created_at") or date.today().isoformat(),
        "updated_at": src.get("updated_at") or date.today().isoformat(),
        "license": "CC-BY-NC-4.0",
    }


def load_source_effects() -> list[dict]:
    return read_json(SOURCE_JSON, [])


def build_effects() -> tuple[list[dict], list[dict]]:
    source = load_source_effects()
    effects = [effect_from_source(item) for item in source]
    category_counts = Counter(item["discipline"] for item in effects)
    categories = [
        {
            "id": discipline,
            "title": discipline_title(discipline),
            "page": f"docs/zh/effects/categories/{discipline}.md",
            "lead_count": category_counts[discipline],
            "active_count": 0,
        }
        for discipline in sorted(category_counts)
    ]
    return effects, categories


def render_effect_page(effect: dict) -> str:
    title = format_bilingual_title(effect["title"].get("zh"), effect["title"].get("en"))
    novelty = effect.get("academic_novelty", {})
    cats = ", ".join(effect.get("categories", [])) or "none"
    source_refs = effect.get("source_refs", [])
    external = effect.get("external_sources", [])
    related_functions = effect.get("related_functions", [])
    related_cases = effect.get("related_cases", [])
    related_discoveries = effect.get("related_discoveries", [])
    related_predictions = effect.get("related_predictions", [])
    related_solutions = effect.get("related_analytic_solutions", [])
    trigger_conditions = effect.get("trigger_conditions", [])
    lines = [
        f"# {title}",
        "",
        f"- ID: `{effect['id']}`",
        f"- Status: `{effect['status']}`",
        f"- Bootstrap status: `{effect.get('bootstrap_status', '')}`",
        f"- Discipline: `{effect.get('discipline', '')}`",
        f"- Categories: {cats}",
        f"- Effect direction: `{effect.get('effect_direction', '')}`",
        f"- Trigger conditions: {'; '.join(trigger_conditions) if trigger_conditions else 'None yet'}",
        f"- Observed change: {effect.get('observed_change', '')}",
        f"- Measurable signal: {effect.get('measurable_signal', '')}",
        f"- Academic novelty: `{novelty.get('status', '')}`",
        "",
        "## Related Objects",
        f"- Related functions: {', '.join(related_functions) if related_functions else 'None'}",
        f"- Related cases: {', '.join(related_cases) if related_cases else 'None'}",
        f"- Related discoveries: {', '.join(related_discoveries) if related_discoveries else 'None'}",
        f"- Related predictions: {', '.join(related_predictions) if related_predictions else 'None'}",
        f"- Related analytic solutions: {', '.join(related_solutions) if related_solutions else 'None'}",
        "",
        "## Mathematical Formalization",
        f"- Object type: `{effect.get('mathematical_formalization', {}).get('object_type', '')}`",
        f"- Symbol: `{effect.get('mathematical_formalization', {}).get('symbol', '')}`",
        f"- Expression: `{effect.get('mathematical_formalization', {}).get('math_expression', '')}`",
        f"- Domain: `{effect.get('mathematical_formalization', {}).get('domain', '')}`",
        f"- Codomain: `{effect.get('mathematical_formalization', {}).get('codomain', '')}`",
        f"- Validity condition: `{effect.get('mathematical_formalization', {}).get('validity_condition', '')}`",
        "",
        "## Derivation",
        f"- Status: `{effect.get('mathematical_derivation', {}).get('status', '')}`",
        f"- Kind: `{effect.get('mathematical_derivation', {}).get('kind', '')}`",
        f"- Forward: `{effect.get('mathematical_derivation', {}).get('forward_check', {}).get('status', '')}`",
        f"- Reverse: `{effect.get('mathematical_derivation', {}).get('reverse_check', {}).get('status', '')}`",
        "",
        "## Sources",
        f"- Source refs: {', '.join(source_refs) if source_refs else 'None'}",
        f"- External sources: {', '.join(src.get('id') if isinstance(src, dict) else str(src) for src in external) if external else 'None'}",
    ]
    return "\n".join(lines) + "\n"


def render_category_page(category: dict, effects: list[dict]) -> str:
    matched = [item for item in effects if category["id"] in item.get("categories", [])]
    lines = [
        f"# {format_bilingual_title(category['title'].get('zh'), category['title'].get('en'))}",
        "",
        f"- ID: `{category['id']}`",
        f"- Lead count: {category.get('lead_count', len(matched))}",
        f"- Active count: {category.get('active_count', 0)}",
        "",
        "## Items",
    ]
    if matched:
        for item in sorted(matched, key=lambda row: row["id"]):
            lines.append(f"- [{item['id']} {format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}](../items/{item['id']}.md)")
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def render_index_md(effects: list[dict], categories: list[dict]) -> str:
    by_status = Counter(item.get("status") for item in effects)
    lines = [
        "# Effects Index",
        "",
        f"- Total leads: {by_status.get('lead', 0)}",
        f"- Total active: {by_status.get('active', 0)}",
        "",
        "## Categories",
    ]
    for category in categories:
        lines.append(f"- [{format_bilingual_title(category['title'].get('zh'), category['title'].get('en'))}]({category['page']}) - {category.get('lead_count', 0)} leads")
    lines.extend(["", "## Items"])
    for effect in sorted(effects, key=lambda item: item["id"]):
        lines.append(f"- {effect['id']} {format_bilingual_title(effect['title'].get('zh'), effect['title'].get('en'))}")
    return "\n".join(lines) + "\n"


def render_human_md(effects: list[dict], categories: list[dict]) -> str:
    lines = [
        "# Effect Layer / 效应层",
        "",
        "## Summary",
        f"- Leads: {len(effects)}",
        f"- Active: {sum(1 for item in effects if item['status'] == 'active')}",
        "",
        "## Categories",
    ]
    for category in categories:
        lines.append(f"- [{format_bilingual_title(category['title'].get('zh'), category['title'].get('en'))}]({category['page']}) - {category.get('lead_count', 0)} leads")
    lines.extend(["", "## Items"])
    for effect in sorted(effects, key=lambda item: item["id"]):
        lines.append(f"- [{effect['id']} {format_bilingual_title(effect['title'].get('zh'), effect['title'].get('en'))}]({effect['page']})")
    return "\n".join(lines) + "\n"
