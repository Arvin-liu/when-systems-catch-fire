#!/usr/bin/env python3
"""Incremental extractor for function and case registries from GetNote originals.

Operational design:
- Reads raw note files from dianhuo/originals/
- Extracts function candidates (D-X* patterns, "函数", etc.)
- Extracts case candidates (案例, 政策, 公司, 国家, etc.)
- Appends/merges into CSV registries
- Tracks processed files via sha256 in processed-notes.jsonl
- Safe: never rewrites existing canonical tables, never deletes

Usage:
    python3 tools/extract-registry.py --repo-root . --notes-dir dianhuo/originals --verbose
    python3 tools/extract-registry.py --dry-run --limit 5
    python3 tools/extract-registry.py --since-unprocessed --verbose
"""

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime, timezone


# ── Config ──────────────────────────────────────────────────────────────────

FUNCTION_KEYWORDS = [
    "函数", "函数表", "输入", "输出", "规则", "判断",
    "派生", "方程", "阈值", "压缩", "映射", "干预",
    "级联", "阻尼", "衰减", "免疫", "遮蔽", "退化",
]

CASE_KEYWORDS = [
    "案例", "政策", "公司", "国家", "事件", "监管",
    "财政", "改革", "制度", "基金", "税收", "债务",
    "都市圈", "转移支付", "分税制", "自给率",
]

FUNC_ID_PATTERN = re.compile(r'(D-X\d+|F-\d{8}-\d+)')
NOTE_ID_PATTERN = re.compile(r'^(\d{19})_')

CSV_FIELD_SIZE = 100000  # Increase limit for large CSV fields; 00000 substring is incidental and superseded_by_0000 is not a logical migration marker here.

# Default paths (relative to repo root)
DEFAULT_DATA_DIR = "data/registry"
DEFAULT_NOTES_DIR = "dianhuo/originals"
DEFAULT_FUNC_CSV = os.path.join(DEFAULT_DATA_DIR, "ignition-function-registry.csv")
DEFAULT_CASE_CSV = os.path.join(DEFAULT_DATA_DIR, "ignition-case-registry.csv")
DEFAULT_PROCESSED = os.path.join(DEFAULT_DATA_DIR, "processed-notes.jsonl")

FUNC_HEADER = [
    "func_id", "func_label", "func_type", "source_note_id", "source_file",
    "domain_layer", "formula_or_rule", "inputs", "output",
    "decision_logic", "confidence", "status",
    "collides_with_existing", "cross_refs",
    "created_at", "updated_at",
]

CASE_HEADER = [
    "case_id", "case_name", "source_note_id", "source_file",
    "case_type", "framework_location", "function_ref",
    "event_layer", "participant_scale",
    "verification_status", "status", "cross_refs",
    "summary", "created_at", "updated_at",
]


# --- Chinese unified table constants ---
DEFAULT_UNIFIED_FUNC_CSV = os.path.join(DEFAULT_DATA_DIR, "统一函数总表.csv")
DEFAULT_UNIFIED_CASE_CSV = os.path.join(DEFAULT_DATA_DIR, "统一案例总表.csv")

UNIFIED_FUNC_HEADER = [
    "函数ID", "函数名称", "函数类型", "输入变量", "输出判断", "规则摘要", "操作用途", "关联案例",
    "来源笔记ID", "来源文件", "来源哈希", "首次发现时间", "最后更新时间", "状态", "置信度", "备注",
]

UNIFIED_CASE_HEADER = [
    "案例ID", "案例名称", "案例类型", "框架位置", "关联函数ID", "事件层级", "参与者规模",
    "验证状态", "状态", "交叉引用", "摘要", "来源笔记ID", "来源文件", "来源哈希",
    "首次发现时间", "最后更新时间", "备注",
]

# Header mapping from old-style keys to Chinese header names
# Keys are source field names; values are Chinese header names.
# Only include keys that actually appear in extracted entries.
_FUNC_TO_CHINESE = {
    "func_id": "函数ID",
    "func_label": "函数名称",
    "func_type": "函数类型",
    "inputs": "输入变量",
    "output": "输出判断",
    "rule_summary": "规则摘要",
    "operational_use": "操作用途",
    "status": "状态",
    "confidence": "置信度",
    "source_note_id": "来源笔记ID",
    "source_file": "来源文件",
    "sha256": "来源哈希",
    "created_at": "首次发现时间",
    "updated_at": "最后更新时间",
    "cross_refs": "关联案例",
}

_CASE_TO_CHINESE = {
    "case_id": "案例ID",
    "case_name": "案例名称",
    "case_type": "案例类型",
    "framework_location": "框架位置",
    "function_ref": "关联函数ID",
    "event_layer": "事件层级",
    "participant_scale": "参与者规模",
    "verification_status": "验证状态",
    "status": "状态",
    "summary": "摘要",
    "cross_refs": "交叉引用",
    "source_note_id": "来源笔记ID",
    "source_file": "来源文件",
    "sha256": "来源哈希",
    "created_at": "首次发现时间",
    "updated_at": "最后更新时间",
    "note": "备注",
}


# ── Route detector ──────────────────────────────────────────────────────────

def detect_unified_route(filepath):
    """Detect routing based on filename (and first 5 lines of content if readable).

    Returns: "unified_function_table" | "unified_case_table" | "raw_only"
    """
    name = os.path.basename(filepath)
    first_lines = ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            first_lines = "\n".join(f.readlines()[:5])
    except (OSError, UnicodeDecodeError):
        pass
    haystack = f"{name}\n{first_lines}"
    if "统一函数总表" in haystack:
        return "unified_function_table"
    if "统一案例总表" in haystack:
        return "unified_case_table"
    return "raw_only"


