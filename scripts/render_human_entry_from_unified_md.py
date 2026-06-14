#!/usr/bin/env python3
"""Render bilingual human-readable entrances from unified function/case tables.

The source of truth remains the reconstructed Markdown tables:

* data/functions/统一函数总表_470条_源文交叉重建版_v4.md
* data/cases/统一案例总表_578案例_源文交叉重建版_v4.md

This script converts them into:

* bilingual README entrance
* card-style FUNCTIONS.md / CASES.md
* bilingual docs/zh/functions.md / docs/zh/cases.md
* per-item detail pages
* machine-readable JSON / JSONL / minified JSON / markdown indexes
* a render report with counts and dangling references

The English layer is rule-generated with a conservative glossary. It is useful
for browsing and should still be reviewed by a human later.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Iterable, List, Sequence

from repository_overview_utils import count_repository_objects, render_repository_overview_block
from display_utils import format_bilingual_title, normalize_bilingual_text


REPO_ROOT = Path(__file__).resolve().parents[1]
FUNC_SOURCE = REPO_ROOT / "data/functions/统一函数总表_470条_源文交叉重建版_v4.md"
CASE_SOURCE = REPO_ROOT / "data/cases/统一案例总表_578案例_源文交叉重建版_v4.md"

OUT_FUNC_JSON = REPO_ROOT / "data/functions/unified-functions.json"
OUT_FUNC_JSONL = REPO_ROOT / "data/functions/unified-functions.jsonl"
OUT_FUNC_MIN_JSON = REPO_ROOT / "data/functions/unified-functions.min.json"
OUT_FUNC_INDEX_MD = REPO_ROOT / "data/functions/unified-functions-index.md"
OUT_FUNC_META_JSON = REPO_ROOT / "data/functions/meta-functions.json"
OUT_FUNC_META_JSONL = REPO_ROOT / "data/functions/meta-functions.jsonl"
OUT_FUNC_META_INDEX_MD = REPO_ROOT / "data/functions/meta-functions-index.md"
OUT_FUNC_BOOTSTRAP_TABLE_JSON = REPO_ROOT / "data/functions/bootstrap-meta-function-table.json"
OUT_FUNC_BOOTSTRAP_TABLE_JSONL = REPO_ROOT / "data/functions/bootstrap-meta-function-table.jsonl"
OUT_FUNC_BOOTSTRAP_TABLE_MD = REPO_ROOT / "data/functions/bootstrap-meta-function-table.md"
OUT_FUNC_DERIVATION_SUPPLEMENTS_JSON = REPO_ROOT / "data/functions/function-derivation-supplements.json"
OUT_MATH_FORMALIZATION_SUPPLEMENTS_JSON = REPO_ROOT / "data/rebuild/math-formalization-supplements.json"

OUT_CASE_JSON = REPO_ROOT / "data/cases/unified-cases.json"
OUT_CASE_JSONL = REPO_ROOT / "data/cases/unified-cases.jsonl"
OUT_CASE_MIN_JSON = REPO_ROOT / "data/cases/unified-cases.min.json"
OUT_CASE_INDEX_MD = REPO_ROOT / "data/cases/unified-cases-index.md"

OUT_REPORT = REPO_ROOT / "data/rebuild/human-entry-render-report.md"

README = REPO_ROOT / "README.md"
ROOT_FUNCTIONS = REPO_ROOT / "FUNCTIONS.md"
ROOT_CASES = REPO_ROOT / "CASES.md"
ROOT_DISCOVERIES = REPO_ROOT / "DISCOVERIES.md"
DOC_FUNC_INDEX = REPO_ROOT / "docs/zh/functions.md"
DOC_FUNC_META_DIR = REPO_ROOT / "docs/zh/functions/meta"
DOC_FUNC_META_ITEMS_DIR = REPO_ROOT / "docs/zh/functions/meta/items"
DOC_CASE_INDEX = REPO_ROOT / "docs/zh/cases.md"
DOC_FUNC_DIR = REPO_ROOT / "docs/zh/functions/items"
DOC_CASE_DIR = REPO_ROOT / "docs/zh/cases/items"
DOC_DISC_DIR = REPO_ROOT / "docs/zh/discoveries/items"

OUT_DISC_JSON = REPO_ROOT / "data/discoveries/unified-discoveries.json"
OUT_DISC_JSONL = REPO_ROOT / "data/discoveries/unified-discoveries.jsonl"
OUT_DISC_INDEX_MD = REPO_ROOT / "data/discoveries/unified-discoveries-index.md"

PROJECT_POSITIONING_ZH = "《点火》不是一本固定成书，也不是单个人类传记式项目，而是一个开放维护的函数、案例、发现、预测与新答案知识库。"
PROJECT_POSITIONING_EN = "When Systems Catch Fire is not a fixed book or a single-human biographical project, but an open and maintained knowledge base of functions, cases, discoveries, predictions, and new answers."
PROJECT_POSITIONING_LOCK = "项目定位锁定 / Project positioning lock：以上定位为当前仓库的规范定位，任何 agent、脚本或人工改写不得把项目定位改回“一个人类”叙事或旧书稿定位；如需调整，必须新增独立变更说明并通过仓库验证。"


STATUS_TRANSLATIONS = {
    "CROSS_VERIFIED": "交叉验证 / Cross-verified",
    "GETNOTE_ONLY": "仅来自原始笔记 / From source notes only",
    "SINGLE_SOURCE": "单源 / Single source",
}

LEVEL_TRANSLATIONS = {
    "公理": "Axiom",
    "定理": "Theorem",
    "推论": "Derived function",
}

COMMON_TRANSLATIONS: list[tuple[str, str]] = [
    ("模拟8步资源投入", "simulate 8-step resource allocation"),
    ("先防守后进攻", "defend first, attack later"),
    ("级联防御", "cascade defense"),
    ("贪心优化", "greedy optimization"),
    ("门槛附近维度", "threshold-near dimension"),
    ("弹性最高维度", "highest-elasticity dimension"),
    ("无需人为切换", "no manual switching required"),
    ("系统状态", "system state"),
    ("第5步跑通但留隐患", "Step 5 validated but leaves a hidden risk"),
    ("第5步跑通", "Step 5 validated"),
    ("第4步跑通", "Step 4 validated"),
    ("第3步未满足", "Step 3 not satisfied"),
    ("第2步未满足", "Step 2 not satisfied"),
    ("第5步延迟300年", "Step 5 delayed by 300 years"),
    ("资源投入", "resource allocation"),
    ("数学必然", "mathematical necessity"),
    ("提议者意识", "proposer awareness"),
    ("提议者姿态的激进程度", "proposer posture aggressiveness"),
    ("应约者感知退出权", "perceived responder exit right"),
    ("应约者退出权", "responder exit right"),
    ("退出权", "exit right"),
    ("感知退出权", "perceived exit right"),
    ("退出概率", "exit probability"),
    ("退出成本", "exit cost"),
    ("遮蔽函数（双源）", "obscuration function (dual-source)"),
    ("遮蔽函数", "obscuration function"),
    ("遮蔽", "obscuration"),
    ("决策维度", "decision dimension"),
    ("点火充要条件", "ignition necessary and sufficient condition"),
    ("乘法归零律", "multiplication zero law"),
    ("ε双向动力学", "epsilon bidirectional dynamics"),
    ("乘法对称变换", "multiplicative symmetry transform"),
    ("凯利公式认知边界", "Kelly-formula cognitive boundary"),
    ("自举激活条件", "bootstrap activation condition"),
    ("好奇心驱动函数", "curiosity-driven function"),
    ("ε相变级联", "epsilon phase-transition cascade"),
    ("自主意识函数", "autonomous consciousness function"),
    ("缓存倒U型", "cache inverted-U curve"),
    ("生存域函数", "survival domain function"),
    ("信息门效率统一", "information-gate efficiency unification"),
    ("三效率冲突三角约束", "three-efficiency conflict triangle constraint"),
    ("自举元函数层级", "bootstrap meta-function hierarchy"),
    ("乘法临界漂移统一", "multiplicative critical-drift unification"),
    ("两个反向单调函数相乘必然生成倒U型", "two oppositely monotone functions multiplied together necessarily generate an inverted-U curve"),
    ("Φ=零温自由能", "Phi = zero-temperature free energy"),
    ("跨域稳定性定理", "cross-domain stability theorem"),
    ("共生外部注入函数", "symbiotic external-injection function"),
    ("权力腐败函数", "power-corruption function"),
    ("物理大统一本质函数", "physical grand-unification essential function"),
    ("门控函数稳定性必要条件", "necessary condition for gate-function stability"),
    ("高斯门控函数", "Gaussian gate function"),
    ("门控函数进化三阶段", "three-stage evolution of gate functions"),
    ("门控-路径积分同构与极小熵原理", "gate / path-integral isomorphism and minimum-entropy principle"),
    ("门控信息熵跃迁函数", "gate information-entropy transition function"),
    ("认知分辨率函数", "cognitive resolution function"),
    ("A-B型门控面冲突函数", "A-B type gate-surface conflict function"),
    ("量子引力Φ框架函数", "quantum-gravity Phi framework function"),
    ("点火", "Ignition"),
    ("跑通", "validated"),
    ("未满足", "not satisfied"),
    ("部分满足", "partially satisfied"),
    ("进行中", "in progress"),
    ("未在当前函数表中找到", "not found in the current function table"),
    ("未在当前案例表中找到", "not found in the current case table"),
    ("退出权信号", "exit-right signal"),
    ("应约者退出的成本", "responder exit cost"),
    ("认知规范破缺函数", "cognitive norm-breaking function"),
]

CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8").splitlines()


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, value) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, rows: Sequence[dict]) -> None:
    body = "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows)
    write_text(path, body + ("\n" if body else ""))


def read_json_file(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return default
    return json.loads(text)


REFERENCE_CACHE: dict[str, object] = {}


def rel_link(from_path: Path, to_path: Path) -> str:
    return os.path.relpath(to_path, from_path.parent).replace(os.sep, "/")


def is_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and not stripped.startswith("|---")


def normalize_pipe_literals(text: str) -> str:
    return text.replace("\\|", "[[PIPE]]")


def restore_pipe_literals(text: str) -> str:
    return text.replace("[[PIPE]]", "|")


def split_row(line: str) -> List[str]:
    safe = normalize_pipe_literals(line.strip())
    parts = [part.strip() for part in safe.split("|")]
    return [restore_pipe_literals(part) for part in parts]


def source_ref_to_note_id(source_ref: str) -> str:
    source_ref = source_ref.strip()
    if source_ref.startswith("getnote:"):
        parts = source_ref.split(":")
        if len(parts) >= 2:
            return parts[1]
    if ":" in source_ref:
        return source_ref.rsplit(":", 1)[0]
    return source_ref


def source_ref_to_file(source_ref: str) -> str:
    source_ref = source_ref.strip()
    if ":" in source_ref:
        return source_ref.rsplit(":", 1)[0]
    return source_ref


def clean_title(text: str) -> str:
    text = restore_pipe_literals(text).strip()
    text = re.sub(r"[，,。．.\s]+$", "", text)
    return text.strip()


def strip_markdown_links(text: str) -> str:
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)


def normalize_signature(text: str) -> str:
    text = strip_markdown_links(text)
    chars: list[str] = []
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
            chars.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            chars.append(ch)
        elif ch == "|" and depth > 0:
            chars.append(",")
        else:
            chars.append(ch)
    normalized = "".join(chars)
    normalized = re.sub(r"\s*,\s*", ",", normalized)
    return normalized


def strip_formula_prefix(text: str) -> str:
    stripped = re.sub(r"^[A-Za-zΦΨΩμσΔεθρλγβ0-9_(),\s]+", "", text).strip()
    return stripped or text.strip()


def translate_text(text: str) -> str:
    if not text:
        return ""

    result = text
    # Longer phrases first.
    for zh, en in sorted(COMMON_TRANSLATIONS, key=lambda item: len(item[0]), reverse=True):
        result = result.replace(zh, en)

    replacements = {
        "（": "(",
        "）": ")",
        "：": ": ",
        "；": "; ",
        "、": ", ",
        "。": ". ",
        "，": ", ",
        "—": " - ",
        "→": " -> ",
        "×": " x ",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "／": "/",
        "｜": "|",
        "\u3000": " ",
    }
    for src, dst in replacements.items():
        result = result.replace(src, dst)

    result = re.sub(r"\s+", " ", result)
    result = result.replace(" ,", ",").replace(" .", ".").replace(" :", ":")
    return result.strip()


def safe_english(text: str) -> str:
    """Return a conservative English rendering with no Chinese characters."""
    if not text:
        return ""
    if CJK_RE.search(text):
        return "Rule-based English rendering pending human review."
    return text


def translate_level(level: str) -> str:
    if level in LEVEL_TRANSLATIONS:
        return LEVEL_TRANSLATIONS[level]
    translated = translate_text(level)
    translated = translated.replace("格 ", "Tier ")
    translated = translated.replace("Tier  ", "Tier ")
    return translated


def translate_status(status: str) -> str:
    return STATUS_TRANSLATIONS.get(status, translate_text(status))


def render_bilingual(zh: str, en: str, label_zh: str = "中文", label_en: str = "English") -> str:
    lines = [f"{label_zh}：{zh or '—'}", f"{label_en}: {en or '—'}"]
    return "\n".join(lines)


def parse_function_middle(middle_parts: List[str]) -> tuple[str, str]:
    blob = " | ".join(middle_parts).strip()
    blob = restore_pipe_literals(blob)
    if not blob:
        return "", ""

    if "—" in blob:
        left, right = blob.split("—", 1)
        title = clean_title(normalize_signature(left).strip())
        content = right.strip()
        return title, content

    assign = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=", blob)
    if assign:
        left = blob[: assign.start()].strip()
        var = assign.group(1)
        right = blob[assign.start():].strip()
        title = clean_title(normalize_signature(left).strip())
        content = right
        if title.endswith(var):
            title = title[: -len(var)].rstrip(" ，,")
        return title, content

    title = clean_title(normalize_signature(blob).strip())
    return title, ""


def parse_case_middle(middle_parts: List[str]) -> tuple[str, str, str]:
    blob = " | ".join(middle_parts).strip()
    blob = restore_pipe_literals(blob)
    if not blob:
        return "", "", ""

    if "—" in blob:
        left, right = blob.split("—", 1)
        title = clean_title(normalize_signature(left).strip())
        content = right.strip()
        return title, content, ""

    assign = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=", blob)
    if assign:
        left = blob[: assign.start()].strip()
        var = assign.group(1)
        right = blob[assign.start():].strip()
        title = clean_title(normalize_signature(left).strip())
        if title.endswith(var):
            title = title[: -len(var)].rstrip(" ，,")
        return title, right, ""

    title = clean_title(normalize_signature(blob).strip())
    return title, "", ""


def parse_function_table(path: Path) -> List[dict]:
    lines = read_lines(path)
    header_idx = next((i for i, line in enumerate(lines) if "| 序 | 函数ID |" in line), None)
    if header_idx is None:
        raise RuntimeError(f"Could not find function table header in {path}")

    records: List[dict] = []
    for lineno in range(header_idx + 2, len(lines) + 1):
        line = lines[lineno - 1]
        if not is_row(line):
            if records:
                break
            continue
        parts = split_row(line)
        if len(parts) < 10:
            raise RuntimeError(f"Malformed function row at {path}:{lineno}: {line}")

        seq = parts[1]
        fid = strip_markdown_links(parts[2]).strip()
        level_zh = strip_markdown_links(parts[3]).strip()
        middle_parts = [strip_markdown_links(part) for part in parts[4:-4]]
        source_ref = parts[-4]
        source_type = parts[-3]
        status = parts[-2]

        if len(middle_parts) == 1:
            title_zh = normalize_signature(middle_parts[0]).strip()
            content_zh = ""
        elif len(middle_parts) == 2:
            if not middle_parts[1].strip():
                title_zh = clean_title(normalize_signature(middle_parts[0]).strip())
                content_zh = ""
            elif ("=" in middle_parts[0]) or (middle_parts[0].count("(") > middle_parts[0].count(")")) or middle_parts[0].endswith("("):
                title_zh, content_zh = parse_function_middle(middle_parts)
            else:
                title_zh = clean_title(normalize_signature(middle_parts[0]).strip())
                content_zh = restore_pipe_literals(middle_parts[1].strip())
        else:
            title_zh, content_zh = parse_function_middle(middle_parts)

        if not title_zh.strip():
            title_zh = fid

        concept_zh = strip_formula_prefix(title_zh)
        explanation_zh = (
            f"该函数通过 {content_zh} 描述 {concept_zh}。"
            if content_zh
            else f"该函数用于刻画 {concept_zh}。"
        )

        record = {
            "id": fid,
            "normalized_id": fid,
            "title": {
                "zh": title_zh,
                "en": normalize_bilingual_text(title_zh, translate_text(title_zh)),
            },
            "title_text": title_zh,
            "level": {
                "zh": level_zh,
                "en": normalize_bilingual_text(level_zh, translate_level(level_zh)),
            },
            "level_text": level_zh,
            "status": status,
            "status_text": translate_status(status),
            "content": {
                "zh": content_zh,
                "en": normalize_bilingual_text(content_zh, translate_text(content_zh)) if content_zh else "",
            },
            "explanation": {
                "zh": explanation_zh,
                "en": normalize_bilingual_text(explanation_zh, translate_text(explanation_zh)),
            },
            "source": {
                "source_table": str(path.relative_to(REPO_ROOT)),
                "source_line": lineno,
                "source_note_id": source_ref_to_note_id(source_ref),
                "source_file": source_ref_to_file(source_ref),
                "source_reference": source_ref,
                "source_type": source_type,
                "raw_excerpt": line.strip(),
            },
            "links": {
                "human_page": f"docs/zh/functions/items/{fid}.md",
            },
            "_seq": int(seq),
            "_source_middle": " | ".join(middle_parts).strip(),
        }
        records.append(record)

    if not records:
        raise RuntimeError(f"No functions parsed from {path}")

    seen = set()
    for record in records:
        if record["id"] in seen:
            raise RuntimeError(f"Duplicate function ID detected: {record['id']}")
        seen.add(record["id"])
        if not record["title"]["zh"].strip():
            raise RuntimeError(f"Empty function title for {record['id']}")
    attach_function_derivations(records)
    attach_math_formalizations(records)
    return records


def attach_function_derivations(records: List[dict]) -> None:
    if not OUT_FUNC_DERIVATION_SUPPLEMENTS_JSON.exists():
        return
    supplements = json.loads(OUT_FUNC_DERIVATION_SUPPLEMENTS_JSON.read_text(encoding="utf-8"))
    by_id = {item["id"]: item.get("derivation") for item in supplements if item.get("id")}
    for record in records:
        derivation = by_id.get(record["id"])
        if derivation:
            record["derivation"] = derivation


def attach_math_formalizations(records: List[dict]) -> None:
    if not OUT_MATH_FORMALIZATION_SUPPLEMENTS_JSON.exists():
        return
    supplements = json.loads(OUT_MATH_FORMALIZATION_SUPPLEMENTS_JSON.read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in supplements if item.get("id")}
    for record in records:
        item = by_id.get(record.get("normalized_id")) or by_id.get(record.get("id"))
        if item:
            record["mathematical_formalization"] = item.get("mathematical_formalization")
            record["mathematical_derivation"] = item.get("mathematical_derivation")


def parse_case_table(path: Path) -> List[dict]:
    lines = read_lines(path)
    header_idx = next((i for i, line in enumerate(lines) if "| 序 | 案例ID |" in line), None)
    if header_idx is None:
        raise RuntimeError(f"Could not find case table header in {path}")

    records: List[dict] = []
    for lineno in range(header_idx + 2, len(lines) + 1):
        line = lines[lineno - 1]
        if not is_row(line):
            if records:
                break
            continue
        parts = split_row(line)
        if len(parts) < 11:
            raise RuntimeError(f"Malformed case row at {path}:{lineno}: {line}")

        seq = parts[1]
        cid = strip_markdown_links(parts[2]).strip()
        title_zh = normalize_signature(parts[3]).strip() or cid
        level_zh = strip_markdown_links(parts[4]).strip()
        middle_parts = [strip_markdown_links(part) for part in parts[5:-3]]
        source_ref = parts[-3]
        status = parts[-2]

        core_functions_raw = middle_parts[0].strip() if len(middle_parts) >= 1 else ""
        case_description_raw = middle_parts[1].strip() if len(middle_parts) >= 2 else ""
        key_discovery_raw = " | ".join(part.strip() for part in middle_parts[2:]).strip()

        content_lines_zh: list[str] = []
        if case_description_raw:
            content_lines_zh.append(f"案例说明：{case_description_raw}")
        if key_discovery_raw:
            content_lines_zh.append(f"关键发现：{key_discovery_raw}")
        content_zh = "\n".join(content_lines_zh)

        content_lines_en: list[str] = []
        if case_description_raw:
            content_lines_en.append(f"Case description: {translate_text(case_description_raw)}")
        if key_discovery_raw:
            content_lines_en.append(f"Key discovery: {translate_text(key_discovery_raw)}")
        content_en = "\n".join(content_lines_en)

        explanation_zh = key_discovery_raw or case_description_raw or f"该案例围绕 {strip_formula_prefix(title_zh)} 展开。"
        explanation_en = translate_text(explanation_zh)

        numeric_match = re.search(r"#(\d+)", cid)
        numeric = int(numeric_match.group(1)) if numeric_match else 0
        normalized = f"C-{numeric:04d}"

        record = {
            "id": cid,
            "normalized_id": normalized,
            "title": {
                "zh": title_zh,
                "en": normalize_bilingual_text(title_zh, translate_text(title_zh)),
            },
            "title_text": title_zh,
            "level": {
                "zh": level_zh,
                "en": normalize_bilingual_text(level_zh, translate_level(level_zh)),
            },
            "level_text": level_zh,
            "status": status,
            "status_text": translate_status(status),
            "content": {
                "zh": content_zh,
                "en": normalize_bilingual_text(content_zh, content_en),
            },
            "explanation": {
                "zh": explanation_zh,
                "en": normalize_bilingual_text(explanation_zh, explanation_en),
            },
            "source": {
                "source_table": str(path.relative_to(REPO_ROOT)),
                "source_line": lineno,
                "source_note_id": source_ref_to_note_id(source_ref),
                "source_file": source_ref_to_file(source_ref),
                "source_reference": source_ref,
                "core_functions_raw": core_functions_raw,
                "case_description_raw": case_description_raw,
                "key_discovery_raw": key_discovery_raw,
                "raw_excerpt": line.strip(),
            },
            "links": {
                "human_page": f"docs/zh/cases/items/{normalized}.md",
            },
            "_seq": int(seq),
            "_source_middle": " | ".join(middle_parts).strip(),
        }
        records.append(record)

    if not records:
        raise RuntimeError(f"No cases parsed from {path}")

    seen = set()
    for record in records:
        if record["normalized_id"] in seen:
            raise RuntimeError(f"Duplicate case ID detected: {record['normalized_id']}")
        seen.add(record["normalized_id"])
        if not record["title"]["zh"].strip():
            raise RuntimeError(f"Empty case title for {record['id']}")
    attach_math_formalizations(records)
    return records


FUNC_REF_RE = re.compile(r"\b([ATD]\d{1,3})\b")


def extract_function_refs(text: str) -> List[str]:
    refs: List[str] = []
    seen = set()
    for match in FUNC_REF_RE.finditer(text):
        ref = match.group(1)
        if ref not in seen:
            seen.add(ref)
            refs.append(ref)
    return refs


def dedupe(seq: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def build_relationships(functions: List[dict], cases: List[dict]) -> dict:
    function_map = {f["id"]: f for f in functions}
    case_map = {c["normalized_id"]: c for c in cases}
    dangling: List[dict] = []

    for case in cases:
        raw_text = " ".join(
            [
                case["title"]["zh"],
                case["source"].get("core_functions_raw", ""),
                case["source"].get("case_description_raw", ""),
                case["source"].get("key_discovery_raw", ""),
            ]
        )
        related_ids = dedupe(extract_function_refs(raw_text))
        case["related_function_ids"] = related_ids
        related_objects = []
        for ref in related_ids:
            if ref in function_map:
                func = function_map[ref]
                related_objects.append(
                    {
                        "id": func["id"],
                        "normalized_id": func["normalized_id"],
                        "title": func["title"],
                        "page": f"docs/zh/functions/items/{func['id']}.md",
                        "found": True,
                    }
                )
            else:
                dangling.append(
                    {
                        "case": case["normalized_id"],
                        "case_title": case["title"]["zh"],
                        "ref": ref,
                        "source_line": case["source"]["source_line"],
                        "source_excerpt": case["source"]["raw_excerpt"],
                    }
                )
                related_objects.append(
                    {
                        "id": ref,
                        "normalized_id": ref,
                        "title": {
                            "zh": f"{ref}（未在当前函数表中找到）",
                            "en": f"{ref} (not found in the current function table)",
                        },
                        "page": None,
                        "found": False,
                    }
                )
        case["related_functions"] = related_objects

    for func in functions:
        related_cases = []
        for case in cases:
            if func["id"] in case.get("related_function_ids", []):
                related_cases.append(
                    {
                        "id": case["id"],
                        "normalized_id": case["normalized_id"],
                        "title": case["title"],
                        "page": f"docs/zh/cases/items/{case['normalized_id']}.md",
                        "found": True,
                    }
                )
        func["related_cases"] = related_cases

    return {
        "function_map": function_map,
        "case_map": case_map,
        "dangling": dangling,
    }


def minimal_functions(functions: List[dict]) -> List[dict]:
    return [
        {
            "id": f["id"],
            "normalized_id": f["normalized_id"],
            "title": f["title"],
            "level": f["level"],
            "status": f["status"],
            "related_case_count": len(f.get("related_cases", [])),
            "page": f["links"]["human_page"],
        }
        for f in functions
    ]


def minimal_cases(cases: List[dict]) -> List[dict]:
    return [
        {
            "id": c["id"],
            "normalized_id": c["normalized_id"],
            "title": c["title"],
            "level": c["level"],
            "status": c["status"],
            "related_function_count": len(c.get("related_functions", [])),
            "page": c["links"]["human_page"],
        }
        for c in cases
    ]


def render_markdown_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def slug_token(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def level_anchor(level: str) -> str:
    return f"function-level-{slug_token(translate_level(level) or level)}"


def case_range_anchor(start: int, end: int) -> str:
    return f"case-range-{start}-{end}"


def render_root_intro(title_zh: str, title_en: str, intro_zh: str, intro_en: str, quick_lines: list[str]) -> str:
    return "\n".join(
        [
            f"# {title_zh} / {title_en}",
            "",
            f"{intro_zh}",
            f"{intro_en}",
            "",
            "## 快速入口 / Quick Entry",
            "",
            *quick_lines,
            "",
        ]
    )


def render_function_detail_link(func: dict) -> str:
    return f"[{format_bilingual_title(func['title']['zh'], func['title']['en'])}]({func['links']['human_page']})"


def render_case_detail_link(case: dict) -> str:
    return f"[{format_bilingual_title(case['title']['zh'], case['title']['en'])}]({case['links']['human_page']})"


def link_known_references(text: str, current_path: Path) -> str:
    if not text:
        return text
    if "func_map" not in REFERENCE_CACHE:
        REFERENCE_CACHE["func_map"] = {row["id"]: row for row in read_json_file(OUT_FUNC_JSON, [])}
    if "case_rows" not in REFERENCE_CACHE:
        REFERENCE_CACHE["case_rows"] = read_json_file(OUT_CASE_JSON, [])
    func_map = REFERENCE_CACHE["func_map"]
    case_rows = REFERENCE_CACHE["case_rows"]
    case_by_norm = {row["normalized_id"]: row for row in case_rows}
    case_by_hash = {row["id"]: row for row in case_rows}

    def replace_function(match: re.Match) -> str:
        token = match.group(0)
        row = func_map.get(token)
        if not row:
            return token
        link = rel_link(current_path, REPO_ROOT / row["links"]["human_page"])
        return f"[{token}]({link})"

    def replace_case_norm(match: re.Match) -> str:
        token = match.group(0)
        row = case_by_norm.get(token)
        if not row:
            return token
        link = rel_link(current_path, REPO_ROOT / row["links"]["human_page"])
        return f"[{token}]({link})"

    def replace_case_hash(match: re.Match) -> str:
        token = match.group(0)
        row = case_by_hash.get(token)
        if not row:
            return token
        link = rel_link(current_path, REPO_ROOT / row["links"]["human_page"])
        return f"[{token}]({link})"

    protected = re.split(r"(`[^`]*`|\[[^\]]+\]\([^)]*\))", text)
    out: list[str] = []
    for part in protected:
        if not part or part.startswith("`") or re.match(r"\[[^\]]+\]\([^)]*\)", part):
            out.append(part)
            continue
        part = re.sub(r"\b(?:A|T|D)\d+\b", replace_function, part)
        part = re.sub(r"\bC-\d{4}\b", replace_case_norm, part)
        part = re.sub(r"(?<![\\w/])#\d{1,4}\b", replace_case_hash, part)
        out.append(part)
    return "".join(out)


def render_related_functions_block(case: dict, current_path: Path, limit: int | None = None) -> str:
    lines: list[str] = []
    for item in case.get("related_functions", [])[: limit or None]:
        if item.get("found"):
            link = rel_link(current_path, REPO_ROOT / item["page"])
            lines.append(f"- [{format_bilingual_title(item['title']['zh'], item['title']['en'])}]({link})")
        else:
            lines.append(f"- {item['title']['zh']} / {item['title']['en']}")
    if not lines:
        lines.append("- 暂无明确关联函数 / No explicit related functions yet.")
    return "\n".join(lines)


def render_related_cases_block(func: dict, current_path: Path, limit: int | None = None) -> str:
    lines: list[str] = []
    for item in func.get("related_cases", [])[: limit or None]:
        link = rel_link(current_path, REPO_ROOT / item["page"])
        lines.append(f"- [{format_bilingual_title(item['title']['zh'], item['title']['en'])}]({link})")
    if not lines:
        lines.append("- 暂无明确关联案例 / No explicit related cases yet.")
    return "\n".join(lines)


def render_derivation_block(func: dict, current_path: Path | None = None, limit: int | None = None) -> str:
    derivation = func.get("derivation") or {}
    if not derivation:
        return "暂无结构化推导补充 / No structured derivation supplement yet."
    steps = derivation.get("steps") or []
    if limit is not None:
        steps = steps[:limit]
    lines = [
        f"- 推导类型 / Derivation type: `{derivation.get('kind', 'unknown')}`",
        f"- 收敛状态 / Convergence status: `{derivation.get('status', 'unknown')}`",
    ]
    deps = (derivation.get("depends_on") or []) + (derivation.get("meta_depends_on") or [])
    if deps:
        lines.append(f"- 依赖 / Depends on: {', '.join(f'`{dep}`' for dep in deps)}")
    if steps:
        lines.append("- 过程 / Process:")
        lines.extend(f"  - {step}" for step in steps)
    constants = derivation.get("constant_derivations") or []
    if constants:
        lines.append("- 常数项 / Constants:")
        for item in constants[: limit or None]:
            lines.append(
                f"  - `{item.get('value')}`: {item.get('class')} / {item.get('status')} - {item.get('derivation')}"
            )
    return "\n".join(lines)


def render_math_formalization_block(item: dict) -> str:
    formal = item.get("mathematical_formalization") or {}
    derivation = item.get("mathematical_derivation") or {}
    if not formal or not derivation:
        return "暂无纯数学函数与数学推导 / No pure mathematical function and derivation yet."
    lines = [
        f"- 对象 / Object: `{formal.get('symbol', '')}`",
        f"- 定义域 / Domain: `{formal.get('domain', '')}`",
        f"- 值域 / Codomain: `{formal.get('codomain', '')}`",
        f"- 数学表达 / Expression: `{formal.get('math_expression', '')}`",
        f"- 有效条件 / Validity: `{formal.get('validity_condition', '')}`",
        f"- 推导类型 / Derivation type: `{derivation.get('kind', '')}`",
        f"- 收敛状态 / Convergence status: `{derivation.get('status', '')}`",
    ]
    deps = derivation.get("depends_on") or []
    lines.append(f"- 依赖 / Depends on: {', '.join(f'`{dep}`' for dep in deps) if deps else '`source_state`'}")
    steps = derivation.get("steps_math") or []
    if steps:
        lines.append("- 推导步骤 / Steps:")
        lines.extend(f"  - {step}" for step in steps)
    obligations = derivation.get("proof_obligations") or []
    if obligations:
        lines.append("- 证明义务 / Proof obligations:")
        lines.extend(f"  - `{item}`" for item in obligations)
    lines.extend(
        [
            f"- 正向检查 / Forward check: `{(derivation.get('forward_check') or {}).get('condition', '')}`",
            f"- 反向检查 / Reverse check: `{(derivation.get('reverse_check') or {}).get('condition', '')}`",
            f"- 收敛判据 / Convergence: `{derivation.get('convergence', '')}`",
        ]
    )
    return "\n".join(lines)


def render_function_card(func: dict, current_path: Path, related_limit: int = 5) -> str:
    title = format_bilingual_title(func["title"]["zh"], func["title"]["en"])
    detail_link = rel_link(current_path, REPO_ROOT / func["links"]["human_page"])
    content = func["content"]["zh"] or "暂无内容 / No content"
    content_en = safe_english(func["content"]["en"] or translate_text(content))
    explanation = func["explanation"]["zh"]
    explanation_en = safe_english(func["explanation"]["en"] or translate_text(explanation))
    related_block = render_related_cases_block(func, current_path, limit=related_limit)
    derivation_block = render_derivation_block(func, current_path, limit=2)
    math_block = render_math_formalization_block(func)
    more_line = ""
    if len(func.get("related_cases", [])) > related_limit:
        more_line = f"- 更多 / More: [查看函数详情 / View function page]({detail_link})"

    return "\n".join(
        [
            f"### [{func['id']}｜{title}]({detail_link})",
            "",
            "**函数内容 / Function Content**",
            f"中文：{link_known_references(content, current_path)}",
            f"English: {content_en}",
            "",
            "**说明 / Explanation**",
            f"中文：{link_known_references(explanation, current_path)}",
            f"English: {explanation_en}",
            "",
            "**纯数学函数与推导 / Pure Mathematical Function and Derivation**",
            math_block,
            "",
            "**推导补充 / Derivation Supplement**",
            derivation_block,
            "",
            "**关联案例 / Related Cases**",
            related_block,
            *(["", more_line] if more_line else []),
            "",
        ]
    )


def render_case_card(case: dict, current_path: Path, related_limit: int = 5) -> str:
    title = format_bilingual_title(case["title"]["zh"], case["title"]["en"])
    detail_link = rel_link(current_path, REPO_ROOT / case["links"]["human_page"])
    content = case["content"]["zh"] or "暂无内容 / No content"
    content_en = safe_english(case["content"]["en"] or translate_text(content))
    explanation = case["explanation"]["zh"]
    explanation_en = safe_english(case["explanation"]["en"] or translate_text(explanation))
    related_block = render_related_functions_block(case, current_path, limit=related_limit)
    math_block = render_math_formalization_block(case)
    more_line = ""
    if len(case.get("related_functions", [])) > related_limit:
        more_line = f"- 更多 / More: [查看案例详情 / View case page]({detail_link})"

    return "\n".join(
        [
            f"### [{case['id']}｜{title}]({detail_link})",
            "",
            "**案例内容 / Case Content**",
            f"中文：{link_known_references(content, current_path)}",
            f"English: {content_en}",
            "",
            "**它说明了什么 / What It Shows**",
            f"中文：{link_known_references(explanation, current_path)}",
            f"English: {explanation_en}",
            "",
            "**纯数学函数与推导 / Pure Mathematical Function and Derivation**",
            math_block,
            "",
            "**关联函数 / Related Functions**",
            related_block,
            *(["", more_line] if more_line else []),
            "",
        ]
    )


def load_meta_functions(path: Path = OUT_FUNC_META_JSON) -> List[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing meta function file: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    data = json.loads(text)
    if not isinstance(data, list):
        raise RuntimeError(f"Meta function file must contain a list: {path}")
    return data


def load_bootstrap_meta_table(path: Path = OUT_FUNC_BOOTSTRAP_TABLE_JSON) -> List[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing bootstrap meta function table file: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    data = json.loads(text)
    if not isinstance(data, list):
        raise RuntimeError(f"Bootstrap meta function table must contain a list: {path}")
    return data


def meta_text(value) -> str:
    if isinstance(value, dict):
        return str(value.get("text") or value.get("math") or "").strip()
    if value is None:
        return ""
    return str(value).strip()


def render_meta_function_related_block(meta: dict, current_path: Path) -> str:
    lines: list[str] = []
    for item in meta.get("related_objects", []):
        page = item.get("page")
        if not page:
            continue
        link = rel_link(current_path, REPO_ROOT / page)
        label = format_bilingual_title(item.get("title", {}).get("zh", item["id"]), item.get("title", {}).get("en", ""))
        lines.append(f"- [{label}]({link})")
    if not lines:
        lines.append("- 暂无明确关联对象 / No explicit related objects yet.")
    return "\n".join(lines)


def render_meta_function_card(meta: dict, current_path: Path) -> str:
    title = format_bilingual_title(meta["title"]["zh"], meta["title"]["en"])
    detail_link = rel_link(current_path, REPO_ROOT / meta["page"])
    expression = meta_text(meta.get("expression"))
    state_expression = meta_text(meta.get("state_expression"))
    bootstrap_cycle = meta_text(meta.get("bootstrap_cycle"))
    convergence = meta_text(meta.get("convergence"))
    related_block = render_meta_function_related_block(meta, current_path)
    source_refs = meta.get("source_refs", [])
    source_status = meta.get("source_status", "found")

    source_lines = [f"- `{ref}`" for ref in source_refs] or ["- `source_pending`"]

    extra_lines: list[str] = []
    if meta["id"] == "MF-0000":
        bootstrap_items = load_bootstrap_meta_table()
        internal_items = [item for item in bootstrap_items if item.get("id") != "MF-0000"]
        if internal_items:
            extra_lines.extend(
                [
                    "",
                    "**内部元算子 / Internal Meta-Operators**",
                    "",
                    "| 编号 / ID | 名称 / Title | 作用 / Role |",
                    "| --- | --- | --- |",
                ]
            )
            for item in internal_items:
                item_link = rel_link(current_path, REPO_ROOT / item["page"])
                item_title = format_bilingual_title(item["title"]["zh"], item["title"]["en"])
                role = item.get("role", "")
                role_map = {
                    "forward_channel": "计算 J⁺ / Computes J+",
                    "reverse_channel": "计算 J⁻ / Computes J-",
                    "exclusivity_judge": "排除 J⁺=J⁻=1 / Rejects J+=J-=1",
                    "nested_judge": "迭代 M_boot / Iterates M_boot",
                    "convergence_judge": "判定不动点 / Tests fixed point",
                }
                extra_lines.append(f"| [{item['id']}]({item_link}) | {item_title} | {role_map.get(role, role)} |")
            extra_lines.extend(
                [
                    "",
                    "**双通道结构 / Dual-channel Structure**",
                    "",
                    f"- [`bootstrap-meta-function-table.md`]({rel_link(current_path, OUT_FUNC_BOOTSTRAP_TABLE_MD)})",
                    f"- [`bootstrap-meta-function-table.json`]({rel_link(current_path, OUT_FUNC_BOOTSTRAP_TABLE_JSON)})",
                    f"- [`bootstrap-meta-function-table.jsonl`]({rel_link(current_path, OUT_FUNC_BOOTSTRAP_TABLE_JSONL)})",
                ]
            )

    return "\n".join(
        [
            f"### [{meta['id']}｜{title}]({detail_link})",
            "",
            "**位置 / Position**",
            "中文：M_boot 是作用于 B_n 的根元算子。",
            "English: M_boot is the root meta-operator acting on B_n.",
            "",
            "**定义 / Definition**",
            "中文：自举元函数是在抽象状态 B_n 上同时施加正向判定 J⁺ 与反向判定 J⁻，并通过归一化算子 N 达到不动点的元算子。",
            "English: The bootstrap meta-function is a meta-operator on an abstract state B_n that applies both J+ and J- and reaches a fixed point through a normalization operator N.",
            "",
            "**数学表达 / Mathematical Expression**",
            f"中文：{expression}",
            f"English: {expression.replace('×', 'x')}",
            "",
            "**状态空间 / State Space**",
            f"中文：{state_expression}",
            f"English: {state_expression.replace('×', 'x')}",
            "",
            "**自举循环 / Bootstrap Cycle**",
            f"中文：{bootstrap_cycle or 'B(n+1) = B(n) ⊕ ΔB(n)'}",
            f"English: {(bootstrap_cycle or 'B(n+1) = B(n) ⊕ ΔB(n)').replace('⊕', 'merge').replace('Δ', 'Delta')}",
            "",
            "**收敛判据 / Convergence Criteria**",
            f"中文：{convergence or '||ΔB_n|| = 0 且 ||ΔB_{n+1}|| = 0'}",
            f"English: {(convergence or '||DeltaB_n|| = 0 and ||DeltaB_n+1|| = 0').replace('Δ', 'Delta')}",
            "",
            "**三个因子 / Three Factors**",
            "- ε_sense(B_n)：状态可分辨度 / state distinguishability",
            "- P_track(B_n)：并行轨道容量 / parallel-track capacity",
            "- d(ΔK)/dt(B_n)：结构增量速率 / structural-increment rate",
            "",
            *extra_lines,
            "",
        ]
    )


def render_meta_function_page(meta: dict) -> str:
    current_path = DOC_FUNC_META_DIR / f"{meta['id']}.md"
    back_to_list = rel_link(current_path, DOC_FUNC_INDEX)
    back_to_root = rel_link(current_path, README)
    title = format_bilingual_title(meta["title"]["zh"], meta["title"]["en"])
    expression = meta_text(meta.get("expression"))
    state_expression = meta_text(meta.get("state_expression"))
    bootstrap_cycle = meta_text(meta.get("bootstrap_cycle"))
    convergence = meta_text(meta.get("convergence"))
    boundary_note = meta.get("boundary_note", {})
    boundary_note_zh = boundary_note.get("zh", "")
    boundary_note_en = boundary_note.get("en", "")
    source_refs = meta.get("source_refs", [])
    source_status = meta.get("source_status", "found")

    related_lines: list[str] = []
    for item in meta.get("related_objects", []):
        page = item.get("page")
        if not page:
            continue
        link = rel_link(current_path, REPO_ROOT / page)
        title_zh = item.get("title", {}).get("zh") or item["id"]
        title_en = item.get("title", {}).get("en", "")
        related_lines.append(f"- [{format_bilingual_title(title_zh, title_en)}]({link})")
    if not related_lines:
        related_lines.append("- 暂无明确关联对象 / No explicit related objects yet.")

    source_lines = [f"- `{ref}`" for ref in source_refs] or ["- `source_pending`"]

    dual = meta.get("dual_channel", {})
    dual_forward = dual.get("forward", "MF-0001")
    dual_reverse = dual.get("reverse", "MF-0002")
    dual_exclusivity = dual.get("exclusivity_judge", "MF-0003")
    dual_nested = dual.get("nested_judge", "MF-0004")
    dual_convergence = dual.get("convergence_judge", "MF-0005")

    return "\n".join(
        [
            f"# {meta['id']}｜{title}",
            "",
            f"[← 返回入口 / Back to Index]({back_to_list})",
            f"[返回仓库首页 / Back to Repository Home]({back_to_root})",
            "",
            "## 位置 / Position",
            "",
            "中文：M_boot 是作用于 B_n 的根元算子。",
            "English: M_boot is the root meta-operator acting on B_n.",
            "",
            "## 定义 / Definition",
            "",
            "中文：自举元函数是在抽象状态 B_n 上同时施加正向判定 J⁺ 与反向判定 J⁻，并通过归一化算子 N 达到不动点的元算子。",
            "English: The bootstrap meta-function is a meta-operator on an abstract state B_n that applies both J+ and J- and reaches a fixed point through a normalization operator N.",
            "",
            "## 数学表达 / Mathematical Expression",
            "",
            f"中文：{expression}",
            f"English: {expression.replace('×', 'x')}",
            "",
            "## 三个因子 / Three Factors",
            "",
            "- ε_sense(B_n)：状态可分辨度 / state distinguishability",
            "- P_track(B_n)：并行轨道容量 / parallel-track capacity",
            "- d(ΔK)/dt(B_n)：结构增量速率 / structural-increment rate",
            "",
            "## 自举循环 / Bootstrap Cycle",
            "",
            f"中文：{bootstrap_cycle or 'B(n+1) = B(n) ⊕ ΔB(n)'}",
            f"English: {(bootstrap_cycle or 'B(n+1) = B(n) ⊕ ΔB(n)').replace('⊕', 'merge').replace('Δ', 'Delta')}",
            "",
            "## 状态空间 / State Space",
            "",
            f"中文：{state_expression}",
            f"English: {state_expression.replace('×', 'x')}",
            "",
            "## 正反双通道 / Forward-Reverse Dual Channel",
            "",
            "中文：对任意 x∈X_n，同时计算 J_n⁺(x) 与 J_n⁻(x)。J_n⁺(x)=1 且 J_n⁻(x)=0 时接受 x；J_n⁺(x)=0 且 J_n⁻(x)=1 时接受 ¬x；J_n⁺(x)=J_n⁻(x)=1 时判为 contradiction；J_n⁺(x)=J_n⁻(x)=0 时判为 underdetermined。",
            "English: For every x in X_n, compute J_n+(x) and J_n-(x). Accept x when J_n+(x)=1 and J_n-(x)=0; accept not-x when J_n+(x)=0 and J_n-(x)=1; mark contradiction when both are 1; mark underdetermined when both are 0.",
            "",
            "## 判定表 / Judgment Table",
            "",
            "| J⁺(x) | J⁻(x) | Result | Meaning |",
            "|---:|---:|---|---|",
            "| 1 | 0 | true | x holds |",
            "| 0 | 1 | false | x does not hold |",
            "| 1 | 1 | contradiction | bootstrap fails |",
            "| 0 | 0 | underdetermined | evidence or evaluator insufficient |",
            "| ⊥ | any | pending | unresolved |",
            "| any | ⊥ | pending | unresolved |",
            "",
            "## 自举嵌套 / Bootstrap Nesting",
            "",
            "中文：嵌套定义为 M_boot^(k+1)(B_n)=M_boot(M_boot^k(B_n))。若存在 k 使 M_boot^(k+1)(B_n)=M_boot^k(B_n)，且不存在 (J⁺,J⁻)=(1,1)，则嵌套层达到稳定。",
            "English: Nesting is defined as M_boot^(k+1)(B_n)=M_boot(M_boot^k(B_n)). If some k satisfies M_boot^(k+1)(B_n)=M_boot^k(B_n) and no (J+,J-)=(1,1) remains, the nested layer is stable.",
            "",
            "## 收敛判据 / Convergence Criteria",
            "",
            f"中文：{convergence or '||ΔB_n|| = 0 ∧ ||ΔB_(n+1)|| = 0 ∧ LinkGraphStable(B_n) ∧ DynamicCountsStable(B_n) ∧ NoDuplicateLabels(B_n) ∧ AcademicNoveltyGate(B_n)'}",
            f"English: {(convergence or '||DeltaB_n|| = 0 and ||DeltaB_n+1|| = 0 and LinkGraphStable(B_n) and DynamicCountsStable(B_n) and NoDuplicateLabels(B_n) and AcademicNoveltyGate(B_n)').replace('Δ', 'Delta')}",
            "",
            "## 边界注释 / Boundary Note",
            "",
            f"中文：{boundary_note_zh or '自举收敛是当前目标函数与证据状态下的不动点，不等于目标函数绝对正确。'}",
            f"English: {boundary_note_en or 'Bootstrap convergence is a fixed point under the current target function and evidence state; it is not absolute correctness of the target function.'}",
            "",
            "## 双通道入口 / Dual-channel Entry",
            "",
            f"- [{dual_forward}｜正向自举通道 / Forward Bootstrap Channel]({rel_link(current_path, DOC_FUNC_META_ITEMS_DIR / f'{dual_forward}.md')})",
            f"- [{dual_reverse}｜反向自举通道 / Reverse Bootstrap Channel]({rel_link(current_path, DOC_FUNC_META_ITEMS_DIR / f'{dual_reverse}.md')})",
            f"- [{dual_exclusivity}｜正反互斥判定器 / Forward-Reverse Exclusivity Judge]({rel_link(current_path, DOC_FUNC_META_ITEMS_DIR / f'{dual_exclusivity}.md')})",
            f"- [{dual_nested}｜自举嵌套判定器 / Nested Bootstrap Judge]({rel_link(current_path, DOC_FUNC_META_ITEMS_DIR / f'{dual_nested}.md')})",
            f"- [{dual_convergence}｜自举收敛判定器 / Bootstrap Convergence Judge]({rel_link(current_path, DOC_FUNC_META_ITEMS_DIR / f'{dual_convergence}.md')})",
            "",
        ]
    )


def render_detail_function_page(func: dict) -> str:
    current_path = DOC_FUNC_DIR / f"{func['id']}.md"
    back_to_list = rel_link(current_path, DOC_FUNC_INDEX)
    back_to_root = rel_link(current_path, README)
    title = format_bilingual_title(func["title"]["zh"], func["title"]["en"])

    related_lines: list[str] = []
    for item in func.get("related_cases", []):
        link = rel_link(current_path, REPO_ROOT / item["page"])
        relation_zh = "该案例在源表中引用了该函数。"
        relation_en = "The source table links this case to the function."
        related_lines.append(
            "\n".join(
                [
                    f"- [{format_bilingual_title(item['title']['zh'], item['title']['en'])}]({link})",
                    f"  中文：{relation_zh}",
                    f"  English: {relation_en}",
                ]
            )
        )
    if not related_lines:
        related_lines.append("暂无明确关联案例。\nNo explicit related cases yet.")

    return "\n".join(
        [
            f"# {func['id']}｜{title}",
            "",
            f"[← 返回函数表 / Back to Functions]({back_to_list})",
            f"[返回仓库首页 / Back to Repository Home]({back_to_root})",
            "",
            "## 函数内容 / Function Content",
            "",
            "中文：",
            func["content"]["zh"] or "—",
            "",
            "English:",
            safe_english(func["content"]["en"] or translate_text(func["content"]["zh"])),
            "",
            "## 它解决的问题 / Problem It Addresses",
            "",
            "中文：",
            func["explanation"]["zh"],
            "",
            "English:",
            safe_english(func["explanation"]["en"] or translate_text(func["explanation"]["zh"])),
            "",
            "## 纯数学函数 / Pure Mathematical Function",
            "",
            "\n".join(render_math_formalization_block(func).splitlines()[:5]),
            "",
            "## 数学推导 / Mathematical Derivation",
            "",
            "\n".join(render_math_formalization_block(func).splitlines()[5:]),
            "",
            "## 推导补充 / Derivation Supplement",
            "",
            render_derivation_block(func, current_path),
            "",
            "## 关联案例 / Related Cases",
            "",
            *related_lines,
            "",
            "## 来源回指 / Source Reference",
            "",
            f"- 源总表 / Source table：`{func['source']['source_table']}`",
            f"- 源行 / Source line：{func['source']['source_line']}",
            f"- 来源笔记ID / Source note ID：`{func['source']['source_note_id']}`",
            f"- 来源文件 / Source file：`{func['source']['source_file']}`",
            "",
        ]
    )


def render_detail_case_page(case: dict) -> str:
    current_path = DOC_CASE_DIR / f"{case['normalized_id']}.md"
    back_to_list = rel_link(current_path, DOC_CASE_INDEX)
    back_to_root = rel_link(current_path, README)
    title = format_bilingual_title(case["title"]["zh"], case["title"]["en"])

    related_lines: list[str] = []
    for item in case.get("related_functions", []):
        if item.get("found"):
            link = rel_link(current_path, REPO_ROOT / item["page"])
            relation_zh = "该函数在源表中帮助解释本案例。"
            relation_en = "The function helps explain this case in the source table."
            related_lines.append(
                "\n".join(
                    [
                        f"- [{format_bilingual_title(item['title']['zh'], item['title']['en'])}]({link})",
                        f"  中文：{relation_zh}",
                        f"  English: {relation_en}",
                    ]
                )
            )
        else:
            related_lines.append(
                "\n".join(
                    [
                        f"- {item['title']['zh']}",
                        f"  中文：未在当前函数表中找到。",
                        f"  English: Not found in the current function table.",
                    ]
                )
            )
    if not related_lines:
        related_lines.append("暂无明确关联函数。\nNo explicit related functions yet.")

    return "\n".join(
        [
            f"# {case['normalized_id']}｜{title}",
            "",
            f"[← 返回案例表 / Back to Cases]({back_to_list})",
            f"[返回仓库首页 / Back to Repository Home]({back_to_root})",
            "",
            "## 案例内容 / Case Content",
            "",
            "中文：",
            case["content"]["zh"] or "—",
            "",
            "English:",
            safe_english(case["content"]["en"] or translate_text(case["content"]["zh"])),
            "",
            "## 它说明了什么 / What It Shows",
            "",
            "中文：",
            case["explanation"]["zh"],
            "",
            "English:",
            safe_english(case["explanation"]["en"] or translate_text(case["explanation"]["zh"])),
            "",
            "## 纯数学函数 / Pure Mathematical Function",
            "",
            "\n".join(render_math_formalization_block(case).splitlines()[:5]),
            "",
            "## 数学推导 / Mathematical Derivation",
            "",
            "\n".join(render_math_formalization_block(case).splitlines()[5:]),
            "",
            "## 关联函数 / Related Functions",
            "",
            *related_lines,
            "",
            "## 来源回指 / Source Reference",
            "",
            f"- 源总表 / Source table：`{case['source']['source_table']}`",
            f"- 源行 / Source line：{case['source']['source_line']}",
            f"- 来源笔记ID / Source note ID：`{case['source']['source_note_id']}`",
            f"- 来源文件 / Source file：`{case['source']['source_file']}`",
            "",
        ]
    )


def group_functions(functions: List[dict]) -> list[tuple[str, list[dict], bool]]:
    order = ["公理", "定理", "推论"]
    grouped: list[tuple[str, list[dict], bool]] = []
    for level in order:
        items = [f for f in functions if f["level"]["zh"] == level]
        if items:
            grouped.append((level, items, level == "公理"))
    other_levels = [lvl for lvl in sorted({f["level"]["zh"] for f in functions}) if lvl not in order]
    for level in other_levels:
        items = [f for f in functions if f["level"]["zh"] == level]
        if items:
            grouped.append((level, items, False))
    return grouped


def group_cases(cases: List[dict]) -> list[tuple[str, list[dict], bool]]:
    grouped: list[tuple[str, list[dict], bool]] = []
    total = len(cases)
    for start in range(1, total + 1, 100):
        end = min(start + 99, total)
        items = [c for c in cases if start <= c["_seq"] <= end]
        if items:
            grouped.append((f"#{start}–#{end}", items, start == 1))
    return grouped


def render_meta_functions_section(meta_functions: List[dict], current_path: Path) -> list[str]:
    if not meta_functions:
        return []
    bootstrap_items = load_bootstrap_meta_table()
    parts = [
        '<a id="section-0-bootstrap-meta-function"></a>',
        "<details open>",
        f"<summary>第 0 节：自举元函数 / Section 0: Bootstrap Meta-Function (1+5)</summary>",
        "",
    ]
    for meta in meta_functions:
        parts.append(render_meta_function_card(meta, current_path))
    parts.append("</details>")
    parts.append("")
    return parts


def render_functions_collection(functions: List[dict], current_path: Path) -> str:
    meta_functions = load_meta_functions()
    bootstrap_items = load_bootstrap_meta_table()
    total = len(functions)
    meta_count = len(meta_functions)
    bootstrap_internal = max(len(bootstrap_items) - 1, 0)
    meta_label = "root meta-function" if meta_count == 1 else "root meta-functions"
    quick_lines = [
        f"- [第 0 节 / Section 0](#section-0-bootstrap-meta-function)：{meta_count} 条主入口 + {bootstrap_internal} 条内部子项 / {meta_count} root entry + {bootstrap_internal} internal subitems",
        f"- [公理层 / Axioms](#{level_anchor('公理')})：{sum(1 for f in functions if f['level']['zh'] == '公理')} 条 / {sum(1 for f in functions if f['level']['zh'] == '公理')} entries",
        f"- [定理层 / Theorems](#{level_anchor('定理')})：{sum(1 for f in functions if f['level']['zh'] == '定理')} 条 / {sum(1 for f in functions if f['level']['zh'] == '定理')} entries",
        f"- [推论层 / Derived functions](#{level_anchor('推论')})：{sum(1 for f in functions if f['level']['zh'] == '推论')} 条 / {sum(1 for f in functions if f['level']['zh'] == '推论')} entries",
        f"- [普通函数 / Ordinary functions](#{level_anchor('推论')})：{total} 条 / {total} entries",
        f"- 机器数据 / Machine data：[`data/functions/meta-functions.json`](data/functions/meta-functions.json), [`data/functions/unified-functions.json`](data/functions/unified-functions.json)",
        f"- 双通道结构 / Dual-channel structure：[`data/functions/bootstrap-meta-function-table.md`](data/functions/bootstrap-meta-function-table.md), [`data/functions/bootstrap-meta-function-table.json`](data/functions/bootstrap-meta-function-table.json), [`data/functions/bootstrap-meta-function-table.jsonl`](data/functions/bootstrap-meta-function-table.jsonl)",
        f"- JSONL：[`data/functions/meta-functions.jsonl`](data/functions/meta-functions.jsonl), [`data/functions/unified-functions.jsonl`](data/functions/unified-functions.jsonl)",
        f"- 重建审计 / Rebuild audit：[`data/rebuild/human-entry-render-report.md`](data/rebuild/human-entry-render-report.md)",
    ]
    parts = [
        render_root_intro(
            "统一函数总表",
            "Unified Function Table",
            f"本表收录 {meta_count} 条第 0 节主入口、{bootstrap_internal} 条内部子项和 {total} 条普通函数。每条条目都包含编号、名称、函数内容、关联对象和来源回指。",
            f"This table contains {meta_count} Section 0 {meta_label}, {bootstrap_internal} internal subitems, and {total} ordinary functions. Each entry includes its ID, title, content, related objects, and source reference.",
            quick_lines,
        ),
    ]
    parts.extend(render_meta_functions_section(meta_functions, current_path))
    for level, items, open_flag in group_functions(functions):
        parts.extend(
            [
                f'<a id="{level_anchor(level)}"></a>',
                f"<details{' open' if open_flag else ''}>",
                f"<summary>{level} / {translate_level(level)} ({len(items)})</summary>",
                "",
            ]
        )
        for func in items:
            parts.append(render_function_card(func, current_path))
        parts.append("</details>")
        parts.append("")
    return "\n".join(parts)


def render_cases_collection(cases: List[dict], current_path: Path) -> str:
    total = len(cases)
    quick_lines = [
        *[
            f"- [#{start}–#{min(start + 99, total)}](#{case_range_anchor(start, min(start + 99, total))})"
            for start in range(1, total + 1, 100)
        ],
        f"- 机器数据 / Machine data：[`data/cases/unified-cases.json`](data/cases/unified-cases.json)",
        f"- JSONL：[`data/cases/unified-cases.jsonl`](data/cases/unified-cases.jsonl)",
        f"- 重建审计 / Rebuild audit：[`data/rebuild/human-entry-render-report.md`](data/rebuild/human-entry-render-report.md)",
    ]
    parts = [
        render_root_intro(
            "统一案例总表",
            "Unified Case Table",
            f"本表收录 {total} 个点火案例。每个案例都包含编号、案例内容、关联函数和来源回指。",
            f"This table contains {total} ignition cases. Each case includes its ID, content, related functions, and source reference.",
            quick_lines,
        ),
    ]
    for label, items, open_flag in group_cases(cases):
        start, end = label.removeprefix("#").split("–", 1)
        end = end.removeprefix("#")
        parts.extend(
            [
                f'<a id="{case_range_anchor(int(start), int(end))}"></a>',
                f"<details{' open' if open_flag else ''}>",
                f"<summary>{label} / {label}</summary>",
                "",
            ]
        )
        for case in items:
            parts.append(render_case_card(case, current_path))
        parts.append("</details>")
        parts.append("")
    return "\n".join(parts)


def render_index_page(
    title_zh: str,
    title_en: str,
    intro_zh: str,
    intro_en: str,
    links: list[str],
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
) -> str:
    parts = [
        f"# {title_zh} / {title_en}",
        "",
        intro_zh,
        intro_en,
        "",
        *links,
        "",
        render_markdown_table(headers, rows),
        "",
    ]
    return "\n".join(parts)


def update_readme() -> None:
    text = README.read_text(encoding="utf-8")
    top_intro = "\n".join(
        [
            "# When Systems Catch Fire / 点火",
            "",
            PROJECT_POSITIONING_ZH,
            PROJECT_POSITIONING_EN,
            "",
            PROJECT_POSITIONING_LOCK,
            "",
            "## 入口 / Entrance",
            "",
            render_repository_overview_block(count_repository_objects()),
            "",
        ]
    )

    current_block = "\n".join(
        [
            "## Current Structure / 当前结构",
            "",
            "| Layer | 中文说明 | 主要文件 / Files |",
            "| --- | --- | --- |",
            "| Functions | 点火函数层，保存第 0 节元函数与 D-X 普通函数及其结构化字段 | `data/functions/meta-functions.json`, `data/functions/meta-functions.jsonl`, `data/functions/meta-functions-index.md`, `data/functions/unified-functions.json`, `data/functions/unified-functions.jsonl`, `data/functions/items/` |",
            "| Cases | 案例层，保存案例与函数关系 | `data/cases/unified-cases.json`, `data/cases/unified-cases.jsonl`, `data/cases/items/` |",
            "| Discoveries | 新发现说明层，面向人类阅读和传播 | `DISCOVERIES.md`, `data/discoveries/unified-discoveries.json`, `data/discoveries/unified-discoveries.jsonl`, `docs/zh/discoveries/items/` |",
            "| Predictions | 预测说明层，面向人类阅读和验证 | `PREDICTIONS.md`, `data/predictions/unified-predictions.json`, `data/predictions/unified-predictions.jsonl`, `docs/zh/predictions/items/` |",
            "| Registry | 原始统一总表，作为生成 JSON 的来源 | `data/registry/统一函数总表.csv`, `data/registry/统一案例总表.csv` |",
            "| Legacy Book | 旧书籍结构，保留为历史材料 | `archive/book-legacy/` |",
            "| Raw Notes | 原始笔记与来源材料，不作为 canonical item | `dianhuo/originals/` |",
            "",
        ]
    )

    agents_block = "\n".join(
        [
            "## For AI Agents / 给 AI Agent",
            "",
            "1. Read `llms.txt`.",
            "2. Read `AGENT_ENTRY.md`.",
            "3. Use `data/functions/meta-functions.jsonl` for Section 0 meta-function lookup.",
            "4. Use `data/functions/unified-functions.jsonl` for ordinary function lookup.",
            "5. Use `data/cases/unified-cases.jsonl` for case lookup.",
            "6. Use `data/discoveries/unified-discoveries.jsonl` for structured discovery entries.",
            "7. Use `data/predictions/unified-predictions.jsonl` for structured prediction entries.",
            "8. Use `data/functions/items/*.json` and `data/cases/items/*.json` as canonical machine-readable records.",
            "",
            "Do not treat raw notes as canonical. Raw notes are sources. Current structured entries live under `data/functions/`, `data/cases/`, `data/discoveries/`, and `data/predictions/`.",
            "",
        ]
    )

    human_block = "\n".join(
        [
            "## Human Reading / 人类阅读入口",
            "",
            "- 中文函数入口 / Chinese functions: `FUNCTIONS.md`, `docs/zh/functions.md`",
            "- 中文案例入口 / Chinese cases: `CASES.md`, `docs/zh/cases.md`",
            "- 中文发现入口 / Chinese discoveries: `DISCOVERIES.md`, `docs/zh/discoveries/items/`",
            "- 中文预测入口 / Chinese predictions: `PREDICTIONS.md`, `docs/zh/predictions/items/`",
            "",
        ]
    )

    current_idx = text.find("## Current Structure / 当前结构")
    data_policy_idx = text.find("## Data Policy / 数据原则")
    if current_idx == -1 or data_policy_idx == -1:
        write_text(README, top_intro + text)
        return

    tail = text[data_policy_idx:]
    write_text(README, top_intro + "\n" + current_block + "\n" + agents_block + "\n" + human_block + tail)


def make_report(functions: List[dict], cases: List[dict], dangling: List[dict]) -> str:
    func_cases = sum(len(f.get("related_cases", [])) for f in functions)
    case_funcs = sum(len(c.get("related_functions", [])) for c in cases)
    dangling_lines = [
        f"- {item['case']} → {item['ref']} (line {item['source_line']})"
        for item in dangling[:30]
    ]
    if not dangling_lines:
        dangling_lines = ["- 无 / None"]
    elif len(dangling) > 30:
        dangling_lines.append(f"- … 还有 {len(dangling) - 30} 条 / {len(dangling) - 30} more")

    return "\n".join(
        [
            "# Human Entry Render Report / 人类入口渲染报告",
            "",
            "## Source Tables / 源表",
            "",
            f"- `{FUNC_SOURCE.relative_to(REPO_ROOT)}`",
            f"- `{CASE_SOURCE.relative_to(REPO_ROOT)}`",
            "",
            "## Counts / 数量",
            "",
            f"- 函数 / Functions：{len(functions)}",
            f"- 第 0 节元函数 / Section 0 meta-functions：{len(load_meta_functions())}",
            f"- 案例 / Cases：{len(cases)}",
            f"- 函数关联案例总数 / Function-related cases：{func_cases}",
            f"- 案例关联函数总数 / Case-related functions：{case_funcs}",
            f"- dangling references：{len(dangling)}",
            "",
            "## Dangling References / 悬空引用",
            "",
            *dangling_lines,
            "",
            "## Translation Note / 翻译说明",
            "",
            "English text was rule-generated and needs later human review.",
            "英文为规则翻译，后续仍需人工校订。",
            "",
            "## English Status / 英文状态",
            "",
            "中文：当前英文层为规则翻译，已去除明显中英混杂句，但仍需要后续人工校订。",
            "English: The current English layer is rule-generated. Obvious Chinese-English mixed sentences have been removed, but later human review is still required.",
            "",
        ]
    )


def write_outputs(functions: List[dict], cases: List[dict], dangling: List[dict]) -> None:
    meta_functions = load_meta_functions()
    ensure_dir(DOC_FUNC_DIR)
    ensure_dir(DOC_FUNC_META_DIR)
    ensure_dir(DOC_CASE_DIR)
    ensure_dir(OUT_REPORT.parent)

    for meta in meta_functions:
        write_text(DOC_FUNC_META_DIR / f"{meta['id']}.md", render_meta_function_page(meta))
    for func in functions:
        write_text(DOC_FUNC_DIR / f"{func['id']}.md", render_detail_function_page(func))
    for case in cases:
        write_text(DOC_CASE_DIR / f"{case['normalized_id']}.md", render_detail_case_page(case))

    write_text(ROOT_FUNCTIONS, render_functions_collection(functions, ROOT_FUNCTIONS))
    write_text(ROOT_CASES, render_cases_collection(cases, ROOT_CASES))
    write_text(DOC_FUNC_INDEX, render_functions_collection(functions, DOC_FUNC_INDEX))
    write_text(DOC_CASE_INDEX, render_cases_collection(cases, DOC_CASE_INDEX))

    meta_public = [{k: v for k, v in m.items() if not k.startswith("_")} for m in meta_functions]
    func_public = [{k: v for k, v in f.items() if not k.startswith("_")} for f in functions]
    case_public = [{k: v for k, v in c.items() if not k.startswith("_")} for c in cases]

    write_json(OUT_FUNC_META_JSON, meta_public)
    write_jsonl(OUT_FUNC_META_JSONL, meta_public)

    meta_rows = [
        [
            f"[{m['id']}]({rel_link(OUT_FUNC_META_INDEX_MD, REPO_ROOT / m['page'])})",
            format_bilingual_title(m["title"]["zh"], m["title"]["en"]),
            f"Section 0 / 第 0 节",
            m["status"],
            "no",
        ]
        for m in meta_public
    ]
    write_text(
        OUT_FUNC_META_INDEX_MD,
        render_index_page(
            "元函数机器索引",
            "Meta Function Machine Index",
            "机器可读索引，保留第 0 节元函数的中英标题、状态和是否计入普通函数。",
            "Machine-readable index that keeps Section 0 meta-function titles, status, and whether the entry counts as an ordinary function.",
            [
                "- [`data/functions/meta-functions.json`](meta-functions.json)",
                "- [`data/functions/meta-functions.jsonl`](meta-functions.jsonl)",
            ],
            ["编号 / ID", "名称 / Title", "位置 / Position", "状态 / Status", "计入普通函数 / Counted as ordinary"],
            meta_rows,
        ),
    )

    write_json(OUT_FUNC_JSON, func_public)
    write_jsonl(OUT_FUNC_JSONL, func_public)
    write_json(OUT_FUNC_MIN_JSON, minimal_functions(func_public))

    func_rows = [
        [
            f"[{f['id']}]({f['links']['human_page']})",
            format_bilingual_title(f["title"]["zh"], f["title"]["en"]),
            f"{f['level']['zh']} / {f['level']['en']}",
            f["status_text"],
            str(len(f.get("related_cases", []))),
        ]
        for f in func_public
    ]
    write_text(
        OUT_FUNC_INDEX_MD,
        render_index_page(
            "函数机器索引",
            "Function Machine Index",
            "机器可读索引，保留中文标题、英文标题、层级、状态和关联计数。",
            "Machine-readable index that keeps Chinese titles, English titles, levels, status, and relation counts.",
            [
                "- [`data/functions/unified-functions.json`](unified-functions.json)",
                "- [`data/functions/unified-functions.jsonl`](unified-functions.jsonl)",
            ],
            ["编号 / ID", "名称 / Title", "层级 / Level", "状态 / Status", "关联案例 / Related cases"],
            func_rows,
        ),
    )

    write_json(OUT_CASE_JSON, case_public)
    write_jsonl(OUT_CASE_JSONL, case_public)
    write_json(OUT_CASE_MIN_JSON, minimal_cases(case_public))

    case_rows = [
        [
            f"[{c['id']}]({c['links']['human_page']})",
            format_bilingual_title(c["title"]["zh"], c["title"]["en"]),
            f"{c['level']['zh']} / {c['level']['en']}",
            c["status_text"],
            str(len(c.get("related_functions", []))),
        ]
        for c in case_public
    ]
    write_text(
        OUT_CASE_INDEX_MD,
        render_index_page(
            "案例机器索引",
            "Case Machine Index",
            "机器可读索引，保留中文标题、英文标题、层级、状态和关联计数。",
            "Machine-readable index that keeps Chinese titles, English titles, levels, status, and relation counts.",
            [
                "- [`data/cases/unified-cases.json`](unified-cases.json)",
                "- [`data/cases/unified-cases.jsonl`](unified-cases.jsonl)",
            ],
            ["编号 / ID", "名称 / Title", "层级 / Level", "状态 / Status", "关联函数 / Related functions"],
            case_rows,
        ),
    )

    write_text(OUT_REPORT, make_report(func_public, case_public, dangling))
    update_readme()

    print(
        json.dumps(
            {
                "functions": len(func_public),
                "cases": len(case_public),
                "function_pages": len(list(DOC_FUNC_DIR.glob("*.md"))),
                "case_pages": len(list(DOC_CASE_DIR.glob("*.md"))),
                "dangling_references": len(dangling),
            },
            ensure_ascii=False,
        )
    )


def validate_outputs(functions: List[dict], cases: List[dict]) -> None:
    assert functions, len(functions)
    assert cases, len(cases)
    assert len({f["id"] for f in functions}) == len(functions)
    assert len({c["normalized_id"] for c in cases}) == len(cases)
    assert all(f["title"]["zh"].strip() for f in functions)
    assert all(c["title"]["zh"].strip() for c in cases)
    assert all(f["source"]["source_table"] and f["source"]["source_line"] for f in functions)
    assert all(c["source"]["source_table"] and c["source"]["source_line"] for c in cases)


def validate_meta_outputs(meta_functions: List[dict]) -> None:
    assert len(meta_functions) == 1, len(meta_functions)
    meta = meta_functions[0]
    assert meta["id"] == "MF-0000", meta["id"]
    assert meta["section"] == 0, meta.get("section")
    assert meta["ordinary_function_counted"] is False, meta.get("ordinary_function_counted")
    assert meta["title"]["zh"].strip() == "自举元函数", meta["title"]["zh"]
    assert meta["title"]["en"].strip() == "Bootstrap Meta-Function", meta["title"]["en"]
    assert meta.get("page") == "docs/zh/functions/meta/MF-0000.md", meta.get("page")
    assert meta.get("source_status") in {"found", "source_pending"}, meta.get("source_status")
    assert meta.get("source_refs"), "Section 0 meta-function must have source references"


def main() -> None:
    meta_functions = load_meta_functions()
    functions = parse_function_table(FUNC_SOURCE)
    cases = parse_case_table(CASE_SOURCE)
    rel = build_relationships(functions, cases)
    dangling = rel["dangling"]

    validate_outputs(functions, cases)
    validate_meta_outputs(meta_functions)
    write_outputs(functions, cases, dangling)

    # Lightweight post-write checks.
    func_pages = list(DOC_FUNC_DIR.glob("*.md"))
    case_pages = list(DOC_CASE_DIR.glob("*.md"))
    assert len(func_pages) == len(functions), len(func_pages)
    assert len(case_pages) == len(cases), len(case_pages)
    assert ROOT_FUNCTIONS.exists()
    assert ROOT_CASES.exists()
    assert DOC_FUNC_INDEX.exists()
    assert DOC_CASE_INDEX.exists()


if __name__ == "__main__":
    main()
