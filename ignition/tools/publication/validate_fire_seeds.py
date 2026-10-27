#!/usr/bin/env python3
"""Validate the human and machine Fire Seeds publication layer.

The validator checks closure, provenance paths, source dispositions and
epistemic wording. It does not judge the truth of a seed.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
HUMAN = ROOT / "PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md"
CENSUS = ROOT / "data/publication/fire-seeds/seed-census.json"
LOG = ROOT / "data/publication/fire-seeds/CHANGELOG.jsonl"
LAYERED = ROOT / "data/governance/knowledge-experience/layered-reading.jsonl"
MIGRATION = ROOT / "data/foundation/migrations/legacy-table-migration.jsonl"
HEADING_RE = re.compile(r"^## ((?:CF|FS)-\d+) (.+)$", re.MULTILINE)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
DISPOSITIONS = {
    "SEED_CREATED",
    "MERGED_INTO_SEED",
    "NO_SEED_DELTA",
    "EXCLUDED_NONCONTENT",
}


def _resolve_link(target: str) -> Path | None:
    target = unquote(target.split("#", 1)[0].strip())
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None
    resolved = (HUMAN.parent / target).resolve()
    try:
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError:
        return Path("__OUTSIDE_REPOSITORY__")
    return resolved


def _blocks(text: str) -> list[tuple[str, str, str]]:
    matches = list(HEADING_RE.finditer(text))
    output = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        output.append((match.group(1), match.group(2).strip(), text[match.end() : end]))
    return output


def validate() -> dict[str, int]:
    errors: list[str] = []
    if not HUMAN.is_file():
        errors.append(f"missing human Fire Seeds asset: {HUMAN}")
        raise AssertionError("\n".join(errors))
    if not CENSUS.is_file():
        errors.append(f"missing machine Fire Seeds census: {CENSUS}")
        raise AssertionError("\n".join(errors))
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    migration = {
        row["legacy_path"]: row["content_sha256"]
        for row in (json.loads(line) for line in MIGRATION.read_text(encoding="utf-8").splitlines() if line.strip())
        if row.get("legacy_path") and row.get("content_sha256")
    } if MIGRATION.is_file() else {}
    text = HUMAN.read_text(encoding="utf-8")
    blocks = _blocks(text)
    ids = [item[0] for item in blocks]
    content_blocks = [item for item in blocks if item[0].startswith("CF-")]
    method_blocks = [item for item in blocks if item[0].startswith("FS-")]
    if not content_blocks:
        errors.append("human Fire Seeds page has no content seeds")
    if len(method_blocks) < 20:
        errors.append(f"methodology Fire Seeds unexpectedly short: {len(method_blocks)}")
    if len(ids) != len(set(ids)):
        errors.append("duplicate Fire Seeds entry IDs")
    for seed_id, title, block in blocks:
        body = block
        for marker in ("**为什么值得追：**", "**当前边界：**", "**继续追：**", "**边界：**", "**继续阅读：**"):
            body = body.split(marker, 1)[0]
        if len(body.strip()) < 80:
            errors.append(f"{seed_id} lacks a sufficiently developed human body")
        if seed_id.startswith("CF-"):
            required = ("**为什么值得追：**", "**当前边界：**", "**继续追：**")
        else:
            required = ("**边界：**", "**继续阅读：**")
        for marker in required:
            if marker not in block:
                errors.append(f"{seed_id} lacks {marker}")
        if re.search(r"(原创发现|人类首次|首次发现)", block):
            errors.append(f"{seed_id} contains unbounded external novelty wording")
        for target in LINK_RE.findall(block):
            resolved = _resolve_link(target)
            if resolved is None:
                continue
            if str(resolved) == "__OUTSIDE_REPOSITORY__" or not resolved.exists():
                errors.append(f"{seed_id} has broken or escaping link: {target}")

    seeds = census.get("seeds", [])
    clusters = census.get("clusters", [])
    if census.get("candidate_count") != len(blocks):
        errors.append("census candidate_count does not match human entry count")
    if census.get("cluster_count") != len(clusters) or len(clusters) != len(blocks):
        errors.append("census cluster count does not match human entry count")
    if census.get("seed_count") != len(seeds) or len(seeds) != len(blocks):
        errors.append("census seed registry does not match human entry count")
    if census.get("content_seed_count") != len(content_blocks):
        errors.append("census content seed count does not match human content count")
    if census.get("methodology_seed_count") != len(method_blocks):
        errors.append("census methodology seed count does not match human method count")
    if [item.get("id") for item in seeds] != ids:
        errors.append("machine seed order or IDs do not match the human page")

    seed_ids = set(ids)
    source_to_seeds: dict[str, set[str]] = {}
    for seed in seeds:
        seed_id = seed.get("id")
        if seed_id not in seed_ids:
            errors.append(f"machine seed not present in human page: {seed_id}")
        if seed.get("kind") not in {"CONTENT", "METHODOLOGY"}:
            errors.append(f"invalid seed kind: {seed_id}")
        if seed.get("external_novelty_status") != "NOT_CHECKED":
            errors.append(f"external novelty must remain NOT_CHECKED: {seed_id}")
        links = seed.get("source_links", [])
        if not links:
            errors.append(f"seed has no source links: {seed_id}")
        for source in links:
            source_to_seeds.setdefault(source, set()).add(seed_id)
            if not (ROOT / source).is_file() and source not in migration:
                errors.append(f"seed source link is not app-relative/current: {source}")
        if sorted(seed.get("source_chain", [])) != sorted(links):
            errors.append(f"source chain diverges from source links: {seed_id}")

    source_census = census.get("source_census", [])
    if not source_census:
        errors.append("source census is empty")
    seen_sources = set()
    disposition_counts: Counter[str] = Counter()
    for source in source_census:
        path = source.get("source_path")
        if not path or path in seen_sources:
            errors.append(f"duplicate or blank source census path: {path}")
        seen_sources.add(path)
        if not (ROOT / str(path)).is_file() and str(path) not in migration:
            errors.append(f"missing source census path: {path}")
        if source.get("disposition") not in DISPOSITIONS:
            errors.append(f"invalid source disposition: {path}")
        disposition_counts[source.get("disposition")] += 1
        if source.get("source_kind") == "KNOWLEDGE_EXPERIENCE_LAYERED_READING":
            actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest() if (ROOT / path).is_file() else migration.get(path)
            if actual != source.get("source_sha256"):
                errors.append(f"source hash drift: {path}")
    summary = census.get("source_census_summary", {})
    if summary.get("source_count") != len(source_census):
        errors.append("source census summary source_count mismatch")
    if dict(sorted(disposition_counts.items())) != summary.get("disposition_counts", {}):
        errors.append("source census disposition summary mismatch")
    layered_count = sum(
        1
        for line in LAYERED.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    if census.get("knowledge_experience", {}).get("layered_reading_source_origins") != layered_count:
        errors.append("knowledge layered-reading source-origin count drift")
    if summary.get("knowledge_experience_source_origins") != layered_count:
        errors.append("source census knowledge origin count drift")
    for source in source_to_seeds:
        if source not in seen_sources:
            errors.append(f"seed source is absent from source census: {source}")
    for conflict in census.get("conflicts", []):
        for seed_id in conflict.get("seed_ids", []):
            if seed_id not in seed_ids:
                errors.append(f"conflict references unknown seed: {conflict.get('id')}")

    for target in LINK_RE.findall(text):
        resolved = _resolve_link(target)
        if resolved is None:
            continue
        if str(resolved) == "__OUTSIDE_REPOSITORY__" or not resolved.exists():
            errors.append(f"broken human Fire Seeds link: {target}")
    if "external novelty" not in text and "外部新颖性" not in text:
        errors.append("human page does not state the external novelty boundary")

    actions: list[str] = []
    if not LOG.is_file():
        errors.append(f"missing Fire Seeds changelog: {LOG}")
    else:
        for line_no, line in enumerate(LOG.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid Fire Seeds changelog JSON at line {line_no}: {exc}")
                continue
            if row.get("action") not in {"SEED_DELTA", "NO_SEED_DELTA"}:
                errors.append(f"invalid Fire Seeds changelog action at line {line_no}")
            actions.append(str(row.get("action")))
    if not actions:
        errors.append("Fire Seeds changelog is empty")
    if errors:
        raise AssertionError("\n".join(errors))
    return {
        "entries": len(blocks),
        "clusters": len(clusters),
        "content_seed_count": len(content_blocks),
        "methodology_seed_count": len(method_blocks),
        "source_count": len(source_census),
        "changelog_records": len(actions),
    }


if __name__ == "__main__":
    result = validate()
    print("FIRE_SEEDS_VALID " + " ".join(f"{key}={value}" for key, value in result.items()))
