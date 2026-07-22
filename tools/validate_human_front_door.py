#!/usr/bin/env python3
"""Validate that human front doors describe the current capability set."""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from tools.generate_interactive_system_map import build_projection, load_spec, render_svg, validate_spec
except ModuleNotFoundError:  # Direct script execution adds tools/, not repository root, to sys.path.
    from generate_interactive_system_map import build_projection, load_spec, render_svg, validate_spec


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GUIDE = ROOT / "docs/ai-assistant-usage-reference.md"
CURRENT_STATE = ROOT / "docs/project-current-state.md"
AI_START = ROOT / "AI-START-HERE.md"
AI_HANDOFF = ROOT / "AI-HANDOFF.md"
LLMS = ROOT / "llms.txt"
PAGES_WORKFLOW = ROOT / ".github/workflows/pages.yml"
SHOWCASE_REGISTRY = ROOT / "data/publication/zhiyuan-writing-showcase.json"
SHOWCASE_INDEX = ROOT / "docs/publication/zhiyuan-writing-showcase.md"
SYSTEM_MAP_SPEC = ROOT / "data/architecture/interactive-system-map.json"
SYSTEM_MAP_SVG = ROOT / "pages/generated/ignition-system-map.svg"
SYSTEM_MAP_PAGE = ROOT / "pages/system-map.html"

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
VERSION_FACTS = {
    "current_method": "1.3.0",
    "historical_method": "1.2.0",
    "earlier_historical_method": "1.1.0",
    "current_map": "0.3.0",
    "historical_map": "0.2.0",
    "earlier_historical_map": "0.1.0",
}
ROLLBACK_TYPO = "roll" + "bar"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_text_prompt(text: str, source: str) -> str:
    matches = re.findall(r"```text\n(.*?)\n```", text, flags=re.DOTALL)
    require(len(matches) == 1, f"{source}: expected exactly one fenced text prompt")
    return matches[0]


def validate_texts(readme: str, guide: str, current_state: str, pages: str) -> None:
    require(readme.count("## 项目现状") == 1, "README must expose exactly one project-current-state heading")
    required_order = ["## 项目现状", "## 之元写作法成果", "## 生命共同体价值宪章", "## 完整可点击系统图", "## 使用指南"]
    positions = [readme.index(heading) for heading in required_order]
    require(positions == sorted(positions), "README top-level information architecture is out of order")
    require("<summary>展开：当前能力、限制与完整项目现状</summary>" in readme, "README omits folded current-state detail")
    require("<summary>展开：完整 AI 首次阅读提示词</summary>" in readme, "README AI prompt is not folded")
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


def validate_version_front_doors(ai_start: str, ai_handoff: str, llms: str) -> None:
    sources = {"AI-START-HERE.md": ai_start, "AI-HANDOFF.md": ai_handoff, "llms.txt": llms}
    for source, text in sources.items():
        for value in VERSION_FACTS.values():
            require(value in text, f"{source}: missing version fact {value}")
        require(re.search(r"(?:current|当前)[^\n]{0,80}1\.3\.0|1\.3\.0[^\n]{0,80}(?:Current|当前)", text, re.IGNORECASE), f"{source}: method 1.3.0 is not explicitly Current")
        require(re.search(r"(?:historical|历史)[^\n]{0,80}1\.2\.0|1\.2\.0[^\n]{0,80}(?:Historical|历史)", text, re.IGNORECASE), f"{source}: method 1.2.0 is not explicitly Historical")
        require(re.search(r"(?:historical|历史)[^\n]{0,80}1\.1\.0|1\.1\.0[^\n]{0,80}(?:Historical|历史)", text, re.IGNORECASE), f"{source}: method 1.1.0 is not explicitly Historical")
        require(re.search(r"(?:current|当前)[^\n]{0,80}0\.3\.0|0\.3\.0[^\n]{0,80}(?:Current|当前)", text, re.IGNORECASE), f"{source}: map 0.3.0 is not explicitly Current")
        require(re.search(r"(?:historical|历史)[^\n]{0,80}0\.2\.0|0\.2\.0[^\n]{0,80}(?:Historical|历史)", text, re.IGNORECASE), f"{source}: map 0.2.0 is not explicitly Historical")
        require(not re.search(r"(?:current|当前)(?:迭代)?(?:方法|method)[^\n]{0,20}(?:1\.1\.0|1\.2\.0)", text, re.IGNORECASE), f"{source}: stale Current method")
        require(ROLLBACK_TYPO not in text.lower(), f"{source}: misspelled rollback term")


