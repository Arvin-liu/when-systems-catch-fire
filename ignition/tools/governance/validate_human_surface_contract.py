#!/usr/bin/env python3
"""Validate the structural contract shared by every current Human Surface.

This validator checks routing, provenance fields, machine/human separation,
and the presence of the 之元写作法 sections. It intentionally does not judge
literary quality, truth, causality, proof, or external novelty.
"""
from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/governance/human-surface-editorial-contract.md"
MATERIALITY = ROOT / "data/governance/human-surface/materiality-manifest.json"
FUNCTION_REGISTRY = ROOT / "data/foundation/function-assets/census.jsonl"
NONFUNCTION_REGISTRY = ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl"
MIGRATION = ROOT / "data/foundation/migrations/legacy-table-migration.jsonl"
SYSTEM_MAP = ROOT / "data/architecture/interactive-system-map.json"
SYSTEM_MAP_SVG = ROOT / "docs/generated/ignition-system-architecture.svg"
COMPONENTS = ROOT / "data/operations/project-components.json"

HUMAN_ROOTS = [ROOT / "docs/human/function-assets", ROOT / "docs/human/nonfunction-assets"]
REQUIRED_SECTIONS = ("它在说什么", "为什么值得看", "可以怎么用", "不能从这里推出什么", "还缺什么")
RAW_ENUMS = (
    "UNSPECIFIED_IN_SOURCE",
    "NOT_STATED_OR_NOT_APPLICABLE",
    "QUARANTINED_AMBIGUOUS",
    "REQUIRES_HUMAN_REVIEW",
)
CURRENT_SURFACES = (
    ROOT.parent / ".github/README.md",
    ROOT / "SUMMARY.md",
    ROOT / "HUMAN-READING.md",
    ROOT / "AI-START-HERE.md",
    ROOT / "AI-HANDOFF.md",
    ROOT / "llms.txt",
    ROOT / "STATE-CHANGELOG.md",
    ROOT / "docs/project-current-state.md",
    ROOT / "KNOWLEDGE/README.md",
    ROOT / "KNOWLEDGE/MAP.md",
    ROOT / "KNOWLEDGE/READING-LAYERS.md",
    ROOT / "KNOWLEDGE/SEARCH.md",
    ROOT / "KNOWLEDGE/WHATS-NEW.md",
    ROOT / "RESULTS/LATEST.md",
    ROOT / "RESULTS/RESEARCH-AND-ARTICLES.md",
    ROOT / "PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md",
)
RETIRED_ROUTE_TOKENS = (
    "统一函数总表/",
    "统一案例总表/",
    "docs/human/nonfunction-claims/",
    "函数资产人类浏览器",
    "非函数断言人类浏览器",
    "ignition-overall-architecture.svg",
    "ignition-system-map.svg",
)
CURRENT_SNAPSHOT_BLOCK = re.compile(
    r"<!-- CURRENT-SNAPSHOT:BEGIN profile=(?:human|ai|machine) schema=current-snapshot-r1 -->\n"
    r".*?<!-- CURRENT-SNAPSHOT:END -->\n?",
    re.DOTALL,
)


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def source_hash(path: str, migration_rows: dict[str, dict]) -> str | None:
    candidate = ROOT / path
    if candidate.is_file():
        # The compiler-owned Current Snapshot is a derived projection, not
        # source prose for a Human Surface claim. Exclude it symmetrically
        # with build_claim_browsers.py so projection refreshes do not create
        # false source-hash drift.
        text = candidate.read_text(encoding="utf-8")
        normalized = CURRENT_SNAPSHOT_BLOCK.sub("", text).encode("utf-8")
        return hashlib.sha256(normalized).hexdigest()
    if path in migration_rows:
        return migration_rows[path].get("content_sha256")
    return None


