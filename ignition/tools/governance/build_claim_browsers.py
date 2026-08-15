#!/usr/bin/env python3
"""Build the small, human-readable surfaces for function and non-function assets.

The canonical JSONL registries remain the machine authority. This projection
writes prose only for materially useful records and gives the remaining bulk
a clear machine-only explanation. Every page follows the current 之元写作法
structure: what it is, why it matters, what it can support, what it cannot
establish, and what remains to do.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
MATERIALITY = ROOT / "data/governance/human-surface/materiality-manifest.json"
FUNCTION_SOURCE = ROOT / "data/foundation/function-assets/census.jsonl"
NONFUNCTION_SOURCE = ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl"
MIGRATION_SOURCE = ROOT / "data/foundation/migrations/legacy-table-migration.jsonl"
METHOD = "docs/publication/zhiyuan-writing-method.md"
METHOD_VERSION = "0.5.0"
MAX_FUNCTION_ENTRIES = 24
MAX_NONFUNCTION_ENTRIES = 24


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def clean(value: object, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


PLAIN_ENUMS = {
    "UNSPECIFIED_IN_SOURCE": "来源没有明确写出",
    "UNSPECIFIED": "尚未明确",
    "NOT_APPLICABLE": "不适用",
    "REQUIRES_HUMAN_REVIEW": "需要人工复核",
    "NOT_STATED_OR_NOT_APPLICABLE": "来源没有写明或不适用",
    "PENDING": "尚未闭合",
    "QUARANTINED_AMBIGUOUS": "因歧义暂时隔离",
    "HISTORICAL_ONLY": "仅作历史记录",
    "WITHDRAWN": "已撤回",
}


def plain(value: object, limit: int = 420) -> str:
    text = clean(value, limit)
    for enum, translation in sorted(PLAIN_ENUMS.items(), key=lambda item: -len(item[0])):
        text = text.replace(enum, translation)
    return text


def md(value: object, limit: int = 420) -> str:
    return clean(value, limit).replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def link(label: str, relative: str) -> str:
    return f"[{label}]({quote(relative, safe='/#:_-.~()')})"


def root_link(label: str, relative: str) -> str:
    return link(label, f"../../../{relative}")


def human_join(values: object, empty: str = "暂未登记") -> str:
    if isinstance(values, str):
        return md(values)
    if not isinstance(values, list):
        return empty
    cleaned = [plain(item, 260) for item in values if str(item).strip()]
    return "；".join(cleaned[:6]) if cleaned else empty


def machine_hash(row: dict) -> str:
    return digest(row)


def migration_hashes() -> dict[str, str]:
    if not MIGRATION_SOURCE.is_file():
        return {}
    return {row["legacy_path"]: row["content_sha256"] for row in read_jsonl(MIGRATION_SOURCE) if row.get("legacy_path") and row.get("content_sha256")}


def source_fingerprint(paths: list[str], migrated: dict[str, str]) -> tuple[str, str]:
    for path in paths:
        candidate = ROOT / path
        if candidate.is_file():
            return path, hashlib.sha256(candidate.read_bytes()).hexdigest()
        if path in migrated:
            return path, migrated[path]
    return "canonical registry record", "UNAVAILABLE_SOURCE_FILE__USE_MACHINE_RECORD_HASH"


def source_link(source_path: str) -> str:
    if source_path == "canonical registry record" or source_path.startswith(("统一函数总表/", "统一案例总表/")):
        return root_link("迁移 manifest", "data/foundation/migrations/legacy-table-migration.jsonl")
    return root_link(source_path, source_path)


def function_theme(row: dict) -> str:
    return {
        "STRICT_MATHEMATICAL_FUNCTION": "公式与可计算对象",
        "ALGORITHM_OR_WORKFLOW": "步骤与操作",
        "RELATION_OR_CONSTRAINT": "关系与约束",
        "SCORE_OR_INDEX": "指标与信号",
        "PARAMETRIC_MODEL": "模型与参数",
        "GATE_OR_DECISION_RULE": "判断与门槛",
        "CONJECTURE_OR_PENDING_CLAIM": "待研究问题",
        "HEURISTIC": "经验性工具",
    }.get(row.get("identity"), "待澄清的登记")


def nonfunction_theme(row: dict) -> str:
    disposition = row.get("final_disposition", "")
    if "WITHDRAWN" in disposition or "HISTORICAL" in disposition:
        return "撤回、历史与边界"
    if "PENDING" in disposition or "QUARANTIN" in disposition or "REWRITE" in disposition:
        return "尚未闭合的问题"
    return {
        "THEOREM_OR_MATHEMATICAL_CLAIM": "数学与形式化",
        "EMPIRICAL_OR_LITERATURE_CLAIM": "经验与文献",
        "MECHANISM_OR_CAUSAL_CLAIM": "机制与因果候选",
        "CROSS_DOMAIN_CORRESPONDENCE": "跨域对应与类比",
        "NORMATIVE_OR_GOVERNANCE_CLAIM": "治理与规范",
        "DESCRIPTIVE_REPOSITORY_CLAIM": "仓库事实与约定",
    }.get(row.get("claim_class"), "解释与研究候选")


def function_priority(row: dict) -> tuple[int, str]:
    preferred = {"MF1", "MF2", "MF3", "MF4", "MF5", "Y1", "A1", "A2", "T2", "D127", "D182", "D183", "D184", "D185", "D186", "D187", "D188", "D189", "D190", "D260"}
    return (0 if row.get("stable_id") in preferred else 1, row.get("stable_id", ""))


def nonfunction_priority(row: dict) -> tuple[int, str]:
    preferred = {"CLAIM-T2", "CLAIM-D127", "CLAIM-D182", "CLAIM-D183", "CLAIM-D184", "CLAIM-D185", "CLAIM-D186", "CLAIM-D187", "CLAIM-D188", "CLAIM-D189", "CLAIM-D190", "CLAIM-D260"}
    disposition = row.get("final_disposition", "")
    public = any(a.get("source_context") == "CURRENT_PUBLIC_SURFACE" for a in row.get("source_anchors", []))
    return (0 if row.get("canonical_id") in preferred else 1 if "WITHDRAWN" in disposition else 2 if public else 3 if disposition not in {"QUARANTINED_AMBIGUOUS", "HISTORICAL_ONLY"} else 4, row.get("canonical_id", ""))


def select_material(rows: list[dict], kind: str, limit: int) -> list[dict]:
    priority = function_priority if kind == "function" else nonfunction_priority
    selected: list[dict] = []
    seen_themes: set[str] = set()
    theme = function_theme if kind == "function" else nonfunction_theme
    for row in sorted(rows, key=priority):
        current_theme = theme(row)
        if current_theme not in seen_themes:
            selected.append(row)
            seen_themes.add(current_theme)
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        already = {row.get("stable_id") or row.get("canonical_id") for row in selected}
        for row in sorted(rows, key=priority):
            identifier = row.get("stable_id") or row.get("canonical_id")
            if identifier not in already:
                selected.append(row)
                already.add(identifier)
            if len(selected) >= limit:
                break
    return selected


def function_prose(row: dict, source_path: str, source_hash: str) -> list[str]:
    identifier = row["stable_id"]
    title = clean(row.get("title") or identifier, 240)
    theme = function_theme(row)
    definition = row.get("definition", {})
    obligations = row.get("proof_obligations", []) + row.get("empirical_obligations", [])
    return [
        f"# {title}", "",
        f"这是一条关于“{md(title, 220)}”的函数资产记录。它被放在“{theme}”这一组，是为了让读者先看懂它在点火流程里扮演什么角色，再决定是否需要打开机器记录。", "",
        "## 它在说什么", "",
        f"目前能直接读到的内容是：它试图把 {plain(definition.get('domain') or '来源中给出的对象范围')} 与 {plain(definition.get('codomain') or definition.get('output') or '尚未明确的输出')} 联系起来。这里的“联系”是登记对象的定义范围，不是对现实世界已经成立的断言。", "",
        "## 为什么值得看", "",
        f"它把一个容易被混在长文里的问题单独标出来：{md(row.get('claim_ceiling') or '需要回到来源确认其边界')}。单独登记的价值在于，后续可以为它补定义、找反例、补证明或决定降级，而不必把整套材料一起当成结论。", "",
        "## 可以怎么用", "",
        f"{human_join(row.get('allowed_uses'), '可以用于候选盘点与人工复核路线规划。')}。", "",
        "## 不能从这里推出什么", "",
        f"{human_join(row.get('forbidden_uses'), '不能仅凭登记、公式外形、内部测试或重复出现次数推出数学证明、外部证据或现实真值。')}。", "",
        "## 还缺什么", "",
        f"{human_join(obligations, '仍需确认定义、类型、范围、反例与适用边界。')}。", "",
        "## 技术记录（给维护者）", "",
        f"- 机器 ID：`{identifier}`；身份标签：`{clean(row.get('identity'))}`。",
        f"- M/E：数学成熟度 `{clean(row.get('mathematical_maturity'))}`；外部证据成熟度 `{clean(row.get('external_evidence'))}`。",
        f"- 处置：`{clean(row.get('disposition'))}`；claim ceiling：{md(row.get('claim_ceiling'), 520)}",
        f"- 机器记录指纹：`{machine_hash(row)}`；来源指纹：`{source_hash}`。来源：{source_link(source_path)}。",
        f"- 机器权威：{root_link('identity cards', 'data/foundation/function-assets/identity-cards.jsonl')}；生成方法：{root_link('之元写作法 0.5.0', METHOD)}。", "",
        "> 这页是人类可读的解释入口，不改变机器登记的状态，也不把人话摘要当成新的来源。来源文件变化时，先更新 canonical registry，再重新生成本页。", "",
    ]


def nonfunction_prose(row: dict, source_path: str, source_hash: str) -> list[str]:
    identifier = row["canonical_id"]
    title = clean(row.get("canonical_title") or row.get("minimal_atomic_claim") or identifier, 240)
    theme = nonfunction_theme(row)
    scope = row.get("scope_and_quantifiers", {})
    obligations = [item for values in (row.get("obligations") or {}).values() for item in values]
    return [
        f"# {title}", "",
        f"这是一条关于“{md(title, 220)}”的非函数资产记录。它被放在“{theme}”这一组，供读者理解一条说法如何被保留、限制、待查或撤回。", "",
        "## 它在说什么", "",
        f"在当前登记范围内，这条材料讨论的是：{plain(row.get('minimal_atomic_claim') or title, 520)}。范围写的是“{plain(scope.get('scope') or '来源未明确')}”；这只是记录的适用边界，不是把范围之外的情况一并覆盖。", "",
        "## 为什么值得看", "",
        "它把一条容易被文章语气放大的说法拆出来，读者可以同时看到它的来源、目前的处置和还没有完成的工作。这样做的目的，是让“有一个说法”与“已经被证明”保持距离。", "",
        "## 可以怎么用", "",
        "可以把它当作带边界的阅读线索：回到来源、核对范围、寻找反例或继续完成登记中的义务。它也可以帮助写作者知道哪些词需要收窄。", "",
        "## 不能从这里推出什么", "",
        f"当前记录不能超出这个上限：{plain(row.get('claim_ceiling'), 560)}。不能把处置标签、内部一致、相似案例、工程通过或 Agent 共识直接变成外部事实、普遍因果或已证明定理。", "",
        "## 还缺什么", "",
        f"{human_join(obligations, '需要继续确认来源、定义、证据、反例、复现或公开范围；具体缺口见机器记录。')}。", "",
        "## 技术记录（给维护者）", "",
        f"- 机器 ID：`{identifier}`；断言类别：`{clean(row.get('claim_class'))}`；断言类型：`{clean(row.get('assertion_type'))}`。",
        f"- M/E：数学成熟度 `{clean(row.get('mathematical_maturity'))}`；外部证据成熟度 `{clean(row.get('external_evidence_maturity'))}`；复现：`{clean(row.get('replication_status'))}`。",
        f"- 处置：`{clean(row.get('final_disposition'))}`；机器记录指纹：`{machine_hash(row)}`；来源指纹：`{source_hash}`。",
        f"- 来源：{source_link(source_path)}；机器权威：{root_link('claim registry', 'data/foundation/nonfunction-claims/claim-registry.jsonl')}；生成方法：{root_link('之元写作法 0.5.0', METHOD)}。", "",
        "> 这页是可读解释，不是第二份断言数据库。任何状态变化都必须先发生在 canonical registry，并通过生成器重新投影。", "",
    ]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or hashlib.sha256(value.encode()).hexdigest()[:16]


THEME_SLUGS = {
    "公式与可计算对象": "formulas-and-computable-objects",
    "步骤与操作": "steps-and-operations",
    "关系与约束": "relations-and-constraints",
    "指标与信号": "metrics-and-signals",
    "模型与参数": "models-and-parameters",
    "判断与门槛": "decisions-and-thresholds",
    "待研究问题": "open-research-questions",
    "经验性工具": "heuristics",
    "待澄清的登记": "records-needing-clarification",
    "撤回、历史与边界": "withdrawals-history-and-boundaries",
    "尚未闭合的问题": "unfinished-questions",
    "数学与形式化": "mathematics-and-formalization",
    "经验与文献": "evidence-and-literature",
    "机制与因果候选": "mechanism-and-causal-candidates",
    "跨域对应与类比": "cross-domain-correspondence",
    "治理与规范": "governance-and-norms",
    "仓库事实与约定": "repository-facts-and-conventions",
    "解释与研究候选": "interpretations-and-research-candidates",
}


def theme_slug(theme: str) -> str:
    return THEME_SLUGS.get(theme, slug(theme))


def render_theme(theme: str, items: list[dict], kind: str, paths: dict[str, str]) -> str:
    lines = [f"# {theme}", "", "这一页按问题家族组织可读入口；它不把同组对象合并成一个命题，也不把数量当成发现数量。", ""]
    for row in items:
        identifier = row.get("stable_id") or row.get("canonical_id")
        title = row.get("title") if kind == "function" else row.get("canonical_title") or row.get("minimal_atomic_claim")
        summary = "它是一个需要回到定义、边界和反例的函数登记。" if kind == "function" else "它是一条需要同时阅读来源、处置和 claim ceiling 的说法登记。"
        lines.extend([f"## {md(title, 220)}", "", f"{summary} {link('打开人话说明', f'../entries/{paths[identifier]}.md')}", ""])
    if not items:
        lines.extend(["当前没有被 materiality policy 选入本组的独立人话页面。", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_bulk(kind: str, rows: list[dict], selected: list[dict]) -> str:
    title = "函数资产：机器登记部分" if kind == "function" else "非函数资产：机器登记部分"
    source = "data/foundation/function-assets/census.jsonl" if kind == "function" else "data/foundation/nonfunction-claims/claim-registry.jsonl"
    selected_text = "函数资产" if kind == "function" else "非函数资产"
    return "\n".join([
        f"# {title}", "",
        f"当前机器记录中有 **{len(rows)}** 条{selected_text}，其中 **{len(selected)}** 条按本轮 materiality policy 生成了独立的人话说明；其余 **{len(rows) - len(selected)}** 条仍保留在机器 registry 中，作为可搜索、可回链、可重新筛选的 bulk 记录。", "",
        "这不是“其余内容不重要”，而是避免把每一条自动登记都伪装成文章。机器侧记录保留 ID、来源锚点、M/E、处置、claim ceiling、依赖和待办；需要完整审计时请直接打开 canonical registry。", "",
        f"- 机器权威：{root_link(source, source)}",
        f"- 本轮选择清单与来源指纹：{root_link('materiality manifest', 'data/governance/human-surface/materiality-manifest.json')}",
        f"- 人类写作制度：{root_link('Human Surface 编辑契约', 'docs/governance/human-surface-editorial-contract.md')}", "",
        "> 机器记录规模不是发现数量、质量分数或真值指标；本页也不作这样的解释。", "",
    ])


def render_readme(kind: str, rows: list[dict], selected: list[dict], themes: dict[str, list[dict]], source: str) -> str:
    title = "函数资产" if kind == "function" else "非函数资产"
    why = "把公式、算法、关系、指标和待澄清对象从长语料中分离出来，供人先理解用途和边界。" if kind == "function" else "把文章、案例、研究和治理材料里的说法拆开，供人先看范围、状态、证据义务和不能推出什么。"
    lines = [
        f"# {title}", "", f"这是{title}的人类入口。{why}", "",
        "## 普通读者从这里开始", "",
        "先按主题进入一组，再打开少量有独立说明的材料；如果你要查全量 ID、来源锚点或精确处置，直接进入机器登记。这里没有把机器 registry 伪装成文章，也没有用分页代替阅读结构。", "",
        "- [按主题与处置阅读](themes/README.md)",
        "- [打开 materiality 说明与机器 bulk 入口](bulk-explanation.md)",
        "- [查看 Human Surface 编辑契约](../../../docs/governance/human-surface-editorial-contract.md)", "",
        "## 这轮覆盖了什么", "",
        f"机器记录规模：**{len(rows)}** 条；独立人话说明：**{len(selected)}** 条。前一个数字是当前登记量，不是本轮发现量；后一个数字是按 materiality policy 选出的可读样本，不代表其余记录无价值。", "",
        "主题层同时保留对象类型、处置和边界的分组；条目层才展开“它在说什么 / 为什么值得看 / 可以怎么用 / 不能推出什么 / 还缺什么”。精确的 ID、M/E、处置和 claim ceiling 放在每条说明的技术记录段落。", "",
        "## 主题入口", "",
    ]
    for theme in sorted(themes):
        lines.append(f"- {link(theme, f'themes/{theme_slug(theme)}.md')}：{len(themes[theme])} 条人话说明")
    lines.extend([
        "", "## 机器权威与新鲜度", "",
        f"- 当前机器权威：{root_link(source, source)}",
        f"- 本轮 materiality manifest：{root_link('materiality-manifest.json', 'data/governance/human-surface/materiality-manifest.json')}",
        "- 每条人话说明都记录机器记录指纹与来源指纹；指纹变化时，本页必须重新生成。人话说明本身不改变来源状态。", "",
        "## 解释边界", "",
        "登记闭合、自动提取、重复出现、内部测试、工程通过或读者共鸣，都不能单独抬升数学成熟度、外部证据或现实真值。撤回、降级、隔离和开放问题继续可见。", "",
    ])
    return "\n".join(lines).rstrip() + "\n"


def expected_outputs(functions: list[dict], claims: list[dict]) -> tuple[dict[Path, str], dict]:
    migrated = migration_hashes()
    selected = {"function": select_material(functions, "function", MAX_FUNCTION_ENTRIES), "nonfunction": select_material(claims, "nonfunction", MAX_NONFUNCTION_ENTRIES)}
    all_rows = {"function": functions, "nonfunction": claims}
    products: dict[Path, str] = {}
    manifest_rows: list[dict] = []
    for kind, rows in all_rows.items():
        base = ROOT / "docs/human" / ("function-assets" if kind == "function" else "nonfunction-assets")
        source = "data/foundation/function-assets/census.jsonl" if kind == "function" else "data/foundation/nonfunction-claims/claim-registry.jsonl"
        chosen = selected[kind]
        key = (lambda row: row["stable_id"]) if kind == "function" else (lambda row: row["canonical_id"])
        paths = {key(row): slug(key(row)) for row in chosen}
        theme_fn = function_theme if kind == "function" else nonfunction_theme
        themes: dict[str, list[dict]] = defaultdict(list)
        for row in chosen:
            themes[theme_fn(row)].append(row)
            anchors = row.get("source_anchors", []) if kind == "nonfunction" else row.get("source_evidence", {}).get("occurrence_paths", [])
            anchor_paths = [item.get("path", "") for item in anchors if isinstance(item, dict)] if kind == "nonfunction" else [item for item in anchors if isinstance(item, str)]
            source_path, source_hash = source_fingerprint(anchor_paths, migrated)
            identifier = key(row)
            body = function_prose(row, source_path, source_hash) if kind == "function" else nonfunction_prose(row, source_path, source_hash)
            products[base / "entries" / f"{paths[identifier]}.md"] = "\n".join(body)
            manifest_rows.append({
                "asset_kind": "FUNCTION_ASSET" if kind == "function" else "NONFUNCTION_ASSET",
                "machine_id": identifier,
                "machine_source": source,
                "human_path": (base / "entries" / f"{paths[identifier]}.md").relative_to(ROOT).as_posix(),
                "machine_record_sha256": machine_hash(row),
                "source_path": source_path,
                "source_sha256": source_hash,
                "writing_method": f"之元写作法 {METHOD_VERSION}",
                "selection_reason": "materiality policy: representative, boundary-sensitive, or disposition-sensitive record",
            })
        products[base / "README.md"] = render_readme(kind, rows, chosen, themes, source)
        products[base / "bulk-explanation.md"] = render_bulk(kind, rows, chosen)
        products[base / "themes" / "README.md"] = "\n".join([f"# {('函数资产' if kind == 'function' else '非函数资产')}：主题与处置", "", "主题页只负责导航和分组；不把同组对象合并成一条命题。", ""] + [f"- {link(theme, f'{theme_slug(theme)}.md')}：{len(items)} 条人话说明" for theme, items in sorted(themes.items())] + [""])
        for theme, items in sorted(themes.items()):
            products[base / "themes" / f"{theme_slug(theme)}.md"] = render_theme(theme, items, kind, paths)
    manifest = {
        "schema_version": "1.0.0",
        "policy": "Material entries receive human prose; remaining records remain machine-only with a bulk explanation.",
        "writing_method": f"之元写作法 {METHOD_VERSION}",
        "machine_human_boundary": "Human prose is a deterministic explanation and never a state authority.",
        "counts": {"function_machine": len(functions), "function_human": len(selected["function"]), "nonfunction_machine": len(claims), "nonfunction_human": len(selected["nonfunction"])},
        "entries": sorted(manifest_rows, key=lambda row: (row["asset_kind"], row["machine_id"])),
    }
    products[MATERIALITY] = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return products, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    functions = read_jsonl(FUNCTION_SOURCE)
    claims = read_jsonl(NONFUNCTION_SOURCE)
    products, _ = expected_outputs(functions, claims)
    managed_roots = [ROOT / "docs/human/function-assets", ROOT / "docs/human/nonfunction-assets"]
    existing: dict[Path, str] = {}
    for managed in managed_roots:
        if managed.exists():
            for path in managed.rglob("*.md"):
                existing[path] = path.read_text(encoding="utf-8")
    stale = sorted(path for path in existing if path not in products)
    changed = sorted(path for path, content in products.items() if not path.is_file() or path.read_text(encoding="utf-8") != content)
    if args.check:
        if stale or changed:
            print(f"HUMAN_ASSETS_STALE changed={len(changed)} stale={len(stale)}")
            return 1
    else:
        for path, content in products.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        for path in stale:
            path.unlink()
        for managed in managed_roots:
            for directory in sorted((p for p in managed.rglob("*") if p.is_dir()), reverse=True):
                if not any(directory.iterdir()):
                    directory.rmdir()
    print(f"HUMAN_ASSETS_{'CHECK_OK' if args.check else 'BUILT'} function_machine={len(functions)} function_human={len(select_material(functions, 'function', MAX_FUNCTION_ENTRIES))} nonfunction_machine={len(claims)} nonfunction_human={len(select_material(claims, 'nonfunction', MAX_NONFUNCTION_ENTRIES))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
