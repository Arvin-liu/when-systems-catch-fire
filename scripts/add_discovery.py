#!/usr/bin/env python3
"""Append a new discovery entry and keep the discovery index in sync."""

from __future__ import annotations

import argparse
import json
import re
import os
from datetime import date
from pathlib import Path

from discovery_category_utils import CATEGORY_DIR, CATEGORY_MAP_JSON, render_category_page, resolve_categories, update_category_map_with_discovery
from derive_math_formalizations import discovery_formalization


REPO_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_JSON = REPO_ROOT / "data/discoveries/unified-discoveries.json"
DISCOVERY_JSONL = REPO_ROOT / "data/discoveries/unified-discoveries.jsonl"
DISCOVERY_INDEX_MD = REPO_ROOT / "data/discoveries/unified-discoveries-index.md"
DISCOVERY_LIST_MD = REPO_ROOT / "DISCOVERIES.md"
DISCOVERY_DIR = REPO_ROOT / "docs/zh/discoveries/items"

FUNC_JSON = REPO_ROOT / "data/functions/unified-functions.json"
CASE_JSON = REPO_ROOT / "data/cases/unified-cases.json"

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
DISCOVERY_ID_RE = re.compile(r"^DISC-(\d{4})$")


def read_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return default
    return json.loads(text)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, value) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, rows) -> None:
    body = "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows)
    write_text(path, body + ("\n" if body else ""))


def rel_link(from_path: Path, to_path: Path) -> str:
    return Path(os.path.relpath(to_path, from_path.parent)).as_posix()


def safe_english(text: str) -> str:
    if not text:
        return ""
    if CJK_RE.search(text):
        return "Rule-based English rendering pending human review."
    return text


def parse_csv_ids(value: str) -> list[str]:
    items = []
    for raw in value.split(","):
        token = raw.strip()
        if token:
            items.append(token)
    return items


def normalize_case_token(token: str) -> tuple[str, str]:
    raw = token.strip()
    if not raw:
        return "", ""
    numeric = re.fullmatch(r"#?(\d+)", raw)
    if numeric:
        seq = int(numeric.group(1))
        return f"#{seq}", f"C-{seq:04d}"
    normalized = re.fullmatch(r"C-(\d{4})", raw.upper())
    if normalized:
        seq = int(normalized.group(1))
        return f"#{seq}", f"C-{seq:04d}"
    return raw, raw


def next_discovery_id(items: list[dict]) -> str:
    max_num = 0
    for item in items:
        match = DISCOVERY_ID_RE.match(item.get("id", ""))
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"DISC-{max_num + 1:04d}"


def load_function_map() -> dict[str, dict]:
    items = read_json(FUNC_JSON, [])
    return {item["id"].upper(): item for item in items}


def load_case_map() -> dict[str, dict]:
    items = read_json(CASE_JSON, [])
    return {item["normalized_id"].upper(): item for item in items}


def build_related_functions(ids: list[str], func_map: dict[str, dict]) -> tuple[list[dict], list[str]]:
    related = []
    warnings = []
    seen = set()
    for fid in ids:
        key = fid.upper()
        if key in seen:
            continue
        seen.add(key)
        func = func_map.get(key)
        if func:
            related.append(
                {
                    "id": func["id"],
                    "title": func["title"],
                    "page": func["links"]["human_page"],
                    "found": True,
                }
            )
        else:
            warnings.append(f"warning: function {fid} not found in unified-functions.json")
            related.append(
                {
                    "id": fid,
                    "title": {
                        "zh": f"{fid}（未在当前函数表中找到 / Not found in the current function table）",
                        "en": f"{fid} (not found in the current function table)",
                    },
                    "page": None,
                    "found": False,
                }
            )
    return related, warnings


