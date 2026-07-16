#!/usr/bin/env python3
"""Validate that human front doors describe the current capability set."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GUIDE = ROOT / "docs/ai-assistant-usage-reference.md"
CURRENT_STATE = ROOT / "docs/project-current-state.md"
PAGES_WORKFLOW = ROOT / ".github/workflows/pages.yml"

CAPABILITIES = {
    "MCF": "docs/architecture/multiscale-causal-fabric.md",
    "PSD": "docs/architecture/probabilistic-system-dynamics.md",
    "ARN": "docs/architecture/adaptive-relational-network.md",
    "点火迭代操作法": "ITERATION.md",
}
BOUNDARY_PHRASES = (
    "候选派生表示",
    "不是新的真值层",
    "已证明的科学理论",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_text_prompt(text: str, source: str) -> str:
    matches = re.findall(r"```text\n(.*?)\n```", text, flags=re.DOTALL)
    require(len(matches) == 1, f"{source}: expected exactly one fenced text prompt")
    return matches[0]


def validate_texts(readme: str, guide: str, current_state: str, pages: str) -> None:
    visible = readme.split("## 项目现状", 1)[1].split("## 生命共同体价值宪章", 1)[0]
    prompt = extract_text_prompt(readme, "README.md")
    guide_prompt = extract_text_prompt(guide, "docs/ai-assistant-usage-reference.md")

    for name, path in CAPABILITIES.items():
        require(name in visible, f"README visible current state omits {name}")
        require(path in readme, f"README omits direct link for {name}: {path}")
        require(path in prompt, f"README prompt omits priority file for {name}: {path}")
        require(path in guide_prompt, f"expanded guide prompt omits priority file for {name}: {path}")

    require(prompt == guide_prompt, "README and expanded AI guide prompts diverge")
    for phrase in BOUNDARY_PHRASES:
        require(phrase in visible or phrase in prompt, f"README omits claim boundary: {phrase}")
        require(phrase in guide_prompt or phrase in guide, f"expanded guide omits claim boundary: {phrase}")

    require("MCF、PSD 与 ARN 怎样分工" in prompt, "prompt omits MCF/PSD/ARN relationship question")
    require("PR #55 was merged" not in current_state, "current-state scope still claims PR #55 total baseline")
    require("PR #56" in current_state and "121Q24D" in current_state, "current-state scope omits Q24 closeout boundary")

    require("cat README.md" in pages, "Pages workflow is not derived from README.md")
    require("Build README reading site" in pages, "Pages workflow omits declared README build step")
    require("README.md" in pages, "Pages workflow does not watch README.md")


def validate_all(root: Path = ROOT) -> dict[str, object]:
    paths = {
        "readme": root / "README.md",
        "guide": root / "docs/ai-assistant-usage-reference.md",
        "current_state": root / "docs/project-current-state.md",
        "pages": root / ".github/workflows/pages.yml",
    }
    for label, path in paths.items():
        require(path.is_file(), f"missing {label} surface: {path}")
    validate_texts(*(path.read_text(encoding="utf-8") for path in paths.values()))
    return {
        "status": "PASS",
        "scope": "repository_local_human_front_door_consistency_only",
        "capabilities": sorted(CAPABILITIES),
        "rendered_pages_live_verified": False,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(validate_all(), ensure_ascii=False, sort_keys=True))
