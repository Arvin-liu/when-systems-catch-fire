#!/usr/bin/env python3
"""Validate the small, append-only AI state-delta log contract."""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
PATH = ROOT / "STATE-CHANGELOG.md"
ENTRY_RE = re.compile(r"^## (?P<date>\d{4}-\d{2}-\d{2}) — (?P<label>.+)$", re.MULTILINE)
SHA_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
REQUIRED_FIELDS = (
    "main_state",
    "delta",
    "authority_changes",
    "epistemic_state",
    "obligations",
    "stale_knowledge",
    "next_read",
)


def _section(text: str, start: int, end: int) -> str:
    return text[start:end]


def validate(path: Path = PATH) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing {path.relative_to(ROOT)}"]
    text = path.read_text(encoding="utf-8")
    if not text.startswith("# STATE-CHANGELOG\n"):
        errors.append("title must be exactly # STATE-CHANGELOG")
    if "append-only" not in text:
        errors.append("append-only protocol is missing")
    entries = list(ENTRY_RE.finditer(text))
    if len(entries) < 2:
        errors.append("baseline and at least one formal delta are required")
        return errors
    if "BASELINE-CURRENT" not in entries[0].group("label"):
        errors.append("first entry must be BASELINE-CURRENT")
    if not any("BASELINE-CURRENT" not in entry.group("label") for entry in entries):
        errors.append("at least one non-baseline formal delta is required")

    for index, entry in enumerate(entries):
        end = entries[index + 1].start() if index + 1 < len(entries) else len(text)
        section = _section(text, entry.start(), end)
        try:
            date.fromisoformat(entry.group("date"))
        except ValueError:
            errors.append(f"entry {index + 1} has invalid ISO date")
        if not SHA_RE.search(section):
            errors.append(f"entry {index + 1} must bind an exact base main tip")
        for field in REQUIRED_FIELDS:
            if not re.search(rf"^- {re.escape(field)}:\s*\S", section, re.MULTILINE):
                errors.append(f"entry {index + 1} missing nonblank field {field}")

    for target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target_path = target.split("#", 1)[0]
        if not target_path:
            continue
        resolved = (path.parent / target_path).resolve()
        try:
            resolved.relative_to(REPO_ROOT.resolve())
        except ValueError:
            errors.append(f"link escapes repository: {target}")
            continue
        if not resolved.exists():
            errors.append(f"broken repository link: {target}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: append-only state log has baseline, formal delta fields, main bindings and live links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
