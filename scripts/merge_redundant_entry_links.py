#!/usr/bin/env python3
"""Merge redundant entry/link columns in human-readable Markdown pages.

The script scans the repository's readable Markdown pages and removes table
columns that merely repeat an entry link for the same object name. When the
name and the link/page target represent the same object, the name cell becomes
the link and the redundant Entry / Link / Page column is removed.

Usage:
    python3 scripts/merge_redundant_entry_links.py
    python3 scripts/merge_redundant_entry_links.py --check
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_MD = REPO_ROOT / "data/rebuild/link-entry-merge-report.md"
REPORT_JSON = REPO_ROOT / "data/rebuild/link-entry-merge-report.json"

SKIP_DIRS = {".git", "archive", "node_modules", "dist", "build"}

LABEL_HEADERS = {
    "名称",
    "分类",
    "区域",
    "层",
    "layer",
    "category",
    "title",
    "标题",
    "function",
    "函数",
    "case",
    "案例",
    "discovery",
    "发现",
    "id",
    "编号",
    "学科分类",
}

ENTRY_HEADERS = {
    "入口",
    "entry",
    "link",
    "链接",
    "跳转",
    "page",
    "open",
    "查看",
}

MD_LINK_RE = re.compile(r"^\[(?P<label>.*)\]\((?P<target>[^)]+)\)$")


@dataclass
class FileReport:
    path: str
    tables_merged: int = 0
    columns_removed: int = 0
    notes: list[str] = field(default_factory=list)


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def split_row(line: str) -> list[str]:
    text = line.rstrip("\n")
    escaped = text.replace("\\|", "[[PIPE]]")
    cells = [cell.strip() for cell in escaped.split("|")]
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return [cell.replace("[[PIPE]]", "|") for cell in cells]


def join_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def header_key(cell: str) -> str:
    text = re.sub(r"\s+", " ", cell).strip().lower()
    text = text.replace(" / ", " ").replace("/", " ")
    return text


def header_matches(cell: str, aliases: set[str]) -> bool:
    haystack = header_key(cell)
    return any(alias in haystack for alias in aliases)


def is_separator_row(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and set(stripped) <= {"|", "-", ":", " "}


def parse_markdown_table(lines: list[str], start: int) -> tuple[list[str], list[list[str]], int] | None:
    if start >= len(lines) or "|" not in lines[start]:
        return None
    header = split_row(lines[start])
    if not header:
        return None
    if start + 1 >= len(lines):
        return None
    if not is_separator_row(lines[start + 1]):
        return None

    rows: list[list[str]] = []
    idx = start + 2
    while idx < len(lines):
        line = lines[idx]
        if "|" not in line or line.lstrip().startswith("```"):
            break
        if not line.strip():
            break
        if not line.lstrip().startswith("|"):
            break
        rows.append(split_row(line))
        idx += 1
    return header, rows, idx


def markdown_link_target(cell: str) -> tuple[str | None, str | None]:
    match = MD_LINK_RE.match(cell.strip())
    if not match:
        return None, None
    return match.group("label"), match.group("target")


def looks_like_single_target(cell: str) -> bool:
    text = cell.strip()
    if not text:
        return False
    if "," in text:
        return False
    if " and " in text.lower():
        return False
    if text.startswith("`") and text.endswith("`"):
        text = text[1:-1].strip()
    return bool(re.search(r"\.(md|json|jsonl|csv|txt)$", text) or "/" in text)


def merge_table(header: list[str], rows: list[list[str]]) -> tuple[list[str], list[list[str]], int, int, list[str]]:
    label_idx = None
    for idx, cell in enumerate(header):
        if header_matches(cell, LABEL_HEADERS):
            label_idx = idx
            break
    entry_idx = None
    for idx, cell in enumerate(header):
        if header_matches(cell, ENTRY_HEADERS):
            entry_idx = idx
            break

    if label_idx is None or entry_idx is None or label_idx == entry_idx:
        return header, rows, 0, 0, []

    merged_rows: list[list[str]] = []
    notes: list[str] = []
    changed = False

    for row in rows:
        if entry_idx >= len(row) or label_idx >= len(row):
            return header, rows, 0, 0, []
        label_cell = row[label_idx].strip()
        entry_cell = row[entry_idx].strip()
        if not entry_cell:
            return header, rows, 0, 0, []

        link_label, link_target = markdown_link_target(entry_cell)
        if link_target:
            merged_label = label_cell if label_cell.startswith("[") else f"[{label_cell}]({link_target})"
        elif looks_like_single_target(entry_cell):
            target = entry_cell.strip("`")
            merged_label = f"[{label_cell}]({target})"
        else:
            return header, rows, 0, 0, []

        new_row = list(row)
        new_row[label_idx] = merged_label
        del new_row[entry_idx]
        merged_rows.append(new_row)
        changed = True

    if not changed:
        return header, rows, 0, 0, []

    new_header = list(header)
    removed_header = new_header.pop(entry_idx)
    notes.append(f"removed column: {removed_header}")
    return new_header, merged_rows, 1, 1, notes


def process_text(text: str) -> tuple[str, int, int, list[str]]:
    lines = text.splitlines()
    i = 0
    output: list[str] = []
    tables_merged = 0
    columns_removed = 0
    notes: list[str] = []

    while i < len(lines):
        parsed = parse_markdown_table(lines, i)
        if not parsed:
            output.append(lines[i])
            i += 1
            continue

        header, rows, end = parsed
        new_header, new_rows, merged_count, removed_count, table_notes = merge_table(header, rows)
        if merged_count and removed_count:
            tables_merged += 1
            columns_removed += removed_count
            notes.extend(table_notes)
            output.append(join_row(new_header))
            output.append("| " + " | ".join(["---"] * len(new_header)) + " |")
            for row in new_rows:
                output.append(join_row(row))
        else:
            output.extend(lines[i:end])
        i = end

    return "\n".join(output) + ("\n" if text.endswith("\n") else ""), tables_merged, columns_removed, notes


def build_report(entries: list[FileReport], scanned: int) -> tuple[str, dict]:
    total_tables = sum(item.tables_merged for item in entries)
    total_columns = sum(item.columns_removed for item in entries)
    changed = [item for item in entries if item.tables_merged]
    report = {
        "scanned_files": scanned,
        "changed_files": len(changed),
        "tables_merged": total_tables,
        "columns_removed": total_columns,
        "files": [
            {
                "path": item.path,
                "tables_merged": item.tables_merged,
                "columns_removed": item.columns_removed,
                "notes": item.notes,
            }
            for item in changed
        ],
    }
    md_lines = [
        "# Link Entry Merge Report / 链接入口合并报告",
        "",
        f"- Scanned files / 扫描文件：{scanned}",
        f"- Changed files / 变更文件：{len(changed)}",
        f"- Tables merged / 合并表格：{total_tables}",
        f"- Columns removed / 删除列：{total_columns}",
        "",
    ]
    if changed:
        md_lines.append("## Files Changed / 变更文件")
        md_lines.append("")
        for item in changed:
            md_lines.append(f"- `{item.path}`: {item.tables_merged} table(s), {item.columns_removed} column(s)")
        md_lines.append("")
    else:
        md_lines.append("No redundant entry/link columns found.")
        md_lines.append("")
    return "\n".join(md_lines), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report changes without writing files")
    args = parser.parse_args()

    reports: list[FileReport] = []
    changed_any = False
    scanned = 0

    for path in iter_markdown_files(REPO_ROOT):
        scanned += 1
        original = path.read_text(encoding="utf-8")
        updated, tables_merged, columns_removed, notes = process_text(original)
        if tables_merged:
            changed_any = True
            reports.append(
                FileReport(
                    path=path.relative_to(REPO_ROOT).as_posix(),
                    tables_merged=tables_merged,
                    columns_removed=columns_removed,
                    notes=notes,
                )
            )
            if not args.check:
                path.write_text(updated, encoding="utf-8", newline="\n")

    report_md, report_json = build_report(reports, scanned)
    if not args.check:
        REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        REPORT_MD.write_text(report_md, encoding="utf-8", newline="\n")
        REPORT_JSON.write_text(json.dumps(report_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.check and changed_any:
        print(report_md)
        return 1

    print(report_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