def validate_system_map(root: Path, readme: str, pages: str) -> int:
    for path in (SYSTEM_MAP_SPEC, SYSTEM_MAP_SVG, SYSTEM_MAP_PAGE):
        require(path.is_file(), f"missing interactive system-map asset: {path}")
    spec = load_spec(SYSTEM_MAP_SPEC)
    require(spec == build_projection(), "interactive system-map materialized spec is stale or hand-maintained")
    validate_spec(spec, root)
    require(SYSTEM_MAP_SVG.read_bytes() == render_svg(spec, root), "interactive system-map SVG is stale")

    required_groups = {"front_doors", "layers", "core", "models", "operations", "governance", "writing", "feedback", "boundaries"}
    require({group["id"] for group in spec["groups"]} == required_groups, "interactive system map has incomplete or unexpected groups")
    required_nodes = {
        "readme", "summary", "usage", "ai_guide", "current_state",
        "l0", "l1", "l2", "l3", "l4", "l5", "l6",
        "foundation", "function_os", "mcf", "psd", "arn",
        "q12", "q13", "q14", "iteration", "sync", "charter", "licensing", "sustainability",
        "external_input", "ignition_increment", "source_pool", "zhiyuan_method",
        "case_source", "point_fire_analysis", "accepted_work", "showcase", "showcase_registry",
        "public_response", "provenance_capture", "candidate_return", "feedback_routes",
        "no_l7", "no_truth_upgrade", "no_totality_proof",
        "copyright_governance_jurisdiction_registry", "copyright_governance_source_rights",
        "copyright_governance_material_classification", "copyright_governance_history_remediation",
        "copyright_governance_publication_gate_validator", "copyright_governance_non_republication_principle",
        "copyright_governance_tests",
        "discovery_commitment_claim_contract", "discovery_commitment_gate_validator",
        "discovery_commitment_pilot_q33",
        "agent_responsibility_contract", "agent_responsibility_gate_validator",
        "agent_responsibility_pilot_q34",
        "observation_prediction_contract", "observation_prediction_gate_validator",
        "observation_prediction_pilot_q34",
        "intervention_failure_contract", "intervention_failure_gate_validator",
        "intervention_failure_pilot",
        "analogy_audit_contract", "analogy_audit_gate_validator", "analogy_audit_pilot",
        "evidence_retrieval_contract", "evidence_retrieval_gate_validator", "evidence_retrieval_pilot",
        "failure_lineage_contract", "failure_lineage_gate_validator", "failure_lineage_pilot",
        "symbolic_power_perspective_contract", "symbolic_power_perspective_gate_validator", "symbolic_power_perspective_pilot",
    }
    require({node["id"] for node in spec["nodes"]} == required_nodes, "interactive system map does not cover the declared complete node set")

    svg_root = ET.fromstring(SYSTEM_MAP_SVG.read_bytes())
    links = svg_root.findall(".//{http://www.w3.org/2000/svg}a")
    require(len(links) == len(spec["nodes"]), "not every system-map node is a clickable SVG link")
    linked_ids = {link.attrib.get("data-node-id") for link in links}
    require(linked_ids == required_nodes, "SVG clickable node ids diverge from spec")
    for link in links:
        require(link.attrib.get("href", "").startswith("https://github.com/Arvin-liu/when-systems-catch-fire/"), f"node link is not canonical HTTPS: {link.attrib}")
        require(link.attrib.get("data-target"), f"SVG node link lacks data-target: {link.attrib}")

    charter = readme.index("## 生命共同体价值宪章")
    system_map = readme.index("## 完整可点击系统图")
    usage = readme.index("## 使用指南")
    require(charter < system_map < usage, "README system map must follow Charter and precede usage")
    require("<object data=\"./generated/ignition-system-map.svg\"" in readme, "Pages homepage does not directly embed the complete interactive SVG")
    require("./pages/generated/ignition-system-map.svg" in readme, "GitHub README does not preserve the complete SVG preview")
    require("打开交互版完整图" in readme, "GitHub README lacks an explicit interactive-map entrance")
    require("cp pages/generated/ignition-system-map.svg site/generated/ignition-system-map.svg" in pages, "Pages workflow omits generated SVG publication")
    require("cp pages/system-map.html site/system-map.html" in pages, "Pages workflow omits canonical interactive page")
    require("generate_interactive_system_map.py --check" in pages, "Pages workflow does not reject stale generated SVG")
    require("cp docs/architecture/typed-change-propagation.md site/docs/architecture/typed-change-propagation.md" in pages, "Pages artifact omits typed propagation documentation")
    require("cp reports/operations/121Q32-change-propagation-impact.md site/reports/operations/121Q32-change-propagation-impact.md" in pages, "Pages artifact omits propagation impact report")
    for asset in (
        "data/operations/project-components.json",
        "data/operations/change-propagation-topology.json",
        "data/operations/component-execution-profiles.json",
        "data/architecture/interactive-system-map-layout.json",
        "data/architecture/interactive-system-map.json",
    ):
        require(f"cp {asset} site/{asset}" in pages, f"Pages artifact omits linked map authority: {asset}")
    require(spec.get("schema_version") == "2.0.0", "system map is not the registry-derived candidate projection")
    require({edge["relation_domain"] for edge in spec["edges"]} <= {"substantive_causal_candidate", "repository_dependency", "synchronization_obligation"}, "system-map relation domains escape declared authority classes")

    page = SYSTEM_MAP_PAGE.read_text(encoding="utf-8")
    require("generated/ignition-system-map.svg" in page and "<object" in page, "canonical interactive page does not embed the SVG")
    public_text = "\n".join([readme, pages, page, SYSTEM_MAP_SPEC.read_text(encoding="utf-8"), SYSTEM_MAP_SVG.read_text(encoding="utf-8")])
    require("/Users/" not in public_text and "/tmp/" not in public_text and "file://" not in public_text, "interactive system-map surfaces leak a local path")
    return len(spec["nodes"])


