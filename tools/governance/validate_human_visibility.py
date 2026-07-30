#!/usr/bin/env python3
"""Fail closed when current machine knowledge lacks a readable repository surface."""

from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / "data/governance/human-results/config.json").read_text(encoding="utf-8"))
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
]
CRITICAL_DESTINATIONS = {
    "RESULTS/LATEST.md",
    "RESULTS/CORRECTIONS.md",
    "RESULTS/OPEN-QUESTIONS.md",
    "RESULTS/ADJUDICATION-SUMMARY.md",
    "RESULTS/RESEARCH-AND-ARTICLES.md",
    "RESULTS/CHRONOLOGY.md",
    "KNOWLEDGE/README.md",
    "KNOWLEDGE/WHATS-NEW.md",
    "KNOWLEDGE/MAP.md",
    "KNOWLEDGE/ASSET-CARDS.md",
    "KNOWLEDGE/READING-LAYERS.md",
    "KNOWLEDGE/SEARCH.md",
    "KNOWLEDGE/EVOLUTION.md",
    "KNOWLEDGE/COVERAGE.md",
    "data/foundation/function-assets/closure-summary.json",
    "data/foundation/nonfunction-claims/closure-summary.json",
}


def local_links(path: str) -> set[str]:
    text = (ROOT / path).read_text(encoding="utf-8")
    links = set()
    for raw in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
        target = raw.strip().split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = urllib.parse.unquote(target)
        resolved = ((ROOT / path).parent / target).resolve()
        try:
            links.add(resolved.relative_to(ROOT.resolve()).as_posix())
        except ValueError as exc:
            raise AssertionError(f"link escapes repository: {path} -> {raw}") from exc
    return links


def validate() -> dict:
    errors: list[str] = []
    for path in CORE:
        if not (ROOT / path).is_file():
            errors.append(f"missing human surface: {path}")
    if errors:
        raise AssertionError("\n".join(errors))

    for path in CORE + ["docs/project-current-state.md", "SUMMARY.md"]:
        text = (ROOT / path).read_text(encoding="utf-8")
        if "<details" in text.lower():
            errors.append(f"essential content is hidden by details: {path}")
        for target in local_links(path):
            if not (ROOT / target).exists():
                errors.append(f"broken local link: {path} -> {target}")

    if (ROOT / "pages").exists() or (ROOT / ".github/workflows/pages.yml").exists():
        errors.append("retired Pages product files still exist")

    current_scope = CORE + [
        "docs/project-current-state.md",
        "SUMMARY.md",
        "ITERATION.md",
        "AI-START-HERE.md",
        "AI-HANDOFF.md",
        "llms.txt",
        "docs/architecture/interactive-system-map.md",
        "docs/operations/stage-snapshot-publication.md",
        "data/operations/synchronization-surfaces.json",
        "data/operations/project-components.json",
        "data/operations/change-propagation-topology.json",
        ".github/workflows/foundation-validation.yml",
    ]
    forbidden = (
        "arvin-liu.github.io/when-systems-catch-fire",
        ".github/workflows/pages.yml",
        "pages/system-map.html",
        "pages/generated/ignition-system-map.svg",
        "human.pages_source",
        "external.pages_homepage",
        "pages_pipeline",
    )
    for path in current_scope:
        text = (ROOT / path).read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                errors.append(f"retired Pages reference remains in current surface: {path}: {token}")

    readme_links = local_links("README.md")
    second_hop = set(readme_links)
    for path in sorted(readme_links):
        if (ROOT / path).is_file() and (ROOT / path).suffix in {".md", ".txt"}:
            second_hop.update(local_links(path))
    missing_reachability = sorted(CRITICAL_DESTINATIONS - second_hop)
    if missing_reachability:
        errors.append("not reachable within two README clicks: " + ", ".join(missing_reachability))

    for pair in CONFIG["machine_human_pairs"]:
        if not (ROOT / pair["machine"]).is_file():
            errors.append(f"missing machine result: {pair['machine']}")
        if not (ROOT / pair["human"]).is_file():
            errors.append(f"missing human counterpart: {pair['human']}")

    census = json.loads((ROOT / "data/governance/human-results/census.json").read_text(encoding="utf-8"))
    ledger_count = sum(1 for line in (ROOT / "data/governance/human-results/result-ledger.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
    if census["source_documents"] != ledger_count or not census["all_sources_have_human_record"]:
        errors.append("human result census and ledger disagree")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ("当前结论", "已完成的纠正", "仍然开放的问题", "研究、复算与文章结果", "函数与断言裁决结果", "持续自我纠错"):
        if f"## {heading}" not in readme:
            errors.append(f"README lacks visible section: {heading}")
    current_state = (ROOT / "docs/project-current-state.md").read_text(encoding="utf-8")
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
