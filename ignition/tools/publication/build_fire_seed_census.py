#!/usr/bin/env python3
"""Build the deterministic Fire Seeds source census and seed registry.

This is a publication projection. It reads the human Fire Seeds page, the
knowledge-experience layered reading origins, and a bounded set of substantive
human-source globs. It does not adjudicate truth, proof, evidence, or external
novelty.
"""
from __future__ import annotations

import hashlib
import json
import re
import argparse
from collections import Counter
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
HUMAN = ROOT / "PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md"
LAYERED = ROOT / "data/governance/knowledge-experience/layered-reading.jsonl"
MANIFEST = ROOT / "data/governance/knowledge-experience/manifest.json"
MIGRATION = ROOT / "data/foundation/migrations/legacy-table-migration.jsonl"
OUT = ROOT / "data/publication/fire-seeds/seed-census.json"

SUPPLEMENTAL_GLOBS = [
    "PUBLICATIONS/pointfire-results-book/*.md",
    "docs/editorial/articles/*.md",
    "docs/publication/*.md",
    "docs/publication/works/*.md",
    "docs/publication/cases/*.md",
    "docs/publication/method-sources/*.md",
    "reports/research/**/*.md",
    "reports/publication/**/*.md",
    "reports/architecture/**/*.md",
    "outputs/collisions/**/*.md",
    "RESULTS/*.md",
    "KNOWLEDGE/*.md",
]

CONFLICTS = [
    {
        "id": "CONFLICT-001",
        "seed_ids": ["CF-03", "CF-04", "CF-14"],
        "tension": "制度上的退出、感知上的退出和退出后的可持续生活不能被当作同一变量。",
        "handling": "保留为三个内容入口；不把形式出口直接解释成行为自由。",
    },
    {
        "id": "CONFLICT-002",
        "seed_ids": ["CF-07", "CF-11", "CF-16"],
        "tension": "支持与共同体可以提供资源，也可能覆盖主体、转移风险或扩大责任不对称。",
        "handling": "并列记录资源、决定权、异议和修复义务，暂不合并成单一机制。",
    },
    {
        "id": "CONFLICT-003",
        "seed_ids": ["CF-12", "CF-13", "CF-25"],
        "tension": "协作需要共享接口，但共享接口、摘要和身份叙事也可能消除差异与解释权。",
        "handling": "把协作、描述和导航分开回链，保留被描述者和原始来源的修订位置。",
    },
    {
        "id": "CONFLICT-004",
        "seed_ids": ["CF-19", "CF-20", "CF-30"],
        "tension": "事后历史结果、进行中观察和多尺度模型对同一结构提供不同可见性。",
        "handling": "按时间点、证据等级和模型尺度分层，不以事后结果覆盖当时未知。",
    },
    {
        "id": "CONFLICT-005",
        "seed_ids": ["CF-21", "CF-22", "CF-23"],
        "tension": "生成速度、任务能力、评估能力和复核容量可能沿不同方向变化。",
        "handling": "保留条件化能力语言，不用单一能力分数代表整个系统。",
    },
    {
        "id": "CONFLICT-006",
        "seed_ids": ["CF-27", "CF-29", "CF-31"],
        "tension": "结构表示、函数族归纳和物理投影都能产生启发，但相似不等于同构或统一。",
        "handling": "记录表示层、候选层和开放统一层的不同义务，默认不升级。",
    },
    {
        "id": "CONFLICT-007",
        "seed_ids": ["CF-36", "CF-37"],
        "tension": "有感染力的历史写作能让结构可感，也可能让类比和解释显得比来源更确定。",
        "handling": "正文与来源、证据等级、类比边界并置，保留未解释部分。",
    },
    {
        "id": "CONFLICT-008",
        "seed_ids": ["CF-38", "CF-39", "CF-40"],
        "tension": "修复成功、工程收据、撤回和不可识别都不能被压缩为同一种完成状态。",
        "handling": "保留原始失败、收据范围和下一步义务；负结果不改写成成功叙事。",
    },
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def migrated_hashes() -> dict[str, str]:
    if not MIGRATION.is_file():
        return {}
    return {
        row["legacy_path"]: row["content_sha256"]
        for row in (json.loads(line) for line in MIGRATION.read_text(encoding="utf-8").splitlines() if line.strip())
        if row.get("legacy_path") and row.get("content_sha256")
    }


def source_hash(relative: str, migration: dict[str, str]) -> str:
    path = ROOT / relative
    return sha256(path) if path.is_file() else migration.get(relative, "MISSING_SOURCE_HASH")


def relative_source(target: str) -> str | None:
    target = unquote(target.split("#", 1)[0].strip())
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None
    resolved = (HUMAN.parent / target).resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        try:
            return "../" + resolved.relative_to(REPO_ROOT.resolve()).as_posix()
        except ValueError:
            return None


def parse_seeds() -> list[dict]:
    text = HUMAN.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^## ((?:CF|FS)-\d+) (.+)$", text, re.MULTILINE))
    current_section = "unsectioned"
    parsed: list[dict] = []
    for index, match in enumerate(matches):
        prefix = text[: match.start()]
        section_matches = list(re.finditer(r"^### (.+)$", prefix, re.MULTILINE))
        if section_matches:
            current_section = section_matches[-1].group(1).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end() : end]
        marker = "**继续追：**" if match.group(1).startswith("CF-") else "**继续阅读：**"
        links = []
        marker_pos = block.find(marker)
        link_text = block[marker_pos:] if marker_pos >= 0 else block
        for _, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", link_text):
            source = relative_source(target)
            if source and source not in links:
                links.append(source)
        kind = "CONTENT" if match.group(1).startswith("CF-") else "METHODOLOGY"
        parsed.append(
            {
                "id": match.group(1),
                "title": match.group(2).strip(),
                "kind": kind,
                "section": current_section,
                "internal_type": "content_research_writing_seed" if kind == "CONTENT" else "methodology_boundary_seed",
                "source_links": links,
                "external_novelty_status": "NOT_CHECKED",
                "status": "CONTENT_CANDIDATE" if kind == "CONTENT" else "METHODOLOGY_CANDIDATE",
            }
        )
    return parsed