def build_related_cases(ids: list[str], case_map: dict[str, dict]) -> tuple[list[dict], list[str]]:
    related = []
    warnings = []
    seen = set()
    for token in ids:
        display_id, normalized = normalize_case_token(token)
        key = normalized.upper()
        if key in seen:
            continue
        seen.add(key)
        case = case_map.get(key)
        if case:
            related.append(
                {
                    "id": display_id,
                    "normalized_id": case["normalized_id"],
                    "title": case["title"],
                    "page": case["links"]["human_page"],
                    "found": True,
                }
            )
        else:
            warnings.append(f"warning: case {token} not found in unified-cases.json")
            related.append(
                {
                    "id": display_id,
                    "normalized_id": normalized,
                    "title": {
                        "zh": f"{token}（未在当前案例表中找到 / Not found in the current case table）",
                        "en": f"{token} (not found in the current case table)",
                    },
                    "page": None,
                    "found": False,
                }
            )
    return related, warnings


def render_discovery_page(item: dict) -> str:
    current_path = DISCOVERY_DIR / f"{item['id']}.md"
    formal = item.get("mathematical_formalization") or {}
    derivation = item.get("mathematical_derivation") or {}
    lines = [
        f"# {item['id']}｜{item['title']['zh']} / {item['title']['en']}",
        "",
        f"[← 返回发现总表 / Back to Discoveries]({rel_link(current_path, DISCOVERY_LIST_MD)})",
        f"[返回仓库首页 / Back to Repository Home]({rel_link(current_path, REPO_ROOT / 'README.md')})",
        "",
        "## 基本信息 / Basic Information",
        "",
        f"- 发现编号 / Discovery ID：{item['id']}",
        f"- 中文标题 / Chinese title：{item['title']['zh']}",
        f"- English title：{item['title']['en']}",
        f"- 状态 / Status：{item['status']}",
        f"- 日期 / Date：{item['source']['date']}",
        f"- 来源 / Source：{item['source']['source_note'] or item['source']['conversation'] or '—'}",
        "",
        "## 分类 / Categories",
        "",
    ]
    categories = item.get("categories", [])
    if categories:
        for cat in categories:
            if cat.get("page"):
                lines.append(
                    f"- [{cat['title']['zh']} / {cat['title']['en']}]({rel_link(current_path, REPO_ROOT / cat['page'])})"
                )
            else:
                lines.append(f"- {cat['title']['zh']} / {cat['title']['en']}")
    else:
        lines.append("- 其他 / Other")

    lines.extend(
        [
            "",
            "## 发现内容 / Discovery",
            "",
            "中文：",
            item["content"]["zh"],
            "",
            "English:",
            safe_english(item["content"]["en"]),
            "",
            "## 它为什么重要 / Why It Matters",
            "",
            "中文：",
            item["why_it_matters"]["zh"],
            "",
            "English:",
            safe_english(item["why_it_matters"]["en"]),
            "",
            "## 推论链条 / Inference Chain",
            "",
            "中文：",
            item["inference_chain"]["zh"],
            "",
            "English:",
            safe_english(item["inference_chain"]["en"]),
            "",
            "## 纯数学函数 / Pure Mathematical Function",
            "",
            f"- 对象 / Object: `{formal.get('symbol', '')}`",
            f"- 定义域 / Domain: `{formal.get('domain', '')}`",
            f"- 值域 / Codomain: `{formal.get('codomain', '')}`",
            f"- 数学表达 / Expression: `{formal.get('math_expression', '')}`",
            f"- 有效条件 / Validity: `{formal.get('validity_condition', '')}`",
            "",
            "## 数学推导 / Mathematical Derivation",
            "",
            f"- 推导类型 / Derivation type: `{derivation.get('kind', '')}`",
            f"- 收敛状态 / Convergence status: `{derivation.get('status', '')}`",
            f"- 依赖 / Depends on: {', '.join(f'`{dep}`' for dep in derivation.get('depends_on', [])) if derivation.get('depends_on') else '`source_state`'}",
            "- 推导步骤 / Steps:",
            *(f"  - {step}" for step in derivation.get("steps_math", [])),
            "- 证明义务 / Proof obligations:",
            *(f"  - `{obligation}`" for obligation in derivation.get("proof_obligations", [])),
            f"- 正向检查 / Forward check: `{(derivation.get('forward_check') or {}).get('condition', '')}`",
            f"- 反向检查 / Reverse check: `{(derivation.get('reverse_check') or {}).get('condition', '')}`",
            f"- 收敛判据 / Convergence: `{derivation.get('convergence', '')}`",
            "",
            "## 相关函数 / Related Functions",
            "",
        ]
    )
    related_functions = item.get("related_functions", [])
    if related_functions:
        for entry in related_functions:
            if entry.get("found") and entry.get("page"):
                lines.append(
                    f"- [{entry['id']}｜{entry['title']['zh']} / {entry['title']['en']}]({rel_link(current_path, REPO_ROOT / entry['page'])})"
                )
            else:
                lines.append(f"- {entry['title']['zh']}")
    else:
        lines.extend(["暂无明确相关函数。", "No explicit related functions yet."])

    lines.extend(
        [
            "",
            "## 相关案例 / Related Cases",
            "",
        ]
    )
    related_cases = item.get("related_cases", [])
    if related_cases:
        for entry in related_cases:
            if entry.get("found") and entry.get("page"):
                lines.append(
                    f"- [{entry['id']}｜{entry['title']['zh']} / {entry['title']['en']}]({rel_link(current_path, REPO_ROOT / entry['page'])})"
                )
            else:
                lines.append(f"- {entry['title']['zh']}")
    else:
        lines.extend(["暂无明确相关案例。", "No explicit related cases yet."])

    lines.extend(
        [
            "",
            "## 来源 / Sources",
            "",
            f"- 对话来源 / Conversation source：{item['source']['conversation'] or '—'}",
            f"- 源笔记 / Source note：{item['source']['source_note'] or '—'}",
            f"- 相关提交 / Related commit：{item['source']['related_commit'] or '—'}",
            "",
        ]
    )
    return "\n".join(lines)


