from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path("data/operations/iterations/112/publication")
rows = [json.loads(line) for line in (ROOT / "r0-original/01-百轮成果总台账.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


SETS = {
    "RESEARCH_RESULT": {"001", "002", "004", "005", "012", "016", "018", "021", "022", "023", "024", "025", "034", "036", "048", "055", "066", "072", "073", "075", "078"},
    "CORRECTION_RESULT": {"011", "014", "015", "016", "028", "031", "033", "038", "052", "053", "054", "055", "056", "057", "058", "059", "060", "061", "062", "063", "078"},
    "EMPIRICAL_OR_REPLICATION_RESULT": {"017", "028", "029", "030", "031", "032", "033", "035", "038", "045", "046"},
    "THEORY_OR_FORMALIZATION_RESULT": {"014", "017", "021", "022", "023", "024", "025", "053"},
    "METHOD_RESULT": {"002", "004", "005", "007", "011", "012", "018", "042", "078", "080"},
    "INFRASTRUCTURE_ONLY": {"009", "010", "013", "019", "020", "026", "040", "041", "043", "044", "051", "076", "077"},
    "MAINTENANCE_ONLY": {"047", "079"},
}

PRIMARY = {
    "001": "RESEARCH_RESULT", "002": "METHOD_RESULT", "004": "METHOD_RESULT", "005": "METHOD_RESULT",
    "006": "INFRASTRUCTURE_ONLY", "007": "MIXED", "008": "RESEARCH_RESULT", "009": "INFRASTRUCTURE_ONLY",
    "010": "INFRASTRUCTURE_ONLY", "011": "CORRECTION_RESULT", "012": "METHOD_RESULT", "013": "INFRASTRUCTURE_ONLY",
    "014": "THEORY_OR_FORMALIZATION_RESULT", "015": "CORRECTION_RESULT", "016": "CORRECTION_RESULT",
    "017": "THEORY_OR_FORMALIZATION_RESULT", "018": "CORRECTION_RESULT", "019": "INFRASTRUCTURE_ONLY",
    "020": "INFRASTRUCTURE_ONLY", "021": "RESEARCH_RESULT", "022": "RESEARCH_RESULT", "023": "RESEARCH_RESULT",
    "024": "RESEARCH_RESULT", "025": "RESEARCH_RESULT", "026": "INFRASTRUCTURE_ONLY", "027": "MIXED",
    "028": "EMPIRICAL_OR_REPLICATION_RESULT", "029": "EMPIRICAL_OR_REPLICATION_RESULT", "030": "EMPIRICAL_OR_REPLICATION_RESULT",
    "031": "CORRECTION_RESULT", "032": "EMPIRICAL_OR_REPLICATION_RESULT", "033": "CORRECTION_RESULT",
    "034": "RESEARCH_RESULT", "035": "EMPIRICAL_OR_REPLICATION_RESULT", "036": "RESEARCH_RESULT", "037": "RESEARCH_RESULT",
    "038": "CORRECTION_RESULT", "039": "CORRECTION_RESULT", "040": "INFRASTRUCTURE_ONLY", "041": "INFRASTRUCTURE_ONLY",
    "042": "METHOD_RESULT", "043": "INFRASTRUCTURE_ONLY", "044": "INFRASTRUCTURE_ONLY", "045": "EMPIRICAL_OR_REPLICATION_RESULT",
    "046": "EMPIRICAL_OR_REPLICATION_RESULT", "047": "MAINTENANCE_ONLY", "048": "RESEARCH_RESULT", "049": "MIXED",
    "050": "MIXED", "051": "INFRASTRUCTURE_ONLY", "052": "CORRECTION_RESULT", "053": "CORRECTION_RESULT",
    "054": "CORRECTION_RESULT", "055": "CORRECTION_RESULT", "056": "CORRECTION_RESULT", "057": "CORRECTION_RESULT",
    "058": "CORRECTION_RESULT", "059": "CORRECTION_RESULT", "060": "CORRECTION_RESULT", "061": "CORRECTION_RESULT",
    "062": "CORRECTION_RESULT", "063": "CORRECTION_RESULT", "064": "NO_RECOVERABLE_KNOWLEDGE_INCREMENT",
    "065": "NO_RECOVERABLE_KNOWLEDGE_INCREMENT", "066": "NO_RECOVERABLE_KNOWLEDGE_INCREMENT", "067": "NO_RECOVERABLE_KNOWLEDGE_INCREMENT",
    "068": "MIXED", "069": "MIXED", "070": "MIXED", "071": "MIXED", "072": "NO_RECOVERABLE_KNOWLEDGE_INCREMENT",
    "073": "NO_RECOVERABLE_KNOWLEDGE_INCREMENT", "074": "MAINTENANCE_ONLY", "075": "NO_RECOVERABLE_KNOWLEDGE_INCREMENT",
    "076": "INFRASTRUCTURE_ONLY", "077": "INFRASTRUCTURE_ONLY", "078": "CORRECTION_RESULT", "079": "MAINTENANCE_ONLY", "080": "MIXED",
}


def current_validity(row: dict[str, object]) -> str:
    d = str(row.get("disposition", ""))
    if d in {"OPEN", "WORK_IN_PROGRESS", "UNRESOLVED_VISIBILITY", "CAUSAL_IDENTIFICATION_PENDING"}:
        return "OPEN_OR_INCOMPLETE"
    if d == "EXECUTABLE_TARGET_ABSENT":
        return "TARGET_ABSENT"
    if d == "BASELINE_BOUNDARY":
        return "CURRENT_STATE_BOUNDARY_111_TERMINAL_RECOVERY_VERIFIED"
    if "FAILED" in d:
        return "FAILED_RETAINED_FOR_HISTORY"
    if "WITHDRAW" in d or "CORRECT" in d or "DOWNGRADE" in d or "REPAIRED" in d or "BLOCKED" in d:
        return "CORRECTED_OR_DOWNGRADED"
    if "METADATA" in d:
        return "SUPPORTED_METADATA_ONLY"
    if d in {"WORKFLOW_PASSED", "SCHEMA_VALIDATED", "LOCAL_OPERATIONAL_EVIDENCE"}:
        return "WORKFLOW_OR_SCHEMA_EVIDENCE_ONLY"
    if d in {"HISTORICAL_ONLY", "READ_ONLY_CANDIDATE_HISTORY"}:
        return "HISTORICAL_NOT_CURRENT"
    if d in {"MAINTENANCE", "NAVIGATION_ASSET", "SOURCE_POOL"}:
        return "CURRENT_ASSET_WITHOUT_NEW_EXTERNAL_RESULT"
    return "CURRENT_WITH_EXPLICIT_LIMITS"


def output_class(row: dict[str, object]) -> str:
    rid = str(row["record_id"]).split("-")[-1]
    if rid in PRIMARY:
        return PRIMARY[rid]
    hits = [name for name, ids in SETS.items() if rid in ids]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        return "MIXED"
    d = str(row.get("disposition", ""))
    if d in {"OPEN", "WORK_IN_PROGRESS", "UNRESOLVED_VISIBILITY", "CAUSAL_IDENTIFICATION_PENDING"}:
        return "NO_RECOVERABLE_KNOWLEDGE_INCREMENT"
    if d in {"MAINTENANCE", "READ_ONLY_CANDIDATE_HISTORY"}:
        return "MAINTENANCE_ONLY"
    if "出版" in str(row.get("record_kind", "")) or "出版" in "".join(row.get("classification", [])):
        return "MIXED"
    return "MIXED"


def ceiling(row: dict[str, object], cls: str, validity: str) -> str:
    if validity == "OPEN_OR_INCOMPLETE":
        return "开放问题或出版缺口；不能写成已经完成的结果"
    if validity == "TARGET_ABSENT":
        return "案例/实验目标审计；不能写成历史复原或程序运行失败"
    if validity == "SUPPORTED_METADATA_ONLY":
        return "书目元数据和匹配规则；不能写成正文或机制支持"
    if validity == "FAILED_RETAINED_FOR_HISTORY":
        return "声明版本、输入和失败现场；不能外推为全路线失败"
    if validity == "WORKFLOW_OR_SCHEMA_EVIDENCE_ONLY":
        return "声明的 schema、工作流和运行范围；不能写成科学正确"
    if cls == "INFRASTRUCTURE_ONLY" or cls == "MAINTENANCE_ONLY":
        return "保存、导航、同步或维护能力；不产生自动外部知识"
    if cls == "THEORY_OR_FORMALIZATION_RESULT":
        return "声明对象、假设和形式系统内的结果；不能越界到现实本体"
    if cls == "EMPIRICAL_OR_REPLICATION_RESULT":
        return "声明样本、版本、环境和 oracle 内的观察；不替代外部复制"
    return "当前来源和版本可支持的窄结论；不超过其证据层"


def visible_work(row: dict[str, object]) -> str:
    value = str(row.get("human_work", ""))
    if value in {"有", "完整长文", "完整作品", "完整报告", "完整说明", "完整审计", "完整导航", "方法说明", "审计报告", "状态说明", "报告", "README 与报告", "benchmark report"}:
        return f"已有可读材料：{value}"
    if value in {"待本工程生成", "待研究", "问题清单", "部分", "分散在报告中", "未作为正文证据", "本台账"}:
        return f"人类作品状态：{value}；需由本卷或附录明确承接"
    return value or "需要回到来源审读"


def render_record(row: dict[str, object]) -> str:
    cls = output_class(row)
    validity = current_validity(row)
    paths = "；".join(str(x) for x in row.get("source_paths", [])) or "未提供单一来源路径"
    commits = "、".join(str(x) for x in row.get("source_commits", [])) or "未提供提交锚点"
    targets = "、".join(str(x) for x in row.get("chapter_targets", [])) or "附录/未指定"
    correction = str(row.get("corrected_withdrawn_superseded", "none"))
    return "\n".join(
        [
            f"### {row['record_id']}｜{row['name']}",
            "",
            f"- 原始问题：{row['origin_problem']}",
            f"- 新增认识：{row['new_understanding']}",
            f"- 证据类型：{'、'.join(str(x) for x in row.get('evidence_type', []))}",
            f"- 112 输出类别：`{cls}`",
            f"- 当前有效性：`{validity}`",
            f"- 当前结论：{row['current_conclusion']}",
            f"- 当前边界：{row['current_boundary']}",
            f"- 纠正/撤回/取代：{correction}",
            f"- 已有人类作品：{visible_work(row)}",
            f"- 正文目的地：{targets}",
            f"- 来源路径：{paths}",
            f"- 来源提交：{commits}",
            f"- 结论天花板：{ceiling(row, cls, validity)}",
            "",
        ]
    )


counts = Counter(output_class(row) for row in rows)
header = """# 百轮成果台账

本台账回答的不是“仓库有多少文件”，而是“每个可恢复成果记录改变了什么判断、当前还能说到哪里”。它保留 R0 的 80 个唯一记录，并为每条记录补上 112 的输出类别、当前有效性、可读作品状态、章节去向和结论天花板。

## 读法

“百轮”是混合的长期迭代史，不是一百个独立实验。`RESEARCH_RESULT`、`CORRECTION_RESULT`、`EMPIRICAL_OR_REPLICATION_RESULT`、`THEORY_OR_FORMALIZATION_RESULT`、`METHOD_RESULT`、`INFRASTRUCTURE_ONLY`、`MAINTENANCE_ONLY`、`MIXED` 和 `NO_RECOVERABLE_KNOWLEDGE_INCREMENT` 不是荣誉等级；它们说明记录承担的责任不同。分类基于问题、证据、当前状态和输出，而不是只看任务标题或文件名。

R0 记录来自固定基线前置材料；任务 111 的生命周期事实已对正式仓库当前 `main=302362f66dad4e8a9c9e72400f4267c12b0b0d00` 复核。来源路径和提交用于定位，目录/集合不等于逐项全文阅读；任何 `CURRENT_WITH_EXPLICIT_LIMITS` 都不意味着外部共同体已经接受。

## 统计摘要

| 输出类别 | 记录数 |
| --- | ---: |
"""
body = "\n".join(f"| `{k}` | {counts[k]} |" for k in sorted(counts))
tail = """

类别之间按记录可能是混合关系；表中的数量只用于检索和审计，不相加为研究成果总数。完整来源文件级哈希见 `R0_FILE_MANIFEST.json`，逐项主张证据见 `R0_CLAIM_AUDIT.jsonl`。

## 逐项记录

"""
content = header + body + tail + "\n".join(render_record(row) for row in rows)
Path("PUBLICATIONS/hundred-iteration-achievement-ledger.md").write_text(content, encoding="utf-8")

machine = []
for row in rows:
    cls = output_class(row)
    validity = current_validity(row)
    machine.append(
        {
            "record_id": row["record_id"],
            "name": row["name"],
            "origin_problem": row["origin_problem"],
            "knowledge_increment": row["new_understanding"],
            "output_class": cls,
            "current_validity": validity,
            "correction_or_supersession": row.get("corrected_withdrawn_superseded", "none"),
            "visible_work": visible_work(row),
            "chapter_destination": row.get("chapter_targets", []),
            "source_paths": row.get("source_paths", []),
            "source_commits": row.get("source_commits", []),
            "claim_ceiling": ceiling(row, cls, validity),
        }
    )
(ROOT / "FINAL_ACHIEVEMENT_LEDGER.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in machine) + "\n", encoding="utf-8")
print(json.dumps({"records": len(rows), "classes": counts}, ensure_ascii=False))
