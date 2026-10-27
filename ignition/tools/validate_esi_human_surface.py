#!/usr/bin/env python3
"""Validate the ESI human-facing first screen and claim-ceiling language."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SURFACE = ROOT / "docs/architecture/esi-human-surface-r0.md"


REQUIRED_HEADINGS = (
    "它是什么、为什么出现",
    "它可以做什么",
    "它不能推出什么",
    "还缺什么、下一步是什么",
    "如何回到精确记录",
)


def validate(text: str, surface: Path = DEFAULT_SURFACE) -> list[str]:
    errors: list[str] = []
    for heading in REQUIRED_HEADINGS:
        if f"## {heading}" not in text:
            errors.append(f"human surface lacks required reading answer: {heading}")
    required_phrases = (
        "候选现象",
        "CANDIDATE_ESI_SIGNAL",
        "不是已经证明的机制",
        "软",
        "权限、授权、真值",
        "不是脑控、洗脑、永久训练",
        "ANECDOTE_OR_OPEN_QUESTION",
        "NOT_RUN_LIVE_EXTERNAL",
        "之元写作法",
        "不改变 canonical 状态",
    )
    for phrase in required_phrases:
        if phrase not in text:
            errors.append(f"human surface lacks boundary phrase: {phrase}")
    if re.search(r"(?:prompt|提示词).*(?:请|必须)|(?:请|必须).*(?:prompt|提示词)", text, re.IGNORECASE):
        errors.append("human surface must not turn the structural surface into a prompt")
    if "../../data/epistemic-governance/offline-pilot-result-r0.json" in text and not (surface.parent / "../../data/epistemic-governance/offline-pilot-result-r0.json").resolve().is_file():
        errors.append("offline pilot result link is broken")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("surface", type=Path, nargs="?", default=DEFAULT_SURFACE)
    args = parser.parse_args()
    errors = validate(args.surface.read_text(encoding="utf-8"), args.surface)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("ESI_HUMAN_SURFACE_OK first_screen=bounded claim_ceiling=visible writing_method=0.5.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