def render_discoveries_list(items: list[dict]) -> str:
    category_map = read_json(CATEGORY_MAP_JSON, [])
    category_rows = [entry for entry in category_map if entry.get("category_id") and entry["category_id"] != "other"]
    lines = [
        "# 发现总表 / Discovery Index",
        "",
        "中文：这里收录《点火》框架在函数、案例与自举循环中产生的新发现。每条发现都应该独立成条，并连接到相关函数、案例、来源与推论链条。",
        "",
        "English: This index collects new discoveries generated by the Ignition framework through functions, cases, and bootstrap cycles. Each discovery should be recorded as an independent entry and linked to related functions, cases, sources, and inference chains.",
        "",
        "## 如何新增发现 / How to Add a Discovery",
        "",
        "中文：每跑出一个新发现，新增一条发现记录，不要把新发现塞进函数表或案例表里。函数表保存机制，案例表保存证据，发现表保存由机制和证据共同推出的新洞见。",
        "",
        "English: Whenever a new discovery is produced, add it as a separate discovery entry. Do not bury discoveries inside the function table or case table. The function table stores mechanisms, the case table stores evidence, and the discovery table stores new insights derived from mechanisms and evidence.",
        "",
        "## 学科分类 / Categories",
        "",
        "中文：以下分类由当前函数表与案例表的自举扫描生成，不是空壳入口。每条发现可以属于一个或多个分类。",
        "",
        "English: The following categories are generated from a bootstrap scan of the current function and case tables. They are not empty shells, and each discovery may belong to one or more categories.",
        "",
        "| 分类 / Category | 入口 / Entry | 当前覆盖 / Current Coverage |",
        "| --- | --- | --- |",
    ]
    for category in category_rows:
        coverage = category.get("coverage", {})
        lines.append(
            f"| {category['title']['zh']} / {category['title']['en']} | [{category['title']['en']}]({category['page']}) | {coverage.get('related_functions_count', 0)} related functions, {coverage.get('related_cases_count', 0)} related cases |"
        )

    zero_categories = [
        category
        for category in category_rows
        if category.get("coverage", {}).get("related_functions_count", 0) == 0 and category.get("coverage", {}).get("related_cases_count", 0) == 0
    ]
    if zero_categories:
        lines.extend(["", "### 可扩展分类 / Expandable Categories", ""])
        for category in zero_categories:
            lines.append(f"- [{category['title']['zh']} / {category['title']['en']}]({category['page']})")

    lines.extend(
        [
        "## 最近发现 / Recent Discoveries",
        "",
        "<!-- DISCOVERY_LIST_START -->",
    ]
    )
    if items:
        for item in items:
            category_tags = ""
            if item.get("categories"):
                category_tags = " · " + ", ".join(cat["title"]["en"] for cat in item["categories"])
            lines.append(
                f"- [{item['id']}｜{item['title']['zh']} / {item['title']['en']}]({item['links']['human_page']}){category_tags}"
            )
    else:
        lines.extend(["暂无已整理发现。", "No curated discoveries yet."])
    lines.append("<!-- DISCOVERY_LIST_END -->")
    lines.append("")
    return "\n".join(lines)


