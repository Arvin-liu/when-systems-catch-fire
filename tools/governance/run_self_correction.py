#!/usr/bin/env python3
"""Generate Claim Delta, impact, lineage and bounded repository audit products."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import deque
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "data/governance/self-correction/config.json"
OUT = ROOT / "data/governance/self-correction"
CLAIM_REGISTRY = ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl"
DEPENDENCY_GRAPH = ROOT / "data/foundation/nonfunction-claims/dependency-graph.jsonl"
EVIDENCE_LINEAGE = ROOT / "data/foundation/nonfunction-claims/evidence-lineage.jsonl"

MACHINE_OUTPUTS = {
    "claim_delta": OUT / "claim-delta.jsonl",
    "impact": OUT / "impact-analysis.jsonl",
    "lineage": OUT / "evidence-lineage-delta.jsonl",
    "findings": OUT / "audit-findings.jsonl",
    "plan": OUT / "remediation-plan.json",
    "history": OUT / "history.jsonl",
    "summary": OUT / "summary.json",
}
HUMAN_OUTPUTS = {
    "claim_delta": ROOT / "RESULTS/CLAIM-DELTA.md",
    "impact": ROOT / "RESULTS/IMPACT-ANALYSIS.md",
    "lineage": ROOT / "RESULTS/EVIDENCE-LINEAGE.md",
    "audit": ROOT / "RESULTS/SELF-CORRECTION-AUDIT.md",
}

RULES = (
    "proof_obligation",
    "empirical_obligation",
    "cross_domain_mapping",
    "quantifier_inflation",
    "circular_reasoning",
    "analogy_as_isomorphism",
    "model_failure_to_universal_impossibility",
    "conclusion_rebound",
    "hidden_essential_content",
    "retired_pages_surface",
)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(data: bytes | None) -> str | None:
    return hashlib.sha256(data).hexdigest() if data is not None else None


def git_bytes(ref: str, path: str) -> bytes | None:
    result = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True)
    return result.stdout if result.returncode == 0 else None


def tracked_and_untracked() -> set[str]:
    raw = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT)
    return {item.decode("utf-8") for item in raw.split(b"\0") if item}


def changed_paths(base: str) -> list[str]:
    raw = subprocess.check_output(["git", "diff", "--name-only", "-z", base, "--"], cwd=ROOT)
    changed = {item.decode("utf-8") for item in raw.split(b"\0") if item}
    current = tracked_and_untracked()
    base_files = set(
        subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "-z", base], cwd=ROOT)
        .decode("utf-8")
        .split("\0")
    )
    changed.update(current - base_files)
    return sorted(path for path in changed if path)


def is_knowledge_path(path: str, config: dict) -> bool:
    if any(path == item or path.startswith(item) for item in config["generated_exclusions"]):
        return False
    return any(path == prefix or path.startswith(prefix) for prefix in config["knowledge_prefixes"])


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def claim_index() -> tuple[dict[str, list[str]], dict[str, dict]]:
    by_path: dict[str, list[str]] = {}
    claims: dict[str, dict] = {}
    for row in load_jsonl(CLAIM_REGISTRY):
        cid = row["canonical_id"]
        claims[cid] = row
        for anchor in row.get("source_anchors", []):
            by_path.setdefault(anchor["path"], []).append(cid)
    return {path: sorted(set(ids)) for path, ids in by_path.items()}, claims


def build_delta(config: dict) -> list[dict]:
    base = config["source_base_commit"]
    by_path, _ = claim_index()
    rows = []
    for path in changed_paths(base):
        if not is_knowledge_path(path, config):
            continue
        before = git_bytes(base, path)
        current_path = ROOT / path
        after = current_path.read_bytes() if current_path.is_file() else None
        status = "ADDED" if before is None else "DELETED" if after is None else "MODIFIED"
        record = {
            "delta_id": "CD-" + hashlib.sha256(path.encode()).hexdigest()[:16].upper(),
            "path": path,
            "status": status,
            "before_sha256": sha(before),
            "after_sha256": sha(after),
            "linked_claim_ids": by_path.get(path, []),
            "human_result_required": True,
            "source_base_commit": base,
            "claim_ceiling": "Repository change and linked-registry scope only; no truth or maturity upgrade.",
        }
        record["record_sha256"] = hashlib.sha256(canonical_json(record).encode()).hexdigest()
        rows.append(record)
    return rows


def dependency_maps() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    outgoing: dict[str, set[str]] = {}
    incoming: dict[str, set[str]] = {}
    for row in load_jsonl(DEPENDENCY_GRAPH):
        cid = row["canonical_id"]
        outgoing.setdefault(cid, set()).update(item.get("to") for item in row.get("outgoing", []) if item.get("to"))
        incoming.setdefault(cid, set()).update(row.get("incoming_claims", []))
    return outgoing, incoming


def closure(seeds: list[str], outgoing: dict[str, set[str]], incoming: dict[str, set[str]]) -> list[str]:
    seen = set(seeds)
    queue = deque(seeds)
    while queue:
        cid = queue.popleft()
        for other in outgoing.get(cid, set()) | incoming.get(cid, set()):
            if other not in seen:
                seen.add(other)
                queue.append(other)
    return sorted(seen - set(seeds))


def build_impact(delta: list[dict]) -> list[dict]:
    outgoing, incoming = dependency_maps()
    rows = []
    for item in delta:
        seeds = item["linked_claim_ids"]
        affected = closure(seeds, outgoing, incoming)
        rows.append(
            {
                "impact_id": "IA-" + item["delta_id"].removeprefix("CD-"),
                "delta_id": item["delta_id"],
                "path": item["path"],
                "direct_claim_ids": seeds,
                "transitively_affected_claim_ids": affected,
                "direct_claim_count": len(seeds),
                "transitive_claim_count": len(affected),
                "propagation_basis": "Task 100 canonical dependency graph, traversed in both dependency directions.",
                "unresolved_if_empty": not seeds,
                "claim_ceiling": "Repository dependency impact only; graph reachability is not real-world causation.",
            }
        )
    return rows


def build_lineage(delta: list[dict]) -> list[dict]:
    evidence = {row["canonical_id"]: row for row in load_jsonl(EVIDENCE_LINEAGE)}
    claims = sorted({cid for item in delta for cid in item["linked_claim_ids"]})
    return [
        {
            "canonical_id": cid,
            "delta_status": "SOURCE_ASSET_CHANGED",
            "source_evidence": evidence.get(cid, {}).get("source_evidence", []),
            "external_evidence_status": evidence.get(cid, {}).get("external_evidence_status", "NO_LINEAGE_RECORD"),
            "replication_status": evidence.get(cid, {}).get("replication_status", "NOT_RECORDED"),
            "limitation": "Source change triggers re-review; provenance alone does not establish truth, novelty, causation, prediction or replication.",
        }
        for cid in claims
    ]


def negated_or_governed(line: str) -> bool:
    return bool(re.search(r"未证明|没有|不能|不得|并非|撤回|纠正|阻断|风险|旧说法|开放|只表示|不等于|不推出|禁止|不是|尚未|未完成", line, re.I))


def analyze_text(path: str, text: str) -> list[dict]:
    matches: dict[str, list[dict]] = {rule: [] for rule in RULES}
    for number, line in enumerate(text.splitlines(), 1):
        compact = line.strip()
        if not compact:
            continue
        governed = negated_or_governed(compact)
        checks = {
            "proof_obligation": bool(re.search(r"定理|已证明|必然|theorem|proved", compact, re.I)),
            "empirical_obligation": bool(re.search(r"已验证|证实|真实因果|实验表明|validated|verified empirically", compact, re.I)),
            "cross_domain_mapping": bool(re.search(r"跨域|物理.*社会|社会.*物理|意识.*量子|量子.*意识", compact, re.I)),
            "quantifier_inflation": bool(re.search(r"所有|任何|必然|永远|普遍|唯一|all |every |impossible", compact, re.I)),
            "circular_reasoning": bool(re.search(r"因为(.{2,24})，?所以\1", compact)),
            "analogy_as_isomorphism": bool(re.search(r"类比.{0,12}(?:就是|等于|证明).{0,12}同构|相似.{0,12}同构", compact)),
            "model_failure_to_universal_impossibility": bool(re.search(r"模型.{0,24}(?:失败|不成立).{0,24}(?:所有|任何|普遍).{0,12}不可能", compact)),
            "conclusion_rebound": bool(re.search(r"(?:大一统|四力统一).{0,24}(?:已被证明不可能|普遍不可能|不可能定理)", compact)),
            "hidden_essential_content": "<details" in compact.lower(),
            "retired_pages_surface": bool(re.search(r"arvin-liu\.github\.io/when-systems-catch-fire|\.github/workflows/pages\.yml|pages/system-map\.html", compact, re.I)),
        }
        for rule, hit in checks.items():
            if hit:
                severity = "BLOCK" if rule in {"hidden_essential_content", "retired_pages_surface"} else "REVIEW"
                if governed and rule not in {"hidden_essential_content", "retired_pages_surface"}:
                    severity = "BOUNDED_REFERENCE"
                matches[rule].append({"path": path, "line": number, "severity": severity, "excerpt": compact[:240]})
    return [
        {
            "rule_id": rule,
            "status": "BLOCK" if any(item["severity"] == "BLOCK" for item in items) else "REVIEW" if any(item["severity"] == "REVIEW" for item in items) else "PASS",
            "matches": items,
            "scope": "Changed public human-readable knowledge surfaces only; heuristic findings require bounded review.",
        }
        for rule, items in matches.items()
    ]


def build_findings(config: dict) -> list[dict]:
    aggregate: dict[str, dict] = {rule: {"rule_id": rule, "status": "PASS", "matches": [], "scope": "Changed public human-readable knowledge surfaces only; heuristic findings require bounded review."} for rule in RULES}
    for path in config["public_human_surfaces"]:
        source = ROOT / path
        if not source.is_file():
            continue
        for finding in analyze_text(path, source.read_text(encoding="utf-8")):
            aggregate[finding["rule_id"]]["matches"].extend(finding["matches"])
    for finding in aggregate.values():
        severities = {item["severity"] for item in finding["matches"]}
        finding["status"] = "BLOCK" if "BLOCK" in severities else "REVIEW" if "REVIEW" in severities else "PASS"
    return [aggregate[rule] for rule in RULES]


def render_delta(rows: list[dict]) -> str:
    lines = ["# Claim Delta", "", f"本轮识别 {len(rows)} 个新增、删除或修改的知识资产。关联断言来自现行 claim registry；无关联项必须人工确认是否需要新增登记。", ""]
    for row in rows:
        lines.extend([f"## `{row['path']}`", "", f"- 状态：`{row['status']}`", f"- Delta：`{row['delta_id']}`", f"- 关联断言：{row['linked_claim_ids'][:20] or ['NONE_DISCOVERED']}" + ("（仅显示前 20 项）" if len(row['linked_claim_ids']) > 20 else ""), f"- 人类结果义务：`{row['human_result_required']}`", f"- 边界：{row['claim_ceiling']}", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_impact(rows: list[dict]) -> str:
    lines = ["# 影响分析", "", "影响沿任务 100 依赖图双向计算，只代表仓库依赖与复核范围，不代表现实因果。", "", "|资产|直接断言|传递影响|是否需人工建边|", "|---|---:|---:|---|"]
    for row in rows:
        lines.append(f"|`{row['path']}`|{row['direct_claim_count']}|{row['transitive_claim_count']}|{'是' if row['unresolved_if_empty'] else '否'}|")
    return "\n".join(lines) + "\n"


def render_lineage(rows: list[dict]) -> str:
    lines = ["# 证据谱系变化", "", f"共有 {len(rows)} 个已登记断言的来源资产在本轮发生变化。来源变化触发复核，不自动改变真值、成熟度或复现状态。", "", "|断言|外部证据状态|复现状态|来源证据数|", "|---|---|---|---:|"]
    for row in rows:
        lines.append(f"|`{row['canonical_id']}`|`{row['external_evidence_status']}`|`{row['replication_status']}`|{len(row['source_evidence'])}|")
    return "\n".join(lines) + "\n"


def render_audit(findings: list[dict], plan: dict) -> str:
    lines = ["# 自我纠错审计", "", "规则是仓库启发式和结构门禁，不是外部真理裁判。`BLOCK` 阻止 CI；`REVIEW` 要求人工核对；受边界说明保护的历史/纠正性提及不作为回弹。", "", "|规则|状态|匹配数|", "|---|---|---:|"]
    for row in findings:
        lines.append(f"|`{row['rule_id']}`|`{row['status']}`|{len(row['matches'])}|")
    lines.extend(["", "## 整改计划", ""])
    if plan["actions"]:
        for action in plan["actions"]:
            lines.append(f"- `{action['rule_id']}`：{action['action']}（{action['status']}）")
    else:
        lines.append("- 无阻断项；保留 REVIEW 项供精确 Head 人工审查。")
    lines.extend(["", "## 历史保留", "", "撤回、降级、隔离与修订通过 Git 历史、现行 supersession lineage 和本目录 `history.jsonl` 追加记录保留；生成器不删除历史证据，也不改写 Git 历史。", ""])
    return "\n".join(lines)


def build() -> tuple[dict[Path, str], dict]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    delta = build_delta(config)
    impact = build_impact(delta)
    lineage = build_lineage(delta)
    for rows, schema_path in (
        (delta, "schemas/governance/claim-delta.schema.json"),
        (impact, "schemas/governance/impact-analysis.schema.json"),
        (lineage, "schemas/governance/evidence-lineage-delta.schema.json"),
    ):
        schema = json.loads((ROOT / schema_path).read_text(encoding="utf-8"))
        for row in rows:
            jsonschema.validate(row, schema)
    findings = build_findings(config)
    actions = [
        {"rule_id": row["rule_id"], "status": "OPEN", "action": "Remove or bound every blocking match, regenerate products, and rerun exact-head validation."}
        for row in findings
        if row["status"] == "BLOCK"
    ]
    plan = {"schema_version": "1.0.0", "task_id": config["task_id"], "generated_from": "audit-findings.jsonl", "blocker_count": len(actions), "actions": actions}
    history = [
        {
            "history_id": "HIST-" + row["delta_id"].removeprefix("CD-"),
            "path": row["path"],
            "event": row["status"],
            "source_base_commit": config["source_base_commit"],
            "evaluated_at": config["evaluated_at"],
            "history_policy": "Append through future commits; never delete source evidence or rewrite Git history.",
        }
        for row in delta
    ]
    summary = {
        "schema_version": "1.0.0",
        "task_id": config["task_id"],
        "source_base_commit": config["source_base_commit"],
        "knowledge_asset_deltas": len(delta),
        "linked_claims": len({cid for row in delta for cid in row["linked_claim_ids"]}),
        "impact_records": len(impact),
        "evidence_lineage_records": len(lineage),
        "audit_rules": len(findings),
        "blocking_rules": sum(row["status"] == "BLOCK" for row in findings),
        "review_rules": sum(row["status"] == "REVIEW" for row in findings),
        "machine_human_pairing_required": True,
        "claim_ceiling": "Automated repository governance only; no external truth adjudication.",
    }
    products = {
        MACHINE_OUTPUTS["claim_delta"]: "".join(canonical_json(row) + "\n" for row in delta),
        MACHINE_OUTPUTS["impact"]: "".join(canonical_json(row) + "\n" for row in impact),
        MACHINE_OUTPUTS["lineage"]: "".join(canonical_json(row) + "\n" for row in lineage),
        MACHINE_OUTPUTS["findings"]: "".join(canonical_json(row) + "\n" for row in findings),
        MACHINE_OUTPUTS["plan"]: json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        MACHINE_OUTPUTS["history"]: "".join(canonical_json(row) + "\n" for row in history),
        MACHINE_OUTPUTS["summary"]: json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        HUMAN_OUTPUTS["claim_delta"]: render_delta(delta),
        HUMAN_OUTPUTS["impact"]: render_impact(impact),
        HUMAN_OUTPUTS["lineage"]: render_lineage(lineage),
        HUMAN_OUTPUTS["audit"]: render_audit(findings, plan),
    }
    return products, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    products, summary = build()
    if args.check:
        drift = [str(path.relative_to(ROOT)) for path, content in products.items() if not path.is_file() or path.read_text(encoding="utf-8") != content]
        if drift:
            raise SystemExit("SELF_CORRECTION_OUTPUT_DRIFT: " + ", ".join(drift))
    else:
        for path, content in products.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if summary["blocking_rules"]:
        raise SystemExit(f"SELF_CORRECTION_BLOCKED rules={summary['blocking_rules']}")
    print(f"SELF_CORRECTION_OK deltas={summary['knowledge_asset_deltas']} rules={summary['audit_rules']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
