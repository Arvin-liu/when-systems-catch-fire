#!/usr/bin/env python3
"""Validate that known object IDs in Markdown are Markdown links."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "data" / "links" / "object-link-registry.json"

DEFAULT_EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_registry() -> dict[str, dict]:
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {str(key): value for key, value in data.items() if isinstance(value, dict) and value.get("canonical_path")}


def markdown_files(include_archive: bool) -> list[Path]:
    files = []
    for path in ROOT.rglob("*.md"):
        if any(part in DEFAULT_EXCLUDED_PARTS for part in path.parts):
            continue
        if not include_archive and "archive" in path.parts:
            continue
        files.append(path)
    return sorted(files)


def build_id_pattern(ids: list[str]) -> re.Pattern[str]:
    escaped = sorted((re.escape(item) for item in ids), key=len, reverse=True)
    joined = "|".join(escaped)
    return re.compile(rf"(?<![A-Za-z0-9_/#.{{}}-])({joined})(?![A-Za-z0-9_.{{}}-])")


def protected_spans(line: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    patterns = [
        re.compile(r"!\[[^\]]*\]\([^)]*\)"),
        re.compile(r"\[[^\]]+\]\([^)]*\)"),
        re.compile(r"https?://[^\s<>)]+"),
        re.compile(r"<https?://[^>]+>"),
        re.compile(r"`[^`]+`"),
    ]
    for pattern in patterns:
        spans.extend(match.span() for match in pattern.finditer(line))
    spans.sort()
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            old_start, old_end = merged[-1]
            merged[-1] = (old_start, max(old_end, end))
    return merged


def scan_text(text: str, id_re: re.Pattern[str]) -> list[dict]:
    findings: list[dict] = []
    in_fence = False
    for line_number, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        protected = protected_spans(line)
        cursor = 0
        for start, end in protected + [(len(line), len(line))]:
            segment = line[cursor:start]
            for match in id_re.finditer(segment):
                findings.append(
                    {
                        "line": line_number,
                        "object_id": match.group(1),
                        "context": line.strip()[:240],
                    }
                )
            cursor = end
    return findings


def target_for(path: Path, canonical_path: str) -> str:
    return Path(os.path.relpath((ROOT / canonical_path).resolve(), path.parent.resolve())).as_posix()


def validate_link_targets(files: list[Path], registry: dict[str, dict]) -> list[dict]:
    errors: list[dict] = []
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), 1):
            for match in link_re.finditer(line):
                object_id = match.group(1)
                if object_id not in registry:
                    continue
                expected = target_for(path, str(registry[object_id]["canonical_path"]))
                actual = match.group(2)
                if actual != expected:
                    errors.append(
                        {
                            "path": rel(path),
                            "line": line_number,
                            "object_id": object_id,
                            "actual": actual,
                            "expected": expected,
                        }
                    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Markdown object ID links")
    parser.add_argument("--check", action="store_true", help="Run validation")
    parser.add_argument("--include-archive", action="store_true", help="Also scan archive/ Markdown files")
    parser.add_argument("--skip", action="append", default=[], help="Repo-relative Markdown file to skip")
    parser.add_argument("--max-findings", type=int, default=40)
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")

    registry = load_registry()
    id_re = build_id_pattern(sorted(registry))
    skip_paths = set(args.skip)
    files = [path for path in markdown_files(include_archive=args.include_archive) if rel(path) not in skip_paths]

    bare_findings: list[dict] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        findings = scan_text(text, id_re)
        for item in findings:
            item["path"] = rel(path)
        bare_findings.extend(findings)

    target_errors = validate_link_targets(files, registry)
    if bare_findings or target_errors:
        print(
            json.dumps(
                {
                    "passed": False,
                    "bare_id_findings": bare_findings[: args.max_findings],
                    "bare_id_finding_count": len(bare_findings),
                    "target_errors": target_errors[: args.max_findings],
                    "target_error_count": len(target_errors),
                    "skipped_files": sorted(skip_paths),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "passed": True,
                "checked_markdown_files": len(files),
                "skipped_files": sorted(skip_paths),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
