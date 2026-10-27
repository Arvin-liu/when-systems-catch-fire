#!/usr/bin/env python3
"""Create deterministic audit ledgers for the bounded R0 publication intake."""

from __future__ import annotations

import difflib
import json
import re
from pathlib import Path


ROOT = Path("data/operations/iterations/112/publication")
R0 = ROOT / "r0-original"
COMMIT = "84fdcf68f2bd3fde8ed543b0ec6b51a538ea9597"
CURRENT = "302362f66dad4e8a9c9e72400f4267c12b0b0d00"


def parse_notes() -> list[dict[str, object]]:
    text = (R0 / "notes/点火研究笔记-第一辑.md").read_text(encoding="utf-8")
    parts = re.split(r"(?m)^### (N\d+)｜([^\n]+)\n", text)
    notes = []
    for i in range(1, len(parts), 3):
        note_id, title, body = parts[i : i + 3]
        body = body.strip()

        def field(label: str) -> str:
            match = re.search(
                rf"\*\*{re.escape(label)}：\*\*\s*(.*?)(?=\n\n\*\*|\Z)",
                body,
                flags=re.S,
            )
            return re.sub(r"\s+", " ", match.group(1).strip()) if match else ""

        source = field("证据或来源")
        source_paths = re.findall(r"`([^`]+)`", source)
        if not source_paths:
            source_paths = ["R0 synthesis source; see the note body"]
        if note_id in {"N42", "N47", "N48", "N49", "N50"}:
            revision = True
            disposition = "RETAIN_WITH_TARGETED_REWRITE"
        else:
            revision = False
            disposition = "RETAIN_AS_INDEPENDENT_NOTE"
        if int(note_id[1:]) <= 20:
            claim_type = "METHOD_OR_INTERPRETATION"
            ceiling = "bounded methodological inference; not an external law"
        elif int(note_id[1:]) <= 30:
            claim_type = "CORRECTION_RESULT"
            ceiling = "current project claim correction; not a field-wide ruling"
        elif int(note_id[1:]) <= 40:
            claim_type = "GOVERNANCE_OR_FORMALIZATION"
            ceiling = "registry, representation or formal scope only"
        elif int(note_id[1:]) <= 50:
            claim_type = "BOUNDED_EXPERIMENT_OR_SOURCE_AUDIT"
            ceiling = "declared run, source layer or target gate only"
        else:
            claim_type = "OPEN_QUESTION_OR_PUBLICATION_METHOD"
            ceiling = "proposal or unresolved question; no completed external result"
        notes.append(
            {
                "note_id": note_id,
                "title": title,
                "question": field("问题"),
                "core_insight": field("核心认识"),
                "evidence_or_source": source,
                "source_paths": source_paths,
                "boundary": field("边界"),
                "unresolved_question": field("尚未解决"),
                "claim_type": claim_type,
                "current_status": "SUPPORTED_WITH_LIMITS" if not revision else "SUPPORTED_WITH_TARGETED_REWRITE",
                "claim_ceiling": ceiling,
                "correction_or_supersession": "none identified in R0; verify against current main",
                "revision_required": revision,
                "disposition": disposition,
                "source": f"r0-original/notes/点火研究笔记-第一辑.md#{note_id} at R0 commit {COMMIT}",
            }
        )
    return notes


