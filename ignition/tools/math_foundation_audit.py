#!/usr/bin/env python3
"""Build the IGNITION-20260709-075 math-foundation audit artifacts.

This script is intentionally conservative. It does not rewrite formal entries.
It scans the existing repository, classifies inventory items from filenames and
lightweight content signals, and emits reports plus a provenance ledger for
human/GPT review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


DATE_STAMP = "20260712"
ROOT = Path(__file__).resolve().parents[1]
FUNCTION_DIR = ROOT / "统一函数总表"
CASE_DIR = ROOT / "统一案例总表"
DOCS_DIR = ROOT / "docs"
INPUTS_DIR = ROOT / "inputs"
OUTPUTS_DIR = ROOT / "outputs"
DATA_DIR = ROOT / "data"

REPORT_DIR = ROOT / "reports" / "math-foundation"
FOUNDATION_DATA_DIR = ROOT / "data" / "math-foundation"
SCHEMA_DIR = ROOT / "schemas"

FORMAL_TYPES = {
    "FUNCTION",
    "PREDICATE",
    "RELATION",
    "STATE_TRANSITION",
    "CAUSAL_MODEL",
    "PROBABILISTIC_MODEL",
    "METRIC",
    "ORDER",
    "OPTIMIZATION_PROBLEM",
    "OPERATOR",
    "ALGORITHM",
    "FORMAL_PROPOSITION",
    "NATURAL_LANGUAGE_CANDIDATE",
}

PROVENANCE_STATUSES = {
    "DIRECT_SOURCE_FOUND",
    "INDIRECT_SOURCE_ONLY",
    "MULTIPLE_CONFLICTING_SOURCES",
    "SOURCE_NOT_FOUND",
    "GENERATED_WITHOUT_TRACEABLE_SOURCE",
}


@dataclass
class InventoryItem:
    id: str
    title: str
    current_path: str
    current_status: str
    formal_layer: str
    source_kind: str
    object_type: str
    provenance_status: str
    first_known_date: str
    first_known_file: str
    first_known_commit_or_pr: str
    source_note_paths: str
    source_case_ids: str
    intermediate_reports: str
    authoring_agent_or_source: str
    original_natural_language_claim: str
    original_expression: str
    later_rewrites: str
    conflicts: str
    missing_sources: str
    audit_priority: str
    type_issue: bool
    counterexample_flag: bool
    recommend_non_function: bool
    notes: str


def run(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def git_output(args: list[str]) -> str:
    return run(["git", *args], cwd=ROOT)


def safe_git_output(args: list[str]) -> str:
    try:
        return git_output(args)
    except Exception:
        return ""


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_frontmatter_field(text: str, field: str) -> str:
    pattern = rf"(?m)^{re.escape(field)}:\s*\"?(.*?)\"?$"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def infer_object_type(item_id: str, title: str, text: str) -> str:
    blob = f"{title}\n{text}"
    lower = blob.lower()
    if "算法" in blob or "algorithm" in lower:
        return "ALGORITHM"
    if "判定器" in blob or "算子" in blob:
        return "OPERATOR"
    if "状态转移" in blob:
        return "STATE_TRANSITION"
    if "因果" in blob:
        return "CAUSAL_MODEL"
    if "概率" in blob or "probability" in lower:
        return "PROBABILISTIC_MODEL"
    if "排序" in blob or "序" in title:
        return "ORDER"
    if "优化" in blob or "最优" in blob:
        return "OPTIMIZATION_PROBLEM"
    if "命题" in blob or "定理" in blob or "猜想" in blob:
        return "FORMAL_PROPOSITION"
    if "关系" in title or "同构" in title:
        return "RELATION"
    if "判定" in title or "概率" in title:
        return "PREDICATE"
    if item_id.startswith("MF-"):
        return "OPERATOR"
    return "FUNCTION"


def infer_layer(item_id: str) -> str:
    if item_id.startswith("MF-"):
        return "MF"
    if item_id.startswith("A"):
        return "A"
    if item_id.startswith("T"):
        return "T"
    if item_id.startswith("D"):
        return "D"
    if item_id.startswith("BC-") or item_id.startswith("PEND-") or item_id.startswith("SB-"):
        return "CANDIDATE_OR_PENDING"
    return "UNKNOWN"


def find_case_ids(text: str) -> list[str]:
    return sorted(set(re.findall(r"\bC-\d{1,4}\b", text)))


def detect_provenance(text: str) -> tuple[str, str, str]:
    note_paths = sorted(set(re.findall(r"/Users/zhiyuan/[^\s`]+", text)))
    has_source = "原文来源" in text or "Source" in text or "来源" in text
    has_getnote = any("getnote" in p.lower() or "得到大脑" in p for p in note_paths)
    has_pending = "pending" in text.lower()
    has_conflict = "冲突" in text or "conflict" in text.lower()
    if has_conflict:
        status = "MULTIPLE_CONFLICTING_SOURCES"
    elif note_paths:
        status = "DIRECT_SOURCE_FOUND"
    elif has_source:
        status = "INDIRECT_SOURCE_ONLY"
    elif has_pending:
        status = "GENERATED_WITHOUT_TRACEABLE_SOURCE"
    else:
        status = "SOURCE_NOT_FOUND"
    author = "getnote_or_local_note" if has_getnote else "repo_only"
    missing = "" if status == "DIRECT_SOURCE_FOUND" else "direct local note path or raw source artifact missing"
    return status, ";".join(note_paths[:8]), missing


def extract_claim(text: str) -> str:
    for marker in [
        "## 函数内容",
        "**注释 / Annotation**",
        "## 定义 / Definition",
        "## 机制表达",
    ]:
        idx = text.find(marker)
        if idx >= 0:
            snippet = text[idx:].splitlines()[1:4]
            return " ".join(s.strip() for s in snippet if s.strip())[:300]
    return text[:300].replace("\n", " ").strip()


def extract_expression(text: str) -> str:
    patterns = [
        r"`([^`]{5,240})`",
        r"Φ\s*=.*",
        r"V_effective\s*=.*",
        r"F_\{[^}]+\}\(x\)\s*:=.*",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return (match.group(1) if match.groups() else match.group(0))[:300]
    return ""


def classify_priority(item_id: str, title: str, text: str, layer: str, source_kind: str) -> str:
    keywords = ["四力", "引力", "量子", "哥德尔", "猜想", "唯一", "必然", "精确", "解析解", "不可能定理", "同构"]
    if layer in {"MF", "A", "T"}:
        return "HIGH"
    if item_id in {"D189", "D190", "D220", "D225", "D600", "D601", "D602"}:
        return "HIGH"
    if any(k in (title + text) for k in keywords):
        return "HIGH"
    if source_kind != "formal_table":
        return "MEDIUM"
    return "NORMAL"


def analyze_type_issue(object_type: str, text: str) -> tuple[bool, bool]:
    has_placeholder = bool(re.search(r"\bX_[A-Z0-9]+|\bY_[A-Z0-9]+", text))
    has_converged = "converged" in text.lower()
    prose_as_formula = "F_{" in text and " := " in text and any(ch in text for ch in ["是", "即", "所有"])
    return has_placeholder or prose_as_formula or has_converged, prose_as_formula


def analyze_counterexample(text: str, title: str) -> bool:
    blob = f"{title}\n{text}".lower()
    return any(token in blob for token in ["反例", "failure", "contradiction", "falsify", "不可逆竞争", "误写成证明"])


def recommend_non_function(object_type: str, text: str, title: str) -> bool:
    if object_type != "FUNCTION":
        return True
    blob = f"{title}\n{text}"
    return any(k in blob for k in ["同构", "关系", "判定", "边界", "命题", "猜想", "算法", "状态"])


def git_first_seen(path: Path) -> tuple[str, str]:
    rel = path.relative_to(ROOT).as_posix()
    log = safe_git_output(["log", "--follow", "--format=%ad|%H", "--date=short", "--", rel])
    if not log:
        return "", ""
    last_line = log.splitlines()[-1]
    date, commit = last_line.split("|", 1)
    return date, commit


def collect_formal_items() -> list[InventoryItem]:
    items: list[InventoryItem] = []
    for path in sorted(FUNCTION_DIR.glob("*.md")):
        text = read_text(path)
        item_id = parse_frontmatter_field(text, "id")
        if not item_id:
            match = re.search(r"\b(MF-\d{4}|A\d+|T\d+|D\d+)\b", path.name)
            item_id = match.group(1) if match else path.stem
        title = parse_frontmatter_field(text, "title") or path.stem
        layer = infer_layer(item_id)
        first_date, first_commit = git_first_seen(path)
        provenance_status, note_paths, missing = detect_provenance(text)
        object_type = infer_object_type(item_id, title, text)
        type_issue, prose_as_formula = analyze_type_issue(object_type, text)
        counterexample = analyze_counterexample(text, title)
        items.append(
            InventoryItem(
                id=item_id,
                title=title,
                current_path=path.relative_to(ROOT).as_posix(),
                current_status="formal_existing",
                formal_layer=layer,
                source_kind="formal_table",
                object_type=object_type,
                provenance_status=provenance_status,
                first_known_date=first_date,
                first_known_file=path.name,
                first_known_commit_or_pr=first_commit,
                source_note_paths=note_paths,
                source_case_ids=";".join(find_case_ids(text)),
                intermediate_reports="",
                authoring_agent_or_source="repo_formalization",
                original_natural_language_claim=extract_claim(text),
                original_expression=extract_expression(text),
                later_rewrites="contains rescue/frontmatter rewrite" if parse_frontmatter_field(text, "source") else "",
                conflicts="placeholder domain/codomain or converged-only semantics" if type_issue else "",
                missing_sources=missing,
                audit_priority=classify_priority(item_id, title, text, layer, "formal_table"),
                type_issue=type_issue,
                counterexample_flag=counterexample,
                recommend_non_function=recommend_non_function(object_type, text, title),
                notes="prose_as_formula" if prose_as_formula else "",
            )
        )
    return items


def collect_candidate_and_pending_items() -> list[InventoryItem]:
    items: list[InventoryItem] = []
    candidate_sources = [
        DOCS_DIR / "meta-protocols" / "book-validation-22-cases-20260709.md",
        DOCS_DIR / "pending_claims_register.md",
        DATA_DIR / "pending_claims.json",
    ]
    for path in candidate_sources:
        if not path.exists():
            continue
        text = read_text(path)
        if path.suffix == ".json":
            data = json.loads(text)
            rows = data if isinstance(data, list) else data.get("items", [])
            for row in rows:
                item_id = row.get("id") or "pending-json-item"
                title = row.get("claim") or row.get("title") or item_id
                body = json.dumps(row, ensure_ascii=False)
                items.append(build_nonformal_item(path, item_id, title, body, "pending_registry"))
            continue

        for match in re.finditer(r"\|\s*(BC-\d{8}-\d{3}|PEND-\d{3})\s*\|([^\|]+)\|([^\|]+)\|", text):
            item_id = match.group(1).strip()
            title = match.group(2).strip()
            claim = match.group(3).strip()
            items.append(build_nonformal_item(path, item_id, title, claim, "candidate_only" if item_id.startswith("BC-") else "pending"))
    return items


def build_nonformal_item(path: Path, item_id: str, title: str, claim: str, current_status: str) -> InventoryItem:
    text = read_text(path)
    first_date, first_commit = git_first_seen(path)
    provenance_status = "INDIRECT_SOURCE_ONLY" if "source" in claim.lower() or "报告" in claim else "SOURCE_NOT_FOUND"
    object_type = "NATURAL_LANGUAGE_CANDIDATE" if current_status == "candidate_only" else "FORMAL_PROPOSITION"
    return InventoryItem(
        id=item_id,
        title=title,
        current_path=path.relative_to(ROOT).as_posix(),
        current_status=current_status,
        formal_layer=infer_layer(item_id),
        source_kind=current_status,
        object_type=object_type,
        provenance_status=provenance_status,
        first_known_date=first_date,
        first_known_file=path.name,
        first_known_commit_or_pr=first_commit,
        source_note_paths="",
        source_case_ids="",
        intermediate_reports=path.relative_to(ROOT).as_posix(),
        authoring_agent_or_source="governance_registry",
        original_natural_language_claim=claim[:300],
        original_expression="",
        later_rewrites="",
        conflicts="",
        missing_sources="direct source artifact unresolved",
        audit_priority="HIGH" if item_id.startswith("PEND-") else "MEDIUM",
        type_issue=False,
        counterexample_flag=False,
        recommend_non_function=True,
        notes="",
    )


def gather_note_paths() -> list[Path]:
    paths = [
        Path("/Users/zhiyuan/Documents/GetNoteVault/getnote-notes"),
        Path("/Users/zhiyuan/我的笔记/得到大脑"),
        Path("/Users/zhiyuan/我的笔记/2026-07-09 1735"),
        Path("/Users/zhiyuan/我的笔记/2026-07-09 1902"),
    ]
    return paths


def stat_path(path: Path) -> dict[str, str]:
    if not path.exists():
        return {"path": str(path), "exists": "no"}
    if path.is_file():
        files = 1
    else:
        files = sum(1 for p in path.rglob("*") if p.is_file())
    latest = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    size = 0
    hashes = []
    if path.is_file():
        size = path.stat().st_size
        hashes.append({"path": path.name, "sha256": file_sha256(path)})
    else:
        for file_path in sorted(p for p in path.rglob("*") if p.is_file())[:25]:
            size += file_path.stat().st_size
            hashes.append({"path": str(file_path.relative_to(path)), "sha256": file_sha256(file_path)})
    return {
        "path": str(path),
        "exists": "yes",
        "files": str(files),
        "latest_mtime": latest,
        "sampled_total_size_bytes": str(size),
        "hashes": hashes,
    }


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def render_note_sync_report(note_stats: list[dict]) -> str:
    lines = ["# Local Note Sync Report", "", "## Scope", ""]
    for stat in note_stats:
        lines.append(f"- `{stat['path']}`: exists={stat['exists']}")
        if stat["exists"] == "yes":
            lines.append(
                f"  files={stat['files']}, latest_mtime={stat['latest_mtime']}, sampled_total_size_bytes={stat['sampled_total_size_bytes']}"
            )
    lines.extend(
        [
            "",
            "## Sync Result",
            "",
            "- 本轮未调用得到大脑进行数学判断、理论修正或函数重写。",
            "- 仅对本地可见目录做只读覆盖检查和哈希抽样。",
            "- `/Users/zhiyuan/Documents/GetNoteVault/getnote-notes` 与 `/Users/zhiyuan/我的笔记/得到大脑` 当前缺失，纳入 blocker。",
            "- `2026-07-09 1735` 与 `2026-07-09 1902` 目录存在，可作为局部来源补充。",
            "",
            "## Hash Sample",
            "",
        ]
    )
    for stat in note_stats:
        if stat["exists"] != "yes":
            continue
        lines.append(f"### {stat['path']}")
        for entry in stat["hashes"][:10]:
            lines.append(f"- `{entry['path']}` sha256 `{entry['sha256']}`")
        lines.append("")
    lines.extend(
        [
            "## Coverage Assessment",
            "",
            "- 当前可确认落地覆盖到 2026-07-09 的两批本地导出目录。",
            "- 默认 Obsidian/得到大脑正文源目录在本机当前不可见，因此无法声明连续覆盖。",
            "- 同步失败不阻断 075，其影响已转入 blocker 与 provenance 缺口状态。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_inventory_report(items: list[InventoryItem]) -> str:
    counts = Counter(item.formal_layer for item in items)
    lines = [
        "# Full Object Inventory",
        "",
        "## Counts",
        "",
        f"- formal function entries: {sum(1 for i in items if i.source_kind == 'formal_table')}",
        f"- candidate_only entries: {sum(1 for i in items if i.current_status == 'candidate_only')}",
        f"- pending entries: {sum(1 for i in items if i.current_status == 'pending')}",
        f"- MF layer: {counts['MF']}",
        f"- A layer: {counts['A']}",
        f"- T layer: {counts['T']}",
        f"- D layer: {counts['D']}",
        "",
        "## Notes",
        "",
        "- 本清单来自正式函数目录、候选治理表和 pending 机器数据。",
        "- 当前仓库未发现独立的 `candidate/functions` 目录；候选主要存在于治理文档和 collision 输出链。",
        "- 本轮不重编号、不增删正式条目，只生成审计视图。",
        "",
        "## High-Risk Targets Included",
        "",
    ]
    high = [i for i in items if i.audit_priority == "HIGH"][:80]
    for item in high:
        lines.append(f"- `{item.id}` {item.title} [{item.current_status}] -> {item.object_type}")
    return "\n".join(lines) + "\n"


def render_provenance_report(items: list[InventoryItem]) -> str:
    counts = Counter(item.provenance_status for item in items)
    lines = [
        "# Provenance Audit",
        "",
        "## Summary",
        "",
    ]
    for status in sorted(PROVENANCE_STATUSES):
        lines.append(f"- {status}: {counts[status]}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `DIRECT_SOURCE_FOUND`: 当前文本中能定位到原始笔记路径或明确原文来源。",
            "- `INDIRECT_SOURCE_ONLY`: 仅能定位到治理文档、报告或来源描述，未恢复直接原始材料。",
            "- `MULTIPLE_CONFLICTING_SOURCES`: 同一对象出现多来源冲突信号，需要人工比对。",
            "- `SOURCE_NOT_FOUND`: 当前仓库与可见本地目录中未恢复到来源痕迹。",
            "- `GENERATED_WITHOUT_TRACEABLE_SOURCE`: 看起来是生成/救援重写结果，但没有可追溯原始来源。",
            "",
            "## Selected Gaps",
            "",
        ]
    )
    for item in [i for i in items if i.provenance_status != "DIRECT_SOURCE_FOUND"][:60]:
        lines.append(f"- `{item.id}` {item.title}: {item.provenance_status}; missing={item.missing_sources}")
    return "\n".join(lines) + "\n"


def select_pilot_items(items: list[InventoryItem]) -> list[InventoryItem]:
    wanted_ids = {
        "MF-0000", "MF-0001", "MF-0002", "MF-0003", "MF-0004", "MF-0005",
        "D189", "D190", "D220", "D225", "D600", "D601", "D602",
    }
    pilot = [i for i in items if i.id in wanted_ids or i.formal_layer in {"A", "T", "MF"}]
    candidate_pool = [i for i in items if i.current_status in {"candidate_only", "pending"}][:12]
    normal_d = [i for i in items if i.formal_layer == "D" and i.audit_priority != "HIGH"][:20]
    seen = set()
    ordered = []
    for item in pilot + candidate_pool + normal_d:
        if item.id in seen:
            continue
        seen.add(item.id)
        ordered.append(item)
    return ordered


def render_pilot_report(pilot_items: list[InventoryItem]) -> str:
    lines = [
        "# Pilot Formal Audit",
        "",
        "## Method",
        "",
        "- 本试审只做审计，不改正式正文。",
        "- 判定维度：对象类型、定义域/值域占位、变量/单位、散文伪公式、类型错误、反例、案例-证明混淆、框架内收敛误写为外部真理。",
        "",
        "## Item Reviews",
        "",
    ]
    for item in pilot_items:
        lines.extend(
            [
                f"### {item.id} {item.title}",
                f"- 原始命题: {item.original_natural_language_claim or 'n/a'}",
                f"- 原始来源: {item.source_note_paths or item.intermediate_reports or item.current_path}",
                f"- 当前对象类型: {item.object_type}",
                f"- 定义域和值域: {'占位/未恢复' if item.type_issue else '需人工复核'}",
                f"- 变量和单位: {'不明确' if item.type_issue else '部分可见，仍需补字段'}",
                f"- 表达式是否散文伪公式: {'是' if item.notes == 'prose_as_formula' else '否/未自动触发'}",
                f"- 类型错误: {'是' if item.type_issue else '未自动触发'}",
                f"- 反例信号: {'是' if item.counterexample_flag else '未自动触发'}",
                f"- 案例支持误写成证明: {'是' if 'converged' in item.conflicts or item.current_status == 'candidate_only' else '需人工复核'}",
                f"- 框架内判定误写外部真理: {'是' if item.audit_priority == 'HIGH' else '需人工复核'}",
                f"- 建议新对象类型: {'保留 ' + item.object_type if not item.recommend_non_function else '改为 ' + item.object_type}",
                f"- 建议新形式表达: {item.original_expression or '先补语义命题，再定义正式表达'}",
                f"- 仍无法解决的问题: {item.missing_sources or '需要独立证明义务与外部证据'}",
                f"- 推荐状态: {item.provenance_status} / {'TYPE_ERROR' if item.type_issue else 'FORMALIZATION_INCOMPLETE'}",
                f"- 后续订正成本: {'high' if item.audit_priority == 'HIGH' else 'medium'}",
                "",
            ]
        )
    return "\n".join(lines)


def render_blockers(note_stats: list[dict], items: list[InventoryItem]) -> str:
    missing_note_roots = [s["path"] for s in note_stats if s["exists"] == "no"]
    no_source_count = sum(1 for i in items if i.provenance_status in {"SOURCE_NOT_FOUND", "GENERATED_WITHOUT_TRACEABLE_SOURCE"})
    return "\n".join(
        [
            "# Blockers",
            "",
            "## Active Blockers",
            "",
            f"- 默认本地来源根缺失: {', '.join(missing_note_roots) if missing_note_roots else 'none'}",
            "- 当前任务工作目录不是正式 repo；必须在真实仓库分支执行。",
            f"- 仍有 {no_source_count} 个对象未恢复到直接来源，不能宣称数学成立或来源闭环。",
            "- Draft PR 远端状态尚未在本轮重新写入，因为需要后续 push / PR 创建步骤。",
            "- 试审只能给出高风险分流与订正协议，不能自动判断数学真伪。",
            "",
            "## Non-Blockers",
            "",
            "- 正式两张表保持零修改是本轮硬约束，不影响宪法和审计材料建立。",
            "- 得到大脑零推理调用不阻止本轮做本地来源追溯审计。",
        ]
    ) + "\n"


def build_schema_files() -> tuple[dict, dict]:
    formal = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Ignition Formal Entry",
        "type": "object",
        "required": [
            "id", "title", "object_type", "domain", "codomain", "variables",
            "units", "assumptions", "expression", "semantics", "scope",
            "boundary_conditions", "failure_conditions", "sources",
            "proof_obligations", "validation_method", "workflow_status",
            "formal_status", "proof_status", "evidence_status",
            "scope_status", "provenance_status",
        ],
        "properties": {
            "id": {"type": "string", "minLength": 1},
            "title": {"type": "string", "minLength": 1},
            "object_type": {"enum": sorted(FORMAL_TYPES)},
            "domain": {"type": "string", "minLength": 1},
            "codomain": {"type": "string", "minLength": 1},
            "variables": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["name", "type"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "type": {"type": "string", "minLength": 1},
                        "unit": {"type": "string"},
                    },
                },
            },
            "units": {"type": "string", "minLength": 1},
            "assumptions": {"type": "array", "items": {"type": "string"}},
            "expression": {"type": "string", "minLength": 1},
            "semantics": {"type": "string", "minLength": 1},
            "scope": {"type": "string", "minLength": 1},
            "boundary_conditions": {"type": "array", "items": {"type": "string"}},
            "failure_conditions": {"type": "array", "items": {"type": "string"}},
            "sources": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
            "proof_obligations": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            "validation_method": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            "workflow_status": {"type": "string", "minLength": 1},
            "formal_status": {"enum": ["UNFORMALIZED", "WELL_FORMED", "TYPE_ERROR", "SEMANTICALLY_UNDEFINED", "FORMALIZATION_INCOMPLETE", "COUNTEREXAMPLE_FOUND"]},
            "proof_status": {"enum": ["DEFINITION_ONLY", "UNPROVED_PROPOSITION", "PROVED_IN_DECLARED_SYSTEM", "EXTERNAL_THEOREM", "DISPROVED", "NOT_APPLICABLE"]},
            "evidence_status": {"enum": ["SOURCE_ONLY", "CASE_SUPPORTED", "MULTI_CASE_SUPPORTED", "EMPIRICALLY_TESTED", "EXTERNALLY_VALIDATED", "PENDING"]},
            "scope_status": {"type": "string", "minLength": 1},
            "provenance_status": {"enum": sorted(PROVENANCE_STATUSES)},
            "converged": {"not": {}},
        },
        "additionalProperties": True,
    }
    provenance = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Ignition Provenance Entry",
        "type": "object",
        "required": [
            "id", "title", "current_path", "current_status", "formal_layer",
            "first_known_date", "first_known_file", "first_known_commit_or_pr",
            "source_note_paths", "source_case_ids", "intermediate_reports",
            "authoring_agent_or_source", "original_natural_language_claim",
            "original_expression", "later_rewrites", "provenance_status",
            "conflicts", "missing_sources", "audit_priority",
        ],
        "properties": {
            "id": {"type": "string", "minLength": 1},
            "title": {"type": "string", "minLength": 1},
            "current_path": {"type": "string", "minLength": 1},
            "current_status": {"type": "string", "minLength": 1},
            "formal_layer": {"type": "string", "minLength": 1},
            "first_known_date": {"type": "string"},
            "first_known_file": {"type": "string"},
            "first_known_commit_or_pr": {"type": "string"},
            "source_note_paths": {"type": "string"},
            "source_case_ids": {"type": "string"},
            "intermediate_reports": {"type": "string"},
            "authoring_agent_or_source": {"type": "string"},
            "original_natural_language_claim": {"type": "string"},
            "original_expression": {"type": "string"},
            "later_rewrites": {"type": "string"},
            "provenance_status": {"enum": sorted(PROVENANCE_STATUSES)},
            "conflicts": {"type": "string"},
            "missing_sources": {"type": "string"},
            "audit_priority": {"enum": ["HIGH", "MEDIUM", "NORMAL"]},
        },
        "additionalProperties": True,
    }
    return formal, provenance


def write_constitution_docs() -> None:
    docs = {
        "00-project-ontology.md": """# Project Ontology

