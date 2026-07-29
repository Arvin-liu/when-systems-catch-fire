#!/usr/bin/env python3
"""Build a conservative human-readable census of existing result documents."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "data/governance/human-results/config.json"
LEDGER = ROOT / "data/governance/human-results/result-ledger.jsonl"
CENSUS = ROOT / "data/governance/human-results/census.json"
HUMAN = ROOT / "RESULTS/CHRONOLOGY.md"


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def tracked_paths() -> list[str]:
    raw = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    )
    return sorted(item.decode("utf-8") for item in raw.split(b"\0") if item)


def discover(config: dict) -> list[str]:
    roots = tuple(root.rstrip("/") + "/" for root in config["source_roots"])
    excluded = tuple(config["excluded_prefixes"])
    return [
        path
        for path in tracked_paths()
        if path.endswith(".md") and path.startswith(roots) and not path.startswith(excluded)
    ]


def clean_inline(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"[`*_>#]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def title_and_summary(path: str) -> tuple[str, str]:
    lines = (ROOT / path).read_text(encoding="utf-8", errors="replace").splitlines()
    title = next((clean_inline(line[2:]) for line in lines if line.startswith("# ")), Path(path).stem)
    paragraphs: list[str] = []
    current: list[str] = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if stripped.startswith(("#", "|", "- ", "* ", ">", "<", "![")) or re.match(r"^\d+\.\s", stripped):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    summary = next((clean_inline(item) for item in paragraphs if len(clean_inline(item)) >= 24), "原文件保存该项结果的完整问题、过程与边界。")
    if len(summary) > 300:
        summary = summary[:297].rstrip() + "…"
    return title or Path(path).stem, summary


def date_hint(path: str) -> str:
    match = re.search(r"(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)", path)
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}" if match else "UNSPECIFIED"


def category(path: str) -> str:
    if path.startswith("reports/external-research/"):
        return "EXTERNAL_RESEARCH"
    if path.startswith("docs/publication/") or path.startswith("reports/publication/"):
        return "ARTICLE_OR_PUBLICATION"
    if path.startswith("docs/foundation/") or path.startswith("reports/foundation-architecture/"):
        return "FOUNDATION_AND_ADJUDICATION"
    if path.startswith("docs/architecture/"):
        return "ARCHITECTURE_AND_MODEL"
    if path.startswith("docs/operations/") or path.startswith("reports/operations/"):
        return "ITERATION_AND_AUDIT"
    return "OTHER_REPOSITORY_RESULT"


def originating_iteration(path: str) -> str:
    task = re.search(r"(?:^|/)(?:IGNITION-)?((?:121Q\d+[A-Z]*|0?\d{2,3})(?:[-_][A-Z0-9]+)*)", path, re.IGNORECASE)
    if task:
        return task.group(1).upper()
    return "REPOSITORY_HISTORY_SOURCE"


def build_records(config: dict) -> list[dict]:
    records = []
    for path in discover(config):
        title, summary = title_and_summary(path)
        record = {
            "result_id": "HR-" + hashlib.sha256(path.encode()).hexdigest()[:16].upper(),
            "title": title,
            "date": date_hint(path),
            "originating_iteration": originating_iteration(path),
            "category": category(path),
            "question": f"此来源记录了什么：{title}？",
            "method_or_evidence_class": "SOURCE_DOCUMENT_RECOVERY_AND_NAVIGATION",
            "result_summary": summary,
            "maturity_and_evidence": "SOURCE_DEFINED; inspect the linked source and current adjudication before reuse.",
            "change_record": "Recovered into the task 101 human-readable ledger without altering the source.",
            "limitations": "This is a conservative navigation summary, not a new adjudication, proof, empirical verification or lifecycle promotion.",
            "source": path,
            "final_disposition": "HUMAN_INDEX_ONLY",
            "claim_ceiling": config["claim_ceiling"],
        }
        record["record_sha256"] = hashlib.sha256(canonical_json(record).encode()).hexdigest()
        records.append(record)
    return sorted(records, key=lambda row: (row["date"] == "UNSPECIFIED", row["date"], row["source"]), reverse=True)


def render(records: list[dict], config: dict) -> str:
    groups: dict[str, list[dict]] = {}
    for row in records:
        groups.setdefault(row["category"], []).append(row)
    lines = [
        "# 历史结果台账",
        "",
        f"本台账从 {len(records)} 份现存研究、文章、架构、Foundation 与迭代文档确定性恢复。它只提供保真导航，不改变原来源的证据权限。",
        "",
        f"**统一断言上限：** {config['claim_ceiling']}",
        "",
    ]
    for group in sorted(groups):
        lines.extend([f"## {group}", ""])
        for row in groups[group]:
            lines.extend(
                [
                    f"### [{row['title']}](../{row['source']})",
                    "",
                    f"- **结果 ID：** `{row['result_id']}`",
                    f"- **日期：** {row['date']}",
                    f"- **来源任务/运行：** `{row['originating_iteration']}`",
                    f"- **问题：** {row['question']}",
                    f"- **方法/证据类别：** {row['method_or_evidence_class']}",
                    f"- **来源摘要：** {row['result_summary']}",
                    f"- **成熟度与证据：** {row['maturity_and_evidence']}",
                    f"- **变化：** {row['change_record']}",
                    f"- **局限：** {row['limitations']}",
                    f"- **处置：** `{row['final_disposition']}`",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def outputs() -> dict[Path, str]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    records = build_records(config)
    schema = json.loads((ROOT / "schemas/governance/human-result.schema.json").read_text(encoding="utf-8"))
    for record in records:
        jsonschema.validate(record, schema)
    ledger = "".join(canonical_json(row) + "\n" for row in records)
    categories: dict[str, int] = {}
    for row in records:
        categories[row["category"]] = categories.get(row["category"], 0) + 1
    census = {
        "schema_version": "1.0.0",
        "snapshot_date": config["snapshot_date"],
        "source_documents": len(records),
        "human_records": len(records),
        "all_sources_have_human_record": True,
        "category_distribution": dict(sorted(categories.items())),
        "claim_ceiling": config["claim_ceiling"],
    }
    return {
        LEDGER: ledger,
        CENSUS: json.dumps(census, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        HUMAN: render(records, config),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    products = outputs()
    if args.check:
        drift = [str(path.relative_to(ROOT)) for path, content in products.items() if not path.is_file() or path.read_text(encoding="utf-8") != content]
        if drift:
            raise SystemExit("HUMAN_RESULT_OUTPUT_DRIFT: " + ", ".join(drift))
    else:
        for path, content in products.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print(f"HUMAN_RESULTS_OK records={len(products[LEDGER].splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