def render_discovery_index_md(items: list[dict]) -> str:
    rows = []
    for item in items:
        categories = ", ".join(cat["title"]["en"] for cat in item.get("categories", [])) or "other"
        novelty = item.get("academic_novelty", {}).get("status", "pending")
        rows.append(
            [
                f"[{item['id']}]({item['links']['human_page']})",
                f"{item['title']['zh']} / {item['title']['en']}",
                categories,
                item["status"],
                novelty,
                str(len(item.get("related_functions", []))),
                str(len(item.get("related_cases", []))),
                item["links"]["human_page"],
            ]
        )
    table = [
        "| 编号 / ID | 标题 / Title | 分类 / Categories | 状态 / Status | 学术独有性 / Academic novelty | 相关函数 / Related functions | 相关案例 / Related cases | 页面 / Page |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    table.extend("| " + " | ".join(row) + " |" for row in rows)
    if not rows:
        table.extend(["", "暂无条目 / No entries yet.", ""])
    return "\n".join(
        [
            "# 发现机器索引 / Discovery Machine Index",
            "",
            "机器可读索引，保留中文标题、英文标题、状态和关联计数。",
            "Machine-readable index that keeps Chinese titles, English titles, categories, status, and relation counts.",
            "",
            "- [`data/discoveries/unified-discoveries.json`](unified-discoveries.json)",
            "- [`data/discoveries/unified-discoveries.jsonl`](unified-discoveries.jsonl)",
            "",
            *table,
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Append a discovery entry.")
    parser.add_argument("--title-zh", required=True)
    parser.add_argument("--title-en", required=True)
    parser.add_argument("--content-zh", required=True)
    parser.add_argument("--content-en", required=True)
    parser.add_argument("--why-zh", required=True)
    parser.add_argument("--why-en", required=True)
    parser.add_argument("--chain-zh", required=True)
    parser.add_argument("--chain-en", required=True)
    parser.add_argument("--functions", default="")
    parser.add_argument("--cases", default="")
    parser.add_argument("--source", default="")
    parser.add_argument("--conversation", default="")
    parser.add_argument("--source-note", default="")
    parser.add_argument("--related-commit", default="")
    parser.add_argument("--categories", default="")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--status", default="draft")
    parser.add_argument("--academic-query", default="", help="Optional novelty query terms, comma-separated.")
    parser.add_argument("--academic-source", default="", help="Optional novelty source labels, comma-separated.")
    parser.add_argument("--nearest-match", default="", help="Optional nearest match summary.")
    parser.add_argument("--novelty-status", default="pending", help="Academic novelty status.")
    parser.add_argument("--novelty-claim-zh", default="", help="Optional Chinese novelty claim.")
    parser.add_argument("--novelty-claim-en", default="", help="Optional English novelty claim.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    items = read_json(DISCOVERY_JSON, [])
    if not isinstance(items, list):
        raise SystemExit("data/discoveries/unified-discoveries.json is not a list")

    discovery_id = next_discovery_id(items)
    func_map = load_function_map()
    case_map = load_case_map()
    category_ids = parse_csv_ids(args.categories) or ["other"]
    categories = resolve_categories(category_ids)

    related_functions, func_warnings = build_related_functions(parse_csv_ids(args.functions), func_map)
    related_cases, case_warnings = build_related_cases(parse_csv_ids(args.cases), case_map)

    for warning in func_warnings + case_warnings:
        print(warning)

    item = {
        "id": discovery_id,
        "title": {"zh": args.title_zh, "en": args.title_en},
        "content": {"zh": args.content_zh, "en": args.content_en},
        "why_it_matters": {"zh": args.why_zh, "en": args.why_en},
        "inference_chain": {"zh": args.chain_zh, "en": args.chain_en},
        "related_functions": related_functions,
        "related_cases": related_cases,
        "categories": categories,
        "source": {
            "conversation": args.conversation,
            "source_note": args.source_note or args.source,
            "related_commit": args.related_commit,
            "date": args.date,
        },
        "status": args.status,
        "academic_novelty": {
            "status": args.novelty_status,
            "checked_at": args.date,
            "query_terms": [item.strip() for item in args.academic_query.split(",") if item.strip()],
            "sources_checked": [item.strip() for item in args.academic_source.split(",") if item.strip()],
            "nearest_matches": ([{"title": args.nearest_match, "url": "", "reason_not_same": ""}] if args.nearest_match else []),
            "novelty_claim": {
                "zh": args.novelty_claim_zh or "待补充 / Pending",
                "en": args.novelty_claim_en or "Pending",
            },
            "reviewer_note": "",
        },
        "links": {"human_page": f"docs/zh/discoveries/items/{discovery_id}.md"},
    }
    if item["academic_novelty"]["status"] != "passed":
        if item["status"] == "active":
            item["status"] = "active_pending_novelty_review"
        elif item["status"] == "draft":
            item["status"] = "draft_pending_novelty_review"
    formal, derivation = discovery_formalization(item)
    item["mathematical_formalization"] = formal
    item["mathematical_derivation"] = derivation

    preview = {
        "id": item["id"],
        "title": item["title"],
        "status": item["status"],
        "categories": [entry["id"] for entry in categories],
        "related_functions": [entry["id"] for entry in related_functions],
        "related_cases": [entry["id"] for entry in related_cases],
        "links": item["links"],
    }
    print(json.dumps(preview, ensure_ascii=False, indent=2))

    if args.dry_run or args.validate:
        print("dry-run: no files were written")
        return

    items.append(item)
    items.sort(key=lambda row: row["id"])

    write_json(DISCOVERY_JSON, items)
    write_jsonl(DISCOVERY_JSONL, items)
    write_text(DISCOVERY_LIST_MD, render_discoveries_list(items))
    write_text(DISCOVERY_INDEX_MD, render_discovery_index_md(items))
    write_text(DISCOVERY_DIR / f"{discovery_id}.md", render_discovery_page(item))

    category_map = read_json(CATEGORY_MAP_JSON, [])
    if isinstance(category_map, list) and category_map:
        category_map = update_category_map_with_discovery(category_map, item)
        write_json(CATEGORY_MAP_JSON, category_map)
        write_jsonl(CATEGORY_MAP_JSON.with_suffix(".jsonl"), category_map)
        for category in category_map:
            write_text(CATEGORY_DIR / f"{category['category_id']}.md", render_category_page(category))
        write_text(DISCOVERY_LIST_MD, render_discoveries_list(items))

    print(f"added {discovery_id}")


if __name__ == "__main__":
    main()
