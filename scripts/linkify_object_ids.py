#!/usr/bin/env python3
"""Linkify known object IDs across Markdown files.

The link text remains the object ID itself. Code fences, existing Markdown links,
URLs, and non-ID inline code spans are left untouched.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "data" / "links" / "object-link-registry.json"
REBUILD = ROOT / "data" / "rebuild"
REPORT_JSON = REBUILD / "object-id-linkification-report.json"
REPORT_MD = REBUILD / "object-id-linkification-report.md"

DEFAULT_EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}


@dataclass(frozen=True)
class Replacement:
    object_id: str
    target: str


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def load_registry() -> dict[str, dict]:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"missing registry: {rel(REGISTRY_PATH)}")
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {str(key): value for key, value in data.items() if isinstance(value, dict) and value.get("canonical_path")}


def build_id_pattern(ids: list[str]) -> re.Pattern[str]:
    escaped = sorted((re.escape(item) for item in ids), key=len, reverse=True)
    joined = "|".join(escaped)
    return re.compile(rf"(?<![A-Za-z0-9_/#.{{}}-])({joined})(?![A-Za-z0-9_.{{}}-])")


def markdown_files(include_archive: bool) -> list[Path]:
    files = []
    for path in ROOT.rglob("*.md"):
        if any(part in DEFAULT_EXCLUDED_PARTS for part in path.parts):
            continue
        if not include_archive and "archive" in path.parts:
            continue
        files.append(path)
    return sorted(files)


def relative_target(source: Path, canonical_path: str) -> str:
    target = (ROOT / canonical_path).resolve()
    raw = os.path.relpath(target, source.parent.resolve())
    return Path(raw).as_posix()


def protect_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []

    patterns = [
        re.compile(r"!\[[^\]]*\]\([^)]*\)"),
        re.compile(r"\[[^\]]+\]\([^)]*\)"),
        re.compile(r"https?://[^\s<>)]+"),
        re.compile(r"<https?://[^>]+>"),
    ]
    for pattern in patterns:
        spans.extend(match.span() for match in pattern.finditer(text))

    spans.sort()
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            old_start, old_end = merged[-1]
            merged[-1] = (old_start, max(old_end, end))
    return merged


def inline_code_exact_id_pattern(ids: list[str]) -> re.Pattern[str]:
    escaped = sorted((re.escape(item) for item in ids), key=len, reverse=True)
    return re.compile(rf"`({'|'.join(escaped)})`")


def replace_inline_exact_ids(line: str, source: Path, registry: dict[str, dict], code_id_re: re.Pattern[str]) -> tuple[str, int, list[Replacement]]:
    count = 0
    replacements: list[Replacement] = []

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        object_id = match.group(1)
        target = relative_target(source, str(registry[object_id]["canonical_path"]))
        count += 1
        replacements.append(Replacement(object_id=object_id, target=target))
        return f"[{object_id}]({target})"

    return code_id_re.sub(repl, line), count, replacements


def fix_existing_object_id_link_targets(line: str, source: Path, registry: dict[str, dict]) -> tuple[str, int]:
    fixed = 0
    link_re = re.compile(r"(!?)\[([^\]]+)\]\(([^)]+)\)")

    def repl(match: re.Match[str]) -> str:
        nonlocal fixed
        image_prefix = match.group(1)
        link_text = match.group(2)
        link_target = match.group(3)
        if image_prefix or link_text not in registry:
            return match.group(0)
        if link_target.startswith(("http://", "https://", "#")):
            return match.group(0)
        expected = relative_target(source, str(registry[link_text]["canonical_path"]))
        if link_target == expected:
            return match.group(0)
        fixed += 1
        return f"[{link_text}]({expected})"

    return link_re.sub(repl, line), fixed


def replace_plain_ids(line: str, source: Path, registry: dict[str, dict], id_re: re.Pattern[str]) -> tuple[str, int, list[Replacement]]:
    protected = protect_spans(line)
    output: list[str] = []
    cursor = 0
    count = 0
    replacements: list[Replacement] = []

    def replace_segment(segment: str) -> str:
        nonlocal count

        def repl(match: re.Match[str]) -> str:
            nonlocal count
            object_id = match.group(1)
            target = relative_target(source, str(registry[object_id]["canonical_path"]))
            count += 1
            replacements.append(Replacement(object_id=object_id, target=target))
            return f"[{object_id}]({target})"

        return id_re.sub(repl, segment)

    for start, end in protected:
        if cursor < start:
            output.append(replace_segment(line[cursor:start]))
        output.append(line[start:end])
        cursor = end
    if cursor < len(line):
        output.append(replace_segment(line[cursor:]))

    return "".join(output), count, replacements


def linkify_text(text: str, source: Path, registry: dict[str, dict], id_re: re.Pattern[str], code_id_re: re.Pattern[str]) -> tuple[str, int, dict[str, int]]:
    in_fence = False
    total = 0
    per_id: dict[str, int] = {}
    new_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        body = line[:-1] if line.endswith("\n") else line
        newline = "\n" if line.endswith("\n") else ""
        stripped = body.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            new_lines.append(line)
            continue
        if in_fence:
            new_lines.append(line)
            continue

        body, target_fix_count = fix_existing_object_id_link_targets(body, source, registry)
        body, count1, reps1 = replace_inline_exact_ids(body, source, registry, code_id_re)
        body, count2, reps2 = replace_plain_ids(body, source, registry, id_re)
        for rep in reps1 + reps2:
            per_id[rep.object_id] = per_id.get(rep.object_id, 0) + 1
        total += target_fix_count + count1 + count2
        new_lines.append(body + newline)

    return "".join(new_lines), total, per_id


def build_report(changed: list[dict], checked_files: int, replacement_count: int, dry_run: bool, skipped: list[str]) -> dict:
    return {
        "report_name": "object-id-linkification-report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": git_head(),
        "registry": rel(REGISTRY_PATH),
        "checked_markdown_files": checked_files,
        "changed_markdown_files": len(changed),
        "replacement_count": replacement_count,
        "dry_run": dry_run,
        "skipped_files": skipped,
        "link_text_policy": "object_id_itself",
        "protected_spans": ["code_fences", "existing_markdown_links", "urls", "non_exact_inline_code"],
        "files": changed,
    }


def render_report_md(report: dict) -> str:
    lines = [
        "# Object ID Linkification Report",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- HEAD: `{report['source_commit']}`",
        f"- Registry: `{report['registry']}`",
        f"- Checked Markdown files: {report['checked_markdown_files']}",
        f"- Changed Markdown files: {report['changed_markdown_files']}",
        f"- Replacements: {report['replacement_count']}",
        f"- Dry run: {str(report['dry_run']).lower()}",
        "- Link text policy: object ID itself",
        "",
        "## Changed Files",
        "",
    ]
    if not report["files"]:
        lines.append("None.")
    else:
        lines.extend(["| File | Replacements | Distinct IDs |", "|---|---:|---:|"])
        for item in report["files"]:
            lines.append(f"| `{item['path']}` | {item['replacements']} | {item['distinct_ids']} |")
    if report["skipped_files"]:
        lines.extend(["", "## Skipped Files", ""])
        for path in report["skipped_files"]:
            lines.append(f"- `{path}`")
    return "\n".join(lines) + "\n"


def run(dry_run: bool, include_archive: bool, skip_paths: set[str]) -> dict:
    registry = load_registry()
    ids = sorted(registry)
    id_re = build_id_pattern(ids)
    code_id_re = inline_code_exact_id_pattern(ids)
    files = markdown_files(include_archive=include_archive)

    changed: list[dict] = []
    replacement_count = 0
    skipped: list[str] = []
    for path in files:
        relative = rel(path)
        if relative in skip_paths:
            skipped.append(relative)
            continue
        old = path.read_text(encoding="utf-8", errors="ignore")
        new, count, per_id = linkify_text(old, path, registry, id_re, code_id_re)
        if count:
            replacement_count += count
            changed.append(
                {
                    "path": relative,
                    "replacements": count,
                    "distinct_ids": len(per_id),
                    "ids": dict(sorted(per_id.items())),
                }
            )
            if not dry_run:
                path.write_text(new, encoding="utf-8")

    report = build_report(
        changed=changed,
        checked_files=len(files) - len(skipped),
        replacement_count=replacement_count,
        dry_run=dry_run,
        skipped=skipped,
    )
    if not dry_run:
        REBUILD.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        REPORT_MD.write_text(render_report_md(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Linkify object IDs in Markdown files")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing Markdown files")
    parser.add_argument("--all", action="store_true", help="Write changes")
    parser.add_argument("--include-archive", action="store_true", help="Also process archive/ Markdown files")
    parser.add_argument("--skip", action="append", default=[], help="Repo-relative Markdown file to skip")
    args = parser.parse_args()

    if args.dry_run == args.all:
        parser.error("choose exactly one of --dry-run or --all")

    report = run(dry_run=args.dry_run, include_archive=args.include_archive, skip_paths=set(args.skip))
    print(json.dumps({key: report[key] for key in [
        "report_name",
        "checked_markdown_files",
        "changed_markdown_files",
        "replacement_count",
        "dry_run",
        "skipped_files",
    ]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
