#!/usr/bin/env python3
"""Detect repetitive text patterns across markdown and machine-readable files."""

from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

from display_utils import is_mostly_cjk


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_MD = REPO_ROOT / "data/rebuild/repetitive-text-report.md"
REPORT_JSON = REPO_ROOT / "data/rebuild/repetitive-text-report.json"

SKIP_DIRS = {".git", "node_modules", "dist", "build", "archive"}
SKIP_PREFIXES = {
    ("data", "runs"),
}
SKIP_FILE_PREFIXES = {
    ("data", "rebuild", "dual-channel-"),
}
MARKDOWN_EXT = ".md"
JSON_EXTS = {".json", ".jsonl"}

LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*+]|(?:\d+\.))\s+")
LABEL_DUP_RE = re.compile(r"(?P<left>[^|\n]{1,160}?)\s*/\s*(?P<right>[^|\n]{1,160}?)")


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(REPO_ROOT).parts
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if any(rel_parts[: len(prefix)] == prefix for prefix in SKIP_PREFIXES):
            continue
        if any(
            rel_parts[: len(prefix) - 1] == prefix[:-1] and rel_parts[len(prefix) - 1].startswith(prefix[-1])
            for prefix in SKIP_FILE_PREFIXES
        ):
            continue
        if path.suffix not in {MARKDOWN_EXT, *JSON_EXTS}:
            continue
        files.append(path)
    return sorted(files)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def is_meaningful_block(text: str) -> bool:
    compact = normalize(text)
    if not compact:
        return False
    if compact in {"-", "—", "–", "暂无", "None", "none"}:
        return False
    if len(compact) < 40 and "\n" not in text:
        return False
    return True


def is_duplicate_pair(left: str | None, right: str | None) -> bool:
    if not isinstance(left, str) or not isinstance(right, str):
        return False
    left_text = left.strip()
    right_text = right.strip()
    if not left_text or not right_text:
        return False
    if normalize(left_text) != normalize(right_text):
        return False
    return is_mostly_cjk(left_text) or is_mostly_cjk(right_text)


def scan_markdown(path: Path) -> dict:
    if path.name.endswith("_TEMPLATE.md"):
        return {
            "exact_duplicate_lines": 0,
            "exact_duplicate_blocks": 0,
            "near_duplicate_blocks": 0,
            "bilingual_duplicates": 0,
            "needs_human_review": False,
        }
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_code = False
    exact_duplicate_lines = 0
    exact_duplicate_blocks = 0
    near_duplicate_blocks = 0
    bilingual_duplicates = 0
    previous_nonblank = ""
    previous_list = ""
    previous_block = ""
    block: list[str] = []
    blocks: list[str] = []

    def flush_block() -> None:
        nonlocal previous_block, exact_duplicate_blocks, near_duplicate_blocks
        if not block:
            return
        current = "\n".join(block).strip()
        if current and is_meaningful_block(current):
            if current == previous_block:
                exact_duplicate_blocks += 1
            elif previous_block and SequenceMatcher(None, current, previous_block).ratio() >= 0.92:
                near_duplicate_blocks += 1
            previous_block = current

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_block()
            block.clear()
            in_code = not in_code
            previous_nonblank = ""
            previous_list = ""
            continue
        if in_code:
            continue
        if " / " in line and "://" not in line:
            for match in LABEL_DUP_RE.finditer(line):
                if is_duplicate_pair(match.group("left"), match.group("right")):
                    bilingual_duplicates += 1
        if not stripped:
            flush_block()
            block.clear()
            previous_nonblank = ""
            previous_list = ""
            continue
        if stripped == previous_nonblank:
            exact_duplicate_lines += 1
        if LIST_PREFIX_RE.match(line) and stripped == previous_list:
            exact_duplicate_lines += 1
        previous_nonblank = stripped
        if LIST_PREFIX_RE.match(line):
            previous_list = stripped
        else:
            previous_list = ""
        block.append(line)
    flush_block()

    return {
        "exact_duplicate_lines": exact_duplicate_lines,
        "exact_duplicate_blocks": exact_duplicate_blocks,
        "near_duplicate_blocks": near_duplicate_blocks,
        "bilingual_duplicates": bilingual_duplicates,
        "needs_human_review": near_duplicate_blocks > 0,
    }