点火项目的正式定位是“跨域机制的可追溯形式化建模系统”。

它不是现成数学理论，不是物理理论，不是万能证明器，也不是纯文字知识库。

本项目处理四层资产：

1. 来源层：原始笔记、案例、材料、史料、论文、数据。
2. 语义层：边界明确的自然语言命题、适用范围、失败条件。
3. 形式层：类型明确的数学或计算对象。
4. 有效性层：形式正确性、证明状态、经验支持状态、外部证据状态。

四层不得互相替代。公式不等于证明，案例不等于定理，converged 不等于外部真实。
""",
        "01-formal-object-types.md": """# Formal Object Types

允许的正式对象类型：

- FUNCTION
- PREDICATE
- RELATION
- STATE_TRANSITION
- CAUSAL_MODEL
- PROBABILISTIC_MODEL
- METRIC
- ORDER
- OPTIMIZATION_PROBLEM
- OPERATOR
- ALGORITHM
- FORMAL_PROPOSITION
- NATURAL_LANGUAGE_CANDIDATE

禁止把所有条目统一包装成 `F_ID:X_ID->Y_ID`。
当条目只是一段机制叙述、边界规则或待证命题时，应降级为更合适的对象类型，而不是强制函数化。
""",
        "02-formal-entry-schema.md": """# Formal Entry Schema

