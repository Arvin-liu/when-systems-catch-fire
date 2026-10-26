#!/usr/bin/env python3
"""Compare small caller-supplied relation graphs for explicit structural overlap."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
import sys
from typing import Any, Iterator


TOOL_ID = "reasoning.search_structural_analogies"
TOOL_VERSION = "0.1.0"
SCHEMA_VERSION = "toolbox-structural-analogy-search-input-r0"
OUTPUT_SCHEMA_VERSION = "toolbox-structural-analogy-search-output-r0"
MAX_INPUT_BYTES = 262_144
MAX_OUTPUT_BYTES = 262_144
MAX_CANDIDATES = 8
MAX_NODES = 8
MAX_RELATIONS = 24
MAX_MAPPING_EVALUATIONS = 200_000
MAX_REPORTED_TIES = 8
IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,63}$")
ROLE_CLASSES = {
    "ACTOR", "ACTION", "CONDITION", "CONSTRAINT", "MEASURE", "OUTCOME", "RESOURCE", "STATE", "OTHER",
}
INVARIANTS = [
    "ANALOGY_TRANSFERS_RELATION_NOT_AUTHORITY",
    "SURFACE_SIMILARITY_IS_NOT_STRUCTURAL_MATCH",
    "TRANSFERRED_SOLUTION_REQUIRES_TARGET_DOMAIN_VALIDATION",
    "ANALOGY_DIVERSITY_IS_SEARCH_EXPANSION_NOT_EVIDENCE",
]
CLAIM_CEILING = (
    "Enumerates role-compatible node mappings and exact caller-declared relation-type correspondences over the supplied finite graphs. "
    "A structural overlap is only a candidate analogy; no source authenticity, semantic equivalence, solution validity, target-domain "
    "evidence, causal transfer, scientific truth, or authority is established."
)


class StructuralAnalogySearchError(ValueError):
    """Raised when a bounded structural-analogy request is malformed or too large."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise StructuralAnalogySearchError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _object(value: Any, fields: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise StructuralAnalogySearchError(where + " must be an object")
    if set(value) != fields:
        missing = sorted(fields - set(value))
        extra = sorted(set(value) - fields)
        raise StructuralAnalogySearchError(f"{where} fields mismatch; missing={missing}, extra={extra}")
    return value


def _identifier(value: Any, where: str) -> str:
    if not isinstance(value, str) or IDENTIFIER_RE.fullmatch(value) is None:
        raise StructuralAnalogySearchError(where + " must be a bounded identifier")
    return value


def _unique(items: list[str], where: str) -> None:
    if len(items) != len(set(items)):
        raise StructuralAnalogySearchError(where + " values must be unique")


