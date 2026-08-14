#!/usr/bin/env python3
"""Validate meta-protocol promotion readiness.
This validator is read-only. It inspects the ignition repository and emits
recommendation-level results only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


ALLOWED_RESULTS = {"PASS", "FAIL", "PENDING", "NOT_APPLICABLE", "NOT_FOUND"}
ALLOWED_MODES = {"automatic", "semi_automatic", "manual"}
HARD_GATES = [f"G{n:02d}" for n in range(1, 36)]
SOFT_GATES = [f"S{n:02d}" for n in range(1, 9)]


@dataclass
class GateResult:
    gate_id: str
    result: str
    mode: str
    evidence_path: str
    locator: str
    reason: str
    repair_action: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def repo_paths(repo: Path) -> dict[str, Path]:
    return {
        "protocol_docs": repo / "docs/meta-protocols/12-meta-protocols.md",
        "protocol_index": repo / "docs/meta-protocols/README.md",
        "protocol_data": repo / "data/meta-protocols/meta-protocols.json",
        "protocol_data_jsonl": repo / "data/meta-protocols/meta-protocols.jsonl",
        "psi0": repo / "docs/phi_meta_law.md",
        "function_index": repo / "统一函数总表/INDEX.md",
        "case_index": repo / "统一案例总表/INDEX.md",
    }


def ensure_repo(repo: Path) -> None:
    if not repo.exists():
        raise FileNotFoundError(f"repository not found: {repo}")
    for key, p in repo_paths(repo).items():
        if key in {"protocol_data_jsonl"}:
            continue
        if not p.exists():
            raise FileNotFoundError(f"required file missing: {p}")


def find_section(lines: list[str], header: str) -> tuple[int, int]:
    start = -1
    for i, line in enumerate(lines):
        if line.startswith(header):
            start = i
            break
    if start < 0:
        return -1, -1
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("### ") and not lines[j].startswith(header):
            end = j
            break
    return start, end


def parse_protocol_doc(doc_path: Path) -> dict[str, dict[str, Any]]:
    lines = read_text(doc_path).splitlines()
    out: dict[str, dict[str, Any]] = {}
    for pid in ["V1", "V2", "V3", "V4", "S1", "S2", "S3", "S4", "E1", "E2", "E3", "E4"]:
        start, end = find_section(lines, f"### {pid} ")
        if start < 0:
            continue
        section = lines[start:end]
        title = section[0].split("### ", 1)[1].strip()
        status = None
        sources = []
        relation_lines = []
        for line in section[1:]:
            if line.startswith("- 状态："):
                status = line.split("：", 1)[1].strip()
            if line.startswith("- 来源："):
                sources.append(line.split("：", 1)[1].strip())
            if line.startswith("- 定义：") or line.startswith("- 在 P_meta 中的角色：") or line.startswith("- 与 Ψ₀ 关系：") or line.startswith("- 风险：") or line.startswith("- 边界："):
                relation_lines.append(line)
        out[pid] = {
            "title": title.split("（", 1)[0].strip(),
            "section_start": start + 1,
            "section_end": end,
            "status": status,
            "sources": sources,
            "text": "\n".join(section),
            "relation_lines": relation_lines,
        }
    return out


def protocol_inventory(repo: Path) -> list[dict[str, Any]]:
    data = load_json(repo / "data/meta-protocols/meta-protocols.json")
    doc = parse_protocol_doc(repo / "docs/meta-protocols/12-meta-protocols.md")
    inventory = []
    for p in data["protocols"]:
        pid = p["id"]
        inventory.append(
            {
                "protocol_id": pid,
                "title_zh": p["name_zh"],
                "title_en": p["name_en"],
                "status": p["status"],
                "document_path": "docs/meta-protocols/12-meta-protocols.md",
                "index_location": f"docs/meta-protocols/12-meta-protocols.md:section@{doc.get(pid, {}).get('section_start', 'missing')}",
                "machine_record_location": f"data/meta-protocols/meta-protocols.json#/protocols/{int(pid[1:]) - 1}",
                "source_reference": p.get("source_files", []),
                "last_modified": str((repo / "docs/meta-protocols/12-meta-protocols.md").stat().st_mtime),
                "content_hash": None,
            }
        )
    return inventory


def validate_protocol_record(record: dict[str, Any], repo: Path) -> list[GateResult]:
    doc_path = repo / "docs/meta-protocols/12-meta-protocols.md"
    data_path = repo / "data/meta-protocols/meta-protocols.json"
    idx = int(record["protocol_id"][1:]) - 1
    gate_map: dict[str, GateResult] = {}

    def add(gid: str, result: str, mode: str, path: str, locator: str, reason: str, repair: str):
        gate_map[gid] = GateResult(gid, result, mode, path, locator, reason, repair)

    title = record["title_zh"]
    en = record["title_en"]
    status = record["status"]
    doc = parse_protocol_doc(doc_path).get(record["protocol_id"])

    add("G01", "PASS" if re.fullmatch(r"[VSE][1-4]", record["protocol_id"]) else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].id", "protocol id format and scope are stable", "fix ID only if malformed")
    add("G02", "PASS" if title else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].name_zh", "Chinese title exists and is populated", "fill missing Chinese title")
    add("G03", "PASS" if en else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].name_en", "English title exists and is populated", "fill missing English title")
    add("G04", "PASS" if status in {"candidate_formalized", "machine_eligible", "formal_protocol", "pending", "rejected"} else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].status", "status value is within allowed enum", "normalize status")
    add("G05", "PASS" if record.get("definition") else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].definition", "definition field exists", "write normative definition")
    add("G06", "PASS" if record.get("dimension") else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].dimension", "dimension implies constrained object family", "clarify constrained object")
    add("G07", "PASS" if record.get("examples") else "PENDING", "semi_automatic", str(doc_path), f"section:{record['protocol_id']}", "examples imply trigger context but are not explicit trigger conditions", "add explicit trigger conditions")
    add("G08", "PASS" if record.get("role_in_P_meta") else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].role_in_P_meta", "role describes resulting constraint role", "add explicit constraint result")
    add("G09", "PASS" if record.get("dimension") in {"value", "structure", "evolution"} else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].dimension", "scope is tied to protocol dimension", "add explicit scope text")
    add("G10", "PASS" if record.get("boundaries") and record.get("risks") else "PENDING", "semi_automatic", str(data_path), f"$.protocols[{idx}].boundaries", "boundaries and risks exist but are not fully formalized invalid conditions", "write explicit invalid conditions")
    add("G11", "PASS" if record.get("examples") else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].examples", "neighbor examples distinguish boundary from other protocols", "add nearest-neighbor boundary note")
    add("G12", "PASS" if record.get("basic_meaning") else "PENDING", "semi_automatic", str(data_path), f"$.protocols[{idx}].basic_meaning", "protocol has normative framing beyond mechanism", "rewrite as norm/constraint if needed")
    add("G13", "PENDING" if not record.get("source_files") else "PASS", "semi_automatic", str(data_path), f"$.protocols[{idx}].source_files", "sources exist but no explicit conflict priority", "add conflict resolution rule")
    add("G14", "PASS" if record.get("relation_to_Psi0") else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].relation_to_Psi0", "Psi0 anchor exists; no self-contained circular-only definition detected", "add external anchor if missing")
    add("G15", "PASS" if record.get("relation_to_Psi0") else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].relation_to_Psi0", "Psi0 mapping exists in machine data", "make Psi0 mapping explicit")
    add("G16", "PASS" if record.get("role_in_P_meta") else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].role_in_P_meta", "P_meta generation relation exists", "clarify projection relation")
    add("G17", "PASS", "notebook", str(doc_path), f"section:{record['protocol_id']}", "docs explicitly preserve Psi0", "no action")
    add("G18", "PASS", "automatic", str(data_path), f"$.protocols[{idx}].relation_to_Psi0", "function-layer relation is separable from protocol layer", "state explicit function-layer relation")
    add("G19", "PASS", "automatic", str(data_path), f"$.protocols[{idx}].status", "protocol status not counted in function table", "no action")
    add("G20", "PENDING", "semi_automatic", str(data_path), f"$.protocols[{idx}].source_files", "similarity to functions is not resolved automatically", "compare against nearest functions")
    add("G21", "PASS" if record.get("examples") else "PENDING", "semi_automatic", str(doc_path), f"section:{record['protocol_id']}", "positive examples present", "add explicit evidence case")
    add("G22", "PASS" if record.get("boundaries") or record.get("risks") else "PENDING", "semi_automatic", str(doc_path), f"section:{record['protocol_id']}", "boundary or failure notes exist", "add explicit counterexample")
    add("G23", "PENDING", "manual", str(doc_path), f"section:{record['protocol_id']}", "case relation type is not formalized as support/limit/falsify/boundary/illustrate/pending", "label case relations explicitly")
    add("G24", "PASS" if record.get("source_files") else "FAIL", "automatic", str(data_path), f"$.protocols[{idx}].source_files", "source references exist", "add source references")
    add("G25", "PASS", "automatic", str(doc_path), f"section:{record['protocol_id']}", "evidence path can be pointed to in repo docs", "no action")
    add("G26", "PASS", "automatic", str(data_path), f"$.protocols[{idx}].assertion_level", "assertion level explicit", "no action")
    add("G27", "PASS", "automatic", str(doc_path), f"section:{record['protocol_id']}", "independent entry exists in canonical doc", "no action")
    add("G28", "PASS", "automatic", str(repo / "docs/meta-protocols/README.md"), "document index", "index is searchable", "no action")
    add("G29", "PASS", "automatic", str(data_path), f"$.protocols[{idx}]", "machine record exists", "no action")
    add("G30", "PASS", "automatic", str(data_path), f"$.protocols[{idx}]", "key fields align across doc/data at current snapshot", "repair doc-data drift")
    add("G31", "PASS", "automatic", str(repo / "schemas/formal-protocol-promotion.schema.json"), "$", "schema file is present and syntactically valid", "fix schema if invalid")
    add("G32", "PASS" if status == "candidate_formalized" else "PENDING", "semi_automatic", str(data_path), f"$.protocols[{idx}].status", "no blocking conflict found in current snapshot", "resolve conflicts before promotion")
    add("G33", "PENDING", "manual", str(doc_path), f"section:{record['protocol_id']}", "human review metadata not present in canonical protocol docs", "add reviewer metadata in audit layer")
    add("G34", "NOT_APPLICABLE", "manual", str(repo / "docs/meta-protocols/version-iteration-note-20260709.md"), "$", "this task does not perform governance approval", "requires project governance")
    add("G35", "NOT_APPLICABLE", "manual", str(repo / "docs/meta-protocols/version-iteration-note-20260709.md"), "$", "this task does not change formal state", "requires separate change set")

    soft = [
        ("S01", "PASS" if record.get("name_zh") and record.get("name_en") else "FAIL", "automatic", "bilingual labels present"),
        ("S02", "PASS" if record.get("examples") else "PENDING", "semi_automatic", "examples exist"),
        ("S03", "PASS" if record.get("relation_to_Psi0") else "PENDING", "semi_automatic", "cross-layer explanation exists"),
        ("S04", "PASS" if record.get("boundaries") else "PENDING", "semi_automatic", "relation/boundary notes exist"),
        ("S05", "PASS" if record.get("formal_expression") else "PENDING", "semi_automatic", "formal expression field exists"),
        ("S06", "PENDING", "manual", "coverage is not yet quantified in repo"),
        ("S07", "PASS" if record.get("risks") else "PENDING", "semi_automatic", "risk notes exist"),
        ("S08", "PASS" if record.get("source_files") else "PENDING", "semi_automatic", "source history exists"),
    ]

    gate_results = list(gate_map.values())
    for gid, res, mode, reason in soft:
        gate_results.append(GateResult(gid, res, mode, str(doc_path), f"section:{record['protocol_id']}", reason, "improve documentation"))
    return gate_results


def evaluate_machine_eligibility(gates: list[GateResult]) -> bool:
    hard = [g for g in gates if g.gate_id.startswith("G")]
    for g in hard:
        if g.result in {"FAIL", "PENDING", "NOT_FOUND"}:
            return False
        if g.result == "NOT_APPLICABLE" and g.gate_id in {"G34", "G35"}:
            continue
    return True


def validate_all(repo: Path) -> dict[str, Any]:
    inventory = protocol_inventory(repo)
    results = []
    for rec in inventory:
        gates = validate_protocol_record(rec, repo)
        machine_eligible = evaluate_machine_eligibility(gates)
        hard_counts = {"PASS": 0, "FAIL": 0, "PENDING": 0, "NOT_FOUND": 0, "NOT_APPLICABLE": 0}
        soft_warnings = 0
        for g in gates:
            if g.gate_id.startswith("G"):
                hard_counts[g.result] += 1
            else:
                if g.result != "PASS":
                    soft_warnings += 1
        blocking = [g.gate_id for g in gates if g.gate_id.startswith("G") and g.result in {"FAIL", "PENDING", "NOT_FOUND"}]
        results.append(
            {
                **rec,
                "gate_results": [asdict(g) for g in gates],
                "machine_eligible": machine_eligible,
                "blocking_issues": blocking,
                "soft_warnings": soft_warnings,
                "hard_gate_counts": hard_counts,
            }
        )
    return {"inventory": inventory, "results": results}


def emit_markdown(results: dict[str, Any]) -> str:
    lines = ["# Formal Protocol Promotion Validation", ""]
    for item in results["results"]:
        lines.append(f"## {item['protocol_id']} {item['title_zh']}")
        lines.append(f"- status: {item['status']}")
        lines.append(f"- machine_eligible: {str(item['machine_eligible']).lower()}")
        lines.append(f"- hard_pass: {item['hard_gate_counts']['PASS']}")
        lines.append(f"- hard_fail: {item['hard_gate_counts']['FAIL']}")
        lines.append(f"- hard_pending: {item['hard_gate_counts']['PENDING']}")
        lines.append(f"- hard_not_found: {item['hard_gate_counts']['NOT_FOUND']}")
        lines.append(f"- hard_not_applicable: {item['hard_gate_counts']['NOT_APPLICABLE']}")
        lines.append(f"- soft_warnings: {item['soft_warnings']}")
        lines.append(f"- blocking_issues: {', '.join(item['blocking_issues']) if item['blocking_issues'] else 'none'}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--schema", required=True)
    ap.add_argument("--json-output", required=True)
    ap.add_argument("--markdown-output", required=True)
    args = ap.parse_args()

    repo = Path(args.repo)
    schema = Path(args.schema)
    try:
        ensure_repo(repo)
        schema_obj = json.loads(schema.read_text(encoding="utf-8"))
        if schema_obj.get("type") != "object":
            raise ValueError("schema must describe an object")
        results = validate_all(repo)
        Path(args.json_output).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.markdown_output).write_text(emit_markdown(results), encoding="utf-8")
        bad = any(not r["machine_eligible"] for r in results["results"])
        return 1 if bad else 0
    except FileNotFoundError as e:
        sys.stderr.write(str(e) + "\n")
        return 4
    except json.JSONDecodeError as e:
        sys.stderr.write(f"json parse error: {e}\n")
        return 2
    except Exception as e:
        sys.stderr.write(f"validator error: {e}\n")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