每条形式对象至少包含：

- 对象类型
- 定义域
- 值域或目标类型
- 变量名称与类型
- 单位或量纲
- 参数
- 前提假设
- 数学表达
- 自然语言语义
- 适用范围
- 停止条件
- 边界条件
- 反例或失败条件
- 来源
- 推导依赖
- 证明义务
- 验证方式
- 当前状态

缺任一核心字段时，不得宣称对象已经形式正确。
""",
        "03-validity-and-evidence-axes.md": """# Validity And Evidence Axes

废止用单一 `converged` 同时代表文档完成、数学正确和外部真实的做法。

最少拆分为：

- `workflow_status`
- `formal_status`
- `proof_status`
- `evidence_status`
- `scope_status`
- `provenance_status`

其中：

- `formal_status`: UNFORMALIZED / WELL_FORMED / TYPE_ERROR / SEMANTICALLY_UNDEFINED / FORMALIZATION_INCOMPLETE / COUNTEREXAMPLE_FOUND
- `proof_status`: DEFINITION_ONLY / UNPROVED_PROPOSITION / PROVED_IN_DECLARED_SYSTEM / EXTERNAL_THEOREM / DISPROVED / NOT_APPLICABLE
- `evidence_status`: SOURCE_ONLY / CASE_SUPPORTED / MULTI_CASE_SUPPORTED / EMPIRICALLY_TESTED / EXTERNALLY_VALIDATED / PENDING