def _validate_graph(value: Any, where: str, *, source: bool) -> dict[str, Any]:
    if source:
        graph = _object(value, {"structure_id", "domain_id", "nodes", "relations"}, where)
        graph_id = _identifier(graph["structure_id"], where + ".structure_id")
    else:
        graph = _object(value, {"candidate_id", "structure_id", "domain_id", "nodes", "relations"}, where)
        graph_id = _identifier(graph["candidate_id"], where + ".candidate_id")
        _identifier(graph["structure_id"], where + ".structure_id")
    domain_id = _identifier(graph["domain_id"], where + ".domain_id")
    raw_nodes = graph["nodes"]
    raw_relations = graph["relations"]
    if not isinstance(raw_nodes, list) or not 2 <= len(raw_nodes) <= MAX_NODES:
        raise StructuralAnalogySearchError(f"{where}.nodes must contain 2 to {MAX_NODES} nodes")
    if not isinstance(raw_relations, list) or not 1 <= len(raw_relations) <= MAX_RELATIONS:
        raise StructuralAnalogySearchError(f"{where}.relations must contain 1 to {MAX_RELATIONS} relations")
    nodes: dict[str, str] = {}
    for index, raw in enumerate(raw_nodes):
        path = f"{where}.nodes[{index}]"
        item = _object(raw, {"node_id", "role_class"}, path)
        node_id = _identifier(item["node_id"], path + ".node_id")
        role_class = item["role_class"]
        if not isinstance(role_class, str) or role_class not in ROLE_CLASSES:
            raise StructuralAnalogySearchError(path + ".role_class is not an admitted role class")
        if node_id in nodes:
            raise StructuralAnalogySearchError(where + ".nodes contain duplicate node_id values")
        nodes[node_id] = role_class
    relation_ids: list[str] = []
    relation_keys: set[tuple[str, str, str]] = set()
    relations: list[dict[str, str]] = []
    for index, raw in enumerate(raw_relations):
        path = f"{where}.relations[{index}]"
        item = _object(raw, {"relation_id", "subject_id", "relation_type", "object_id"}, path)
        relation_id = _identifier(item["relation_id"], path + ".relation_id")
        subject_id = _identifier(item["subject_id"], path + ".subject_id")
        relation_type = _identifier(item["relation_type"], path + ".relation_type")
        object_id = _identifier(item["object_id"], path + ".object_id")
        if subject_id not in nodes or object_id not in nodes:
            raise StructuralAnalogySearchError(path + " relation endpoints must name declared nodes")
        relation_ids.append(relation_id)
        triple = (subject_id, relation_type, object_id)
        if triple in relation_keys:
            raise StructuralAnalogySearchError(where + ".relations contain duplicate directed relation triples")
        relation_keys.add(triple)
        relations.append({
            "relation_id": relation_id,
            "subject_id": subject_id,
            "relation_type": relation_type,
            "object_id": object_id,
        })
    _unique(relation_ids, where + ".relations relation_id")
    return {
        "graph_id": graph_id,
        "structure_id": graph["structure_id"],
        "domain_id": domain_id,
        "nodes": nodes,
        "relations": relations,
        "relation_keys": relation_keys,
    }


def _validate_request(request: Any) -> tuple[dict[str, Any], str, int]:
    data = _object(request, {"schema_version", "task_id", "source_structure", "relation_mappings", "target_candidates"}, "request")
    if data["schema_version"] != SCHEMA_VERSION:
        raise StructuralAnalogySearchError("schema_version must be " + SCHEMA_VERSION)
    task_id = _identifier(data["task_id"], "task_id")
    source = _validate_graph(data["source_structure"], "source_structure", source=True)
    raw_maps = data["relation_mappings"]
    if not isinstance(raw_maps, list) or not 1 <= len(raw_maps) <= MAX_RELATIONS:
        raise StructuralAnalogySearchError(f"relation_mappings must contain 1 to {MAX_RELATIONS} entries")
    relation_map: dict[str, str] = {}
    mapped_target_types: set[str] = set()
    for index, raw in enumerate(raw_maps):
        where = f"relation_mappings[{index}]"
        item = _object(raw, {"source_relation_type", "target_relation_type"}, where)
        source_type = _identifier(item["source_relation_type"], where + ".source_relation_type")
        target_type = _identifier(item["target_relation_type"], where + ".target_relation_type")
        if source_type in relation_map:
            raise StructuralAnalogySearchError("each source relation type may have only one declared mapping")
        if target_type in mapped_target_types:
            raise StructuralAnalogySearchError("declared relation mappings must be one-to-one")
        relation_map[source_type] = target_type
        mapped_target_types.add(target_type)
    source_relation_types = {row["relation_type"] for row in source["relations"]}
    if set(relation_map) != source_relation_types:
        raise StructuralAnalogySearchError("relation_mappings must cover exactly the source relation types")

    raw_candidates = data["target_candidates"]
    if not isinstance(raw_candidates, list) or not 1 <= len(raw_candidates) <= MAX_CANDIDATES:
        raise StructuralAnalogySearchError(f"target_candidates must contain 1 to {MAX_CANDIDATES} graphs")
    candidates = [_validate_graph(item, f"target_candidates[{i}]", source=False) for i, item in enumerate(raw_candidates)]
    _unique([candidate["graph_id"] for candidate in candidates], "target_candidates candidate_id")
    estimated_mappings = 0
    for candidate in candidates:
        source_role_counts: dict[str, int] = {}
        target_role_counts: dict[str, int] = {}
        for role in source["nodes"].values():
            source_role_counts[role] = source_role_counts.get(role, 0) + 1
        for role in candidate["nodes"].values():
            target_role_counts[role] = target_role_counts.get(role, 0) + 1
        count = 1
        for role, needed in source_role_counts.items():
            available = target_role_counts.get(role, 0)
            if available < needed:
                count = 0
                break
            count *= math.perm(available, needed)
        estimated_mappings += count
    if estimated_mappings > MAX_MAPPING_EVALUATIONS:
        raise StructuralAnalogySearchError(
            f"estimated node mappings {estimated_mappings} exceed the {MAX_MAPPING_EVALUATIONS} comparison budget"
        )
    return {"source": source, "relation_map": relation_map, "candidates": candidates}, task_id, estimated_mappings


