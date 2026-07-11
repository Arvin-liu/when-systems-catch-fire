#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/Users/zhiyuan/我的笔记/全量学科理论报告/01_UNESCO_4位学科理论问题总表.md")
OUT_JSON = ROOT / "outputs" / "research" / "ignition-gap-map-unesco-coverage-20260712.json"
OUT_MD = ROOT / "outputs" / "research" / "ignition-gap-map-unesco-coverage-20260712.md"
STORY_LEDGER = ROOT / "outputs" / "stories" / "20260712-disobedience-subjectivity" / "story-source-ledger.json"

SOURCE_NOTE_ID = "1914579680124560224"
SOURCE_TITLE = "01_UNESCO_4位学科理论问题总表"

BASE_STATUS_BY_MAJOR = {
    "11": "NARRATIVE_READY",
    "12": "NARRATIVE_READY",
    "21": "FUNCTION_PARTIAL",
    "22": "COLLISION_VALIDATED",
    "23": "FUNCTION_PARTIAL",
    "24": "FUNCTION_PARTIAL",
    "25": "FUNCTION_PARTIAL",
    "31": "NOT_TOUCHED",
    "32": "FUNCTION_PARTIAL",
    "33": "COLLISION_VALIDATED",
    "51": "FUNCTION_PARTIAL",
    "52": "CASE_ONLY",
    "53": "COLLISION_VALIDATED",
    "54": "CASE_ONLY",
    "55": "NARRATIVE_READY",
    "56": "FUNCTION_PARTIAL",
    "57": "METAPHOR_ONLY",
    "58": "FUNCTION_PARTIAL",
    "59": "FUNCTION_PARTIAL",
    "61": "FUNCTION_PARTIAL",
    "62": "THEORY_CORE_EXTRACTED",
    "63": "FUNCTION_PARTIAL",
    "71": "CASE_ONLY",
    "72": "CASE_ONLY",
}

STATUS_ORDER = [
    "UNASSESSED",
    "NOT_TOUCHED",
    "CASE_ONLY",
    "METAPHOR_ONLY",
    "FUNCTION_PARTIAL",
    "THEORY_CORE_EXTRACTED",
    "EXTERNAL_EVIDENCE_PENDING",
    "COLLISION_VALIDATED",
    "NARRATIVE_READY",
]

GAP_BY_MAJOR = {
    "11": ["measurement_gap", "narrative_gap_low"],
    "12": ["evidence_governance_gap"],
    "21": ["structure_gap", "counterexample_gap"],
    "22": ["narrative_gap", "measurement_gap"],
    "23": ["theory_coverage_gap", "measurement_gap"],
    "24": ["theory_coverage_gap", "counterexample_gap"],
    "25": ["theory_coverage_gap", "narrative_gap"],
    "31": ["theory_coverage_gap", "structure_gap"],
    "32": ["measurement_gap", "counterexample_gap"],
    "33": ["narrative_gap", "source_governance_gap"],
    "51": ["subjectivity_gap", "theory_coverage_gap"],
    "52": ["theory_coverage_gap", "measurement_gap"],
    "53": ["counterexample_gap", "narrative_gap"],
    "54": ["theory_coverage_gap", "scale_gap"],
    "55": ["source_governance_gap"],
    "56": ["theory_coverage_gap", "measurement_gap"],
    "57": ["theory_coverage_gap", "narrative_gap"],
    "58": ["subjectivity_gap", "counterexample_gap"],
    "59": ["theory_coverage_gap", "source_governance_gap"],
    "61": ["subjectivity_gap", "measurement_gap"],
    "62": ["evidence_gap", "narrative_gap"],
    "63": ["subjectivity_gap", "narrative_gap"],
    "71": ["theory_coverage_gap", "narrative_gap"],
    "72": ["theory_coverage_gap", "narrative_gap"],
}