def scan_json_value(value, stats: dict, path: str = "") -> None:
    if isinstance(value, dict):
        if "zh" in value and "en" in value and is_duplicate_pair(value.get("zh"), value.get("en")):
            stats["bilingual_duplicates"] += 1
            stats["bilingual_paths"].append(path or "<root>")
        for key, child in value.items():
            scan_json_value(child, stats, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        previous = object()
        for idx, child in enumerate(value):
            if isinstance(child, str):
                if child == previous:
                    stats["exact_duplicate_list_items"] += 1
                previous = child
            else:
                previous = object()
            scan_json_value(child, stats, f"{path}[{idx}]")


def scan_json(path: Path) -> dict:
    stats = {
        "exact_duplicate_list_items": 0,
        "bilingual_duplicates": 0,
        "bilingual_paths": [],
    }
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        for idx, line in enumerate(text.splitlines()):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            scan_json_value(obj, stats, f"{path.as_posix()}#{idx + 1}")
    else:
        try:
            obj = json.loads(text)
        except Exception:
            return stats
        scan_json_value(obj, stats, path.as_posix())
    return stats


def build_report(summary: dict, touched: list[str]) -> tuple[str, dict]:
    payload = {"summary": summary, "touched_files": touched}
    lines = [
        "# Repetitive Text Report",
        "",
        f"- exact_duplicate_lines: {summary['exact_duplicate_lines']}",
        f"- exact_duplicate_blocks: {summary['exact_duplicate_blocks']}",
        f"- near_duplicate_blocks: {summary['near_duplicate_blocks']}",
        f"- bilingual_duplicates: {summary['bilingual_duplicates']}",
        f"- exact_duplicate_list_items: {summary['exact_duplicate_list_items']}",
        f"- needs_human_review: {summary['needs_human_review']}",
        "",
        "## Touched Files",
        "",
    ]
    if touched:
        lines.extend(f"- {item}" for item in touched[:200])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines), payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect repetitive text.")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--fix-exact", action="store_true")
    args = parser.parse_args()

    files = iter_files()
    summary = {
        "exact_duplicate_lines": 0,
        "exact_duplicate_blocks": 0,
        "near_duplicate_blocks": 0,
        "bilingual_duplicates": 0,
        "exact_duplicate_list_items": 0,
        "needs_human_review": False,
    }
    touched: list[str] = []

    for path in files:
        if path.suffix == MARKDOWN_EXT:
            stats = scan_markdown(path)
            summary["exact_duplicate_lines"] += stats["exact_duplicate_lines"]
            summary["exact_duplicate_blocks"] += stats["exact_duplicate_blocks"]
            summary["near_duplicate_blocks"] += stats["near_duplicate_blocks"]
            summary["bilingual_duplicates"] += stats["bilingual_duplicates"]
            summary["needs_human_review"] = summary["needs_human_review"] or stats["needs_human_review"]
            if args.fix_exact and (stats["exact_duplicate_blocks"] or stats["exact_duplicate_lines"]):
                text = path.read_text(encoding="utf-8")
                fixed, changed = fix_markdown_exact_duplicates(text)
                if changed:
                    path.write_text(fixed, encoding="utf-8", newline="\n")
                    touched.append(path.relative_to(REPO_ROOT).as_posix())
        else:
            stats = scan_json(path)
            summary["bilingual_duplicates"] += stats.get("bilingual_duplicates", 0)
            summary["exact_duplicate_list_items"] += stats.get("exact_duplicate_list_items", 0)
            if stats.get("bilingual_duplicates", 0):
                touched.append(path.relative_to(REPO_ROOT).as_posix())
            if stats.get("exact_duplicate_list_items", 0):
                touched.append(path.relative_to(REPO_ROOT).as_posix())

    summary["needs_human_review"] = summary["needs_human_review"] or summary["near_duplicate_blocks"] > 0
    report_text, payload = build_report(summary, sorted(set(touched)))
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(report_text, encoding="utf-8", newline="\n")
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    if args.check:
        if summary["exact_duplicate_lines"] or summary["exact_duplicate_blocks"] or summary["bilingual_duplicates"]:
            print(report_text)
            return 1
        print("Repetitive text check passed")
        return 0

    if args.report:
        print(report_text)
    else:
        print(
            json.dumps(
                {
                    "summary": summary,
                    "report_md": str(REPORT_MD.relative_to(REPO_ROOT)),
                    "report_json": str(REPORT_JSON.relative_to(REPO_ROOT)),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


def fix_markdown_exact_duplicates(text: str) -> tuple[str, bool]:
    lines = text.splitlines()
    out: list[str] = []
    current_block: list[str] = []
    in_code = False
    previous_block = ""
    changed = False

    def flush_block() -> None:
        nonlocal current_block, previous_block, changed
        if not current_block:
            return
        block_text = "\n".join(current_block).strip()
        if block_text and is_meaningful_block(block_text) and block_text == previous_block:
            changed = True
        else:
            if out and out[-1] != "":
                out.append("")
            out.extend(current_block)
            if block_text and is_meaningful_block(block_text):
                previous_block = block_text
        current_block = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_block()
            if out and out[-1] != "":
                out.append("")
            out.append(line)
            in_code = not in_code
            previous_block = ""
            continue
        if in_code:
            out.append(line)
            continue
        if not stripped:
            flush_block()
            continue
        current_block.append(line)

    flush_block()

    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), changed


if __name__ == "__main__":
    raise SystemExit(main())
