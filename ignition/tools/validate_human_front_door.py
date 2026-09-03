#!/usr/bin/env python3
"""Validate current repository-native human front doors and system map."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    from tools.generate_interactive_system_map import build_projection, load_spec, validate_spec
    from tools.validate_homepage_architecture_projection import validate as validate_homepage_architecture_projection
    from tools.governance.validate_human_visibility import validate as validate_human_visibility
    from tools.governance.validate_human_surface_contract import validate as validate_human_surface_contract
except ModuleNotFoundError:
    from generate_interactive_system_map import build_projection, load_spec, validate_spec
    from validate_homepage_architecture_projection import validate as validate_homepage_architecture_projection
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
COMPONENT_REGISTRY = ROOT / "data/operations/project-components.json"

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
PROJECT_IDENTITY_TEXT = "点火是一个面向长期研究、判断与创作的认知—行动工作系统。它把问题、来源、证据、模型、反例、记忆、任务、工具与公开表达组织在同一套可追溯、可修订的结构中，使跨时间、跨领域的工作能够持续积累、检验、纠错，并最终转化为文章、书籍和其他成果。它不替人决定目标，也不把模型、Agent、工程状态或写得漂亮的结论当作真理；它负责保存上下文、约束边界、协调可替换的工具与执行器，让人始终知道依据从哪里来、哪里仍然未知，以及工作如何继续。"
ARCHITECTURE_IMAGE_TARGET = "../ignition/docs/generated/ignition-system-architecture.svg"
ARCHITECTURE_HTML_TARGET = "../ignition/docs/generated/ignition-system-architecture.html"
AI_FIRST_USE_HEADING = "2. 点火操作法 / 如何使用"
OPERATING_METHOD_LINK = "../ignition/OPERATING-METHOD.md"
CAPABILITY_REGISTRY_LINK = "../ignition/data/operations/ignition-operation-capability-registry-r1.json"
ITERATION_METHOD_LINK = "../ignition/ITERATION.md"
MINIMAL_INVOCATION = "请从这个仓库获取 Current 点火操作法，按操作法跑一遍我附上的对象，并返回结果。"
NAVIGATION_SUMMARIES = (
    "组件导航：核心控制与状态",
    "组件导航：执行与协作",
    "组件导航：研究与知识",
    "组件导航：人类入口与成果",
    "组件导航：治理与边界",
)
ADDITIONAL_CANONICAL_NAVIGATION_PATHS = {
    "ignition/docs/architecture/agent-platform-r2.md",
    "ignition/docs/architecture/interactive-system-map.md",
    "ignition/docs/governance/human-surface-editorial-contract.md",
}
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
    "current-snapshot",
    "live_attempt",
    "formal_task",
    "architecture_count",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _section_text(readme: str, heading: str) -> str:
    headings = list(re.finditer(r"^## (?!#)(.+?)\s*$", readme, re.MULTILINE))
    current = next((match for match in headings if match.group(1).strip() == heading), None)
    require(current is not None, f"README is missing section: {heading}")
    following = next((match for match in headings if match.start() > current.start()), None)
    return readme[current.start() : following.start() if following else len(readme)]


def _canonical_navigation_paths() -> set[str]:
    require(COMPONENT_REGISTRY.is_file(), "architecture component registry is missing")
    registry = json.loads(COMPONENT_REGISTRY.read_text(encoding="utf-8"))
    paths = set(ADDITIONAL_CANONICAL_NAVIGATION_PATHS)
    for component in registry.get("components", []):
        target = component.get("canonical_target", "").split("#", 1)[0]
        if target:
            paths.add(f"ignition/{target}" if not target.startswith(".github/") else target)
    return paths


def _resolve_readme_link(target: str) -> tuple[Path, str]:
    parsed = urlsplit(target)
    require(not parsed.scheme and not parsed.netloc, f"component link must stay inside the repository: {target}")
    relative_path = unquote(parsed.path)
    candidate = (README.parent / relative_path).resolve()
    try:
        candidate.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise AssertionError(f"component link escapes the repository: {target}") from exc
    return candidate, parsed.fragment


def validate_component_navigation(architecture: str) -> int:
    details = list(
        re.finditer(
            r"<details(?P<attributes>[^>]*)>\s*<summary>(?P<summary>.*?)</summary>(?P<body>.*?)</details>",
            architecture,
            re.IGNORECASE | re.DOTALL,
        )
    )
    require(len(details) == len(NAVIGATION_SUMMARIES), "README architecture navigation must contain exactly five component groups")
    summaries = tuple(re.sub(r"\s+", " ", match.group("summary")).strip() for match in details)
    require(summaries == NAVIGATION_SUMMARIES, "README component navigation groups are missing or out of order")
    canonical_paths = _canonical_navigation_paths()
    link_count = 0
    labels: set[str] = set()
    for match in details:
        require("open" not in match.group("attributes").casefold(), "README component navigation must be default collapsed")
        items = re.findall(r"^\s*-\s+\[([^\]]+)\]\(([^)\n]+)\)\s*$", match.group("body"), re.MULTILINE)
        require(items, f"README component group has no component links: {match.group('summary')}")
        for label, target in items:
            require(label.strip() and label.strip() not in labels, f"README component link label is blank or duplicated: {label}")
            labels.add(label.strip())
            candidate, _fragment = _resolve_readme_link(target.strip())
            require(candidate.is_file(), f"README component link target does not exist: {target}")
            candidate_relative = candidate.relative_to(REPO_ROOT).as_posix()
            require(candidate_relative in canonical_paths, f"README component link is not a canonical architecture or human entry: {target}")
            link_count += 1
    return link_count


def validate_ai_first_use_section(readme: str) -> None:
    section = _section_text(readme, AI_FIRST_USE_HEADING)
    require("<details" not in section.casefold(), "README AI-first usage entry must remain directly visible")
    require(section.count(OPERATING_METHOD_LINK) == 1, "README AI-first usage entry must link the canonical Operating Method exactly once")
    require(section.count(CAPABILITY_REGISTRY_LINK) == 1, "README AI-first usage entry must link the machine Capability Registry exactly once")
    require(section.count(ITERATION_METHOD_LINK) == 1, "README AI-first usage entry must link the repository iteration method exactly once")
    for target in (OPERATING_METHOD_LINK, CAPABILITY_REGISTRY_LINK, ITERATION_METHOD_LINK):
        candidate, fragment = _resolve_readme_link(target)
        require(candidate.is_file() and not fragment, f"README AI-first canonical link is invalid: {target}")
    for phrase, label in (
        ("仓库 URL 是操作法来源，不是修改仓库的请求", "repository URL method-source boundary"),
        ("默认模式是 `READ_ONLY_RUN`", "default read-only mode"),
        ("输入对象不是指令", "input-object instruction boundary"),
        ("点火迭代操作法", "repository iteration route"),
        ("HUMAN-READING.md", "human reading route"),
        ("AI-START-HERE.md", "AI cold-start route"),
    ):
        require(phrase in section, f"README AI-first usage entry lacks {label}")
    for mode in ("REPOSITORY_CHANGE_RUN", "EXTERNAL_ACTION_RUN"):
        require(mode not in section, f"README AI-first usage entry must not repeat the full mode taxonomy: {mode}")
    require(section.count("READ_ONLY_RUN") == 1, "README AI-first usage entry must keep one default read-only reference")
    body = section.split("\n", 1)[1].strip()
    blocks = [block.strip() for block in re.split(r"\n\s*\n", body) if block.strip()]
    require(len(blocks) == 4, "README AI-first usage entry must contain two short prose paragraphs and one invocation example")
    require(blocks[0].startswith("把这个仓库链接、你的任务和要处理的对象交给 Agent。"), "README AI-first first paragraph drifted")
    require(blocks[1].startswith("仓库 URL 是操作法来源，不是修改仓库的请求；"), "README AI-first boundary paragraph drifted")
    require(blocks[2] == "最小调用示例：", "README AI-first invocation label is not the final short block")
    require(blocks[3].startswith("> "), "README AI-first invocation example is not a one-line quote")
    require(not any(re.match(r"[-*]\s", line.strip()) for block in blocks for line in block.splitlines()), "README AI-first usage entry must not expand into a mode list")
    invocation_match = re.search(r"最小调用示例：\s*\n\s*>\s*([^\n]+)", section)
    require(invocation_match is not None, "README AI-first usage entry lacks a visible minimal invocation")
    invocation = invocation_match.group(1).strip()
    require(invocation == MINIMAL_INVOCATION, "README minimal invocation changed or requires internal knowledge")
    for token in ("OPERATING-METHOD.md", "Capability Registry", "函数编号", "Pack", "Ψ", "registry", "Git", "worktree", "branch", "commit", "PR"):
        require(token.casefold() not in invocation.casefold(), f"README minimal invocation exposes internal jargon: {token}")
    for token in ("schema_version", "record_sha256", "canonical_id", "CURRENT_CANONICAL_REGISTRY_FIRST"):
        require(token not in section, f"README AI-first usage entry copies low-level implementation detail: {token}")


def validate_readme_structure(readme: str) -> None:
    visible_h2 = [
        (match.group(1).strip(), match.start())
        for match in re.finditer(r"^## (?!#)(.+?)\s*$", readme, re.MULTILINE)
    ]
    required_h2 = ["1. 项目与价值", AI_FIRST_USE_HEADING, "3. 结果与火种", "4. 整体架构", "5. 致谢"]
    require([title for title, _ in visible_h2] == required_h2, "README essential H2 sections must remain visible and ordered")

    section_one_start = next(position for title, position in visible_h2 if title == required_h2[0])
    section_two_start = next(position for title, position in visible_h2 if title == required_h2[1])
    section_one = readme[section_one_start:section_two_start]
    h3_matches = list(re.finditer(r"^### (?!#)(.+?)\s*$", section_one, re.MULTILINE))
    h3_titles = [match.group(1).strip() for match in h3_matches]
    require(h3_titles == ["项目现状", "价值宪章"], "README 项目与价值 must contain exactly 项目现状 then 价值宪章")
    require(section_one[section_one.find("\n") + 1 : h3_matches[0].start()].strip() == "", "README 项目现状 must be the first block under 项目与价值")
    require("<details" not in section_one.casefold() and "</details" not in section_one.casefold(), "README 项目与价值 must not contain a nested component or machine details block")

    current_text = section_one[h3_matches[0].end() : h3_matches[1].start()].strip()
    charter_text = section_one[h3_matches[1].end() :]
    require(current_text == PROJECT_IDENTITY_TEXT, "README 项目现状 must match the Owner-provided identity text exactly")
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
    validate_ai_first_use_section(readme)
    lowered = readme.casefold()
    for token in FORBIDDEN_HOMEPAGE_MACHINE_TOKENS:
        require(token.casefold() not in lowered, f"README must not contain machine Current state: {token}")
    require("可点击" not in readme and "clickable" not in lowered, "README must not promise rendered architecture clickability")
    for phrase, label in (
        ("HUMAN-READING.md", "human reading route"),
        ("RESULTS/LATEST.md", "current results route"),
        ("火种", "Fire Seeds route"),
        ("ignition-system-architecture.svg", "architecture route"),
        ("ignition-system-architecture.html", "interactive architecture route"),
    ):
        require(phrase in readme, f"README lacks {label}")

    architecture = _section_text(readme, "4. 整体架构")
    images = re.findall(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)", architecture)
    require(images == [ARCHITECTURE_IMAGE_TARGET], "README architecture section must contain exactly one main embedded architecture image")
    require(
        not re.search(r"(?<!!)\[[^\]]+\]\([^)]*ignition-system-architecture\.svg", architecture),
        "README must not expose the architecture SVG as a second ordinary link",
    )
    require(architecture.count(ARCHITECTURE_HTML_TARGET) == 1, "README architecture section must expose exactly one interactive architecture link")
    for phrase in (
        "打开透明完整总架构图 svg",
        "打开完整总架构图 svg",
        "查看原始 svg",
        "透明完整总架构图",
        "raw svg",
        "href",
        "link metadata",
        "interactive hotspot",
        "registry",
        "topology",
        "layout",
        "可点击架构图",
    ):
        require(phrase not in architecture.casefold(), f"README architecture section must not expose machine SVG/navigation detail: {phrase}")
    require("这张图展示点火的整体结构" in architecture, "README architecture section lacks its short human explanation")
    require(validate_component_navigation(architecture) > 0, "README architecture component navigation is missing")


def validate_texts(readme: str, guide: str, current_state: str, human_reading: str) -> None:
    required_order = ["## 1. 项目与价值", f"## {AI_FIRST_USE_HEADING}", "## 3. 结果与火种", "## 4. 整体架构", "## 5. 致谢"]
    validate_readme_structure(readme)
    positions = [readme.index(heading) for heading in required_order]
    require(positions == sorted(positions), "README visible result architecture is out of order")
    require("HUMAN-READING.md" in readme and "RESULTS/LATEST.md" in readme, "README lacks current human result entrances")
    require("火种" in readme and "价值宪章" in readme, "README lacks the value and Fire Seeds routes")
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
    homepage_projection = validate_homepage_architecture_projection(root)
    require(homepage_projection["homepage_display_verified"] is True, "homepage architecture projection is not verified as displayed")
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