def _node_mappings(source_nodes: dict[str, str], target_nodes: dict[str, str]) -> Iterator[dict[str, str]]:
    source_by_role: dict[str, list[str]] = {}
    target_by_role: dict[str, list[str]] = {}
    for node_id, role in source_nodes.items():
        source_by_role.setdefault(role, []).append(node_id)
    for node_id, role in target_nodes.items():
        target_by_role.setdefault(role, []).append(node_id)
    roles = sorted(source_by_role)
    pools = [
        list(itertools.permutations(sorted(target_by_role.get(role, [])), len(source_by_role[role])))
        for role in roles
    ]
    if any(not pool for pool in pools):
        return
    for selected in itertools.product(*pools):
        mapping: dict[str, str] = {}
        for role, target_ids in zip(roles, selected):
            for source_id, target_id in zip(sorted(source_by_role[role]), target_ids):
                mapping[source_id] = target_id
        yield mapping


def _score_mapping(
    source: dict[str, Any], candidate: dict[str, Any], relation_map: dict[str, str], mapping: dict[str, str],
) -> dict[str, Any]:
    reverse_relation_map = {target: source_type for source_type, target in relation_map.items()}
    target_by_triple = {
        (edge["subject_id"], edge["relation_type"], edge["object_id"]): edge
        for edge in candidate["relations"]
    }
    source_by_triple = {
        (edge["subject_id"], edge["relation_type"], edge["object_id"]): edge
        for edge in source["relations"]
    }
    matched: list[dict[str, str]] = []
    unmatched_source: list[str] = []
    for edge in source["relations"]:
        triple = (
            mapping[edge["subject_id"]],
            relation_map[edge["relation_type"]],
            mapping[edge["object_id"]],
        )
        target_edge = target_by_triple.get(triple)
        if target_edge is None:
            unmatched_source.append(edge["relation_id"])
        else:
            matched.append({
                "source_relation_id": edge["relation_id"],
                "target_relation_id": target_edge["relation_id"],
                "source_relation_type": edge["relation_type"],
                "target_relation_type": target_edge["relation_type"],
                "mapped_subject_id": mapping[edge["subject_id"]],
                "mapped_object_id": mapping[edge["object_id"]],
            })
    inverse_nodes = {target_id: source_id for source_id, target_id in mapping.items()}
    matched_target_ids = {row["target_relation_id"] for row in matched}
    extra_mapped_target: list[str] = []
    unmapped_target: list[str] = []
    for edge in candidate["relations"]:
        if (
            edge["relation_type"] not in reverse_relation_map
            or edge["subject_id"] not in inverse_nodes
            or edge["object_id"] not in inverse_nodes
        ):
            unmapped_target.append(edge["relation_id"])
            continue
        inverse_triple = (
            inverse_nodes[edge["subject_id"]],
            reverse_relation_map[edge["relation_type"]],
            inverse_nodes[edge["object_id"]],
        )
        if edge["relation_id"] not in matched_target_ids and inverse_triple not in source_by_triple:
            extra_mapped_target.append(edge["relation_id"])
    return {
        "mapping": mapping,
        "matched": sorted(matched, key=lambda row: (row["source_relation_id"], row["target_relation_id"])),
        "unmatched_source": sorted(unmatched_source),
        "extra_mapped_target": sorted(extra_mapped_target),
        "unmapped_target": sorted(unmapped_target),
    }