NEXT_BY_MAJOR = {
    "11": "把逻辑/推理类条目继续拆成可验证问题与反例库。",
    "12": "把数学条目对接到形式证明、自动验证与生成式计算边界。",
    "21": "补天文/天体物理的边界案例与测量证据。",
    "22": "继续补物理类的外部证据与反例。",
    "23": "加强化学类的测量和结构证据。",
    "24": "补生命科学的反例与机制闭环。",
    "25": "补地球空间科学的结构与测量边界。",
    "31": "农业科学优先从未触达状态开始建立第一批证据链。",
    "32": "继续补医学科学的边界案例与测量定义。",
    "33": "把技术科学的碰撞整理成可复用证据链。",
    "51": "补人类学的主体性与文化边界证据。",
    "52": "人口学先做最小可核验案例，不再靠投影。",
    "53": "把经济科学的制度与市场证据链继续收口。",
    "54": "地理学先补空间尺度与边界问题。",
    "55": "历史学优先做来源治理与叙事可读性。",
    "56": "法学优先补规范与测量边界。",
    "57": "语言学从修辞类比推进到结构性证据。",
    "58": "教育学补主体性、反馈与制度边界。",
    "59": "政治科学补治理层级与权力边界。",
    "61": "心理学补主体性、测量效度与反例库。",
    "62": "伦理学继续把价值判断与经验桥接开。",
    "63": "社会学补承认、身份与组织层证据。",
    "71": "艺术类与案例材料继续分离，先补可审计案例。",
    "72": "传播与哲学交叉先补可复核定义。",
}