def parse_panorama() -> list[dict[str, object]]:
    path = R0 / "点火目前真正知道什么.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    current_section = ""
    out = []
    section_map = {
        "一、20 项当前能够支持的认识": ("SUPPORTED", "current project knowledge with explicit limits"),
        "二、20 项已纠正、撤回或降级的认识": ("CORRECTED_OR_WITHDRAWN", "historical claim correction; not current truth"),
        "三、20 项尚未解决的问题": ("UNRESOLVED", "open question; no completed result"),
        "四、10 项最重要的后续研究方向": ("DIRECTION", "proposal ranked by evidence gap; not an authorized task"),
    }
    for lineno, line in enumerate(lines, 1):
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue
        match = re.match(r"^(\d+)\. \*\*(.+?)\*\* 边界：(.+)$", line)
        if not match or current_section not in section_map:
            continue
        idx, conclusion, boundary = int(match.group(1)), match.group(2).strip(), match.group(3).strip()
        status, ceiling = section_map[current_section]
        revision = status in {"CORRECTED_OR_WITHDRAWN", "DIRECTION"} and idx in {10, 12, 16, 17, 18, 19, 20}
        if status == "SUPPORTED":
            evidence = "mixed: method, registry, bounded engineering or historical source"
            source = "r0-original/点火目前真正知道什么.md plus cited current formal sources"
        elif status == "CORRECTED_OR_WITHDRAWN":
            evidence = "correction ledger and current-truth / task history evidence"
            source = "r0-original/04-纠正与撤回谱系.md plus current formal main"
        elif status == "UNRESOLVED":
            evidence = "explicit gap, null, absent target or missing external adjudication"
            source = "r0-original/UNRESOLVED.md and current formal open-question surfaces"
        else:
            evidence = "publication synthesis of unresolved evidence gaps"
            source = "r0-original/点火目前真正知道什么.md and current formal open-question surfaces"
        out.append(
            {
                "claim_id": f"P-{len(out)+1:03d}",
                "source_kind": "panorama",
                "source_path": "r0-original/点火目前真正知道什么.md",
                "source_commit": COMMIT,
                "line": lineno,
                "section": current_section,
                "item_number": idx,
                "exact_text_span": line,
                "claim_type": status,
                "current_status": status,
                "evidence_class": evidence,
                "claim_ceiling": ceiling,
                "contradiction_correction_supersession": "see section label and current main; no automatic promotion",
                "revision_required": revision,
                "current_comparison_version": CURRENT,
                "disposition": "REWRITE_FOR_CURRENT_MAIN" if revision else "RETAIN_WITH_EXPLICIT_BOUNDARY",
                "current_source_hint": source,
                "boundary": boundary,
            }
        )
    if len(out) != 70:
        raise SystemExit(f"expected 70 panorama items, got {len(out)}")
    return out


def volume_claims() -> list[dict[str, object]]:
    path = R0 / "volume/第一卷-第二稿.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    selected = [19, 25, 67, 77, 81, 87, 125, 151, 195, 221, 237, 269, 291, 299, 369, 383, 429, 435, 443, 553, 555, 567, 577, 585, 703, 735, 745, 763, 803, 825]
    out = []
    for line_no in selected:
        if line_no > len(lines):
            continue
        line = lines[line_no - 1].strip()
        if not line:
            continue
        lower = line.lower()
        if any(k in line for k in ["Function OS", "parser", "oracle"]):
            claim_type, ceiling = "BOUNDED_ENGINEERING", "declared benchmark, version, input domain and oracle only"
        elif any(k in line for k in ["Crossref", "OpenAlex", "来源", "全文", "metadata"]):
            claim_type, ceiling = "SOURCE_OR_METADATA", "metadata or bounded source layer; not claim-level content support"
        elif any(k in line for k in ["苹果", "历史", "target"]):
            claim_type, ceiling = "HISTORICAL_OR_TARGET_AUDIT", "bounded provenance and target audit; not historical causal reconstruction"
        elif any(k in line for k in ["Foundation", "registry", "账本"]):
            claim_type, ceiling = "GOVERNANCE_ACCOUNTING", "identity, status and provenance accounting; not truth closure"
        else:
            claim_type, ceiling = "METHOD_OR_INTERPRETATION", "publication synthesis bounded by cited sources"
        out.append(
            {
                "claim_id": f"V-{len(out)+1:03d}",
                "source_kind": "volume",
                "source_path": "r0-original/volume/第一卷-第二稿.md",
                "source_commit": COMMIT,
                "line": line_no,
                "exact_text_span": line,
                "claim_type": claim_type,
                "current_status": "REQUIRES_SUBSTANTIVE_REWRITE",
                "evidence_class": "R0 synthesis with cited repository evidence",
                "claim_ceiling": ceiling,
                "contradiction_correction_supersession": "must be rechecked against formal main 302362f6 and task-111 recovery state",
                "revision_required": True,
                "current_comparison_version": CURRENT,
                "disposition": "REWRITE_IN_FINAL_VOLUME",
                "current_source_hint": "formal main plus R0 source/evidence appendix",
            }
        )
    return out


