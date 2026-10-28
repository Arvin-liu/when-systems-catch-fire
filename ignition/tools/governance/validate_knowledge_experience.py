#!/usr/bin/env python3
"""Fail-closed audit for the task-102 knowledge experience."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import urllib.parse
from collections import Counter, deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
CONFIG_PATH = ROOT / "data/governance/knowledge-experience/config.json"
DATA_ROOT = ROOT / "data/governance/knowledge-experience"
HUMAN_ROOT = ROOT / "KNOWLEDGE"

_PUBLIC_LOCAL_PROVENANCE_RE = re.compile(r"/Users/|/home/|/tmp/|file://|/private/var/|[A-Za-z]:[\\/]+Users[\\/]")

SPEC = importlib.util.spec_from_file_location("knowledge_builder", ROOT / "tools/governance/build_knowledge_experience.py")
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(BUILDER)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_required_aliases(aliases: list[dict], config: dict) -> None:
    lookup = {(row["alias"], row["status"], row["destination"]) for row in aliases}
    for row in config["required_historical_aliases"]:
        key = (row["alias"], row["status"], row["destination"])
        if key not in lookup:
            raise AssertionError(f"missing or rebound historical alias: {row['alias']}")
        if row["status"] == "CURRENT_SEARCH_ALIAS":
            raise AssertionError(f"historical correction alias cannot be current: {row['alias']}")


def assert_layer_coverage(results: list[dict], layers: list[dict], cards: list[dict]) -> None:
    result_ids = {row["result_id"] for row in results}
    layer_ids = {row["asset_id"] for row in layers}
    card_ids = {row["asset_id"] for row in cards if row["asset_kind"] == "RESULT_OR_ARTICLE"}
    if result_ids != layer_ids:
        raise AssertionError(f"layered reading mismatch missing={sorted(result_ids-layer_ids)[:5]} orphan={sorted(layer_ids-result_ids)[:5]}")
    if result_ids != card_ids:
        raise AssertionError(f"result card mismatch missing={sorted(result_ids-card_ids)[:5]} orphan={sorted(card_ids-result_ids)[:5]}")
    for row in layers:
        if not row["one_minute"].strip() or not row["five_minute_points"] or not row["full_reading"]:
            raise AssertionError(f"incomplete reading layers: {row['asset_id']}")


def assert_source_hashes(rows: list[dict], root: Path = ROOT) -> None:
    for row in rows:
        source = BUILDER.repo_path(row["canonical_source"])
        if not source.is_file():
            raise AssertionError(f"missing source: {row['canonical_source']}")
        if BUILDER.digest_file(row["canonical_source"]) != row["source_sha256"]:
            raise AssertionError(f"stale source projection: {row.get('asset_id') or row.get('search_id')}")


def markdown_links(path: Path) -> list[tuple[str, str | None]]:
    text = path.read_text(encoding="utf-8")
    found = []
    for raw in re.findall(r"(?<!\\)\]\(([^)]+)\)", text):
        raw = raw.strip()
        if not raw or raw.startswith(("http://", "https://", "mailto:")):
            continue
        target, _, anchor = raw.partition("#")
        found.append((urllib.parse.unquote(target), anchor or None))
    return found


def explicit_anchors(path: Path) -> set[str]:
    return set(re.findall(r"<a\s+id=[\"']([^\"']+)[\"']\s*></a>", path.read_text(encoding="utf-8")))


def resolve_link(source: Path, target: str) -> Path:
    resolved = (source.parent / target).resolve()
    try:
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise AssertionError(f"link escapes repository: {source.relative_to(REPO_ROOT)} -> {target}") from exc
    return resolved


def assert_links_and_anchors(paths: list[Path]) -> int:
    checked = 0
    for source in paths:
        text = source.read_text(encoding="utf-8")
        if "<details" in text.lower():
            raise AssertionError(f"important content hidden by details: {source.relative_to(REPO_ROOT)}")
        for target, anchor in markdown_links(source):
            if not target:
                destination = source
            else:
                destination = resolve_link(source, target)
            if not destination.exists():
                raise AssertionError(f"broken link: {source.relative_to(REPO_ROOT)} -> {target}")
            if anchor:
                if destination.suffix != ".md" or anchor not in explicit_anchors(destination):
                    raise AssertionError(f"broken explicit anchor: {source.relative_to(REPO_ROOT)} -> {target}#{anchor}")
            checked += 1
    return checked


def reachable_within_two_clicks() -> set[str]:
    start = REPO_ROOT / ".github/README.md"
    reached: set[Path] = {start.resolve()}
    queue = deque([(start, 0)])
    while queue:
        current, depth = queue.popleft()
        if depth == 2:
            continue
        for target, _ in markdown_links(current):
            if not target:
                continue
            resolved = resolve_link(current, target)
            if not resolved.is_file() or resolved.suffix not in {".md", ".txt"}:
                continue
            if resolved.resolve() not in reached:
                reached.add(resolved.resolve())
                queue.append((resolved, depth + 1))
    return {
        (path.relative_to(ROOT.resolve()).as_posix() if path.is_relative_to(ROOT.resolve()) else path.relative_to(REPO_ROOT.resolve()).as_posix())
        for path in reached
    }


def validate() -> dict:
    errors: list[str] = []
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    results = BUILDER.knowledge_result_rows(config)
    cards = read_jsonl(DATA_ROOT / "asset-cards.jsonl")
    changes = read_jsonl(DATA_ROOT / "changes.jsonl")
    layers = read_jsonl(DATA_ROOT / "layered-reading.jsonl")
    search = read_jsonl(DATA_ROOT / "search-index.jsonl")
    aliases = read_jsonl(DATA_ROOT / "alias-index.jsonl")
    coverage = json.loads((DATA_ROOT / "coverage.json").read_text(encoding="utf-8"))
    manifest = json.loads((DATA_ROOT / "manifest.json").read_text(encoding="utf-8"))

    try:
        assert_required_aliases(aliases, config)
        assert_layer_coverage(results, layers, cards)
        assert_source_hashes(cards)
        assert_source_hashes(layers)
    except AssertionError as exc:
        errors.append(str(exc))

    ids = [row["asset_id"] for row in cards]
    if len(ids) != len(set(ids)):
        errors.append("duplicate asset card id")
    search_ids = [row["search_id"] for row in search]
    if len(search_ids) != len(set(search_ids)):
        errors.append("duplicate search id")
    search_kinds = Counter(row["asset_kind"] for row in search)
    expected_kinds = {
        "RESULT_OR_ARTICLE": len(results),
        "FUNCTION_ASSET": len(read_jsonl(ROOT / "data/foundation/function-assets/identity-cards.jsonl")),
        "NONFUNCTION_CLAIM": len(read_jsonl(ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl")),
    }
    if dict(search_kinds) != expected_kinds:
        errors.append(f"full search coverage mismatch: {dict(search_kinds)} != {expected_kinds}")

    card_ids = set(ids)
    for row in cards:
        match = next((item for item in search if item["search_id"] == row["asset_id"]), None)
        if not match or match["destination"] != f"KNOWLEDGE/ASSET-CARDS.md#{row['human_anchor']}":
            errors.append(f"orphan asset card: {row['asset_id']}")
    for function_id in config["featured_function_ids"]:
        if function_id not in card_ids:
            errors.append(f"missing featured function card: {function_id}")

    declared = {row["change_id"] for row in changes}
    for row in config["declared_changes"]:
        if row["change_id"] not in declared:
            errors.append(f"missing declared What's New record: {row['change_id']}")
        for source in row["sources"]:
            if not BUILDER.repo_path(source).is_file():
                errors.append(f"unbacked declared change source: {source}")

    if coverage["result_sources"] != len(results) or coverage["layered_reading_records"] != len(layers) or coverage["search_records"] != len(search):
        errors.append("coverage counts are stale")
    if coverage["historical_result_audit"]["SOURCE_MISSING"] != 0:
        errors.append("historical source audit is not closed")

    for path, expected in manifest["source_inputs"].items():
        if not (ROOT / path).is_file() or sha(ROOT / path) != expected:
            errors.append(f"manifest source drift: {path}")
    for path, expected in manifest["generated_outputs"].items():
        if not (ROOT / path).is_file() or sha(ROOT / path) != expected:
            errors.append(f"manifest output drift: {path}")
    for pair in manifest["machine_human_pairs"]:
        if not (ROOT / pair["machine"]).is_file() or not (ROOT / pair["human"]).is_file():
            errors.append(f"broken machine-human pair: {pair}")

    human_paths = sorted(HUMAN_ROOT.rglob("*.md"))
    try:
        link_count = assert_links_and_anchors(human_paths)
    except AssertionError as exc:
        errors.append(str(exc))
        link_count = 0
    oversized = [path.relative_to(ROOT).as_posix() for path in human_paths if path.stat().st_size >= 500_000]
    if oversized:
        errors.append("human Markdown exceeds 500KB render budget: " + ", ".join(oversized))
    anchors = explicit_anchors(HUMAN_ROOT / "ASSET-CARDS.md")
    if {row["human_anchor"] for row in cards} - anchors:
        errors.append("asset-card anchors are incomplete")
    shard_anchors = set().union(*(explicit_anchors(path) for path in sorted((HUMAN_ROOT / "cards").glob("part-*.md"))))
    if {row["human_anchor"] for row in cards} - shard_anchors:
        errors.append("asset-card shard anchors are incomplete")
    if {row["human_anchor"] for row in layers} - explicit_anchors(HUMAN_ROOT / "READING-LAYERS.md"):
        errors.append("reading-layer anchors are incomplete")
    layer_shard_anchors = set().union(*(explicit_anchors(path) for path in sorted((HUMAN_ROOT / "reading-layers").glob("part-*.md"))))
    if {row["human_anchor"] for row in layers} - layer_shard_anchors:
        errors.append("reading-layer shard anchors are incomplete")
    if {row["human_anchor"] for row in changes} - explicit_anchors(HUMAN_ROOT / "WHATS-NEW.md"):
        errors.append("What's New anchors are incomplete")

    reached = reachable_within_two_clicks()
    missing_two_click = sorted(set(config["canonical_human_pages"]) - reached)
    if missing_two_click:
        errors.append("knowledge pages not reachable within two README clicks: " + ", ".join(missing_two_click))

    if (ROOT / "pages").exists() or (ROOT / ".github/workflows/pages.yml").exists():
        errors.append("retired Pages surface returned")
    if any("<details" in (ROOT / path).read_text(encoding="utf-8").lower() for path in config["canonical_human_pages"]):
        errors.append("important knowledge content is hidden")

    expected_products = BUILDER.output_map(BUILDER.build(config), config)
    privacy_leaks = [
        path.relative_to(ROOT).as_posix()
        for path, content in expected_products.items()
        if _PUBLIC_LOCAL_PROVENANCE_RE.search(content)
    ]
    if privacy_leaks:
        errors.append("public knowledge projection contains local/private provenance: " + ", ".join(privacy_leaks))
    drift = [path.relative_to(ROOT).as_posix() for path, content in expected_products.items() if not path.is_file() or path.read_text(encoding="utf-8") != content]
    if drift:
        errors.append("deterministic output drift: " + ", ".join(drift))

    if errors:
        raise AssertionError("\n".join(errors))
    return {"cards": len(cards), "changes": len(changes), "layers": len(layers), "search": len(search), "aliases": len(aliases), "links": link_count, "two_click_pages": len(config["canonical_human_pages"])}


def main() -> int:
    result = validate()
    print("KNOWLEDGE_EXPERIENCE_AUDIT_OK " + " ".join(f"{key}={value}" for key, value in result.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