def validate_showcase(root: Path, readme: str) -> None:
    require(SHOWCASE_REGISTRY.is_file(), f"missing showcase registry: {SHOWCASE_REGISTRY}")
    require(SHOWCASE_INDEX.is_file(), f"missing showcase index: {SHOWCASE_INDEX}")
    registry = json.loads(SHOWCASE_REGISTRY.read_text(encoding="utf-8"))
    limit = registry.get("homepage_limit")
    items = registry.get("items")
    require(isinstance(limit, int) and 1 <= limit <= 3, "showcase homepage_limit must be 1..3")
    require(isinstance(items, list) and items, "showcase registry must contain at least one item")
    require("查看更多之元写作法成果" in readme, "README omits complete showcase link")
    for item in items:
        for key in ("work_path", "case_path", "analysis_path", "method_path"):
            path = root / item[key]
            require(path.is_file(), f"showcase item path is missing: {item[key]}")
        work_path = root / item["work_path"]
        digest = hashlib.sha256(work_path.read_bytes()).hexdigest()
        require(digest == item["accepted_text_sha256"], f"accepted work hash drift: {item['work_id']}")
        require(item["title"] in SHOWCASE_INDEX.read_text(encoding="utf-8"), f"showcase index omits {item['title']}")
    projected = items[:limit]
    for item in projected:
        require(item["title"] in readme, f"README omits recent showcase item: {item['title']}")
    public_assets = [SHOWCASE_INDEX, SHOWCASE_REGISTRY]
    public_assets.extend(root / item[key] for item in items for key in ("work_path", "case_path", "analysis_path"))
    for path in public_assets:
        require("/Users/" not in path.read_text(encoding="utf-8"), f"public showcase leaks local path: {path}")
        require("/tmp/" not in path.read_text(encoding="utf-8"), f"public showcase leaks temp path: {path}")


def validate_all(root: Path = ROOT) -> dict[str, object]:
    paths = {
        "readme": root / "README.md",
        "guide": root / "docs/ai-assistant-usage-reference.md",
        "current_state": root / "docs/project-current-state.md",
        "pages": root / ".github/workflows/pages.yml",
    }
    for label, path in paths.items():
        require(path.is_file(), f"missing {label} surface: {path}")
    contents = [path.read_text(encoding="utf-8") for path in paths.values()]
    validate_texts(*contents)
    validate_version_front_doors(AI_START.read_text(encoding="utf-8"), AI_HANDOFF.read_text(encoding="utf-8"), LLMS.read_text(encoding="utf-8"))
    validate_showcase(root, contents[0])
    system_map_nodes = validate_system_map(root, contents[0], contents[3])
    return {
        "status": "PASS",
        "scope": "repository_local_human_front_door_consistency_only",
        "capabilities": sorted(CAPABILITIES),
        "interactive_system_map_nodes": system_map_nodes,
        "rendered_pages_live_verified": False,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(validate_all(), ensure_ascii=False, sort_keys=True))