任何强断言都必须明确属于哪一轴，不得用 `converged` 混写。
""",
        "04-proof-obligations.md": """# Proof Obligations

数学成立至少要求：

1. 对象类型与语义匹配。
2. 定义域、值域、变量和单位明确。
3. 表达式中出现的符号有声明。
4. 证明义务列明可检查的推导步骤或外部依赖。
5. 已知反例与失败条件被列出。
6. 若声称外部定理或实证成立，必须给出外部证据状态。

点火项目当前能稳妥承诺的是：机制更明确、可计算、可反驳、可修订。它不能仅凭函数化承诺“准确无错误”。
""",
        "05-case-to-model-mapping.md": """# Case To Model Mapping

案例与形式对象之间允许以下关系：

- support
- limit
- falsify
- boundary
- illustrate
- parameterize
- revise

单个案例不得被写成普遍定理的证明。案例最多提供变量实例、参数估计、适用范围限制、反例或模型修订触发器。
""",
        "06-audit-and-correction-protocol.md": """# Audit And Correction Protocol

075 之后的批量订正顺序：

1. 先补来源追溯。
2. 再判对象类型。
3. 再补字段与多轴状态。
4. 再处理高风险断言。
5. 最后才考虑正式表正文改写。

禁止事项：

- 不自动新增函数或案例。
- 不因扫描到相似词就认定直接来源。
- 不把 pending 或 candidate_only 直接升级为正式条目。
- 不把故事化、碰撞或单材料结论写成证明。
""",
        "07-migration-plan.md": """# Migration Plan