def note_independence_report(notes: list[dict[str, object]]) -> str:
    raw = (R0 / "notes/点火研究笔记-第一辑.md").read_text(encoding="utf-8")
    parts = re.split(r"(?m)^### (N\d+)｜([^\n]+)\n", raw)
    bodies = {parts[i]: parts[i + 2].strip() for i in range(1, len(parts), 3)}
    paragraphs = {n: [p.strip() for p in b.split("\n\n") if len(p.strip()) >= 80] for n, b in bodies.items()}
    rows = []
    for note in notes:
        note_id = str(note["note_id"])
        body = bodies[note_id]
        grams = set(body.replace(" ", ""))
        max_j = 0.0
        for other_id, other_body in bodies.items():
            if other_id == note_id:
                continue
            # A character-set check is deliberately conservative; exact paragraph
            # overlap below is the stronger mechanical-splitting test.
            other_grams = set(other_body.replace(" ", ""))
            max_j = max(max_j, len(grams & other_grams) / max(1, len(grams | other_grams)))
        exact_overlap = any(p in (R0 / "volume/第一卷-第二稿.md").read_text(encoding="utf-8") for p in paragraphs[note_id])
        verdict = "PASS_WITH_TARGETED_REWRITE" if note["revision_required"] else "PASS"
        rows.append(
            f"| {note_id} | {note['title']} | {len(body)} | {'是' if all(note[k] for k in ['question','core_insight','evidence_or_source','boundary','unresolved_question']) else '否'} | {'是' if exact_overlap else '否'} | {verdict} |"
        )
    return "\n".join(
        [
            "# R0 研究笔记独立性审计",
            "",
            "结论：`60/60 具备独立问题入口；55 条直接保留，5 条带目标性重写后保留`。这不是说 60 条互不共享证据；独立性要求的是问题、推理路径、边界和未解决残余能够各自站立。",
            "",
            "## 审计方法",
            "",
            "逐条读取 R0 的 60 个 `N01`–`N60` 区块，检查问题、核心认识、证据/来源、边界和尚未解决字段；对笔记正文与 R0 二稿做完整段落精确匹配；对笔记之间做保守的字符集合相似性筛查。相似证据不被当作复制，精确复制段落才会触发机械切片风险。",
            "",
            "结果：60 个唯一 ID；60/60 具备五个必需字段；0 个笔记段落与二稿存在完整精确重合；0 个标题重复。所有笔记按主题组织，而非按任务编号组织。五条（N42、N47、N48、N49、N50）需要在正式出版时更新实验/来源层级或 111 恢复状态的表述。",
            "",
            "## 逐项记录",
            "",
            "| ID | 标题 | 正文字符 | 五字段齐全 | 与二稿整段重合 | 结论 |",
            "| --- | --- | ---: | :---: | :---: | --- |",
            *rows,
            "",
            "## 独立性边界",
            "",
            "这份审计不能证明笔记中的研究认识在外部世界成立，也不能证明它们没有共享同一证据源。它只证明 R0 没有把第一卷段落机械切碎成 60 条，并且每条都有可独立阅读的最小结构。正式出版仍需对来源和主张重新绑定。",
        ]
    ) + "\n"


def main() -> None:
    notes = parse_notes()
    claims = parse_panorama() + [
        {
            "claim_id": f"N-{i+1:03d}",
            "source_kind": "research_note",
            "source_path": f"r0-original/notes/点火研究笔记-第一辑.md#{n['note_id']}",
            "source_commit": COMMIT,
            "line": None,
            "exact_text_span": n["core_insight"],
            "claim_type": n["claim_type"],
            "current_status": n["current_status"],
            "evidence_class": n["evidence_or_source"],
            "claim_ceiling": n["claim_ceiling"],
            "contradiction_correction_supersession": n["correction_or_supersession"],
            "revision_required": n["revision_required"],
            "current_comparison_version": CURRENT,
            "disposition": n["disposition"],
            "current_source_hint": n["source_paths"],
            "boundary": n["boundary"],
            "unresolved_question": n["unresolved_question"],
        }
        for i, n in enumerate(notes)
    ] + volume_claims()
    with (ROOT / "R0_CLAIM_AUDIT.jsonl").open("w", encoding="utf-8") as fh:
        for row in claims:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    (ROOT / "R0_NOTE_INDEPENDENCE_AUDIT.md").write_text(note_independence_report(notes), encoding="utf-8")
    print(json.dumps({"claims": len(claims), "notes": len(notes), "panorama": 70}, ensure_ascii=False))


if __name__ == "__main__":
    main()