def load_layered_rows() -> list[dict]:
    rows = []
    for line in LAYERED.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def source_paths(layered_rows: list[dict], required_sources: set[str]) -> list[str]:
    paths = {str(row["canonical_source"]) for row in layered_rows if row.get("canonical_source")}
    paths.update(required_sources)
    for pattern in SUPPLEMENTAL_GLOBS:
        paths.update(
            path.relative_to(ROOT).as_posix()
            for path in ROOT.glob(pattern)
            if path.is_file()
        )
    return sorted(paths)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare a fresh census without writing the committed projection")
    args = parser.parse_args()
    seeds = parse_seeds()
    layered_rows = load_layered_rows()
    layered_by_path = {
        str(row["canonical_source"]): row
        for row in layered_rows
        if row.get("canonical_source")
    }
    seed_links: dict[str, list[str]] = {}
    first_source: dict[str, str] = {}
    migration = migrated_hashes()
    for seed in seeds:
        for position, source in enumerate(seed["source_links"]):
            seed_links.setdefault(source, []).append(seed["id"])
            if position == 0:
                first_source.setdefault(seed["id"], source)
        seed["conflict_ids"] = [
            conflict["id"]
            for conflict in CONFLICTS
            if seed["id"] in conflict["seed_ids"]
        ]
        seed["source_chain"] = list(seed["source_links"])
        seed["source_links"] = sorted(set(seed["source_links"]))

    census = []
    disposition_counts: Counter[str] = Counter()
    for number, source in enumerate(source_paths(layered_rows, set(seed_links)), 1):
        path = ROOT / source
        row = layered_by_path.get(source, {})
        linked_seed_ids = sorted(seed_links.get(source, []))
        if linked_seed_ids:
            disposition = (
                "SEED_CREATED"
                if any(first_source.get(seed_id) == source for seed_id in linked_seed_ids)
                else "MERGED_INTO_SEED"
            )
            review_basis = "DIRECT_READ"
            review_note = "由正文继续阅读路径直接回链到内容或方法火种。"
        elif source.startswith(("data/", "KNOWLEDGE/", "docs/human/")):
            disposition = "EXCLUDED_NONCONTENT"
            review_basis = "INDEX_OR_GENERATED_PROJECTION"
            review_note = "机器登记、生成索引或导航投影；保留作为覆盖输入，不另造人类内容入口。"
        elif source.startswith(("reports/operations/", "reports/release/", "outputs/audit/")):
            disposition = "EXCLUDED_NONCONTENT"
            review_basis = "EXECUTION_OR_RECEIPT_RECORD"
            review_note = "执行、发布或审计收据；其内容边界已由相关人类入口承接。"
        else:
            disposition = "NO_SEED_DELTA"
            review_basis = (
                "KNOWLEDGE_LAYERED_READING_TRIAGE"
                if source in layered_by_path
                else "SUPPLEMENTAL_HUMAN_CORPUS_TRIAGE"
            )
            review_note = "已纳入本轮语料普查，但当前没有足够的新增人类入口增量。"
        disposition_counts[disposition] += 1
        record = {
            "source_id": f"ORIGIN-{number:04d}",
            "source_path": source,
            "source_kind": (
                "KNOWLEDGE_EXPERIENCE_LAYERED_READING"
                if source in layered_by_path
                else "SUPPLEMENTAL_HUMAN_SOURCE"
            ),
            "title": row.get("title") or path.stem,
            "knowledge_status": row.get("status"),
            "subject": row.get("subject"),
            "source_sha256": source_hash(source, migration),
            "disposition": disposition,
            "seed_ids": linked_seed_ids,
            "review_basis": review_basis,
            "review_note": review_note,
        }
        census.append(record)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    content = [seed for seed in seeds if seed["kind"] == "CONTENT"]
    methods = [seed for seed in seeds if seed["kind"] == "METHODOLOGY"]
    topics = Counter(seed["section"] for seed in content)
    payload = {
        "schema_version": "2.0.0",
        "asset": "FIRE_SEEDS_CENSUS",
        "status": "CURRENT_WITH_OPEN_OBLIGATIONS",
        "purpose": "完整语料考古的出版层收据；不替代来源、registry、evidence、proof、M/E 或 claim ceiling。",
        "source_boundary": {
            "knowledge_manifest": "data/governance/knowledge-experience/manifest.json",
            "knowledge_layered_reading": "data/governance/knowledge-experience/layered-reading.jsonl",
            "supplemental_globs": SUPPLEMENTAL_GLOBS,
            "historical_base_main": "89b005566bdfe266414c850871793b9dd10ba0af",
        },
        "method": {
            "candidate_census": "先读取知识体验层的全部 source origins，再补读成果册、文章、案例、研究报告、函数/案例表、碰撞、结果与开放问题。",
            "clustering": "按人、行动、协作、身份、历史、技术、认知、复杂系统、生命、写作与负结果等问题对象聚类，不按词面或机器 ID 合并。",
            "deduplication": "一个继续追的问题只保留一个人类入口；原始来源、机器记录和历史失败不删除。",
            "conflict_handling": "显式记录退出/共同体、表示/统一、收据/现实、修复/原始失败等张力，不自行裁决真值。",
            "disposition_enum": [
                "SEED_CREATED",
                "MERGED_INTO_SEED",
                "NO_SEED_DELTA",
                "EXCLUDED_NONCONTENT",
            ],
        },
        "knowledge_experience": {
            "manifest_counts": manifest.get("counts", {}),
            "layered_reading_source_origins": len(layered_rows),
            "layered_reading_status_counts": dict(
                sorted(Counter(str(row.get("status")) for row in layered_rows).items())
            ),
        },
        "candidate_count": len(seeds),
        "cluster_count": len(seeds),
        "seed_count": len(seeds),
        "content_seed_count": len(content),
        "methodology_seed_count": len(methods),
        "content_topic_sections": dict(sorted(topics.items())),
        "conflict_count": len(CONFLICTS),
        "conflicts": CONFLICTS,
        "seeds": seeds,
        "clusters": [
            {
                "id": seed["id"].replace("CF-", "C").replace("FS-", "S"),
                "entry": seed["id"],
                "title": seed["title"],
                "kind": seed["kind"],
                "section": seed["section"],
                "source_links": seed["source_links"],
                "conflict_ids": seed["conflict_ids"],
                "conflict_status": "EXPLICIT" if seed["conflict_ids"] else "NONE",
            }
            for seed in seeds
        ],
        "source_census": census,
        "source_census_summary": {
            "source_count": len(census),
            "knowledge_experience_source_origins": len(layered_rows),
            "supplemental_source_count": sum(
                1 for item in census if item["source_kind"] == "SUPPLEMENTAL_HUMAN_SOURCE"
            ),
            "disposition_counts": dict(sorted(disposition_counts.items())),
        },
        "update_protocol": {
            "human_canonical": "PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md",
            "machine_canonical": "data/publication/fire-seeds/seed-census.json",
            "changelog": "data/publication/fire-seeds/CHANGELOG.jsonl",
            "generator": "tools/publication/build_fire_seed_census.py",
            "validator": "tools/publication/validate_fire_seeds.py",
            "external_novelty_status": "NOT_CHECKED",
            "count_is_not_a_quality_metric": True,
        },
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUT.is_file() or OUT.read_text(encoding="utf-8") != rendered:
            print("FIRE_SEEDS_CENSUS_OUT_OF_DATE", flush=True)
            return 1
        print(
            "FIRE_SEEDS_CENSUS_CHECK_OK "
            f"seeds={len(seeds)} sources={len(census)} layered_origins={len(layered_rows)}"
        )
        return 0
    OUT.write_text(rendered, encoding="utf-8")
    print(
        "FIRE_SEEDS_CENSUS_BUILT "
        f"seeds={len(seeds)} content={len(content)} methodology={len(methods)} "
        f"sources={len(census)} layered_origins={len(layered_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
