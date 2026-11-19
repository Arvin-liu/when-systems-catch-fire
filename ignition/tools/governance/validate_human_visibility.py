#!/usr/bin/env python3
"""Fail closed when current machine knowledge lacks a readable repository surface."""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT if (ROOT / ".github/README.md").is_file() else ROOT.parent
CONFIG = json.loads((ROOT / "data/governance/human-results/config.json").read_text(encoding="utf-8"))
PROJECT_COMPONENTS = ROOT / "data/operations/project-components.json"
REQUIRED_VISIBLE_H2_SECTIONS = ("如何使用", "结果与火种", "整体架构", "致谢")
CORE = [
    "README.md",
    "HUMAN-READING.md",
    "KNOWLEDGE/README.md",
    "KNOWLEDGE/WHATS-NEW.md",
    "KNOWLEDGE/MAP.md",
    "KNOWLEDGE/ASSET-CARDS.md",
    "KNOWLEDGE/READING-LAYERS.md",
    "KNOWLEDGE/SEARCH.md",
    "KNOWLEDGE/EVOLUTION.md",
    "KNOWLEDGE/COVERAGE.md",
    "RESULTS/README.md",
    "RESULTS/LATEST.md",
    "RESULTS/CORRECTIONS.md",
    "RESULTS/OPEN-QUESTIONS.md",
    "RESULTS/ADJUDICATION-SUMMARY.md",
    "RESULTS/RESEARCH-AND-ARTICLES.md",
    "RESULTS/CHRONOLOGY.md",
    "RESULTS/CLAIM-DELTA.md",
    "RESULTS/IMPACT-ANALYSIS.md",
    "RESULTS/EVIDENCE-LINEAGE.md",
    "RESULTS/SELF-CORRECTION-AUDIT.md",
    "PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md",
    "docs/human/function-assets/README.md",
    "docs/human/nonfunction-assets/README.md",
    "docs/governance/human-surface-editorial-contract.md",
]
CRITICAL_DESTINATIONS = {
    "ignition/RESULTS/LATEST.md",
    "ignition/RESULTS/CORRECTIONS.md",
    "ignition/RESULTS/OPEN-QUESTIONS.md",
    "ignition/RESULTS/ADJUDICATION-SUMMARY.md",
    "ignition/RESULTS/RESEARCH-AND-ARTICLES.md",
    "ignition/RESULTS/CHRONOLOGY.md",
    "ignition/KNOWLEDGE/README.md",
    "ignition/KNOWLEDGE/WHATS-NEW.md",
    "ignition/KNOWLEDGE/MAP.md",
    "ignition/KNOWLEDGE/ASSET-CARDS.md",
    "ignition/KNOWLEDGE/READING-LAYERS.md",
    "ignition/KNOWLEDGE/SEARCH.md",
    "ignition/KNOWLEDGE/EVOLUTION.md",
    "ignition/KNOWLEDGE/COVERAGE.md",
    "ignition/data/foundation/function-assets/closure-summary.json",
    "ignition/data/foundation/nonfunction-claims/closure-summary.json",
    "ignition/PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md",
    "ignition/docs/human/function-assets/README.md",
    "ignition/docs/human/nonfunction-assets/README.md",
    "ignition/docs/governance/human-surface-editorial-contract.md",
}


def file_for(path: str) -> Path:
    if path == "README.md":
        return REPO_ROOT / ".github/README.md"
    if path == "LICENSE" or path.startswith(".github/"):
        return REPO_ROOT / path
    if path.startswith("ignition/"):
        return REPO_ROOT / path
    return ROOT / path


def local_links(path: str) -> set[str]:
    source = file_for(path)
    text = source.read_text(encoding="utf-8")
    links = set()
    for raw in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
        target = raw.strip().split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = urllib.parse.unquote(target)
        resolved = (source.parent / target).resolve()
        try:
            links.add(resolved.relative_to(REPO_ROOT.resolve()).as_posix())
        except ValueError as exc:
            raise AssertionError(f"link escapes repository: {path} -> {raw}") from exc
    return links


def markdown_heading_anchors(markdown: str) -> set[str]:
    anchors: set[str] = set()
    used: set[str] = set()
    fence: str | None = None
    for line in markdown.splitlines():
        stripped = line.lstrip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith(("```", "~~~")):
            fence = stripped[:3]
            continue
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        base = urllib.parse.unquote(match.group(1)).strip().lower()
        base = re.sub(r"[^\w\- ]", "", base, flags=re.UNICODE)
        base = re.sub(r"\s+", "-", base).strip("-")
        candidate = base
        suffix = 0
        while candidate in used:
            suffix += 1
            candidate = f"{base}-{suffix}"
        used.add(candidate)
        anchors.add(candidate)
    return anchors


def markdown_anchor_exists(markdown: str, fragment: str) -> bool:
    anchor = urllib.parse.unquote(fragment).strip().lower()
    anchor = re.sub(r"[^\w\- ]", "", anchor, flags=re.UNICODE)
    anchor = re.sub(r"\s+", "-", anchor).strip("-")
    return bool(anchor) and anchor in markdown_heading_anchors(markdown)


