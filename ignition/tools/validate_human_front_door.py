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
    "current_map": "0.10.0",
    "historical_map": "0.9.0",
    "earlier_historical_map": "0.8.0",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_texts(readme: str, guide: str, current_state: str, human_reading: str) -> None:
    required_order = ["## 1. 项目与价值", "## 2. 如何使用", "## 3. 结果与火种", "## 4. 整体架构", "## 5. 致谢"]
    positions = [readme.index(heading) for heading in required_order]
    require(positions == sorted(positions), "README visible result architecture is out of order")
    require("<details" not in readme.lower(), "README hides essential content")
    require("HUMAN-READING.md" in readme and "RESULTS/LATEST.md" in readme, "README lacks current human result entrances")
    require("火种" in readme and "价值宪章" in readme and "STATE-CHANGELOG" in readme, "README lacks the value, Fire Seeds and AI recovery routes")
    require("透明可点击完整总架构图 SVG" in readme and "ignition-system-architecture.svg" in readme, "README lacks the single complete architecture entry")
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
    links = svg_root.findall(".//{http://www.w3.org/2000/svg}a")
    require(len(links) == len(spec["nodes"]), "not every system-map node is clickable")
    require(all(link.attrib.get("href", "").startswith("https://github.com/Arvin-liu/when-systems-catch-fire/") for link in links), "system-map node link is not canonical GitHub HTTPS")
    require({node["id"] for node in spec["nodes"]} == {link.attrib.get("data-node-id") for link in links}, "system-map SVG ids diverge from spec")
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
    return {"status": "PASS", "scope": "repository_native_human_surfaces_only", "interactive_system_map_nodes": nodes, "human_visibility": visibility, "human_surface_contract": human_surface, "external_truth_verified": False}


if __name__ == "__main__":
    print(json.dumps(validate_all(), ensure_ascii=False, sort_keys=True))
