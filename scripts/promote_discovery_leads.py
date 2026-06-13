#!/usr/bin/env python3
"""Promote bootstrap discovery leads into structured discovery entries."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path

from discovery_category_utils import (
    DISCOVERY_ID_RE,
    DISCOVERY_JSON,
    DISCOVERY_JSONL,
    build_category_map,
    classify_bootstrap_items,
    read_json,
    resolve_categories,
    write_json,
    write_jsonl,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FUNC_JSON = REPO_ROOT / "data/functions/unified-functions.json"
CASE_JSON = REPO_ROOT / "data/cases/unified-cases.json"


def next_id(existing: list[dict]) -> int:
    max_num = 0
    for item in existing:
        match = DISCOVERY_ID_RE.match(item.get("id", ""))
        if match:
            max_num = max(max_num, int(match.group(1)))
    return max_num + 1


def lead_key(category_id: str, lead: dict) -> str:
    payload = {
        "category_id": category_id,
        "zh": lead.get("zh", ""),
        "en": lead.get("en", ""),
        "related_functions": lead.get("related_functions", []),
        "related_cases": lead.get("related_cases", []),
    }
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def title_from_lead(category: dict, lead: dict) -> dict:
    zh = lead.get("zh", "").strip()
    en = lead.get("en", "").strip()
    zh = re.sub(r"仍可继续整理为.+?方向的独立发现。?$", "", zh).strip()
    zh = re.sub(r"是.+?分类下的补充入口。?$", "", zh).strip()
    zh = zh.replace("｜", " | ")
    if not zh:
        zh = f"{category['title']['zh']}自举发现线索"
    if len(zh) > 80:
        zh = zh[:77] + "..."
    en_title = en
    en_title = re.sub(r"\s+remains a curation lead in .+?\.$", "", en_title).strip()
    en_title = re.sub(r"\s+is a supplemental entry in .+?\.$", "", en_title).strip()
    if not en_title:
        en_title = f"{category['title']['en']} bootstrap discovery lead"
    if len(en_title) > 120:
        en_title = en_title[:117] + "..."
    return {"zh": zh, "en": en_title}


def function_relation(fid: str, functions_by_id: dict[str, dict]) -> dict:
    func = functions_by_id.get(fid.upper())
    if not func:
        return {
            "id": fid,
            "function_id": fid,
            "title": {"zh": fid, "en": fid},
            "page": None,
            "path": None,
            "found": False,
            "unresolved": True,
        }
    page = func["links"]["human_page"]
    return {
        "id": func["id"],
        "function_id": func["id"],
        "title": func["title"],
        "page": page,
        "path": page,
        "found": True,
        "unresolved": False,
    }


def case_relation(token: str, cases_by_id: dict[str, dict]) -> dict:
    normalized = token.upper()
    match = re.fullmatch(r"#?(\d+)", normalized)
    if match:
        normalized = f"C-{int(match.group(1)):04d}"
    case = cases_by_id.get(normalized)
    if not case:
        return {
            "id": token,
            "case_id": token,
            "normalized_id": normalized,
            "title": {"zh": token, "en": token},
            "page": None,
            "path": None,
            "found": False,
            "unresolved": True,
        }
    page = case["links"]["human_page"]
    return {
        "id": case["id"],
        "case_id": case["id"],
        "normalized_id": case["normalized_id"],
        "title": case["title"],
        "page": page,
        "path": page,
        "found": True,
        "unresolved": False,
    }


def build_entry(disc_id: str, category: dict, lead: dict, key: str, functions_by_id: dict[str, dict], cases_by_id: dict[str, dict]) -> dict:
    categories = resolve_categories([category["category_id"]])
    related_functions = [
        function_relation(fid, functions_by_id)
        for fid in lead.get("related_functions", [])
    ]
    related_cases = [
        case_relation(cid, cases_by_id)
        for cid in lead.get("related_cases", [])
    ]
    title = title_from_lead(category, lead)
    zh_content = lead.get("zh", "").strip()
    en_content = lead.get("en", "").strip() or "Rule-based English rendering pending human review."
    source_note = f"bootstrap-discovery-lead:{category['category_id']}:{key}"
    return {
        "id": disc_id,
        "type": "discovery",
        "status": "active_pending_novelty_review",
        "title": title,
        "summary": {"zh": zh_content, "en": en_content},
        "content": {"zh": zh_content, "en": en_content},
        "why_it_matters": {
            "zh": f"该条目把{category['title']['zh']}分类中的自举线索从分类页提升为可审计发现，使相关函数、案例、数学推导和后续独有性检查拥有独立对象。",
            "en": f"This entry promotes a bootstrap lead in {category['title']['en']} into an auditable discovery object with its own functions, cases, mathematical derivation, and novelty review path.",
        },
        "inference_chain": {
            "zh": "由函数—案例自举分类得到候选线索；若相关函数或案例存在可回指对象，则写入独立发现；再由正反交叉自举门控补齐数学表达、推导步骤、正向检查、反向检查与收敛判据。",
            "en": "The lead is generated by function-case bootstrap classification; if its related functions or cases have traceable objects, it is written as an independent discovery and then completed with mathematical expression, derivation steps, forward check, reverse check, and convergence criterion.",
        },
        "related_functions": related_functions,
        "related_cases": related_cases,
        "categories": categories,
        "source": {
            "conversation": "",
            "source_note": source_note,
            "related_commit": "",
            "date": date.today().isoformat(),
        },
        "source_notes": [source_note],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": date.today().isoformat(),
            "query_terms": [title["zh"], title["en"], category["title"]["zh"], category["title"]["en"]],
            "sources_checked": [],
            "nearest_matches": [],
            "reviewer_note": "Bootstrap lead promoted for independent mathematical and novelty review; external academic novelty is not yet finalized.",
            "novelty_claim": {
                "zh": "当前仅判定为框架内部可写入发现对象，外部学术独有性仍需后续检索。",
                "en": "Currently accepted as an internally writable discovery object; external academic novelty still requires later search.",
            },
        },
        "links": {"human_page": f"docs/zh/discoveries/items/{disc_id}.md"},
        "page": f"docs/zh/discoveries/items/{disc_id}.md",
        "human_explanation_path": f"docs/zh/discoveries/items/{disc_id}.md",
        "license": "CC-BY-NC-4.0",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report whether discovery leads are fully promoted")
    args = parser.parse_args()

    functions = read_json(FUNC_JSON, [])
    cases = read_json(CASE_JSON, [])
    discoveries = read_json(DISCOVERY_JSON, [])
    functions_by_id = {row["id"].upper(): row for row in functions}
    cases_by_id = {row["normalized_id"].upper(): row for row in cases}

    category_map = build_category_map(functions, cases, classify_bootstrap_items(functions, cases))
    existing_keys = {
        note.removeprefix("bootstrap-discovery-lead:").split(":", 1)[-1]
        for item in discoveries
        for note in item.get("source_notes", [])
        if isinstance(note, str) and note.startswith("bootstrap-discovery-lead:")
    }
    existing_notes = {
        item.get("source", {}).get("source_note", "")
        for item in discoveries
    }

    next_num = next_id(discoveries)
    additions = []
    for category in category_map:
        for lead in category.get("discovery_leads", []):
            key = lead_key(category["category_id"], lead)
            note = f"bootstrap-discovery-lead:{category['category_id']}:{key}"
            if key in existing_keys or note in existing_notes:
                continue
            disc_id = f"DISC-{next_num:04d}"
            additions.append(build_entry(disc_id, category, lead, key, functions_by_id, cases_by_id))
            next_num += 1

    if args.check:
        if additions:
            print(f"Discovery leads not promoted: {len(additions)}")
            raise SystemExit(1)
        print("all bootstrap discovery leads are promoted")
        return

    discoveries.extend(additions)
    discoveries.sort(key=lambda item: item["id"])
    write_json(DISCOVERY_JSON, discoveries)
    write_jsonl(DISCOVERY_JSONL, discoveries)
    print(f"promoted {len(additions)} discovery leads; total discoveries: {len(discoveries)}")


if __name__ == "__main__":
    main()