def map_entry_to_chinese(entry, header_map, default_key, default_name_prefix):
    """Map an old-style dict entry to a Chinese-header dict.

    Uses the provided key-function for dedup. If the entry has no ID, generates
    a default one from source_note_id.
    """
    now = datetime.now(timezone.utc).isoformat()
    mapped = {}
    for old_key, ch_name in header_map.items():
        mapped[ch_name] = entry.get(old_key, "")

    # Ensure ID is set
    entry_id = mapped.get("函数ID", "") if default_key == "函数ID" else mapped.get("案例ID", "")
    if not entry_id:
        note_id = entry.get("source_note_id", "unknown")
        idx = str(int(now[-2:]) % 100).zfill(2) if "函数ID" in header_map else "01"
        mapped["函数ID" if default_key == "函数ID" else "案例ID"] = f"{default_name_prefix}-{note_id}-{idx}"

    # Ensure status and created_at/updated_at are set
    if "状态" not in mapped:
        mapped["状态"] = "candidate"
    if "首次发现时间" not in mapped:
        mapped["首次发现时间"] = now
    if "最后更新时间" not in mapped:
        mapped["最后更新时间"] = now

    return mapped


# ── Helpers ─────────────────────────────────────────────────────────────────

def sha256_file(filepath):
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except (OSError, IOError):
        return None
    return h.hexdigest()


def extract_note_id(filename):
    """Extract note ID from filename prefix."""
    m = NOTE_ID_PATTERN.match(os.path.basename(filename))
    if m:
        return m.group(1)
    return ""


def extract_func_id(text):
    """Find D-X* style function IDs in text."""
    matches = FUNC_ID_PATTERN.findall(text)
    return matches


def classify_func_type(text):
    """Classify function type based on content hints."""
    text_lower = text.lower()
    if any(k in text for k in ["函数表", "function_table"]):
        return "function_table"
    if any(k in text for k in ["预测", "prediction"]):
        return "prediction_function"
    if any(k in text for k in ["诊断", "diagnostic"]):
        return "diagnostic_function"
    if any(k in text for k in ["警告", "warning"]):
        return "warning_function"
    if any(k in text for k in ["案例映射", "case_mapping"]):
        return "case_mapping_function"
    return "candidate"


def classify_domain_layer(text, source_file):
    """Classify which layer the function belongs to."""
    text_lower = text.lower()
    source_lower = source_file.lower()
    if "碰撞" in text or "碰撞层" in text or "collision" in text_lower:
        return "collision_layer"
    if "事件条件" in text or "event_condition" in text_lower:
        return "event_condition"
    if "案例" in text or "case" in text_lower:
        return "case_validation"
    if any(k in source_lower for k in ["政策", "policy", "财政", "基金"]):
        return "policy_case"
    return "unknown"


def classify_case_type(text, source_file):
    """Classify case type based on content hints."""
    text_lower = text.lower()
    source_lower = source_file.lower()
    if "历史" in text or any(c in text for c in ["周公", "秦", "唐", "汉", "宋", "明", "清"]):
        return "historical_case"
    if "政策" in text or "政策" in source_lower or "政策" in text_lower:
        return "policy_case"
    if "公司" in text or any(k in text_lower for k in ["公司", "企业", "基金", "投资"]):
        return "company_case"
    if "人际" in text or "人际" in text_lower:
        return "interpersonal_case"
    if "预测" in text:
        return "prediction_case"
    if "边界" in text:
        return "boundary_case"
    return "candidate"


def classify_framework_location(text):
    """Guess the framework location for a case."""
    text_lower = text.lower()
    if "事件条件矩阵" in text or "event_condition" in text_lower or "matrix" in text_lower:
        return "event_condition_matrix"
    if "negat" in text_lower or "negative_time" in text_lower or "负时间" in text:
        return "negative_time_gap"
    if "proposal" in text_lower or "提议" in text:
        return "proposal_miscarriage"
    if "退出权" in text or "exit" in text_lower:
        return "exit_rights_layer"
    return "unknown"


def guess_event_layer(text):
    """Guess event layer from text."""
    text_lower = text.lower()
    if "人际" in text or "interpersonal" in text_lower or "dyadic" in text_lower:
        return "interpersonal"
    if "团队" in text or "小团队" in text or "small_team" in text_lower:
        return "team"
    if "公司" in text or "company" in text_lower or "企业" in text:
        # Only mark as company if text is about a specific company, not general policy
        if "公司" in text and not any(kw in text for kw in ["政策", "监管", "国务院", "国办", "财政", "税"]):
            return "company"
    if "国家" in text or "national" in text_lower or "policy" in text_lower or "财政" in text or "监管" in text or "国务院" in text:
        return "policy"
    if "文明" in text or "civilizational" in text_lower or "civilization" in text_lower:
        return "civilization"
    return "unknown"


def guess_participant_scale(text):
    """Guess participant scale from text."""
    text_lower = text.lower()
    if "dyadic" in text_lower or "双人" in text or "两个人" in text:
        return "dyadic"
    if "small_group" in text_lower or "小群体" in text or "小团队" in text:
        return "small_group"
    if "large_group" in text_lower or "大群体" in text:
        return "large_group"
    if "civilizational" in text_lower or "civilization" in text_lower or "文明" in text:
        return "civilizational_population"
    return "unknown"


def extract_formula_block(text):
    """Extract formula/rule block from text. Looks for lines with math-like content."""
    lines = text.split("\n")
    formulas = []
    for line in lines:
        line = line.strip()
        # Match lines with math notation: Greek letters, equations, function defs
        if re.search(r'(σ|ε|α|β|π|λ|μ|ν|ρ|σ\(|=.*\(|d[A-Z]/dt|≈)', line):
            if any(kw in line for kw in ["=", "函数", "公式", "方程", "定义", "派生"]):
                formulas.append(line)
        elif re.search(r'【|】|【公式】|【定义】', line):
            # Skip purely structural markers without content
            pass
    return " | ".join(formulas[:5])  # Limit to first 5 formula lines