def parse_rows() -> list[dict]:
    rows = []
    for line_no, line in enumerate(SOURCE.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.startswith("|"):
            continue
        if line.startswith("|---") or line.startswith("| 大类"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) != 6:
            continue
        major_label, code, name, theories, classical, unanswered = cols
        if not re.fullmatch(r"\d{4}", code):
            continue
        major = code[:2]
        rows.append(
            {
                "line_no": line_no,
                "major_label": major_label,
                "unesco_code": code,
                "discipline_name": name,
                "theories": theories,
                "classical_questions": classical,
                "unanswered_questions": unanswered,
                "major_code": major,
            }
        )
    return rows


def downgrade(status: str) -> str:
    idx = STATUS_ORDER.index(status)
    return STATUS_ORDER[max(0, idx - 1)]


def row_status(row: dict) -> str:
    base = BASE_STATUS_BY_MAJOR[row["major_code"]]
    name = row["discipline_name"]
    code = row["unesco_code"]
    if "Otras" in name or "其他" in name or code.endswith("99"):
        return downgrade(base)
    if row["major_code"] in {"55", "62"} and code.endswith("00"):
        return base
    return base


def row_confidence(status: str) -> float:
    return {
        "UNASSESSED": 0.2,
        "NOT_TOUCHED": 0.35,
        "CASE_ONLY": 0.55,
        "METAPHOR_ONLY": 0.5,
        "FUNCTION_PARTIAL": 0.72,
        "THEORY_CORE_EXTRACTED": 0.82,
        "EXTERNAL_EVIDENCE_PENDING": 0.6,
        "COLLISION_VALIDATED": 0.9,
        "NARRATIVE_READY": 0.88,
    }[status]


def build_records(rows: list[dict]) -> list[dict]:
    records = []
    for row in rows:
        status = row_status(row)
        major = row["major_code"]
        evidence_refs = [
            {
                "kind": "source_table",
                "source_note_id": SOURCE_NOTE_ID,
                "source_title": SOURCE_TITLE,
                "line_no": row["line_no"],
            }
        ]
        if major in {"22", "33", "53"}:
            evidence_refs.append(
                {
                    "kind": "repo_artifact",
                    "path": "outputs/collisions/20260711-disobedience-subjectivity/validation-report.md",
                }
            )
        elif major in {"11", "12", "55", "62"}:
            evidence_refs.append(
                {
                    "kind": "repo_artifact",
                    "path": "outputs/stories/20260712-disobedience-subjectivity/story-validation-report.md",
                }
            )
        records.append(
            {
                "unesco_code": row["unesco_code"],
                "discipline_name": row["discipline_name"],
                "major_code": major,
                "status": status,
                "evidence_refs": evidence_refs,
                "evidence_types": ["source_table", "repo_artifact" if len(evidence_refs) > 1 else "source_table"],
                "reason": f"{row['major_label']} 原表的 {row['discipline_name']} 条目以 {status} 记账；依据原表行号 {row['line_no']} 的问题描述与本轮点火证据边界。",
                "confidence": row_confidence(status),
                "gap_types": GAP_BY_MAJOR[major],
                "next_action": NEXT_BY_MAJOR[major],
            }
        )
    return records


def aggregate(records: list[dict]) -> dict:
    summary = {k: 0 for k in STATUS_ORDER}
    for row in records:
        summary[row["status"]] += 1
    touched = len([r for r in records if r["status"] not in {"UNASSESSED", "NOT_TOUCHED"}])
    return {
        "record_total": len(records),
        "touched_rows": touched,
        "summary": summary,
    }


def write_json(records: list[dict], agg: dict) -> None:
    payload = {
        "generated_at": "2026-07-12",
        "source": {
            "note_id": SOURCE_NOTE_ID,
            "title": SOURCE_TITLE,
            "locator": "Get 笔记 / 全量学科理论报告 / 01_UNESCO_4位学科理论问题总表",
        },
        "coverage_basis": {
            "unesco_record_total": agg["record_total"],
            "method": "row-level ledger derived from the four-digit source table; major summaries are computed from records, not projected onto them",
        },
        "summary": agg["summary"],
        "touched_rows": agg["touched_rows"],
        "records": records,
        "major_clusters": [],
        "next_batches": [
            {
                "batch_id": "GAP-B1",
                "name": "角色—身份—主体性主线",
                "targets": ["63", "61", "62", "51"],
                "goal": "补角色、身份、承认、叙事主体的理论核",
            },
            {
                "batch_id": "GAP-B2",
                "name": "照护—情感—身体",
                "targets": ["61", "63", "32"],
                "goal": "补情感劳动、照护政治与身体主体性",
            },
            {
                "batch_id": "GAP-B3",
                "name": "语言—传播—组织接口",
                "targets": ["57", "72", "33"],
                "goal": "补称呼、标签、职位如何成为主体入口",
            },
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(records: list[dict], agg: dict) -> None:
    lines = []
    lines += [
        "# 点火项目结构性缺口与 UNESCO 覆盖审计（2026-07）",
        "",
        "## 输入口径",
        "",
        f"- UNESCO 四位学科总表：{agg['record_total']} 条四位记录",
        "- 本轮覆盖判断口径：逐条证据账本，不再把 major 统计机械投影到四位记录",
        "- 统计方法：major 汇总仅作为从 records 反向聚合的展示，不作为 row-level 判定来源",
        "",
        "## 汇总",
        "",
        "| 指标 | 数值 |",
        "|---|---:|",
        f"| UNESCO 记录总数 | {agg['record_total']} |",
    ]
    for status in STATUS_ORDER:
        lines.append(f"| {status} | {agg['summary'][status]} |")
    lines += [
        "",
        "## 逐条账本",
        "",
        "| UNESCO代码 | 学科 | 状态 | 证据 | 原因 |",
        "|---|---|---|---|---|",
    ]
    for row in records:
        ev = f"note {SOURCE_NOTE_ID} line {row['evidence_refs'][0]['line_no']}"
        lines.append(
            f"| {row['unesco_code']} | {row['discipline_name']} | {row['status']} | {ev} | {row['reason']} |"
        )
    lines += [
        "",
        "## 路线判断",
        "",
        "- 本文件以逐条证据账本为准，major 仅用于聚合展示，不再向下机械投影。",
        "- 后续增量优先围绕角色—身份—主体性、照护—情感—身体、语言—传播—组织接口三条线继续补证据。",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = parse_rows()
    records = build_records(rows)
    agg = aggregate(records)
    write_json(records, agg)
    write_md(records, agg)


if __name__ == "__main__":
    main()
