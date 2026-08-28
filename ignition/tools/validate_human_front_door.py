#!/usr/bin/env python3
"""Validate current repository-native human front doors and system map."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from tools.generate_interactive_system_map import build_projection, load_spec, render_svg, validate_spec
    from tools.governance.validate_human_visibility import validate as validate_human_visibility
    from tools.governance.validate_human_surface_contract import validate as validate_human_surface_contract
except ModuleNotFoundError:
    from generate_interactive_system_map import build_projection, load_spec, render_svg, validate_spec
    from governance.validate_human_visibility import validate as validate_human_visibility
    from governance.validate_human_surface_contract import validate as validate_human_surface_contract


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT if (ROOT / ".github/README.md").is_file() else ROOT.parent
README = REPO_ROOT / ".github/README.md"
GUIDE = ROOT / "docs/ai-assistant-usage-reference.md"
CURRENT_STATE = ROOT / "docs/project-current-state.md"
AI_START = ROOT / "AI-START-HERE.md"
AI_HANDOFF = ROOT / "AI-HANDOFF.md"
LLMS = ROOT / "llms.txt"
HUMAN_READING = ROOT / "HUMAN-READING.md"
SYSTEM_MAP_SPEC = ROOT / "data/architecture/interactive-system-map.json"
SYSTEM_MAP_SVG = ROOT / "docs/generated/ignition-system-architecture.svg"

CAPABILITIES = {
    "MCF": "docs/architecture/multiscale-causal-fabric.md",
    "PSD": "docs/architecture/probabilistic-system-dynamics.md",
    "ARN": "docs/architecture/adaptive-relational-network.md",
    "点火迭代操作法": "ITERATION.md",
}
VERSION_FACTS = {
    "current_method": "1.4.0",
    "historical_method": "1.3.0",
    "earlier_historical_method": "1.2.0",
    "current_map": "0.16.0",
    "historical_map": "0.14.0",
    "earlier_historical_map": "0.13.0",
}
DETAILS_TOKEN_RE = re.compile(r"<details\b[^>]*>|</details\s*>", re.IGNORECASE)
CURRENT_SNAPSHOT_BLOCK_RE = re.compile(
    r"<!-- CURRENT-SNAPSHOT:BEGIN profile=(?:human|ai|machine) schema=current-snapshot-r1 -->\n"
    r".*?<!-- CURRENT-SNAPSHOT:END -->\n?",
    re.DOTALL,
)
README_DETAILS_SUMMARY = "机器状态与工程细节（展开查看）"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _details_spans(text: str) -> tuple[list[tuple[int, int]], int, int]:
    stack: list[re.Match[str]] = []
    spans: list[tuple[int, int]] = []
    unmatched_closes = 0
    for match in DETAILS_TOKEN_RE.finditer(text):
        token = match.group(0).lower()
        if token.startswith("<details"):
            stack.append(match)
        elif stack:
            opening = stack.pop()
            spans.append((opening.start(), match.end()))
        else:
            unmatched_closes += 1
    return spans, len(stack), unmatched_closes


def _inside_details(position: int, spans: list[tuple[int, int]]) -> bool:
    return any(start < position < end for start, end in spans)


def _outside_occurrence(text: str, needle: str, spans: list[tuple[int, int]]) -> bool:
    return any(not _inside_details(match.start(), spans) for match in re.finditer(re.escape(needle), text))


def validate_readme_structure(readme: str) -> None:
    spans, unclosed, unmatched_closes = _details_spans(readme)
    require(not unclosed and not unmatched_closes, "README details tags are not balanced")
    require(len(spans) == 1, "README must have exactly one details container for machine state")
    details_start, details_end = spans[0]
    summary = f"<summary>{README_DETAILS_SUMMARY}</summary>"
    require(readme.count(summary) == 1, "README machine-state details summary is missing or duplicated")
    summary_position = readme.index(summary)
    require(details_start < summary_position < details_end, "README details summary is outside its container")

    visible_h2 = [
        (match.group(1).strip(), match.start())
        for match in re.finditer(r"^## (?!#)(.+?)\s*$", readme, re.MULTILINE)
        if not _inside_details(match.start(), spans)
    ]
    required_h2 = ["1. 项目与价值", "2. 如何使用", "3. 结果与火种", "4. 整体架构", "5. 致谢"]
    require([title for title, _ in visible_h2] == required_h2, "README essential H2 sections must remain visible and ordered")

    current_headings = list(re.finditer(r"^### 项目现状\s*$", readme, re.MULTILINE))
    require(len(current_headings) == 1, "README must have exactly one human project-current-state heading")
    require(not _inside_details(current_headings[0].start(), spans), "README project current state is hidden by details")

    for phrase, label in (
        ("点火是一个", "project definition"),
        ("生命共同体价值宪章", "value charter"),
        ("工程建设阶段已经收口", "engineering closure"),
        ("使用点火生产", "production transition"),
        ("AWAIT_OWNER_PRODUCTION_BRIEF", "Owner production brief handoff"),
        ("OWNER_DEFERRED", "deferred external qualification"),
        ("OWNER_REVIEW_PENDING", "Owner review state"),
        ("PUBLICATION_ACCEPTANCE_NOT_GRANTED", "publication acceptance state"),
        ("HUMAN-READING.md", "human reading route"),
        ("RESULTS/LATEST.md", "current results route"),
        ("火种", "Fire Seeds route"),
        ("ignition-system-architecture.svg", "architecture route"),
    ):
        require(_outside_occurrence(readme, phrase, spans), f"README hides essential {label}")

    blocks = list(CURRENT_SNAPSHOT_BLOCK_RE.finditer(readme))
    require(len(blocks) == 1, "README must contain exactly one generated Current Snapshot block")
    require(_inside_details(blocks[0].start(), spans), "README generated Current Snapshot must be folded")
    for phrase in ("architecture_counts", "live_attempt_projection", "task_lineage", "### 当前主干怎样理解"):
        require(phrase in readme[details_start:details_end], f"README machine detail is outside the details container: {phrase}")
    require("可点击" not in readme and "clickable" not in readme.lower(), "README must not promise rendered architecture clickability")


def validate_texts(readme: str, guide: str, current_state: str, human_reading: str) -> None:
    required_order = ["## 1. 项目与价值", "## 2. 如何使用", "## 3. 结果与火种", "## 4. 整体架构", "## 5. 致谢"]
    validate_readme_structure(readme)
    positions = [readme.index(heading) for heading in required_order]
    require(positions == sorted(positions), "README visible result architecture is out of order")
    require("HUMAN-READING.md" in readme and "RESULTS/LATEST.md" in readme, "README lacks current human result entrances")
    require("火种" in readme and "价值宪章" in readme and "STATE-CHANGELOG" in readme, "README lacks the value, Fire Seeds and AI recovery routes")
    require("ignition-system-architecture.svg" in readme, "README lacks the single complete architecture entry")
    require("human-surface-editorial-contract.md" in readme or "Human Surface" in readme, "README lacks the Human Surface editorial contract route")
    require("任务 101" in current_state, "current state omits task 101")
    require("机器记录" in human_reading and "人类" in human_reading, "human reading page omits machine-human boundary")
    for name, path in CAPABILITIES.items():
        require(name in readme, f"README omits capability {name}")
        require(path in readme, f"README omits direct capability link {path}")
    require("已证明的科学理论" in guide or "科学理论" in guide, "AI guide omits scientific-theory boundary")


def validate_version_front_doors(ai_start: str, ai_handoff: str, llms: str, readme: str | None = None, current_state: str | None = None, nonimpact_proofs: set[str] | None = None) -> None:
    sources = {"ai.start": ai_start, "agent.handoff": ai_handoff, "machine.llms": llms}
    for surface_id, text in sources.items():
        for value in VERSION_FACTS.values():
            require(value in text, f"{surface_id}: missing version fact {value}")
        require(re.search(r"1\.4\.0[^\n]{0,80}(?:Current|当前)|(?:Current|当前)[^\n]{0,80}1\.4\.0", text, re.I), f"{surface_id}: method 1.4.0 is not Current")
        require(not re.search(r"(?:Current|当前)[^\n]{0,30}(?:1\.1\.0|1\.2\.0|1\.3\.0)", text, re.I), f"{surface_id}: stale Current method")
    for surface_id, text in (("human.readme", readme), ("human.current_state", current_state)):
        if text is None or surface_id in (nonimpact_proofs or set()):
            continue
        require(not re.search(r"(?:Current|当前)[^\n]{0,30}(?:1\.1\.0|1\.2\.0|1\.3\.0)", text, re.I), f"{surface_id}: stale Current method")


def validate_system_map(root: Path = ROOT) -> int:
    require(SYSTEM_MAP_SPEC.is_file() and SYSTEM_MAP_SVG.is_file(), "repository system-map assets are missing")
    spec = load_spec(SYSTEM_MAP_SPEC)
    require(spec == build_projection(), "system-map materialized spec is stale")
    validate_spec(spec, root)
    require(SYSTEM_MAP_SVG.read_bytes() == render_svg(spec, root), "repository system-map SVG is stale")
    svg_root = ET.fromstring(SYSTEM_MAP_SVG.read_bytes())
    source_links = svg_root.findall(".//{http://www.w3.org/2000/svg}a")
    require(len(source_links) == len(spec["nodes"]), "system-map SVG source link metadata does not cover every node")
    require(all(link.attrib.get("href", "").startswith("https://github.com/Arvin-liu/when-systems-catch-fire/") for link in source_links), "system-map source link metadata is not canonical GitHub HTTPS")
    require({node["id"] for node in spec["nodes"]} == {link.attrib.get("data-node-id") for link in source_links}, "system-map source link metadata ids diverge from spec")
    require(not any(node["id"] == "l7" for node in spec["nodes"]), "system map adds forbidden L7")
    return len(spec["nodes"])


def validate_all(root: Path = ROOT) -> dict[str, object]:
    for path in (README, GUIDE, CURRENT_STATE, HUMAN_READING, AI_START, AI_HANDOFF, LLMS):
        require(path.is_file(), f"missing front door: {path}")
    validate_texts(README.read_text(encoding="utf-8"), GUIDE.read_text(encoding="utf-8"), CURRENT_STATE.read_text(encoding="utf-8"), HUMAN_READING.read_text(encoding="utf-8"))
    validate_version_front_doors(AI_START.read_text(encoding="utf-8"), AI_HANDOFF.read_text(encoding="utf-8"), LLMS.read_text(encoding="utf-8"), README.read_text(encoding="utf-8"), CURRENT_STATE.read_text(encoding="utf-8"))
    visibility = validate_human_visibility()
    human_surface = validate_human_surface_contract()
    nodes = validate_system_map(root)
    return {"status": "PASS", "scope": "repository_native_human_surfaces_only", "system_map_source_link_nodes": nodes, "human_visibility": visibility, "human_surface_contract": human_surface, "external_truth_verified": False}


if __name__ == "__main__":
    print(json.dumps(validate_all(), ensure_ascii=False, sort_keys=True))