def _fraction(numerator: int, denominator: int) -> str | None:
    if denominator == 0:
        return None
    return f"{numerator}/{denominator}"


def _candidate_result(source: dict[str, Any], candidate: dict[str, Any], relation_map: dict[str, str]) -> dict[str, Any]:
    best_key: tuple[int, int] | None = None
    best: list[dict[str, Any]] = []
    evaluated = 0
    tied_count = 0
    min_unmapped_target = 0
    max_unmapped_target = 0
    for mapping in _node_mappings(source["nodes"], candidate["nodes"]):
        evaluated += 1
        scored = _score_mapping(source, candidate, relation_map, mapping)
        key = (len(scored["matched"]), -len(scored["extra_mapped_target"]))
        if best_key is None or key > best_key:
            best_key = key
            best = [scored]
            tied_count = 1
            min_unmapped_target = len(scored["unmapped_target"])
            max_unmapped_target = len(scored["unmapped_target"])
        elif key == best_key:
            tied_count += 1
            min_unmapped_target = min(min_unmapped_target, len(scored["unmapped_target"]))
            max_unmapped_target = max(max_unmapped_target, len(scored["unmapped_target"]))
            if len(best) < MAX_REPORTED_TIES:
                best.append(scored)
    if best_key is None:
        return {
            "candidate_id": candidate["graph_id"],
            "structure_id": candidate["structure_id"],
            "domain_id": candidate["domain_id"],
            "status": "NO_ROLE_COMPATIBLE_NODE_MAPPING",
            "evaluated_node_mappings": 0,
            "matched_source_relation_count": 0,
            "source_relation_count": len(source["relations"]),
            "source_relation_coverage_fraction": _fraction(0, len(source["relations"])),
            "matched_mapped_target_relation_count": 0,
            "extra_mapped_target_relation_count": 0,
            "unmapped_target_relation_count_range": [len(candidate["relations"]), len(candidate["relations"])],
            "mapped_target_relation_precision_fraction": None,
            "best_mappings": [],
            "best_mapping_tie_count": 0,
            "best_mapping_ties_truncated": False,
        }
    matched_count = best_key[0]
    extras = -best_key[1]
    source_count = len(source["relations"])
    mapped_target_count = matched_count + extras
    status = "STRUCTURAL_OVERLAP_CANDIDATE" if matched_count else "NO_MAPPED_RELATION_OVERLAP"
    best_mappings = []
    for scored in sorted(best, key=lambda row: tuple(sorted(row["mapping"].items()))):
        transfers = [
            {
                "source_relation_id": item["source_relation_id"],
                "target_relation_id": item["target_relation_id"],
                "status": "REQUIRES_TARGET_DOMAIN_VALIDATION",
            }
            for item in scored["matched"]
        ]
        best_mappings.append({
            "source_to_target_node_map": [
                {"source_node_id": source_id, "target_node_id": target_id}
                for source_id, target_id in sorted(scored["mapping"].items())
            ],
            "matched_relation_pairs": scored["matched"],
            "unmatched_source_relation_ids": scored["unmatched_source"],
            "extra_mapped_target_relation_ids": scored["extra_mapped_target"],
            "unmapped_target_relation_ids": scored["unmapped_target"],
            "transfer_hypotheses": transfers,
        })
    return {
        "candidate_id": candidate["graph_id"],
        "structure_id": candidate["structure_id"],
        "domain_id": candidate["domain_id"],
        "status": status,
        "evaluated_node_mappings": evaluated,
        "matched_source_relation_count": matched_count,
        "source_relation_count": source_count,
        "source_relation_coverage_fraction": _fraction(matched_count, source_count),
        "matched_mapped_target_relation_count": matched_count,
        "extra_mapped_target_relation_count": extras,
        "unmapped_target_relation_count_range": [min_unmapped_target, max_unmapped_target],
        "mapped_target_relation_precision_fraction": _fraction(matched_count, mapped_target_count),
        "best_mappings": best_mappings,
        "best_mapping_tie_count": tied_count,
        "best_mapping_ties_truncated": tied_count > len(best_mappings),
    }


