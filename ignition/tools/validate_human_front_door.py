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
HUMAN_CURRENT_HEADING = "### 项目现状"
HUMAN_CHARTER_HEADING = "### 价值宪章"
CHARTER_LINK = "../ignition/docs/governance/life-community-value-charter.md"
FORBIDDEN_HOMEPAGE_MACHINE_TOKENS = (
    "CURRENT-SNAPSHOT:BEGIN",
    "CURRENT-SNAPSHOT:END",
    "Current Snapshot",
    "generated Current",
    "architecture_counts",
    "live_attempt_projection",
    "formal_task_terminal_history",
    "task_lineage",
    "机器状态与工程细节",
    "当前主干怎样理解",
    "current_identity_epoch",
    "current_formal_task",
    "current_iteration_boundary",
    "release_lifecycle",
    "current_map_version",
    "current_state_status",
    "EPISTEMICALLY_ACCEPTED",
    "CURRENT_WITH_OPEN_OBLIGATIONS",
    "COMPLETED_WITH_OPEN_OBLIGATIONS",
    "AWAIT_OWNER_PRODUCTION_BRIEF",
    "LIVE_EXTERNAL_INVOCATION",
    "OWNER_DEFERRED",
    "OWNER_REVIEW_PENDING",
    "PUBLICATION_ACCEPTANCE_NOT_GRANTED",
    "Reference / Conformance / Fallback",
    "Kernel",
    "Runtime",
    "Federation",
    "Driver Console",
    "current-snapshot",
    "live_attempt",
    "formal_task",
    "architecture_count",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_readme_structure(readme: str) -> None:
    visible_h2 = [
        (match.group(1).strip(), match.start())
        for match in re.finditer(r"^## (?!#)(.+?)\s*$", readme, re.MULTILINE)
    ]
    required_h2 = ["1. 项目与价值", "2. 如何使用", "3. 结果与火种", "4. 整体架构", "5. 致谢"]
    require([title for title, _ in visible_h2] == required_h2, "README essential H2 sections must remain visible and ordered")

    section_one_start = next(position for title, position in visible_h2 if title == required_h2[0])
    section_two_start = next(position for title, position in visible_h2 if title == required_h2[1])
    section_one = readme[section_one_start:section_two_start]
    h3_matches = list(re.finditer(r"^### (?!#)(.+?)\s*$", section_one, re.MULTILINE))
    h3_titles = [match.group(1).strip() for match in h3_matches]
    require(h3_titles == ["项目现状", "价值宪章"], "README 项目与价值 must contain exactly 项目现状 then 价值宪章")
    require(section_one[section_one.find("\n") + 1 : h3_matches[0].start()].strip() == "", "README 项目现状 must be the first block under 项目与价值")

    current_text = section_one[h3_matches[0].end() : h3_matches[1].start()]
    charter_text = section_one[h3_matches[1].end() :]
    for phrase, label in (
        ("工程建设已经收口", "engineering closure"),
        ("使用点火生产", "production transition"),
        ("production brief", "Owner production brief handoff"),
        ("Owner", "Owner decision boundary"),
        ("文章", "article production boundary"),
        ("书籍", "book production boundary"),
        ("external-Agent qualification", "deferred external qualification"),
    ):
        require(phrase in current_text, f"README project status lacks {label}")
    for phrase, label in (
        ("长瞻一宇同叩月", "poetic source"),
        ("生命共同体", "life-community scope"),
        ("未来世代", "future generations"),
        ("非人类生命", "non-human life"),
        ("沉默主体", "silent subjects"),
        ("新型智能", "new intelligences"),
        ("不可逆", "irreversible harm boundary"),
        ("不可补偿", "non-compensable harm boundary"),
        ("非自愿", "non-consensual harm boundary"),
        ("纠错", "correction"),
        ("退出", "exit"),
        ("恢复", "recovery"),
        ("未来选择空间", "future choice space"),
        ("预防原则", "precautionary principle"),
        ("规范性价值", "normative value boundary"),
        ("不是经验事实、数学证明或外部真值来源", "non-epistemic charter boundary"),
    ):
        require(phrase in charter_text, f"README value charter lacks {label}")
    require(CHARTER_LINK in charter_text, "README value charter link is missing or not canonical")
    require("点火是一个仓库原生" not in readme, "README must not retain the superseded project definition")
    require("<details" not in readme.lower() and "</details" not in readme.lower(), "README must not fold machine state into details")
    lowered = readme.casefold()
    for token in FORBIDDEN_HOMEPAGE_MACHINE_TOKENS:
        require(token.casefold() not in lowered, f"README must not contain machine Current state: {token}")
    require("可点击" not in readme and "clickable" not in lowered, "README must not promise rendered architecture clickability")
    for phrase, label in (
        ("HUMAN-READING.md", "human reading route"),
        ("RESULTS/LATEST.md", "current results route"),
        ("火种", "Fire Seeds route"),
        ("ignition-system-architecture.svg", "architecture route"),
    ):
        require(phrase in readme, f"README lacks {label}")


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