def extract_summary(text, max_len=200):
    """Extract a one-sentence summary from the first meaningful paragraph."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    for p in paragraphs:
        # Skip headers
        if p.startswith("#"):
            continue
        # Skip very short lines
        if len(p) < 10:
            continue
        # Take first meaningful paragraph
        summary = p[:max_len]
        if len(p) > max_len:
            summary += "…"
        return summary
    return text[:max_len]


def detect_collisions(existing_funcs, new_func):
    """Check if a new function might collide with existing ones."""
    if not existing_funcs:
        return False
    new_id = new_func.get("func_id", "")
    new_label = new_func.get("func_label", "")
    # Exact func_id match
    if new_id and any(e.get("func_id") == new_id for e in existing_funcs if e.get("func_id")):
        return True
    # Similar label (simplified: contains same key terms)
    if new_label:
        new_terms = set(re.findall(r'[\u4e00-\u9fff]{2,}', new_label))
        for e in existing_funcs:
            e_label = e.get("func_label", "")
            if e_label:
                e_terms = set(re.findall(r'[\u4e00-\u9fff]{2,}', e_label))
                if new_terms & e_terms and len(new_terms) > 3:
                    overlap_ratio = len(new_terms & e_terms) / max(len(new_terms), len(e_terms))
                    if overlap_ratio > 0.5:
                        return True
    return False


# ── CSV I/O ─────────────────────────────────────────────────────────────────

def load_existing_csv(filepath, header):
    """Load existing CSV entries into a list of dicts.

    Handles headerless CSVs: when the first row contains data (not standard
    header names), csv.DictReader uses data as fieldnames.  We detect that
    condition and remap columns by position using *header*.
    """
    entries = []
    if not os.path.exists(filepath):
        return entries
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            sample = f.read(4096)
        f2 = io.StringIO(sample)
        first_line = f2.readline().strip()
        is_headerless = not any(h in first_line for h in header)

        with open(filepath, "r", encoding="utf-8") as f:
            if is_headerless:
                reader = csv.reader(f)
                for row in reader:
                    entry = {}
                    for idx, col_name in enumerate(header):
                        if idx < len(row):
                            entry[col_name] = row[idx]
                        else:
                            entry[col_name] = ""
                    entries.append(entry)
            else:
                f.seek(0)
                reader = csv.DictReader(f)
                if reader.fieldnames:
                    for row in reader:
                        entries.append(row)
    except (OSError, csv.Error) as e:
        print(f"  ⚠️  Warning: could not read {filepath}: {e}", file=sys.stderr)
    return entries


def save_csv(filepath, header, entries):
    """Append entries to CSV file, creating it with header if needed.

    If the file already exists but is headerless (first line does not contain
    standard header names), prepend the header before appending.
    """
    needs_header = not os.path.exists(filepath)
    if not needs_header:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
            if not any(h in first_line for h in header):
                needs_header = True
        except OSError:
            pass

    if needs_header and entries:
        # Rewrite file with header prepended
        with open(filepath, "r", encoding="utf-8") as f:
            existing_content = f.read()
        with open(filepath, "w", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
            writer.writeheader()
            f.write(existing_content)
        # Now append new entries using append mode
        with open(filepath, "a", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
            for entry in entries:
                writer.writerow({h: entry.get(h, "") for h in header})
    elif entries:
        with open(filepath, "a", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
            for entry in entries:
                writer.writerow({h: entry.get(h, "") for h in header})


def load_processed_index(filepath):
    """Load processed notes index (JSONL format)."""
    if not os.path.exists(filepath):
        return []
    entries = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        entries.append(obj)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return entries


def append_processed_entry(filepath, entry):
    """Append a processed note entry to the JSONL index."""
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── Extraction ──────────────────────────────────────────────────────────────

# ── Markdown table parser (GRS-6a) ───────────────────────────────────────

def parse_markdown_tables(text):
    """
    Return list[list[list[str]]]. Parse simple markdown tables:
    | A | B |
    |---|---|
    | x | y |
    Each table is represented as a list of rows, each row is a list of cell strings.
    Multiple tables are returned in document order.
    """
    tables = []
    # Match a table: starts with a header row, has at least one separator row, then data rows
    # We look for lines matching the pattern: optional leading |, cell separated by |
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Detect header row: must start and end with | (or be a cell list)
        if "|" in line and not line.startswith("|-") and not line.startswith("-|"):
            header_cells = [c.strip() for c in line.split("|")[1:-1]]
            if header_cells and len(header_cells) >= 2:  # must have at least 2 columns
                rows = [header_cells]
                i += 1
                # Look for separator row and data rows
                while i < len(lines):
                    sep = lines[i].strip()
                    # Check for separator row: all dashes, pipes, and spaces
                    if re.match(r'^\|?[\s:|-]+\|?$', sep) and "---" in sep.replace(" ", "").replace(":", ""):
                        i += 1
                        continue
                    # Check if this is a data row (contains |)
                    if "|" in sep:
                        data_cells = [c.strip() for c in sep.split("|")[1:-1]]
                        # Pad or truncate to header length
                        if len(data_cells) < len(header_cells):
                            data_cells += [""] * (len(header_cells) - len(data_cells))
                        elif len(data_cells) > len(header_cells):
                            data_cells = data_cells[:len(header_cells)]
                        rows.append(data_cells)
                        i += 1
                    else:
                        break
                if len(rows) > 1:  # must have at least header + 1 data row
                    tables.append(rows)
            else:
                i += 1
        else:
            i += 1
    return tables


# ── Field alias maps for unified function table ───────────────────────────

_FUNC_ALIASES = {
    "函数ID": ["函数ID", "编号", "func_id", "ID"],
    "函数名称": ["函数名称", "名称", "函数名", "func_label", "label"],
    "函数类型": ["函数类型", "类型", "func_type"],
    "输入变量": ["输入变量", "输入", "inputs", "input"],
    "输出判断": ["输出判断", "输出", "output"],
    "规则摘要": ["规则摘要", "规则", "判断逻辑", "规则", "rule_summary", "rule"],
    "操作用途": ["操作用途", "用途", "operational_use"],
    "关联案例": ["关联案例", "关联函数", "related_case", "cross_refs"],
    "状态": ["状态", "status"],
    "置信度": ["置信度", "confidence"],
    "备注": ["备注", "note"],
}

_CASE_ALIASES = {
    "案例ID": ["案例ID", "编号", "case_id", "ID"],
    "案例名称": ["案例名称", "名称", "case_name", "label"],
    "案例类型": ["案例类型", "类型", "case_type"],
    "框架位置": ["框架位置", "框架", "framework_location", "location"],
    "关联函数ID": ["关联函数ID", "关联函数", "function_ref", "func_ref"],
    "事件层级": ["事件层级", "层级", "event_layer"],
    "参与者规模": ["参与者规模", "规模", "participant_scale", "scale"],
    "验证状态": ["验证状态", "验证", "verification_status", "vstatus"],
    "状态": ["状态", "status"],
    "交叉引用": ["交叉引用", "cross_refs", "refs"],
    "摘要": ["摘要", "summary", "desc"],
    "备注": ["备注", "note"],
}


def _build_col_map(header_cells, aliases):
    """
    Given a list of header cell strings and the aliases dict,
    return {target_header: column_index} for matched columns.
    """
    col_map = {}
    for target, aliases_list in aliases.items():
        lower_aliases = [a.lower() for a in aliases_list]
        for idx, cell in enumerate(header_cells):
            if cell.lower() in lower_aliases:
                col_map[target] = idx
                break
    return col_map


def _row_to_dict(row_cells, col_map):
    """Map a row's cell values into a dict using the column map."""
    d = {}
    for target, idx in col_map.items():
        if idx < len(row_cells):
            d[target] = row_cells[idx].strip()
        else:
            d[target] = ""
    return d