def search_structural_analogies(request: Any, *, raw_digest: str | None = None) -> dict[str, Any]:
    validated, task_id, estimated_mappings = _validate_request(request)
    source = validated["source"]
    relation_map = validated["relation_map"]
    results = [_candidate_result(source, candidate, relation_map) for candidate in validated["candidates"]]
    results.sort(key=lambda row: (-row["matched_source_relation_count"], row["extra_mapped_target_relation_count"], row["candidate_id"]))
    for rank, result in enumerate(results, start=1):
        result["structural_rank"] = rank
    status = "STRUCTURAL_OVERLAP_CANDIDATES_FOUND" if any(row["matched_source_relation_count"] for row in results) else "NO_STRUCTURAL_OVERLAP_CANDIDATES_FOUND"
    payload = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    result = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "task_id": task_id,
        "status": status,
        "input_sha256": raw_digest or hashlib.sha256(payload).hexdigest(),
        "source_structure": {
            "structure_id": source["structure_id"],
            "domain_id": source["domain_id"],
            "node_count": len(source["nodes"]),
            "relation_count": len(source["relations"]),
        },
        "relation_mappings": [
            {"source_relation_type": source_type, "target_relation_type": target_type}
            for source_type, target_type in sorted(relation_map.items())
        ],
        "candidate_count": len(results),
        "estimated_node_mappings": estimated_mappings,
        "evaluated_node_mappings": sum(row["evaluated_node_mappings"] for row in results),
        "candidates": results,
        "ranking_rule": "MAXIMIZE_EXACT_MAPPED_SOURCE_RELATIONS_THEN_MINIMIZE_EXTRA_MAPPED_TARGET_RELATIONS_THEN_CANDIDATE_ID; structural counts only",
        "surface_text_used": False,
        "source_authority_verified": False,
        "target_domain_validated": False,
        "analogy_is_evidence": False,
        "authority_transferred": False,
        "execution_authorized": False,
        "invariants_applied": INVARIANTS,
        "claim_ceiling": CLAIM_CEILING,
    }
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode("utf-8")
    if len(encoded) > MAX_OUTPUT_BYTES:
        raise StructuralAnalogySearchError("result exceeds 256 KiB")
    return result


def analyze_bytes(payload: bytes) -> dict[str, Any]:
    digest = hashlib.sha256(payload).hexdigest()
    if len(payload) > MAX_INPUT_BYTES:
        raise StructuralAnalogySearchError("stdin request exceeds 256 KiB")
    try:
        request = json.loads(payload.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except StructuralAnalogySearchError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise StructuralAnalogySearchError("stdin must be one valid UTF-8 JSON object") from exc
    return search_structural_analogies(request, raw_digest=digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON request from stdin")
    parser.parse_args(argv)
    try:
        payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        result = analyze_bytes(payload)
    except (OSError, StructuralAnalogySearchError, TypeError, KeyError, ValueError) as exc:
        print("STRUCTURAL_ANALOGY_SEARCH_NOT_AVAILABLE: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
