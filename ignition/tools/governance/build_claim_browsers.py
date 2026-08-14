#!/usr/bin/env python3
"""Build deterministic human browsers from the canonical claim registries.

The browsers are navigation projections only.  They never infer a new status,
merge records, or replace the canonical JSONL registries.  ``--check`` compares
the complete deterministic projection and fails on stale or missing chunks.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[2]
PAGE_SIZE = 250


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def clean(value: object, limit: int = 320) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def md_link(label: str, path: str) -> str:
    encoded = quote(path, safe="/:@-._~()")
    return f"[{label}](../../../{encoded})"


def source_links(paths: list[str]) -> str:
    unique = []
    for path in paths:
        if path not in unique and (ROOT / path).exists():
            unique.append(path)
    if not unique:
        return "未提供可解析的仓库内来源路径。"
    return " · ".join(md_link(path, path) for path in unique[:3])


def function_row(row: dict) -> str:
    evidence = row.get("source_evidence", {})
    statuses = row.get("status", {})
    return "\n".join(
        [
            f"### {clean(row.get('stable_id', 'UNSPECIFIED'))} · {clean(row.get('title', '未命名来源'))}",
            "",
            f"这是 canonical function-assets census 中的一个登记对象，身份为 `{clean(row.get('identity'))}`，处置为 `{clean(row.get('disposition'))}`，review state 为 `{clean(row.get('review', {}).get('state'))}`。",
            "",
            f"M 轴 `{clean(row.get('mathematical_maturity'))}`；E 轴 `{clean(row.get('external_evidence'))}`。状态记录：" + ", ".join(f"{k}=`{clean(v)}`" for k, v in sorted(statuses.items())) + ".",
            "",
            f"Claim ceiling：{clean(row.get('claim_ceiling'), 500)}",
            "",
            f"来源出现 {evidence.get('occurrence_count', 0)} 次；当前可回链来源：{source_links(evidence.get('occurrence_paths', []))}",
            "",
            "> 浏览器只投影 canonical 记录。自动 census、内部测试和登记闭合不构成外部真理、证明或独立复现。",
            "",
        ]
    )


def nonfunction_row(row: dict) -> str:
    scope = row.get("scope_and_quantifiers", {})
    anchors = row.get("source_anchors", [])
    paths = [item.get("path", "") for item in anchors if isinstance(item, dict)]
    title = clean(row.get("canonical_title") or row.get("minimal_atomic_claim"), 360)
    return "\n".join(
        [
            f"### {clean(row.get('canonical_id', 'UNSPECIFIED'))} · {title}",
            "",
            f"这是 canonical nonfunction-claims registry 中的原子登记。claim class 为 `{clean(row.get('claim_class'))}`，断言类型为 `{clean(row.get('assertion_type'))}`，最终处置为 `{clean(row.get('final_disposition'))}`。",
            "",
            f"M 轴 `{clean(row.get('mathematical_maturity'))}`；E 轴 `{clean(row.get('external_evidence_maturity'))}`；复现状态 `{clean(row.get('replication_status'))}`。",
            "",
            f"范围：{clean(scope.get('scope'))}；量词状态：`{clean(scope.get('quantifier_status'))}`。Claim ceiling：{clean(row.get('claim_ceiling'), 500)}",
            "",
            f"来源锚点：{source_links(paths)}",
            "",
            "> 浏览器只投影 canonical 记录。显式处置或 quarantine 只闭合登记与谱系，不等于数学证明、外部证据、普遍有效或现实真值。",
            "",
        ]
    )


def browser(kind: str, rows: list[dict], check: bool) -> tuple[int, int, int]:
    if kind == "function-assets":
        canonical = "data/foundation/function-assets/census.jsonl"
        title = "函数资产人类浏览器"
        intro = "从 canonical function-assets census 生成的按页人类浏览层。它保留身份、M/E、处置、状态和来源回链，不是第二份函数数据库。"
        renderer = function_row
    else:
        canonical = "data/foundation/nonfunction-claims/claim-registry.jsonl"
        title = "非函数断言人类浏览器"
        intro = "从 canonical nonfunction-claims registry 生成的按页人类浏览层。它保留原子文本、类型、M/E、处置、范围、复现和来源锚点，不是第二份断言数据库。"
        renderer = nonfunction_row

    out = ROOT / "docs" / "human" / kind
    expected: dict[str, str] = {}
    page_count = max(1, math.ceil(len(rows) / PAGE_SIZE))
    index_lines = [
        f"# {title}",
        "",
        intro,
        "",
        f"canonical source: `{canonical}`；记录数：`{len(rows)}`；每页：`{PAGE_SIZE}`。",
        "",
        "> 这里的文字由生成器确定性投影。不要手改页面；若对象状态变化，先更新 canonical asset，再重新生成并运行 `--check`。",
        "",
        "## 分页",
        "",
    ]
    for page_no in range(1, page_count + 1):
        start = (page_no - 1) * PAGE_SIZE
        page_rows = rows[start : start + PAGE_SIZE]
        filename = f"page-{page_no:03d}.md"
        page = [
            f"# {title} · 第 {page_no}/{page_count} 页",
            "",
            f"来源：[`{canonical}`](../../../{canonical})；本页记录 {start + 1}–{start + len(page_rows)}。",
            "",
            "[返回索引](README.md) · "
            + (f"[上一页](page-{page_no - 1:03d}.md) · " if page_no > 1 else "")
            + (f"[下一页](page-{page_no + 1:03d}.md)" if page_no < page_count else ""),
            "",
        ]
        page.extend(renderer(row) for row in page_rows)
        expected[filename] = "\n".join(page).rstrip() + "\n"
        index_lines.append(f"- [第 {page_no:03d} 页](page-{page_no:03d}.md)：记录 {start + 1}–{start + len(page_rows)}")
    index_lines.extend(
        [
            "",
            "## 解释边界",
            "",
            "机器登记、自动提取、内部测试、重复出现次数、M/E 标签和 registry closure 都不能单独抬升断言地位。需要裁决时回到 canonical registry、adjudication、evidence、proof、scope 和 provenance 资产。",
            "",
        ]
    )
    expected["README.md"] = "\n".join(index_lines)

    existing = {p.name: p.read_text(encoding="utf-8") for p in out.glob("*.md")} if out.exists() else {}
    stale = sorted(set(existing) - set(expected))
    changed = sorted(name for name, content in expected.items() if existing.get(name) != content)
    if not check:
        out.mkdir(parents=True, exist_ok=True)
        for name, content in expected.items():
            (out / name).write_text(content, encoding="utf-8")
        for name in stale:
            (out / name).unlink()
    if changed or stale:
        print(f"{kind}: pages={page_count} records={len(rows)} changed={len(changed)} stale={len(stale)}")
        return len(changed), len(stale), page_count
    print(f"{kind}: pages={page_count} records={len(rows)} changed=0 stale=0")
    return 0, 0, page_count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    function_rows = read_jsonl(ROOT / "data/foundation/function-assets/census.jsonl")
    nonfunction_rows = read_jsonl(ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl")
    results = [
        browser("function-assets", function_rows, args.check),
        browser("nonfunction-claims", nonfunction_rows, args.check),
    ]
    if args.check and any(changed or stale for changed, stale, _ in results):
        return 1
    print("CLAIM_BROWSERS_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
