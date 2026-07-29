#!/usr/bin/env python3
"""Build the deterministic, non-authoritative historical function-asset census.

The scanner discovers tracked textual assets. Existing foundation adjudications
remain authoritative; automatic identity labels are candidates. Task 98
corrections are the only human-authoritative overlay consumed by this builder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/foundation/function-assets"
TEXT_EXTENSIONS = {
    ".md", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".py", ".sage",
    ".lean", ".js", ".jsx", ".ts", ".tsx", ".toml", ".txt", ".rst",
}
EXPLICIT_ID = re.compile(r"(?<![A-Za-z0-9_])(?:MF|D|T|M|Y|A|P)\d+(?![A-Za-z0-9_])")
NAMED_ASSET = re.compile(
    r"(函数|方程|定理|公式|定律|算子|门控|门函数|评分|指数|比率|内核|度量|概率|能量|力|模型|判定器|"
    r"function|equation|theorem|formula|law|operator|gate|score|index|ratio|kernel|metric|probability|energy|force|model|classifier)",
    re.I,
)
CODE_ASSET = re.compile(
    r"^\s*(?:(?:async\s+)?def\s+[A-Za-z_]\w*\s*\(|theorem\s+[A-Za-z_]\w*|def\s+[A-Za-z_]\w*|"
    r"function\s+[A-Za-z_$][\w$]*\s*\(|(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*=.*=>)",
)
EXPRESSION_ASSET = re.compile(
    r"(?:[A-Za-zΑ-Ωα-ωΨΦΩΣ][\wΑ-Ωα-ω]*\s*\([^)]{0,120}\)\s*=|[ΨΦΩΣ]\s*=|"
    r"\\int\b|∫|\b(?:argmax|argmin|lim)\b|d[A-Za-zΑ-Ωα-ω]+/d[A-Za-zΑ-Ωα-ω]+)",
    re.I,
)
GENERATED_PREFIX = "data/foundation/function-assets/"
SCANNER_VERSION = "2.0.0"
SNAPSHOT = "function-census-v2-20260729"
GATES = (
    "definition_gate", "dimension_and_type_gate", "counterexample_gate",
    "circular_reasoning_gate", "claim_layer_gate", "claim_ceiling_gate",
    "cross_domain_isomorphism_gate", "universal_quantifier_gate",
    "internal_test_truth_gate", "dependency_impact_gate",
)


def read_jsonl(relative: str) -> list[dict]:
    path = ROOT / relative
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def tracked_text_files() -> list[str]:
    raw = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8")
    return sorted(
        item for item in raw.split("\0")
        if item and not item.startswith(GENERATED_PREFIX) and Path(item).suffix.lower() in TEXT_EXTENSIONS
    )


def implicit_candidate(relative: str, line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 2000 or EXPLICIT_ID.search(stripped):
        return False
    if CODE_ASSET.search(line):
        return True
    if EXPRESSION_ASSET.search(stripped) and ("=" in stripped or relative.endswith((".lean", ".sage"))):
        return True
    if not NAMED_ASSET.search(stripped):
        return False
    if relative.endswith((".md", ".rst")) and stripped.startswith("#"):
        return True
    return bool(re.match(r"^[\-\*]?\s*[\"']?(?:name|title|名称|标题)[\"']?\s*[:：]", stripped, re.I))


def candidate_identity(obj: dict) -> str:
    kind = obj.get("formal_object_type", "")
    mapping = {
        "FUNCTION": "STRICT_MATHEMATICAL_FUNCTION",
        "PARTIAL_FUNCTION": "STRICT_MATHEMATICAL_FUNCTION",
        "PREDICATE": "GATE_OR_DECISION_RULE",
        "STATE_TRANSITION": "ALGORITHM_OR_WORKFLOW",
        "ALGORITHM": "ALGORITHM_OR_WORKFLOW",
        "OPERATOR": "ALGORITHM_OR_WORKFLOW",
        "RELATION": "RELATION_OR_CONSTRAINT",
        "ORDER": "RELATION_OR_CONSTRAINT",
        "METRIC": "SCORE_OR_INDEX",
        "OPTIMIZATION_PROBLEM": "PARAMETRIC_MODEL",
        "CAUSAL_MODEL": "PARAMETRIC_MODEL",
        "PROBABILISTIC_MODEL": "PARAMETRIC_MODEL",
        "MECHANISM_MODEL": "PARAMETRIC_MODEL",
        "ARGUMENT_SCHEMA": "HEURISTIC",
        "FORMAL_PROPOSITION": "CONJECTURE_OR_PENDING_CLAIM",
        "NATURAL_LANGUAGE_CANDIDATE": "CONJECTURE_OR_PENDING_CLAIM",
    }
    return mapping.get(kind, "INVALID_OR_PSEUDO_FUNCTION")


def maturity(obj: dict) -> str:
    status = obj.get("status", {})
    if status.get("proof_status") == "PROVED":
        return "M6"
    if status.get("formal_status") == "WELL_TYPED":
        return "M3"
    if obj.get("domain") not in (None, "", "UNSPECIFIED_IN_SOURCE") and obj.get("codomain_or_target_type"):
        return "M2"
    if obj.get("formal_expression_or_ast") or obj.get("original_natural_language_claim"):
        return "M1"
    return "M0"


def evidence_axis(obj: dict) -> str:
    value = obj.get("status", {}).get("evidence_status", "")
    if value in {"EXTERNALLY_REPLICATED", "MULTI_PARTY_CONFIRMED"}:
        return "E7"
    if value in {"PEER_REVIEWED"}:
        return "E6"
    if value in {"EXTERNAL_DATA_REPLICATED"}:
        return "E5"
    if value in {"INTERNAL_DATA_TESTED"}:
        return "E4"
    if value in {"TESTABLE_OPERATIONALIZATION"}:
        return "E3"
    return "E0"


def sha_payload(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generic_gates(obj: dict, dependencies: list[str]) -> dict[str, str]:
    typed = obj.get("domain") not in (None, "", "UNSPECIFIED_IN_SOURCE") and bool(obj.get("codomain_or_target_type"))
    return {
        "definition_gate": "PASS" if typed else "REQUIRES_HUMAN_REVIEW",
        "dimension_and_type_gate": "REQUIRES_HUMAN_REVIEW",
        "counterexample_gate": "PASS" if obj.get("known_counterexamples") else "REQUIRES_HUMAN_REVIEW",
        "circular_reasoning_gate": "REQUIRES_HUMAN_REVIEW",
        "claim_layer_gate": "REQUIRES_HUMAN_REVIEW",
        "claim_ceiling_gate": "REQUIRES_HUMAN_REVIEW",
        "cross_domain_isomorphism_gate": "REQUIRES_HUMAN_REVIEW",
        "universal_quantifier_gate": "REQUIRES_HUMAN_REVIEW",
        "internal_test_truth_gate": "REQUIRES_HUMAN_REVIEW",
        "dependency_impact_gate": "REQUIRES_HUMAN_REVIEW" if dependencies else "NOT_APPLICABLE",
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


def build(destination: Path) -> dict:
    objects = {row["id"]: row for row in read_jsonl("data/foundation/formal-objects/objects.jsonl")}
    corrections = {}
    for row in read_jsonl("data/foundation/function-assets/corrections.jsonl"):
        stable_id = row.get("stable_id") or row["correction_id"].removeprefix("CORR-98-")
        row["stable_id"] = stable_id
        corrections[stable_id] = row
    files = tracked_text_files()
    occurrences: dict[str, list[dict]] = defaultdict(list)
    implicit: dict[str, dict] = {}
    explicit_ids: set[str] = set()

    for relative in files:
        try:
            lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        per_id: dict[str, list[int]] = defaultdict(list)
        for number, line in enumerate(lines, 1):
            for asset_id in sorted(set(EXPLICIT_ID.findall(line))):
                per_id[asset_id].append(number)
                explicit_ids.add(asset_id)
            if implicit_candidate(relative, line):
                normalized = re.sub(r"\s+", " ", line.strip())
                stable_id = "IMPLICIT-" + hashlib.sha256(f"{relative}\0{normalized}".encode()).hexdigest()[:16].upper()
                implicit[stable_id] = {"stable_id": stable_id, "path": relative, "line": number, "text": normalized}
        for asset_id, line_numbers in sorted(per_id.items()):
            occurrences[asset_id].append({
                "stable_id": asset_id,
                "path": relative,
                "first_line": min(line_numbers),
                "last_line": max(line_numbers),
                "mention_count": len(line_numbers),
                "role": "DEFINITION" if relative in objects.get(asset_id, {}).get("source_paths", []) else "REFERENCE",
            })

    discovery = [item for asset_id in sorted(occurrences) for item in occurrences[asset_id]]
    discovery.extend({**row, "mention_count": 1, "last_line": row["line"], "first_line": row["line"], "role": "IMPLICIT_CANDIDATE"} for row in implicit.values())
    discovery.sort(key=lambda row: (row["stable_id"], row["path"], row["first_line"]))

    census: list[dict] = []
    all_ids = sorted(set(objects) | explicit_ids | set(implicit))
    for asset_id in all_ids:
        obj = objects.get(asset_id, {})
        corr = corrections.get(asset_id)
        occ = occurrences.get(asset_id, [])
        if asset_id in implicit:
            row = implicit[asset_id]
            title = row["text"][:240]
            paths = [row["path"]]
            discovery_kind = "IMPLICIT_NAMED_ASSET"
            count = 1
        else:
            title = obj.get("title") or (occ[0]["path"] if occ else asset_id)
            paths = sorted({item["path"] for item in occ})
            discovery_kind = "REGISTERED_ASSET" if asset_id in objects else "UNDEFINED_EXPLICIT_ID"
            count = sum(item["mention_count"] for item in occ) or 1
        dependencies = sorted(set(obj.get("dependencies", [])))
        identity = corr["formal_identity"] if corr else candidate_identity(obj)
        gates = generic_gates(obj, dependencies)
        if corr:
            gates.update(corr["audit_gates"])
        original_text = obj.get("original_natural_language_claim") or title
        definition_paths = sorted(obj.get("source_paths", []))
        record = {
            "stable_id": asset_id,
            "title": title,
            "discovery_kind": discovery_kind,
            "source_evidence": {
                "definition_paths": definition_paths,
                "occurrence_count": count,
                "occurrence_paths": paths,
                "content_sha256": sha_payload({"id": asset_id, "title": title, "paths": paths, "text": original_text}),
            },
            "identity": identity,
            "identity_authority": "HUMAN_ADJUDICATED_TASK98" if corr else "AUTO_CANDIDATE",
            "mathematical_maturity": corr["mathematical_maturity"] if corr else maturity(obj),
            "external_evidence": corr["external_evidence"] if corr else evidence_axis(obj),
            "definition": {
                "original_text": original_text,
                "original_formula": obj.get("formal_expression_or_ast"),
                "inputs": obj.get("typed_variables", []),
                "output": obj.get("codomain_or_target_type", "UNSPECIFIED"),
                "domain": corr["domain"] if corr else obj.get("domain", "UNSPECIFIED_IN_SOURCE"),
                "codomain": obj.get("codomain_or_target_type", "UNSPECIFIED"),
                "parameters": obj.get("parameters", []),
                "units": obj.get("units_or_dimensions", []),
                "carrier": corr.get("carrier", "UNSPECIFIED") if corr else "UNSPECIFIED",
                "operation": corr.get("operation", "UNSPECIFIED") if corr else "UNSPECIFIED",
            },
            "mathematical_properties": {
                "boundaries": corr.get("boundaries", ["REQUIRES_HUMAN_REVIEW"]) if corr else ["REQUIRES_HUMAN_REVIEW"],
                "singularities": corr["singularities"] if corr else ["REQUIRES_HUMAN_REVIEW"],
                "continuity": corr.get("continuity", "REQUIRES_HUMAN_REVIEW") if corr else "REQUIRES_HUMAN_REVIEW",
                "differentiability": corr.get("differentiability", "REQUIRES_HUMAN_REVIEW") if corr else "REQUIRES_HUMAN_REVIEW",
                "monotonicity": corr.get("monotonicity", "REQUIRES_HUMAN_REVIEW") if corr else "REQUIRES_HUMAN_REVIEW",
                "computability": corr.get("computability", "REQUIRES_HUMAN_REVIEW") if corr else "REQUIRES_HUMAN_REVIEW",
                "counterexamples": ([corr["counterexample"]] if corr["counterexample"] else []) if corr else obj.get("known_counterexamples", []),
                "failure_modes": [corr["rejected_inference"]] if corr else ["AUTOMATIC EXTRACTION IS NOT AN ADJUDICATION"],
            },
            "status": {
                "mathematical": "ADJUDICATED_TASK98" if corr else obj.get("status", {}).get("formal_status", "UNASSESSED"),
                "logical": "ADJUDICATED_TASK98" if corr else obj.get("status", {}).get("logic_status", "UNASSESSED"),
                "dimensional": corr.get("dimension_status", "REQUIRES_HUMAN_REVIEW") if corr else "REQUIRES_HUMAN_REVIEW",
                "numerical": corr.get("numerical_status", "REQUIRES_HUMAN_REVIEW") if corr else "REQUIRES_HUMAN_REVIEW",
                "internal_model": "BOUNDED" if corr else "REQUIRES_HUMAN_REVIEW",
                "external_reality": "NOT_ESTABLISHED" if corr else "REQUIRES_HUMAN_REVIEW",
            },
            "claim_ceiling": corr["claim_ceiling"] if corr else "Automatic discovery only; no mathematical or external truth is conferred.",
            "allowed_uses": corr["allowed_uses"] if corr else ["candidate inventory and human audit routing"],
            "forbidden_uses": corr["forbidden_uses"] if corr else ["treating automatic extraction or an internal test as truth"],
            "disposition": corr["disposition"] if corr else "KEEP",
            "audit_gates": gates,
            "dependencies": dependencies,
            "review": {
                "state": "ADJUDICATED" if corr else "QUEUED",
                "version": "1.0.0",
                "reviewed_at": "2026-07-29" if corr else None,
                "reviewer": "Codex task 98" if corr else None,
            },
        }
        census.append(record)

    dependency_edges = []
    for asset_id, obj in sorted(objects.items()):
        for dependency in sorted(set(obj.get("dependencies", []))):
            dependency_edges.append({
                "from": asset_id, "to": dependency, "edge_type": "DECLARES_DEPENDENCY_ON",
                "source": "data/foundation/formal-objects/objects.jsonl", "review_state": "INHERITED_REQUIRES_REVIEW",
            })
    queue = [{
        "stable_id": row["stable_id"],
        "risk": "CRITICAL" if row["stable_id"] in corrections else "HIGH" if row["discovery_kind"] != "REGISTERED_ASSET" else "STANDARD",
        "state": "COMPLETED_TASK98" if row["stable_id"] in corrections else "QUEUED",
        "resume_key": f"function-census-v2:{row['stable_id']}",
        "required_review": [name for name, value in row["audit_gates"].items() if value == "REQUIRES_HUMAN_REVIEW"],
    } for row in census]
    queue.sort(key=lambda row: ({"CRITICAL": 0, "HIGH": 1, "STANDARD": 2}[row["risk"]], row["stable_id"]))
    reverse = Counter(edge["to"] for edge in dependency_edges)
    summary = {
        "snapshot": SNAPSHOT,
        "scanner_version": SCANNER_VERSION,
        "tracked_text_files_scanned": len(files),
        "registered_assets": sum(row["discovery_kind"] == "REGISTERED_ASSET" for row in census),
        "explicit_undefined_ids": sum(row["discovery_kind"] == "UNDEFINED_EXPLICIT_ID" for row in census),
        "implicit_named_assets": sum(row["discovery_kind"] == "IMPLICIT_NAMED_ASSET" for row in census),
        "deduplicated_assets": len(census),
        "source_occurrence_records": len(discovery),
        "source_mentions": sum(item["mention_count"] for item in discovery),
        "duplicate_mentions": sum(item["mention_count"] for item in discovery) - len(census),
        "dependency_edges": len(dependency_edges),
        "assets_with_dependencies": sum(bool(row["dependencies"]) for row in census),
        "identity_counts": dict(sorted(Counter(row["identity"] for row in census).items())),
        "math_maturity_counts": dict(sorted(Counter(row["mathematical_maturity"] for row in census).items())),
        "external_evidence_counts": dict(sorted(Counter(row["external_evidence"] for row in census).items())),
        "human_adjudicated_task98": len(corrections),
        "queued_for_human_review": len(census) - len(corrections),
        "highest_reverse_dependency_counts": [{"stable_id": key, "dependent_count": value} for key, value in reverse.most_common(20)],
        "authority_boundary": "AUTO_CANDIDATE records never override human adjudication; corrections.jsonl is the task 98 authority overlay.",
    }
    destination.mkdir(parents=True, exist_ok=True)
    write_jsonl(destination / "discovery.jsonl", discovery)
    write_jsonl(destination / "census.jsonl", census)
    write_jsonl(destination / "dependencies.jsonl", dependency_edges)
    write_jsonl(destination / "audit-queue.jsonl", queue)
    (destination / "census-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def compare_directories(left: Path, right: Path) -> list[str]:
    names = ["discovery.jsonl", "census.jsonl", "dependencies.jsonl", "audit-queue.jsonl", "census-summary.json"]
    return [name for name in names if not (left / name).exists() or (left / name).read_bytes() != (right / name).read_bytes()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="ignition-census-") as temporary:
            temp = Path(temporary)
            summary = build(temp)
            changed = compare_directories(OUT, temp)
        if changed:
            print("CENSUS_OUT_OF_DATE " + " ".join(changed))
            return 1
    else:
        summary = build(OUT)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    print("FUNCTION_ASSET_CENSUS_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
