#!/usr/bin/env python3
"""Validate the human Fire Seeds publication layer without judging truth."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HUMAN = ROOT / "PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md"
CENSUS = ROOT / "data/publication/fire-seeds/seed-census.json"
LOG = ROOT / "data/publication/fire-seeds/CHANGELOG.jsonl"


def validate() -> dict[str, int]:
    errors: list[str] = []
    if not HUMAN.is_file():
        errors.append(f"missing human Fire Seeds asset: {HUMAN}")
        raise AssertionError("\n".join(errors))
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    text = HUMAN.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^## (FS-\d+) (.+)$", text, re.M))
    if not 20 <= len(matches) <= 50:
        errors.append(f"Fire Seeds entry count outside 20-50: {len(matches)}")
    ids = [match.group(1) for match in matches]
    if len(ids) != len(set(ids)):
        errors.append("duplicate Fire Seeds entry IDs")
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end() : end]
        body = block.split("**边界：**", 1)[0].strip()
        if not body or len(body) < 40:
            errors.append(f"{match.group(1)} lacks a human body")
        if "**边界：**" not in block:
            errors.append(f"{match.group(1)} lacks explicit boundary")
        if "**继续阅读：**" not in block:
            errors.append(f"{match.group(1)} lacks continuation links")
    clusters = census.get("clusters", [])
    if census.get("candidate_count") != len(matches) or census.get("cluster_count") != len(clusters):
        errors.append("census counts do not match human entry/cluster counts")
    if census.get("candidate_count") != census.get("cluster_count"):
        errors.append("candidate and cluster census counts differ")
    for source in census.get("source_boundary", []):
        if not (ROOT / source).is_file():
            errors.append(f"missing census source boundary asset: {source}")
    for cluster in clusters:
        if not cluster.get("entry") or not cluster.get("source_links"):
            errors.append(f"cluster lacks entry or source links: {cluster.get('id')}")
        for source in cluster.get("source_links", []):
            if source.startswith("../") or not (ROOT / source).exists():
                errors.append(f"cluster source link is not app-relative/current: {source}")
    actions: list[str] = []
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
    return {"entries": len(matches), "clusters": len(clusters), "changelog_records": len(actions)}


if __name__ == "__main__":
    result = validate()
    print("FIRE_SEEDS_VALID " + " ".join(f"{key}={value}" for key, value in result.items()))
