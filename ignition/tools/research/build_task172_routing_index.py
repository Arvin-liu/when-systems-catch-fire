#!/usr/bin/env python3
"""Build the Task172 Step07 compact routing index and bounded pilot.

The index is a generated projection of the already-frozen Step05/06 routing
overlays.  It is deliberately keyed by canonical ID and never copies canonical
authority into a new authority surface.  The paired runtime router rechecks
the Current registries before returning candidates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(ROOT))
from tools.research.task172_routing import retrieve_candidates  # noqa: E402
from tools.research.build_task172_full_routing import expected_count  # noqa: E402


ROUTING = ROOT / "data/research/task172-routing-r1"
INDEX_REL = Path("data/research/task172-routing-r1/step07-routing-index.json")
SOURCE_FREEZE_REL = Path("data/research/task172-routing-r1/step07-routing-index-source-freeze.json")
MANIFEST_REL = Path("data/research/task172-routing-r1/step07-routing-index-manifest.json")
RECEIPT_REL = Path("data/research/task172-routing-r1/step07-routing-index-build-receipt.json")
FUNCTION_OVERLAY_REL = ROUTING.relative_to(ROOT) / "function-routing-overlay.jsonl"
NONFUNCTION_OVERLAY_REL = ROUTING.relative_to(ROOT) / "nonfunction-routing-overlay.jsonl"
QUERIES_REL = ROUTING.relative_to(ROOT) / "step07-routing-pilot-queries.json"
PILOT_REL = ROUTING.relative_to(ROOT) / "step07-routing-pilot.json"
OPERATION_REL = Path("data/operations/iterations/172/step07-routing-index.json")
REPORT_REL = Path("reports/operations/ignition-172-20260915-step07-routing-index.md")
TAGS_REL = Path("KNOWLEDGE/TAGS.md")
BRANCH = "work/IGNITION-20260912-172-knowledge-routing-universal-corpus"
PR_NUMBER = 218
COMMAND_SOURCES = [
    {"repository": "Arvin-liu/1111", "ref": "b7c27fab", "path": "agent-commands/IGNITION-20260912-172.md"},
    {"repository": "Arvin-liu/1111", "ref": "ebc75f9c", "path": "agent-commands/IGNITION-20260912-172-R1.md"},
    {"repository": "Arvin-liu/1111", "ref": "c3d57032", "path": "agent-commands/IGNITION-20260912-173.md"},
    {"repository": "Arvin-liu/1111", "ref": "22e09e3d", "path": "agent-commands/IGNITION-20260912-174.md"},
    {"repository": "Arvin-liu/1111", "ref": "ebc75f9c", "path": "agent-commands/IGNITION-20260913-175.md"},
    {"repository": "Arvin-liu/1111", "ref": "b1fc45fb", "path": "agent-commands/IGNITION-20260913-176.md"},
    {"repository": "Arvin-liu/1111", "ref": "22cbe6f7", "path": "agent-commands/IGNITION-20260913-177.md"},
]
TAXONOMY = {"fields": 24, "primary_disciplines": 245, "primary_subdisciplines": 2178}
def expected_rows(repo_root: Path) -> dict[str, int]:
    return {
        "FUNCTION_ASSET": expected_count("FUNCTION_ASSET", repo_root),
        "NONFUNCTION_CLAIM": expected_count("NONFUNCTION_CLAIM", repo_root),
    }
FACET_OUTPUTS = {
    "unesco_field_codes": "by_unesco_field",
    "unesco_discipline_codes": "by_unesco_discipline",
    "asset_role": "by_asset_role",
    "collision_use": "by_collision_use",
    "topic": "by_topic",
    "classification_state": "by_classification_state",
}
USE_DEFINITIONS = {
    "EXPLAIN": "retrieve assets useful for bounded explanation; never a truth claim",
    "COMPARE": "place governed assets side by side for a stated comparison",
    "ANALOGY_SOURCE": "retrieve a source for a structural analogy review",
    "MECHANISM_TEST": "retrieve an asset for mechanism-boundary inspection",
    "CAUSAL_CHALLENGE": "retrieve an asset for causal-claim challenge, not causal proof",
    "COUNTEREXAMPLE": "retrieve a negative or competing case for boundary testing",
    "EVIDENCE_CHECK": "retrieve an asset whose evidence boundary needs checking",
    "METHOD_TRANSFER": "retrieve a method/formal-scope candidate for cautious transfer review",
    "BOUNDARY_TEST": "retrieve an asset for scope, ceiling or failure-condition review",
    "NORMATIVE_CHECK": "retrieve an asset for an explicit normative boundary review",
    "NARRATIVE_CASE": "retrieve a source-defined narrative or interpretive case",
    "HISTORICAL_CONTEXT": "retrieve historical or withdrawn context without positive promotion",
}


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical(row) + "\n" for row in rows), encoding="utf-8")


def overlay_rows(repo_root: Path) -> list[dict[str, Any]]:
    rows = []
    for relative, expected_kind in (
        (FUNCTION_OVERLAY_REL, "FUNCTION_ASSET"),
        (NONFUNCTION_OVERLAY_REL, "NONFUNCTION_CLAIM"),
    ):
        for row in read_jsonl(repo_root / relative):
            if row.get("asset_kind") != expected_kind:
                raise ValueError(f"overlay asset kind drift: {relative}: {row.get('canonical_id')}")
            rows.append(row)
    rows.sort(key=lambda row: (row["asset_kind"], row["canonical_id"]))
    return rows


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    domain = row.get("domain", {})
    return {
        "asset_kind": row["asset_kind"],
        "canonical_id": row["canonical_id"],
        "source_record_sha": row["source_record_sha"],
        "unesco_field_codes": sorted(domain.get("unesco_field_codes", [])),
        "unesco_discipline_codes": sorted(domain.get("unesco_discipline_codes", [])),
        "classification_state": domain.get("classification_state"),
        "asset_role": sorted(row.get("asset_role", [])),
        "collision_use": sorted(row.get("collision_use", [])),
        "topic": sorted(row.get("topic", [])),
        "routing_confidence": row.get("routing_confidence"),
    }


def build_index(repo_root: Path, source_head: str) -> dict[str, Any]:
    rows = overlay_rows(repo_root)
    counts = expected_rows(repo_root)
    expected_total = sum(counts.values())
    if len(rows) != expected_total:
        raise ValueError(f"routing overlay row count drift: {len(rows)} != {expected_total}")
    refs = [f"{row['asset_kind']}:{row['canonical_id']}" for row in rows]
    if len(refs) != len(set(refs)):
        raise ValueError("routing overlay contains duplicate canonical references")
    records = [compact_row(row) for row in rows]
    facet_values: dict[str, dict[str, set[str]]] = {name: defaultdict(set) for name in FACET_OUTPUTS.values()}
    for row in records:
        ref = f"{row['asset_kind']}:{row['canonical_id']}"
        for field, output_name in FACET_OUTPUTS.items():
            values = row[field] if field != "classification_state" else [row[field]]
            for value in values:
                facet_values[output_name][str(value)].add(ref)
    facets = {
        output_name: {value: sorted(refs) for value, refs in sorted(values.items())}
        for output_name, values in sorted(facet_values.items())
    }
    return {
        "schema_version": "task172-step07-routing-index-v1",
        "step": "Task172 Step07",
        "source_exact_head": source_head,
        "branch": BRANCH,
        "pull_request": PR_NUMBER,
        "operation_id": "knowledge.collide_object",
        "run_mode": "READ_ONLY_RUN",
        "index_contract": {
            "default_top_k": 120,
            "max_top_k": 1000,
            "candidate_strategy": [
                "exact UNESCO four-digit / high-confidence topic / collision-use intersection",
                "UNESCO two-digit and asset role widening",
                "one-hop dependency expansion remains an explicit future bounded operation",
                "global lexical fallback is explicit and reports its reason",
                "every selected ID is revalidated against the Current authority registry",
            ],
            "fallback_is_silent": False,
            "authority_is_index": False,
        },
        "source_overlays": [
            {"asset_kind": "FUNCTION_ASSET", "path": str(FUNCTION_OVERLAY_REL), "sha256": sha256(repo_root / FUNCTION_OVERLAY_REL), "rows": counts["FUNCTION_ASSET"]},
            {"asset_kind": "NONFUNCTION_CLAIM", "path": str(NONFUNCTION_OVERLAY_REL), "sha256": sha256(repo_root / NONFUNCTION_OVERLAY_REL), "rows": counts["NONFUNCTION_CLAIM"]},
        ],
        "taxonomy": {
            "source": "1988 UNESCO primary document locked by Gate T",
            "version_warning": "Historical proposed nomenclature; not the unique modern 2026 UNESCO standard.",
            **TAXONOMY,
        },
        "stats": {
            "records": len(records),
            "function_records": sum(row["asset_kind"] == "FUNCTION_ASSET" for row in records),
            "nonfunction_records": sum(row["asset_kind"] == "NONFUNCTION_CLAIM" for row in records),
            "facet_names": sorted(facets),
            "facet_value_counts": {name: len(values) for name, values in facets.items()},
        },
        "records": records,
        "facets": facets,
        "authority_revalidation": {
            "function_path": "data/foundation/function-assets/identity-cards.jsonl",
            "nonfunction_path": "data/foundation/nonfunction-claims/claim-registry.jsonl",
            "required_fields": ["canonical_id", "record_sha256", "final_disposition", "claim_ceiling"],
        },
        "command_sources": COMMAND_SOURCES,
        "side_effects": {"repository_mutation": False, "external_action": False, "registry_write": False},
    }


def render_tags(index: dict[str, Any]) -> str:
    facets = index["facets"]
    lines = [
        "# Task172 routing facets",
        "",
        "这是 `knowledge.collide_object` 的薄人类入口。它是检索与碰撞路由元数据，不是正确性、重要性、成熟度、证据、公开资格或领域权威。旧的七个 Knowledge subjects 仍然有效；这里的 UNESCO 分面与其正交。",
        "",
        f"机器索引：[`step07-routing-index.json`](../data/research/task172-routing-r1/step07-routing-index.json)。当前索引包含 {index['stats']['records']} 条 canonical-ID 路由记录；返回候选后必须回读 authority registry 做 fingerprint exact validation。",
        "",
        "## 受控 collision-use 标签",
        "",
    ]
    for tag, definition in USE_DEFINITIONS.items():
        refs = facets["by_collision_use"].get(tag, [])
        lines.extend([
            f"### `{tag}`",
            "",
            f"- 含义/可做什么：{definition}。",
            f"- 当前记录数：{len(refs)}；示例：{', '.join('`' + ref + '`' for ref in refs[:3]) or '无'}。",
            "- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。",
            "",
        ])
    lines.extend([
        "## UNESCO 分面",
        "",
        f"- 二位 field facet 值：{len(facets['by_unesco_field'])}；四位 discipline facet 值：{len(facets['by_unesco_discipline'])}。空 discipline 不表示失败：它表示当前 routing 没有足够依据伪造四位等价。",
        "- `OUT_OF_UNESCO_SCOPE` / `UNRESOLVED` 保留为合法状态；内部治理、CI、运行时和 bookkeeping 不为覆盖率强贴科学学科码。",
        "- 该 taxonomy 是 1988 UNESCO proposed nomenclature 的版本化 routing ontology，不应表述为 2026 年唯一现代学科真理标准。",
        "",
        "## 操作边界",
        "",
        "`knowledge.collide_object` 仍是 `CURRENT_BOUNDED + READ_ONLY_RUN`。路由器只读 compact index 与 Current authority；不写 registry、不联网、不改变输入对象、M/E、disposition、claim ceiling 或 evidence status。若 facet 交集不足，结果会显式标记 fallback 和原因。",
        "",
    ])
    return "\n".join(lines).rstrip() + "\n"


def build_pilot(repo_root: Path) -> dict[str, Any]:
    query_document = read_json(repo_root / QUERIES_REL)
    queries = query_document.get("cases", [])
    if query_document.get("schema_version") != "task172-step07-routing-pilot-queries-v1" or not queries:
        raise ValueError("Task172 Step07 pilot query fixture is missing or invalid")
    results = []
    for query in queries:
        case_id = query["case_id"]
        result = retrieve_candidates(repo_root, query, int(query.get("top_k", 50)))
        results.append({"case_id": case_id, "query": query, "result": result})
    return {
        "schema_version": "task172-step07-routing-pilot-v1",
        "step": "Task172 Step07",
        "pilot_scope": "bounded routing transparency only; not a replay adjudication",
        "cases": results,
        "hard_checks": {
            "invalid_id_count": sum(item["result"]["invalid_selection_count"] for item in results),
            "all_selected_exact": all(item["result"]["exact_validation_status"] == "ALL_SELECTED_EXACT" for item in results),
            "max_candidate_universe": max(item["result"]["candidate_universe_size"] for item in results),
            "max_selected": max(item["result"]["selected_count"] for item in results),
            "fallback_reasons_explicit": all(item["result"]["fallback"]["explicit"] for item in results),
        },
        "claim_ceiling": "Candidate retrieval and exact authority validation only; no new claim, evidence, truth, causality, novelty or registry admission.",
    }


def render_report(index: dict[str, Any], pilot: dict[str, Any], source_head: str) -> str:
    cases = pilot["cases"]
    lines = [
        "# IGNITION-172 Step07 — Knowledge Experience routing index",
        "",
        f"This logical step is based on exact frozen parent `{source_head}` on the existing Task172 branch and Draft PR #{PR_NUMBER}.",
        "",
        "- The compact index is a generated, canonical-ID keyed facet projection of the already completed function and nonfunction routing overlays.",
        f"- Coverage: {index['stats']['function_records']} function records + {index['stats']['nonfunction_records']} nonfunction records = {index['stats']['records']} routing records.",
        "- Facets: UNESCO field/discipline when justified, asset role, collision use, topic and classification state. Empty or unresolved facets are retained rather than guessed.",
        "- Operation binding: `knowledge.collide_object` remains `CURRENT_BOUNDED + READ_ONLY_RUN`; the router has no repository, registry or network write permission.",
        "- Candidate policy: bounded facet retrieval → transparent widening/fallback → exact Current authority fingerprint validation. Fallback is never silent.",
        "",
        "## Precision-oriented routing pilot",
        "",
        "|case|candidate universe|selected|fallback|exact validation|",
        "|---|---:|---:|---|---|",
    ]
    for item in cases:
        result = item["result"]
        lines.append(
            f"|`{item['case_id']}`|{result['candidate_universe_size']}|{result['selected_count']}|{result['fallback']['reason'] if result['fallback']['occurred'] else 'NO'}|{result['exact_validation_status']}|"
        )
    lines.extend([
        "",
        f"Hard checks: invalid IDs `{pilot['hard_checks']['invalid_id_count']}`, all selected exact `{pilot['hard_checks']['all_selected_exact']}`, explicit fallback reasons `{pilot['hard_checks']['fallback_reasons_explicit']}`.",
        "",
        "This is routing evidence, not a claim adjudication or scholarly corpus result. Literary/interpretive, empirical, structural-analogy and source-derived material remain separate at the collision protocol layer.",
        "",
        "Decision: `STEP07_ROUTING_INDEX_READY; READ_ONLY; EXACT_VALIDATION_REQUIRED; NO_CANONICAL_MUTATION`.",
        "",
    ])
    return "\n".join(lines)


def require_parent(repo_root: Path, source_head: str) -> None:
    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    if current != source_head:
        raise SystemExit(f"TASK172_STEP07_BUILD_REFUSED: current HEAD {current} != source head {source_head}")


def generated_hashes(repo_root: Path, paths: list[Path]) -> dict[str, str]:
    return {str(path): sha256(repo_root / path) for path in paths}


def write_artifacts(repo_root: Path, source_head: str) -> None:
    require_parent(repo_root, source_head)
    counts = expected_rows(repo_root)
    index = build_index(repo_root, source_head)
    write_json(repo_root / INDEX_REL, index)
    pilot = build_pilot(repo_root)
    write_json(repo_root / PILOT_REL, pilot)
    tags = render_tags(index)
    (repo_root / TAGS_REL).write_text(tags, encoding="utf-8")
    report = render_report(index, pilot, source_head)
    (repo_root / REPORT_REL).parent.mkdir(parents=True, exist_ok=True)
    (repo_root / REPORT_REL).write_text(report, encoding="utf-8")

    source_freeze = {
        "schema": "task172-step07-routing-index-source-freeze-v1",
        "step": "Task172 Step07",
        "freeze_event": "SCAN_INPUT_FREEZE_REUSE",
        "formal_pre_freeze": {"head": source_head, "branch": BRANCH, "pull_request": PR_NUMBER, "state": "OPEN + DRAFT + unmerged"},
        "direction_locks": ["IGNITION-20260913-175", "IGNITION-20260913-176", "IGNITION-20260913-177"],
        "command_sources": COMMAND_SOURCES,
        "inputs": {
            "function_overlay": {"path": str(FUNCTION_OVERLAY_REL), "sha256": sha256(repo_root / FUNCTION_OVERLAY_REL), "rows": counts["FUNCTION_ASSET"]},
            "nonfunction_overlay": {"path": str(NONFUNCTION_OVERLAY_REL), "sha256": sha256(repo_root / NONFUNCTION_OVERLAY_REL), "rows": counts["NONFUNCTION_CLAIM"]},
            "pilot_queries": {"path": str(QUERIES_REL), "sha256": sha256(repo_root / QUERIES_REL)},
        },
        "taxonomy_authority": {"source": "1988 UNESCO primary document locked by Gate T", **TAXONOMY},
        "derived_outputs": {
            "index_sha256": sha256(repo_root / INDEX_REL),
            "pilot_sha256": sha256(repo_root / PILOT_REL),
            "tags_sha256": sha256(repo_root / TAGS_REL),
            "report_sha256": sha256(repo_root / REPORT_REL),
        },
        "decision": "STEP07_ROUTING_INDEX_READY; READ_ONLY; EXACT_VALIDATION_REQUIRED; NO_CANONICAL_MUTATION",
    }
    write_json(repo_root / SOURCE_FREEZE_REL, source_freeze)

    operation = {
        "schema": "task172-step07-routing-index-operation-v1",
        "step": "Task172 Step07",
        "operation_id": "knowledge.collide_object",
        "operation_status": "CURRENT_BOUNDED",
        "execution_mode": "READ_ONLY_RUN",
        "source_exact_head": source_head,
        "knowledge_entrypoints": {
            "machine_search": "data/governance/knowledge-experience/search-index.jsonl",
            "routing_index": str(INDEX_REL),
            "human_tags": str(TAGS_REL),
            "runtime_router": "tools/research/task172_routing.py",
        },
        "required_sequence": [
            "derive bounded query facets",
            "retrieve from routing index",
            "widen to explicit fallback only when required",
            "validate canonical ID and source fingerprint against Current authority",
            "report candidate universe, facet reasons, exact status and fallback warning",
        ],
        "default_top_k": 120,
        "pilot": {"path": str(PILOT_REL), "sha256": sha256(repo_root / PILOT_REL)},
        "index": {"path": str(INDEX_REL), "sha256": sha256(repo_root / INDEX_REL), "rows": index["stats"]["records"]},
        "source_freeze_sha256": sha256(repo_root / SOURCE_FREEZE_REL),
        "report_sha256": sha256(repo_root / REPORT_REL),
        "network": False,
        "repository_mutation": False,
        "registry_write": False,
        "canonical_mutation": False,
        "decision": "STEP07_ROUTING_INDEX_READY; READ_ONLY; EXACT_VALIDATION_REQUIRED; NO_CANONICAL_MUTATION",
    }
    write_json(repo_root / OPERATION_REL, operation)

    receipt_paths = [INDEX_REL, PILOT_REL, TAGS_REL, REPORT_REL, SOURCE_FREEZE_REL, OPERATION_REL]
    receipt = {
        "schema": "task172-step07-routing-index-build-receipt-v1",
        "step": "Task172 Step07",
        "operation_id": "knowledge.collide_object",
        "source_exact_head": source_head,
        "inputs": source_freeze["inputs"],
        "counts": index["stats"],
        "pilot_hard_checks": pilot["hard_checks"],
        "outputs": generated_hashes(repo_root, receipt_paths),
        "network": False,
        "repository_mutation": False,
        "registry_write": False,
        "deterministic": True,
        "decision": "STEP07_ROUTING_INDEX_READY; READ_ONLY; EXACT_VALIDATION_REQUIRED; NO_CANONICAL_MUTATION",
    }
    write_json(repo_root / RECEIPT_REL, receipt)

    manifest_paths = receipt_paths + [RECEIPT_REL]
    manifest = {
        "schema": "task172-step07-routing-index-manifest-v1",
        "step": "Task172 Step07",
        "source_exact_head": source_head,
        "source_freeze_sha256": sha256(repo_root / SOURCE_FREEZE_REL),
        "generated_outputs": generated_hashes(repo_root, manifest_paths),
        "counts": index["stats"],
        "machine_human_pairs": [{"machine": str(INDEX_REL), "human": str(TAGS_REL)}, {"machine": str(PILOT_REL), "human": str(REPORT_REL)}],
        "claim_ceiling": "Bounded repository-local routing and exact authority validation only; no new claim, evidence, truth, causality, novelty or registry admission.",
    }
    write_json(repo_root / MANIFEST_REL, manifest)
    print(f"TASK172_STEP07_ROUTING_INDEX_BUILT rows={index['stats']['records']} source_head={source_head}")


def check_artifacts(repo_root: Path) -> None:
    required = [INDEX_REL, SOURCE_FREEZE_REL, MANIFEST_REL, RECEIPT_REL, QUERIES_REL, PILOT_REL, OPERATION_REL, REPORT_REL, TAGS_REL]
    missing = [str(path) for path in required if not (repo_root / path).is_file()]
    if missing:
        raise SystemExit("TASK172_STEP07_CHECK_FAILED missing=" + ",".join(missing))
    source_head = read_json(repo_root / MANIFEST_REL).get("source_exact_head", "")
    index = build_index(repo_root, source_head)
    if read_json(repo_root / INDEX_REL) != index:
        raise SystemExit("TASK172_STEP07_CHECK_FAILED index drift")
    pilot = build_pilot(repo_root)
    if read_json(repo_root / PILOT_REL) != pilot:
        raise SystemExit("TASK172_STEP07_CHECK_FAILED pilot drift")
    if (repo_root / TAGS_REL).read_text(encoding="utf-8") != render_tags(index):
        raise SystemExit("TASK172_STEP07_CHECK_FAILED tags drift")
    if (repo_root / REPORT_REL).read_text(encoding="utf-8") != render_report(index, pilot, source_head):
        raise SystemExit("TASK172_STEP07_CHECK_FAILED report drift")
    print(f"TASK172_STEP07_ROUTING_INDEX_DETERMINISTIC rows={index['stats']['records']} source_head={source_head}")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    parser.add_argument("--source-head", help="exact current parent head required by --write")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    if args.write:
        if not args.source_head or len(args.source_head) != 40:
            raise SystemExit("--write requires a 40-character --source-head")
        write_artifacts(repo_root, args.source_head)
    else:
        check_artifacts(repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
