#!/usr/bin/env python3
"""Normalize bilingual labels and drop duplicated Chinese/Chinese pairs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from display_utils import is_mostly_cjk


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_MD = REPO_ROOT / "data/rebuild/bilingual-label-cleanup-report.md"
REPORT_JSON = REPO_ROOT / "data/rebuild/bilingual-label-cleanup-report.json"

SKIP_DIRS = {".git", "node_modules", "dist", "build", "archive"}
MARKDOWN_EXT = ".md"
JSON_EXTS = {".json", ".jsonl"}

DUP_LABEL_RE = re.compile(r"(?P<left>[^|\n]{1,160}?)\s*/\s*(?P<right>[^|\n]{1,160}?)")


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix not in {MARKDOWN_EXT, *JSON_EXTS}:
            continue
        files.append(path)
    return sorted(files)


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", "", text or "").strip()


def is_duplicate_pair(left: str | None, right: str | None) -> bool:
    if not isinstance(left, str) or not isinstance(right, str):
        return False
    left_text = left.strip()
    right_text = right.strip()
    if not left_text or not right_text:
        return False
    if normalize_ws(left_text) != normalize_ws(right_text):
        return False
    return is_mostly_cjk(left_text) or is_mostly_cjk(right_text)


def clean_markdown_text(text: str) -> tuple[str, int]:
    lines = text.splitlines()
    out: list[str] = []
    in_code = False
    changes = 0
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if in_code or "://" in line or " / " not in line:
            out.append(line)
            continue

        def repl(match: re.Match[str]) -> str:
            left = match.group("left").strip()
            right = match.group("right").strip()
            if is_duplicate_pair(left, right):
                nonlocal_changes[0] += 1
                return left
            return match.group(0)

        nonlocal_changes = [0]
        new_line = DUP_LABEL_RE.sub(repl, line)
        changes += nonlocal_changes[0]
        out.append(new_line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), changes


def clean_bilingual_pairs(obj, stats: dict, path: str = ""):
    if isinstance(obj, dict):
        if "zh" in obj and "en" in obj and is_duplicate_pair(obj.get("zh"), obj.get("en")):
            if obj.get("en") != "":
                obj["en"] = ""
                stats["bilingual_pairs_cleared"] += 1
                stats["paths"].append(path or "<root>")
        for key, value in list(obj.items()):
            child_path = f"{path}.{key}" if path else key
            clean_bilingual_pairs(value, stats, child_path)
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            clean_bilingual_pairs(value, stats, f"{path}[{idx}]")
    return obj


def clean_json_text(text: str, stats: dict, path: Path) -> str:
    if not text.strip():
        return text
    if path.suffix == ".jsonl":
        lines = []
        for idx, line in enumerate(text.splitlines()):
            if not line.strip():
                lines.append(line)
                continue
            obj = json.loads(line)
            clean_bilingual_pairs(obj, stats, f"{path.as_posix()}#{idx+1}")
            lines.append(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
        return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    obj = json.loads(text)
    clean_bilingual_pairs(obj, stats, path.as_posix())
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def build_report(stats: dict, touched_files: list[str]) -> tuple[str, dict]:
    payload = {
        "generated_at": stats.get("generated_at", ""),
        "files_scanned": stats["files_scanned"],
        "markdown_files_changed": stats["markdown_files_changed"],
        "json_files_changed": stats["json_files_changed"],
        "bilingual_pairs_cleared": stats["bilingual_pairs_cleared"],
        "duplicate_labels_removed": stats["duplicate_labels_removed"],
        "touched_files": touched_files,
    }
    lines = [
        "# Bilingual Label Cleanup Report",
        "",
        f"- files_scanned: {payload['files_scanned']}",
        f"- markdown_files_changed: {payload['markdown_files_changed']}",
        f"- json_files_changed: {payload['json_files_changed']}",
        f"- bilingual_pairs_cleared: {payload['bilingual_pairs_cleared']}",
        f"- duplicate_labels_removed: {payload['duplicate_labels_removed']}",
        "",
        "## Touched Files",
        "",
    ]
    if touched_files:
        lines.extend(f"- {item}" for item in touched_files[:200])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines), payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize bilingual labels.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    files = iter_files()
    stats = {
        "generated_at": "",
        "files_scanned": len(files),
        "markdown_files_changed": 0,
        "json_files_changed": 0,
        "bilingual_pairs_cleared": 0,
        "duplicate_labels_removed": 0,
        "paths": [],
    }
    touched: list[str] = []
    changed = False
    for path in files:
        original = path.read_text(encoding="utf-8")
        updated = original
        if path.suffix == MARKDOWN_EXT:
            updated, label_changes = clean_markdown_text(original)
            stats["duplicate_labels_removed"] += label_changes
            if updated != original:
                stats["markdown_files_changed"] += 1
                changed = True
                touched.append(path.relative_to(REPO_ROOT).as_posix())
        else:
            updated = clean_json_text(original, stats, path)
            if updated != original:
                stats["json_files_changed"] += 1
                changed = True
                touched.append(path.relative_to(REPO_ROOT).as_posix())
        if not args.dry_run and not args.check and updated != original:
            path.write_text(updated, encoding="utf-8", newline="\n")

    report_text, payload = build_report(stats, touched)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(report_text, encoding="utf-8", newline="\n")
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    if args.check:
        if changed:
            print(report_text)
            return 1
        print("Bilingual label cleanup check passed")
        return 0

    print(
        json.dumps(
            {
                "files_scanned": stats["files_scanned"],
                "markdown_files_changed": stats["markdown_files_changed"],
                "json_files_changed": stats["json_files_changed"],
                "bilingual_pairs_cleared": stats["bilingual_pairs_cleared"],
                "duplicate_labels_removed": stats["duplicate_labels_removed"],
                "report_md": str(REPORT_MD.relative_to(REPO_ROOT)),
                "report_json": str(REPORT_JSON.relative_to(REPO_ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