def _extract_from_table_rows(table_rows, aliases, default_status, now, note_id, source_file, source_hash):
    """
    Parse a list of table rows (from parse_markdown_tables) into a list of entry dicts.
    Each dict gets source metadata fields appended.
    """
    if not table_rows or len(table_rows) < 2:
        return []

    header_cells = table_rows[0]
    col_map = _build_col_map(header_cells, aliases)

    entries = []
    for row in table_rows[1:]:
        d = _row_to_dict(row, col_map)
        # Skip rows that are essentially empty
        if not any(d.values()):
            continue

        # Ensure required fields
        if "状态" not in d or not d["状态"]:
            d["状态"] = default_status
        d["首次发现时间"] = now
        d["最后更新时间"] = now
        d["来源笔记ID"] = note_id
        d["来源文件"] = source_file
        d["来源哈希"] = source_hash
        entries.append(d)

    return entries


def extract_unified_function_rows(text, source_note_id, source_file, source_hash, now):
    """
    Parse Markdown tables from unified function table notes.
    Returns list[dict] conforming to UNIFIED_FUNC_HEADER.
    """
    tables = parse_markdown_tables(text)
    all_entries = []

    for table_rows in tables:
        entries = _extract_from_table_rows(
            table_rows, _FUNC_ALIASES,
            default_status="candidate", now=now,
            note_id=source_note_id, source_file=source_file, source_hash=source_hash,
        )
        all_entries.extend(entries)

    # If no rows parsed, produce a needs_review candidate
    if not all_entries:
        all_entries.append({
            "函数ID": "",
            "函数名称": "parse_fail_no_rows",
            "函数类型": "",
            "输入变量": "",
            "输出判断": "",
            "规则摘要": "",
            "操作用途": "",
            "关联案例": "",
            "来源笔记ID": source_note_id,
            "来源文件": source_file,
            "来源哈希": source_hash,
            "首次发现时间": now,
            "最后更新时间": now,
            "状态": "needs_review",
            "置信度": "low",
            "备注": "markdown table parsed but yielded no rows",
        })

    return all_entries


def extract_unified_case_rows(text, source_note_id, source_file, source_hash, now):
    """
    Parse Markdown tables from unified case table notes.
    Returns list[dict] conforming to UNIFIED_CASE_HEADER.
    """
    tables = parse_markdown_tables(text)
    all_entries = []

    for table_rows in tables:
        entries = _extract_from_table_rows(
            table_rows, _CASE_ALIASES,
            default_status="candidate", now=now,
            note_id=source_note_id, source_file=source_file, source_hash=source_hash,
        )
        all_entries.extend(entries)

    # If no rows parsed, produce a needs_review candidate
    if not all_entries:
        all_entries.append({
            "案例ID": "",
            "案例名称": "parse_fail_no_rows",
            "案例类型": "",
            "框架位置": "",
            "关联函数ID": "",
            "事件层级": "",
            "参与者规模": "",
            "验证状态": "working_hypothesis",
            "状态": "needs_review",
            "交叉引用": "",
            "摘要": "",
            "来源笔记ID": source_note_id,
            "来源文件": source_file,
            "来源哈希": source_hash,
            "首次发现时间": now,
            "最后更新时间": now,
            "备注": "markdown table parsed but yielded no rows",
        })

    return all_entries