def validate_visible_readme_sections(readme: str) -> None:
    visible_h2 = [
        match.group(1).strip()
        for match in re.finditer(r"^## (?!#)(.+?)\s*$", readme, re.MULTILINE)
    ]
    missing = [
        section for section in REQUIRED_VISIBLE_H2_SECTIONS
        if not any(section in heading for heading in visible_h2)
    ]
    if missing:
        raise AssertionError("README lacks visible section(s): " + ", ".join(missing))


def project_component_anchor_errors() -> list[str]:
    registry = json.loads(PROJECT_COMPONENTS.read_text(encoding="utf-8"))
    errors: list[str] = []
    for component in registry["components"]:
        target = component.get("canonical_target", "")
        path, separator, fragment = target.partition("#")
        if not separator:
            continue
        source = file_for(path)
        if not source.is_file():
            errors.append(f"mapped anchor source is missing: {component['component_id']} -> {target}")
            continue
        markdown = source.read_text(encoding="utf-8")
        if not markdown_anchor_exists(markdown, fragment):
            errors.append(f"mapped anchor does not exist: {component['component_id']} -> {target}")
    return errors


def validate() -> dict:
    errors: list[str] = []
    for path in CORE:
        if not file_for(path).is_file():
            errors.append(f"missing human surface: {path}")
    if errors:
        raise AssertionError("\n".join(errors))

    for path in CORE + ["docs/project-current-state.md", "SUMMARY.md"]:
        text = file_for(path).read_text(encoding="utf-8")
        if path == "README.md":
            try:
                from tools.validate_human_front_door import validate_readme_structure
            except ModuleNotFoundError:
                tools_path = str(ROOT / "tools")
                if tools_path not in sys.path:
                    sys.path.insert(0, tools_path)
                from validate_human_front_door import validate_readme_structure
            try:
                validate_readme_structure(text)
            except AssertionError as exc:
                errors.append(f"README front-door structure invalid: {exc}")
        elif "<details" in text.lower():
            errors.append(f"essential content is hidden by details: {path}")
        for target in local_links(path):
            if not file_for(target).exists():
                errors.append(f"broken local link: {path} -> {target}")

    if (REPO_ROOT / "pages").exists() or (REPO_ROOT / ".github/workflows/pages.yml").exists():
        errors.append("retired Pages product files still exist")

    current_scope = CORE + [
        "docs/project-current-state.md",
        "SUMMARY.md",
        "ITERATION.md",
        "AI-START-HERE.md",
        "AI-HANDOFF.md",
        "llms.txt",
        "docs/architecture/interactive-system-map.md",
        "docs/governance/human-surface-editorial-contract.md",
        "docs/operations/stage-snapshot-publication.md",
        "data/operations/synchronization-surfaces.json",
        "data/operations/project-components.json",
        "data/operations/change-propagation-topology.json",
        ".github/workflows/foundation-validation.yml",
    ]
    forbidden = (
        "arvin-liu.github.io/when-systems-catch-fire/system-map.html",
        "arvin-liu.github.io/when-systems-catch-fire/generated/",
        ".github/workflows/pages.yml",
        "pages/system-map.html",
        "pages/generated/ignition-system-map.svg",
        "docs/generated/ignition-overall-architecture.svg",
        "docs/generated/ignition-system-map.svg",
        "human.pages_source",
        "external.pages_homepage",
        "pages_pipeline",
    )
    for path in current_scope:
        text = file_for(path).read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                errors.append(f"retired Pages reference remains in current surface: {path}: {token}")

    readme_links = local_links("README.md")
    second_hop = set(readme_links)
    for path in sorted(readme_links):
        if file_for(path).is_file() and file_for(path).suffix in {".md", ".txt"}:
            second_hop.update(local_links(path))
    missing_reachability = sorted(CRITICAL_DESTINATIONS - second_hop)
    if missing_reachability:
        errors.append("not reachable within two README clicks: " + ", ".join(missing_reachability))

    for pair in CONFIG["machine_human_pairs"]:
        if not file_for(pair["machine"]).is_file():
            errors.append(f"missing machine result: {pair['machine']}")
        if not file_for(pair["human"]).is_file():
            errors.append(f"missing human counterpart: {pair['human']}")

    census = json.loads((ROOT / "data/governance/human-results/census.json").read_text(encoding="utf-8"))
    ledger_count = sum(1 for line in (ROOT / "data/governance/human-results/result-ledger.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
    if census["source_documents"] != ledger_count or not census["all_sources_have_human_record"]:
        errors.append("human result census and ledger disagree")

    readme = file_for("README.md").read_text(encoding="utf-8")
    try:
        validate_visible_readme_sections(readme)
    except AssertionError as exc:
        errors.append(str(exc))
    errors.extend(project_component_anchor_errors())
    current_state = file_for("docs/project-current-state.md").read_text(encoding="utf-8")
    if "任务 101" not in current_state or "任务 102" not in current_state:
        errors.append("project current state does not preserve task 101 and task 102 state")
    if errors:
        raise AssertionError("\n".join(errors))
    return {"human_surfaces": len(CORE), "machine_human_pairs": len(CONFIG["machine_human_pairs"]), "two_click_destinations": len(CRITICAL_DESTINATIONS)}


def main() -> int:
    result = validate()
    print("HUMAN_VISIBILITY_OK " + " ".join(f"{key}={value}" for key, value in result.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