def validate() -> dict[str, int]:
    errors: list[str] = []
    require = lambda condition, message: errors.append(message) if not condition else None

    require(CONTRACT.is_file(), "Human Surface editorial contract is missing")
    contract = CONTRACT.read_text(encoding="utf-8") if CONTRACT.is_file() else ""
    for phrase in ("之元写作法 0.5.0", "不判断文学质量", "枚举、ID、M/E 和 registry 字段不能直接充当段落", "所有 Human Surface"):
        require(phrase in contract, f"editorial contract lacks required rule: {phrase}")
    for phrase in ("它是什么、为什么出现", "它可以做什么", "它不能推出什么", "还缺什么、下一步是什么", "如何回到精确记录"):
        require(phrase in contract, f"editorial contract lacks mandatory reading answer: {phrase}")

    for root, title in zip(HUMAN_ROOTS, ("函数资产", "非函数资产")):
        readme = root / "README.md"
        require(readme.is_file(), f"human asset README is missing: {readme}")
        if readme.is_file():
            text = readme.read_text(encoding="utf-8")
            require(text.startswith(f"# {title}\n"), f"human asset title is not plain-language: {readme}")
        for path in root.rglob("*") if root.exists() else ():
            if path.is_file():
                relative = path.relative_to(root).as_posix().lower()
                require("browser" not in relative and "浏览器" not in path.name, f"browser-style human route remains: {path}")
                require(not re.search(r"(?:^|/)page-\d+\.md$", relative), f"pagination IA remains in human assets: {path}")
                if path.suffix.lower() == ".md":
                    text = path.read_text(encoding="utf-8")
                    require("browser" not in text.lower() and "浏览器" not in text, f"browser wording remains in human asset: {path}")

    require(MATERIALITY.is_file(), "materiality manifest is missing")
    manifest = json.loads(MATERIALITY.read_text(encoding="utf-8")) if MATERIALITY.is_file() else {}
    require(manifest.get("writing_method") == "之元写作法 0.5.0", "materiality manifest is not bound to 之元写作法 0.5.0")
    require(manifest.get("counts", {}).get("function_human", 0) <= 24, "function human surface exceeds the materiality cap")
    require(manifest.get("counts", {}).get("nonfunction_human", 0) <= 24, "nonfunction human surface exceeds the materiality cap")
    functions = {row.get("stable_id"): row for row in read_jsonl(FUNCTION_REGISTRY)} if FUNCTION_REGISTRY.is_file() else {}
    claims = {row.get("canonical_id"): row for row in read_jsonl(NONFUNCTION_REGISTRY)} if NONFUNCTION_REGISTRY.is_file() else {}
    migration_rows = {row.get("legacy_path"): row for row in read_jsonl(MIGRATION)} if MIGRATION.is_file() else {}
    entries = manifest.get("entries", [])
    for entry in entries:
        human_path = ROOT / entry.get("human_path", "")
        require(human_path.is_file(), f"materiality human entry is missing: {entry.get('human_path')}")
        identifier = entry.get("machine_id")
        registry = functions if entry.get("asset_kind") == "FUNCTION_ASSET" else claims
        row = registry.get(identifier)
        require(row is not None, f"materiality entry has no machine record: {identifier}")
        if row is not None:
            require(entry.get("machine_record_sha256") == sha256_text(canonical(row)), f"machine record hash drift: {identifier}")
        path_text = human_path.read_text(encoding="utf-8") if human_path.is_file() else ""
        for section in REQUIRED_SECTIONS:
            require(f"## {section}" in path_text, f"human entry lacks section {section}: {human_path}")
        for field in ("机器 ID", "机器记录指纹", "来源指纹", "技术记录", "之元写作法 0.5.0"):
            require(field in path_text, f"human entry lacks {field}: {human_path}")
        for raw_enum in RAW_ENUMS:
            require(raw_enum not in path_text.split("## 技术记录", 1)[0], f"raw enum leaked into human prose: {human_path}: {raw_enum}")
        for line in path_text.splitlines():
            if re.match(r"^\s*[\[{](?:\s*[\"{\[])\s*", line):
                errors.append(f"raw JSON-like line leaked into human entry: {human_path}")
                break
        declared_source = entry.get("source_path", "")
        declared_hash = entry.get("source_sha256", "")
        expected_source_hash = source_hash(declared_source, migration_rows)
        require(bool(declared_source and declared_hash), f"human entry lacks source fingerprint: {human_path}")
        if expected_source_hash is not None and not declared_hash.startswith("UNAVAILABLE_"):
            require(declared_hash == expected_source_hash, f"source hash drift: {human_path}")

    require(SYSTEM_MAP.is_file() and SYSTEM_MAP_SVG.is_file(), "single complete architecture graph is missing")
    old_graphs = [ROOT / "docs/generated/ignition-overall-architecture.svg", ROOT / "docs/generated/ignition-system-map.svg"]
    for path in old_graphs:
        require(not path.exists(), f"retired architecture graph remains: {path}")
    generated_dir = ROOT / "docs/generated"
    if generated_dir.exists():
        require(not any(path.is_file() and path.suffix.lower() == ".png" for path in generated_dir.iterdir()), "PNG architecture projection remains")
    spec = json.loads(SYSTEM_MAP.read_text(encoding="utf-8")) if SYSTEM_MAP.is_file() else {}
    components = json.loads(COMPONENTS.read_text(encoding="utf-8")) if COMPONENTS.is_file() else {"components": []}
    component_rows = {row["component_id"]: row for row in components.get("components", [])}
    visible = {key for key, row in component_rows.items() if row.get("map_projection", {}).get("visible")}
    node_ids = {row.get("id") for row in spec.get("nodes", [])}
    require(node_ids == visible, f"architecture graph does not cover visible registry components: missing={sorted(visible-node_ids)} extra={sorted(node_ids-visible)}")
    hidden = {key: row for key, row in component_rows.items() if not row.get("map_projection", {}).get("visible")}
    for key, row in hidden.items():
        representative = row.get("map_projection", {}).get("represented_by")
        require(representative in visible, f"hidden component lacks visible representative: {key}")
    require(len(spec.get("nodes", [])) == len(node_ids), "architecture graph contains duplicate or missing node IDs")
    require(spec.get("projection_status") == "CURRENT_DERIVED_PROJECTION", "architecture graph is not a derived current projection")
    require(len(spec.get("edges", [])) > 0 and all(edge.get("relation_domain") for edge in spec.get("edges", [])), "architecture graph lacks typed relation edges")
    try:
        svg_root = ET.fromstring(SYSTEM_MAP_SVG.read_bytes())
        links = svg_root.findall(".//{http://www.w3.org/2000/svg}a")
        require(len(links) == len(node_ids), "architecture graph does not make every node clickable")
    except (ET.ParseError, OSError) as exc:
        errors.append(f"architecture SVG cannot be parsed: {exc}")

    for path in CURRENT_SURFACES:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for token in RETIRED_ROUTE_TOKENS:
            require(token not in text, f"retired current route remains in {path}: {token}")

    if errors:
        raise AssertionError("\n".join(errors))
    return {"human_entries": len(entries), "machine_components": len(component_rows), "visible_graph_nodes": len(node_ids), "typed_graph_edges": len(spec.get("edges", []))}


def main() -> int:
    result = validate()
    print("HUMAN_SURFACE_CONTRACT_OK " + " ".join(f"{key}={value}" for key, value in result.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