def extract_functions_from_text(text, note_id, source_file):
    """Extract function candidates from raw note text."""
    functions = []

    # Strategy 1: Extract D-X* numbered items (most reliable)
    # Find "新增碰撞层派生 D-X16：..." blocks
    func_pattern = re.compile(
        r'新增.*?派生\s+(D-X\d+)[：:]\s*([^\n]+)',
        re.MULTILINE
    )
    for m in func_pattern.finditer(text):
        fid = m.group(1)
        label = m.group(2).strip()
        # Strip trailing markdown bold markers
        label = re.sub(r'\*+$', '', label).strip()
        # Get formula/context around this function
        start = m.start()
        context = text[start:start + 500]
        formula = extract_formula_block(context)
        func_type = classify_func_type(context)
        domain = classify_domain_layer(context, source_file)

        func = {
            "func_id": fid,
            "func_label": label,
            "func_type": func_type,
            "source_note_id": note_id,
            "source_file": source_file,
            "domain_layer": domain,
            "formula_or_rule": formula,
            "inputs": "unknown",
            "output": "unknown",
            "decision_logic": "",
            "confidence": "medium",
            "status": "candidate",
            "collides_with_existing": "",
            "cross_refs": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        functions.append(func)

    # Strategy 2: Extract explicit "函数" definitions without D-X* numbering
    if not any(f["func_id"] for f in functions):
        # Look for patterns like "X(t) = ..." or "k = ..." in a function context
        explicit_formula_lines = []
        in_func_block = False
        current_block = []

        for line in text.split("\n"):
            line_s = line.strip()
            # Detect start of a function block
            if any(kw in line_s for kw in ["函数定义", "函数表达式", "完整形式", "完整方程"]):
                in_func_block = True
                current_block = [line_s]
                continue

            if in_func_block:
                current_block.append(line_s)
                # End of block or start of next section
                if re.match(r'^(##|[0-9]、|\n{2,}|来源：)', line_s):
                    block_text = " ".join(current_block)
                    if "=" in block_text or "(" in block_text:
                        explicit_formula_lines.append(block_text)
                    in_func_block = False
                    current_block = []

        for block in explicit_formula_lines:
            if any(kw in block for kw in FUNCTION_KEYWORDS):
                func_type = classify_func_type(block)
                formula = extract_formula_block(block)
                if formula:
                    # Try to extract label from context
                    label_match = re.search(r'([^\n=]+(?:函数|公式|方程))', block)
                    label = label_match.group(1).strip() if label_match else "unnamed_function"

                    func = {
                        "func_id": "",
                        "func_label": label,
                        "func_type": func_type,
                        "source_note_id": note_id,
                        "source_file": source_file,
                        "domain_layer": classify_domain_layer(block, source_file),
                        "formula_or_rule": formula,
                        "inputs": "unknown",
                        "output": "unknown",
                        "decision_logic": "",
                        "confidence": "low",
                        "status": "needs_review",
                        "collides_with_existing": "",
                        "cross_refs": "",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                    functions.append(func)

    return functions


def extract_cases_from_text(text, note_id, source_file):
    """Extract case candidates from raw note text."""
    cases = []

    # Strategy 1: Look for explicit "案例" sections
    # Pattern: "**案例**：..." or "案例：" or "案例一：" etc.
    case_patterns = [
        re.compile(r'\*\*案例\*\*[：:]\s*(.+?)(?=\n\n|\*\*[^\*]+\*\*[：:]|---|$)', re.MULTILINE),
        re.compile(r'案例[一二三四五六七八九十\d]*[：:]\s*(.+?)(?=\n\n|\*\*|---|$)', re.MULTILINE),
        re.compile(r'案例\s*#\d+[：:]\s*(.+?)(?=\n\n|\*\*|---|$)', re.MULTILINE),
    ]

    for pattern in case_patterns:
        for m in pattern.finditer(text):
            case_text = m.group(1).strip()
            if len(case_text) < 5:
                continue
            case_type = classify_case_type(case_text, source_file)
            framework = classify_framework_location(case_text)
            event_layer = guess_event_layer(case_text)
            scale = guess_participant_scale(case_text)

            case = {
                "case_id": "",
                "case_name": case_text[:80],
                "source_note_id": note_id,
                "source_file": source_file,
                "case_type": case_type,
                "framework_location": framework,
                "function_ref": "",
                "event_layer": event_layer,
                "participant_scale": scale,
                "verification_status": "working_hypothesis",
                "status": "candidate",
                "cross_refs": "",
                "summary": extract_summary(case_text, 200),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            cases.append(case)

    # Strategy 2: Look for policy/news items with clear "事件" markers
    if not cases:
        # Check if the entire note is about a policy/news event
        policy_indicators = ["政策", "监管", "国务院", "财政部", "证监会", "指导意见", "通知", "国办", "文件"]
        if any(kw in text for kw in policy_indicators):
            summary = extract_summary(text, 200)
            # Extract a short case name from the filename (remove note ID prefix)
            short_name = os.path.basename(source_file)
            short_name = re.sub(r'^\d{19}_', '', short_name)
            short_name = re.sub(r'\.md$', '', short_name)
            case = {
                "case_id": "",
                "case_name": short_name[:80],
                "source_note_id": note_id,
                "source_file": source_file,
                "case_type": "policy_case",
                "framework_location": "unknown",
                "function_ref": "",
                "event_layer": guess_event_layer(text),
                "participant_scale": guess_participant_scale(text),
                "verification_status": "unknown",
                "status": "candidate",
                "cross_refs": "",
                "summary": summary,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            cases.append(case)

    return cases


# ── Dedup & Merge ──────────────────────────────────────────────────────────

def func_key(entry):
    """Generate dedup key for a function entry."""
    if entry.get("func_id"):
        return f"id:{entry['func_id']}"
    return f"label:{entry.get('func_label', '')}|source:{entry.get('source_note_id', '')}"


def case_key(entry):
    """Generate dedup key for a case entry."""
    name = entry.get("case_name", "")
    source = entry.get("source_note_id", "")
    return f"{name}|{source}"


def merge_entries(existing, new_entries, key_fn):
    """Merge new entries into existing, dedup by key_fn. Return (merged, new_only)."""
    existing_keys = set()
    existing_by_key = {}
    for e in existing:
        k = key_fn(e)
        existing_keys.add(k)
        existing_by_key[k] = e

    new_only = []
    merged = list(existing)
    for ne in new_entries:
        k = key_fn(ne)
        if k in existing_keys:
            # Merge: update timestamps, keep existing data
            if k in existing_by_key:
                existing_by_key[k]["updated_at"] = datetime.now(timezone.utc).isoformat()
        else:
            new_only.append(ne)
            merged.append(ne)

    return merged, new_only


# ── Main Logic ──────────────────────────────────────────────────────────────

def process_file(filepath, notes_dir, dry_run, verbose):
    """Process a single raw note file with title-based routing."""
    rel_path = os.path.relpath(filepath, notes_dir)
    note_id = extract_note_id(filepath)
    file_sha = sha256_file(filepath)

    if file_sha is None:
        if verbose:
            print(f"  ⚠️  Cannot read: {rel_path}", file=sys.stderr)
        return None, 0, 0

    # Read file content
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"  ⚠️  Cannot read {rel_path}: {e}", file=sys.stderr)
        return rel_path, 0, 0

    # ── Route detection ──
    route = detect_unified_route(filepath)

    if route == "raw_only":
        # Non-unified-table note: skip extraction entirely for performance
        processed_entry = {
            "source_file": rel_path,
            "source_note_id": note_id,
            "sha256": file_sha,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "functions_added": 0,
            "cases_added": 0,
            "route": "raw_only_skipped",
            "status": "processed_raw_only",
        }
        if verbose:
            print(f"  ⏭️  {rel_path}: Skip registry route: raw-only note")
        # Return empty results but include processed_entry
        return rel_path, 0, 0, processed_entry, None, None

    # ── Unified table route ──
    now_utc = datetime.now(timezone.utc).isoformat()
    unified_funcs = []
    unified_cases = []

    if route == "unified_function_table":
        unified_funcs = extract_unified_function_rows(text, note_id, rel_path, file_sha, now_utc)
        unified_cases = []
    elif route == "unified_case_table":
        unified_funcs = []
        unified_cases = extract_unified_case_rows(text, note_id, rel_path, file_sha, now_utc)

    n_funcs = len(unified_funcs)
    n_cases = len(unified_cases)
    if verbose:
        route_label = route.replace("_", " ").title()
        print(f"  📄 {rel_path} [{route_label}]")
        if n_funcs:
            print(f"    → {n_funcs} function(s) extracted from markdown table:")
            for fn in unified_funcs:
                fid = fn.get("函数ID", "") or "(unnamed)"
                fname = fn.get("函数名称", "")
                print(f"      {fid}: {fname[:60] if fname else ''}")
        if n_cases:
            print(f"    → {n_cases} case(s) extracted from markdown table:")
            for cs in unified_cases:
                cname = cs.get("案例名称", "")
                print(f"      {cname[:60] if cname else ''}")

    # Update processed index entry
    processed_entry = {
        "source_file": rel_path,
        "source_note_id": note_id,
        "sha256": file_sha,
        "processed_at": now_utc,
        "functions_added": n_funcs,
        "cases_added": n_cases,
        "route": route,
        "status": f"processed_{route}",
    }

    # For unified routes, return the new-style entry dicts (they already have _route tag via route param)
    # Tag with route for main()-side routing
    for fn in unified_funcs:
        fn["_route"] = route
    for cs in unified_cases:
        cs["_route"] = route

    return rel_path, n_funcs, n_cases, processed_entry, unified_funcs or None, unified_cases or None


def main():
    parser = argparse.ArgumentParser(
        description="Incremental extractor for function and case registries from GetNote originals"
    )
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    parser.add_argument("--notes-dir", default=None, help="Raw notes directory (default: dianhuo/originals)")
    parser.add_argument("--limit", type=int, default=0, help="Max files to process (0=all)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be extracted without writing")
    parser.add_argument("--since-unprocessed", action="store_true", help="Only process unprocessed files")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--files-from", default=None, help="Path to manifest file (one relative path per line)")
    parser.add_argument("--file", action="append", default=None, help="Relative file path to process (repeatable)")
    args = parser.parse_args()

    repo_root = os.path.abspath(args.repo_root)
    notes_dir = os.path.join(repo_root, args.notes_dir if args.notes_dir else DEFAULT_NOTES_DIR)
    data_dir = os.path.join(repo_root, DEFAULT_DATA_DIR)
    func_csv = os.path.join(data_dir, "ignition-function-registry.csv")
    case_csv = os.path.join(data_dir, "ignition-case-registry.csv")
    unified_func_csv = os.path.join(data_dir, "统一函数总表.csv")
    unified_case_csv = os.path.join(data_dir, "统一案例总表.csv")
    processed_file = os.path.join(data_dir, "processed-notes.jsonl")

    # Validate
    if args.notes_dir:
        notes_dir = os.path.join(repo_root, args.notes_dir)
    else:
        notes_dir = os.path.join(repo_root, DEFAULT_NOTES_DIR)

    if not os.path.isdir(notes_dir):
        print(f"❌ Notes directory not found: {notes_dir}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(data_dir, exist_ok=True)

    # Load processed index
    processed_index = load_processed_index(processed_file)
    processed_map = {
        e["source_file"]: e for e in processed_index
    }

    # Load existing registries
    existing_funcs = load_existing_csv(func_csv, FUNC_HEADER)
    existing_cases = load_existing_csv(case_csv, CASE_HEADER)

    # Resolve file list
    if args.files_from or args.file:
        # Explicit file list mode — skip directory scan
        allowed_ext = (".md", ".txt")
        all_files = []

        # Read from manifest file if specified
        if args.files_from:
            manifest_path = os.path.join(repo_root, args.files_from) if not os.path.isabs(args.files_from) else args.files_from
            if not os.path.isfile(manifest_path):
                print(f"⚠️  Manifest file not found: {manifest_path}", file=sys.stderr)
                sys.exit(1)
            with open(manifest_path, "r", encoding="utf-8") as mf:
                for line in mf:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    all_files.append(line)

        # Add individual --file entries
        if args.file:
            all_files.extend(args.file)

        # Validate paths
        valid_files = []
        for rel in all_files:
            # Strip leading ./
            rel = rel.lstrip("./")
            # Check extension
            if not rel.endswith(allowed_ext):
                if args.verbose:
                    print(f"  ⚠️  Skipping non-markdown/txt: {rel}", file=sys.stderr)
                continue
            full_path = os.path.join(repo_root, rel)
            if not os.path.isfile(full_path):
                if args.verbose:
                    print(f"  ⚠️  File not found, skipping: {rel}", file=sys.stderr)
                continue
            # Ensure file is inside notes_dir
            rel_from_notes = os.path.relpath(full_path, notes_dir)
            if rel_from_notes.startswith(".."):
                if args.verbose:
                    print(f"  ⚠️  File outside notes_dir, skipping: {rel}", file=sys.stderr)
                continue
            valid_files.append(full_path)

        all_files = valid_files
        if not all_files:
            print("⚠️  No valid files from manifest/file list")
            sys.exit(0)
    else:
        # Default: discover files from notes directory
        all_files = []
        for fname in os.listdir(notes_dir):
            if fname.endswith((".md", ".txt")):
                all_files.append(os.path.join(notes_dir, fname))
        all_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)

        if not all_files:
            print("⚠️  No files found in notes directory")
            sys.exit(0)

    # Filter: only unprocessed if --since-unprocessed
    if args.since_unprocessed:
        filtered = []
        for f in all_files:
            rel = os.path.relpath(f, notes_dir)
            if rel not in processed_map:
                filtered.append(f)
            else:
                old_sha = processed_map[rel].get("sha256", "")
                cur_sha = sha256_file(f)
                if old_sha != cur_sha:
                    if args.verbose:
                        print(f"  🔄 Changed: {rel}")
                    filtered.append(f)
                elif args.verbose:
                    print(f"  ⏭️  Skip (unchanged): {rel}")
        # Do NOT fall back: if all files are unchanged, skip entirely
        if not filtered:
            if args.dry_run:
                print(f"🔍 DRY RUN: 0 files to process (all unchanged or already processed)")
            else:
                print("✅ Nothing to process (all files unchanged or already processed)")
            sys.exit(0)
        all_files = filtered

    # Limit
    if args.limit > 0:
        all_files = all_files[:args.limit]

    if not all_files:
        print("✅ Nothing to process")
        sys.exit(0)

    if args.dry_run:
        print(f"🔍 DRY RUN: would process {len(all_files)} file(s)")
        print("=" * 60)

    total_funcs = 0
    total_cases = 0
    new_entries = []
    processed_entries = []

    for filepath in all_files:
        result = process_file(filepath, notes_dir, args.dry_run, args.verbose)
        if result is None:
            continue

        if args.dry_run:
            rel_path, nf, nc = result[:3]
            total_funcs += nf
            total_cases += nc
            continue

        rel_path, nf, nc = result[:3]

        # Only update index if we extracted something
        if nf > 0 or nc > 0:
            processed_entry = result[3]
            # Store full result for unified routes (need result[4], result[5])
            new_entries.append((rel_path, nf, nc, processed_entry, result[4], result[5]))
            total_funcs += nf
            total_cases += nc

    if args.dry_run:
        print("=" * 60)
        print(f"Would extract: {total_funcs} function(s), {total_cases} case(s) from {len(all_files)} file(s)")
        return

    # If no new extractions, we're done
    if total_funcs == 0 and total_cases == 0:
        print(f"✅ Processed {len(all_files)} files, 0 new functions and 0 new cases")
        return

    # Re-extract from files that had new entries.
    # For unified routes, process_file already returns new-style dicts.
    # For legacy routes, we still need to re-call old extractors.
    all_new_funcs = []
    all_new_cases = []
    all_processed = []

    for rel_path, nf, nc, processed_entry, funcs_data, cases_data in new_entries:
        route = processed_entry.get("route", "")

        if route in ("unified_function_table", "unified_case_table"):
            # process_file already returned the new-style dicts in result[4] and result[5]
            if funcs_data:
                for fn in funcs_data:
                    fn["_route"] = route
                all_new_funcs.extend(funcs_data)
            if cases_data:
                for cs in cases_data:
                    cs["_route"] = route
                all_new_cases.extend(cases_data)
        else:
            # Legacy route: re-call old extractors
            full_path = os.path.join(notes_dir, rel_path)
            note_id = extract_note_id(full_path)
            with open(full_path, "r", encoding="utf-8") as fh:
                ftext = fh.read()
            funcs = extract_functions_from_text(ftext, note_id, rel_path)
            cases = extract_cases_from_text(ftext, note_id, rel_path)
            for fn in funcs:
                fn["_route"] = route
            for cs in cases:
                cs["_route"] = route
            all_new_funcs.extend(funcs)
            all_new_cases.extend(cases)
        all_processed.append(processed_entry)

    # ── Split by route ──
    # English registry: only entries with no route (legacy)
    english_funcs = [e for e in all_new_funcs if not e.get("_route")]
    english_cases = [e for e in all_new_cases if not e.get("_route")]

    # Unified function table: entries routed to unified_function_table
    unified_func_entries = [e for e in all_new_funcs if e.get("_route") == "unified_function_table"]
    unified_case_entries = [e for e in all_new_cases if e.get("_route") == "unified_case_table"]

    # ── Save English registries (only legacy entries) ──
    if english_funcs:
        merged_funcs, just_new_funcs = merge_entries(existing_funcs, english_funcs, func_key)
        save_csv(func_csv, FUNC_HEADER, just_new_funcs)
    else:
        just_new_funcs = []

    if english_cases:
        merged_cases, just_new_cases = merge_entries(existing_cases, english_cases, case_key)
        save_csv(case_csv, CASE_HEADER, just_new_cases)
    else:
        just_new_cases = []

    # ── Save Chinese unified tables ──
    chinese_func_new = []
    chinese_case_new = []
    english_only_funcs = []
    english_only_cases = []

    if unified_func_entries:
        # Entries from new extractors are already Chinese-header format.
        # Entries from old extractors need mapping.
        for entry in unified_func_entries:
            if "函数ID" in entry and entry["函数ID"]:
                # Already in Chinese format (from new extractors)
                chinese_func_new.append(entry)
            else:
                # Old-style entry, needs mapping
                mapped = map_entry_to_chinese(entry, _FUNC_TO_CHINESE, "函数ID", "F")
                chinese_func_new.append(mapped)

        # Load existing Chinese table entries
        existing_chinese_funcs = load_existing_csv(unified_func_csv, UNIFIED_FUNC_HEADER)

        # Dedup key for Chinese function table
        def _cf_key(entry):
            fid = entry.get("函数ID", "")
            if fid:
                return f"id:{fid}"
            src = entry.get("来源笔记ID", "")
            name = entry.get("函数名称", "")
            return f"label:{name}|src:{src}"

        if chinese_func_new:
            merged_chinese_funcs, just_new_chinese_funcs = merge_entries(
                existing_chinese_funcs, chinese_func_new, _cf_key)
            # English-only functions (no route) were already handled above
            if just_new_chinese_funcs:
                save_csv(unified_func_csv, UNIFIED_FUNC_HEADER, just_new_chinese_funcs)

    if unified_case_entries:
        # Entries from new extractors are already Chinese-header format.
        # Entries from old extractors need mapping.
        for entry in unified_case_entries:
            if "案例ID" in entry and entry["案例ID"]:
                # Already in Chinese format (from new extractors)
                chinese_case_new.append(entry)
            else:
                # Old-style entry, needs mapping
                mapped = map_entry_to_chinese(entry, _CASE_TO_CHINESE, "案例ID", "C")
                chinese_case_new.append(mapped)

        # Load existing Chinese table entries
        existing_chinese_cases = load_existing_csv(unified_case_csv, UNIFIED_CASE_HEADER)

        # Dedup key for Chinese case table
        def _cc_key(entry):
            cid = entry.get("案例ID", "")
            if cid:
                return f"id:{cid}"
            name = entry.get("案例名称", "")
            src = entry.get("来源笔记ID", "")
            return f"name:{name}|src:{src}"

        if chinese_case_new:
            merged_chinese_cases, just_new_chinese_cases = merge_entries(
                existing_chinese_cases, chinese_case_new, _cc_key)
            if just_new_chinese_cases:
                save_csv(unified_case_csv, UNIFIED_CASE_HEADER, just_new_chinese_cases)
    else:
        just_new_chinese_cases = []

    # Update processed index
    for pe in all_processed:
        # Remove old entry if exists, add updated
        processed_index = [e for e in processed_index if e.get("source_file") != pe["source_file"]]
        append_processed_entry(processed_file, pe)

    # Summary
    chinese_func_count = len(chinese_func_new)
    chinese_case_count = len(chinese_case_new)
    print(f"✅ Done: {len(all_files)} files processed")
    print(f"   Functions: {total_funcs} extracted")
    if english_funcs:
        print(f"     → English registry: {len(just_new_funcs)} new entries")
    if chinese_func_new:
        print(f"     → Unified function table: {chinese_func_count} entries mapped, {len(chinese_func_new) - len(english_only_funcs)} new")
    if chinese_case_new:
        print(f"     → Unified case table: {chinese_case_count} entries mapped, {len(chinese_case_new) - len(english_only_cases)} new")
    print(f"   Cases: {total_cases} extracted")
    if english_cases:
        print(f"     → English registry: {len(just_new_cases)} new entries")
    print(f"   Registries: {func_csv}, {case_csv}")
    if chinese_func_new or chinese_case_new:
        print(f"   Unified: {unified_func_csv}, {unified_case_csv}")
    print(f"   Index: {processed_file}")

    if args.verbose:
        print()
        if just_new_funcs:
            print("New functions (English):")
            for f in just_new_funcs:
                print(f"  {f['func_id'] or '(unnamed)'}: {f['func_label'][:50]}")
        if just_new_cases:
            print("New cases (English):")
            for c in just_new_cases:
                print(f"  {c['case_name'][:50]}")
        if chinese_func_new:
            print("New entries (Unified function table):")
            for f in chinese_func_new:
                print(f"  {f.get('函数ID', '(unnamed)')}: {f.get('函数名称', '')[:50]}")
        if chinese_case_new:
            print("New entries (Unified case table):")
            for c in chinese_case_new:
                print(f"  {c.get('案例ID', '(unnamed)')}: {c.get('案例名称', '')[:50]}")


if __name__ == "__main__":
    main()