后续 617 条订正建议按四批进行：

1. 高风险批：MF、A、T、D189/D190/D220/D225/D600-D602 以及所有数学/物理/唯一性/必然性条目。
2. 来源缺口批：`SOURCE_NOT_FOUND` 与 `GENERATED_WITHOUT_TRACEABLE_SOURCE`。
3. 类型失真批：占位定义域/值域、散文伪公式、converged 混写。
4. 普通整理批：字段补齐、案例关系标注、状态轴拆分。

每批都先出审计清单，再进入正式改写。
""",
    }
    target_dir = DOCS_DIR / "math-foundation"
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, body in docs.items():
        (target_dir / name).write_text(body, encoding="utf-8")


def write_validator(formal_schema: dict, provenance_schema: dict) -> None:
    validator_path = ROOT / "tools" / "validate_math_foundation.py"
    validator_path.write_text(
        """#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


FORMAL_TYPES = {
    "FUNCTION",
    "PREDICATE",
    "RELATION",
    "STATE_TRANSITION",
    "CAUSAL_MODEL",
    "PROBABILISTIC_MODEL",
    "METRIC",
    "ORDER",
    "OPTIMIZATION_PROBLEM",
    "OPERATOR",
    "ALGORITHM",
    "FORMAL_PROPOSITION",
    "NATURAL_LANGUAGE_CANDIDATE",
}

FORMAL_STATUS = {"UNFORMALIZED", "WELL_FORMED", "TYPE_ERROR", "SEMANTICALLY_UNDEFINED", "FORMALIZATION_INCOMPLETE", "COUNTEREXAMPLE_FOUND"}
PROOF_STATUS = {"DEFINITION_ONLY", "UNPROVED_PROPOSITION", "PROVED_IN_DECLARED_SYSTEM", "EXTERNAL_THEOREM", "DISPROVED", "NOT_APPLICABLE"}
EVIDENCE_STATUS = {"SOURCE_ONLY", "CASE_SUPPORTED", "MULTI_CASE_SUPPORTED", "EMPIRICALLY_TESTED", "EXTERNALLY_VALIDATED", "PENDING"}
PROVENANCE_STATUS = {"DIRECT_SOURCE_FOUND", "INDIRECT_SOURCE_ONLY", "MULTIPLE_CONFLICTING_SOURCES", "SOURCE_NOT_FOUND", "GENERATED_WITHOUT_TRACEABLE_SOURCE"}


def validate_entry(entry: dict) -> list[str]:
    errors = []
    required = [
        "id", "title", "object_type", "domain", "codomain", "variables", "units",
        "expression", "semantics", "sources", "proof_obligations", "validation_method",
        "workflow_status", "formal_status", "proof_status", "evidence_status",
        "scope_status", "provenance_status",
    ]
    for key in required:
        if key not in entry or entry[key] in ("", [], {}):
            errors.append(f"missing_or_empty:{key}")
    if entry.get("object_type") not in FORMAL_TYPES:
        errors.append("invalid:object_type")
    if entry.get("formal_status") not in FORMAL_STATUS:
        errors.append("invalid:formal_status")
    if entry.get("proof_status") not in PROOF_STATUS:
        errors.append("invalid:proof_status")
    if entry.get("evidence_status") not in EVIDENCE_STATUS:
        errors.append("invalid:evidence_status")
    if entry.get("provenance_status") not in PROVENANCE_STATUS:
        errors.append("invalid:provenance_status")
    variables = entry.get("variables", [])
    declared = {v.get("name") for v in variables if isinstance(v, dict)}
    expr = entry.get("expression", "")
    for symbol in sorted(set(part for part in [s.strip() for s in expr.replace("(", " ").replace(")", " ").replace(",", " ").split()] if part.isidentifier())):
        if symbol.isupper():
            continue
    if "converged" in entry and entry.get("converged") not in ("", None):
        errors.append("forbidden:converged_standalone")
    if any(word in entry.get("semantics", "") for word in ["证明了", "解决了", "唯一真理"]) and entry.get("proof_status") not in {"PROVED_IN_DECLARED_SYSTEM", "EXTERNAL_THEOREM"}:
        errors.append("strong_claim_without_proof_status")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl_path", type=Path)
    args = parser.parse_args()
    seen = set()
    failures = []
    for line_no, line in enumerate(args.jsonl_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry["id"] in seen:
            failures.append((line_no, "duplicate_id"))
        seen.add(entry["id"])
        for err in validate_entry(entry):
            failures.append((line_no, err))
    if failures:
        for line_no, err in failures:
            print(f"line {line_no}: {err}")
        return 1
    print(f"validated {len(seen)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""",
        encoding="utf-8",
    )
    sample_dir = ROOT / "tests" / "fixtures"
    sample_dir.mkdir(parents=True, exist_ok=True)
    sample_path = sample_dir / "math-foundation-valid-sample.jsonl"
    sample = {
        "id": "SAMPLE-001",
        "title": "Sample Predicate",
        "object_type": "PREDICATE",
        "domain": "AgentState",
        "codomain": "{0,1}",
        "variables": [{"name": "x", "type": "AgentState", "unit": "dimensionless"}],
        "units": "dimensionless",
        "assumptions": ["sample assumption"],
        "expression": "P(x)=1",
        "semantics": "A sample well-formed predicate.",
        "scope": "demo only",
        "boundary_conditions": ["none"],
        "failure_conditions": ["counterexample observed"],
        "sources": ["tests/fixtures/source.md"],
        "proof_obligations": ["type correctness"],
        "validation_method": ["manual review"],
        "workflow_status": "draft",
        "formal_status": "WELL_FORMED",
        "proof_status": "DEFINITION_ONLY",
        "evidence_status": "SOURCE_ONLY",
        "scope_status": "bounded",
        "provenance_status": "DIRECT_SOURCE_FOUND",
    }
    sample_path.write_text(json.dumps(sample, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write artifacts")
    args = parser.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FOUNDATION_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)

    items = collect_formal_items() + collect_candidate_and_pending_items()
    items.sort(key=lambda i: (i.current_status, i.formal_layer, i.id))
    note_stats = [stat_path(p) for p in gather_note_paths()]

    ledger_rows = [item.__dict__ for item in items]
    formal_schema, provenance_schema = build_schema_files()
    pilot_items = select_pilot_items(items)

    outputs = {
        REPORT_DIR / f"local-note-sync-report-{DATE_STAMP}.md": render_note_sync_report(note_stats),
        REPORT_DIR / f"full-object-inventory-{DATE_STAMP}.md": render_inventory_report(items),
        REPORT_DIR / f"provenance-audit-{DATE_STAMP}.md": render_provenance_report(items),
        REPORT_DIR / f"pilot-formal-audit-{DATE_STAMP}.md": render_pilot_report(pilot_items),
        REPORT_DIR / f"blockers-{DATE_STAMP}.md": render_blockers(note_stats, items),
        FOUNDATION_DATA_DIR / "function-provenance-ledger.csv": None,
        FOUNDATION_DATA_DIR / "function-provenance-ledger.jsonl": None,
        SCHEMA_DIR / "ignition-formal-entry.schema.json": json.dumps(formal_schema, ensure_ascii=False, indent=2) + "\n",
        SCHEMA_DIR / "ignition-provenance-entry.schema.json": json.dumps(provenance_schema, ensure_ascii=False, indent=2) + "\n",
    }

    if args.write:
        write_constitution_docs()
        for path, content in outputs.items():
            if content is None:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        write_csv(FOUNDATION_DATA_DIR / "function-provenance-ledger.csv", ledger_rows)
        write_jsonl(FOUNDATION_DATA_DIR / "function-provenance-ledger.jsonl", ledger_rows)
        write_validator(formal_schema, provenance_schema)

        summary = {
            "generated_at": datetime.now().isoformat(),
            "formal_count": sum(1 for i in items if i.source_kind == "formal_table"),
            "candidate_only_count": sum(1 for i in items if i.current_status == "candidate_only"),
            "pending_count": sum(1 for i in items if i.current_status == "pending"),
            "provenance_counts": Counter(i.provenance_status for i in items),
            "pilot_count": len(pilot_items),
            "type_errors": sum(1 for i in items if i.type_issue),
            "counterexamples": sum(1 for i in items if i.counterexample_flag),
            "non_function_recommendations": sum(1 for i in items if i.recommend_non_function),
        }
        (REPORT_DIR / f"summary-{DATE_STAMP}.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    else:
        print(json.dumps({"items": len(items), "pilot": len(pilot_items)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
