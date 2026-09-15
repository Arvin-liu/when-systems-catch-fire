#!/usr/bin/env python3
"""Read-only Task172 Step07 routing over the frozen compact facet index.

The routing index is a bounded discovery aid.  It never becomes an authority:
the selected canonical IDs are re-read from the Current registries and their
record fingerprints are checked before they are returned.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


INDEX_REL = Path("data/research/task172-routing-r1/step07-routing-index.json")
FUNCTION_AUTHORITY_REL = Path("data/foundation/function-assets/identity-cards.jsonl")
NONFUNCTION_AUTHORITY_REL = Path("data/foundation/nonfunction-claims/claim-registry.jsonl")
DEFAULT_TOP_K = 120

FACET_KEYS = {
    "unesco_field_codes": "by_unesco_field",
    "unesco_discipline_codes": "by_unesco_discipline",
    "asset_role": "by_asset_role",
    "collision_use": "by_collision_use",
    "topic": "by_topic",
    "classification_state": "by_classification_state",
}
WEIGHTS = {
    "unesco_field_codes": 4,
    "unesco_discipline_codes": 8,
    "asset_role": 2,
    "collision_use": 3,
    "topic": 2,
    "classification_state": 1,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_index(repo_root: Path) -> dict[str, Any]:
    index = read_json(repo_root / INDEX_REL)
    if index.get("schema_version") != "task172-step07-routing-index-v1":
        raise ValueError("Task172 Step07 routing index schema is not supported")
    return index


def _normalise_values(query: dict[str, Any], key: str) -> set[str]:
    value = query.get(key, [])
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        raise ValueError(f"query facet must be a list or string: {key}")
    return {str(item) for item in value if str(item).strip()}


def _ref_key(asset_kind: str, canonical_id: str) -> str:
    return f"{asset_kind}:{canonical_id}"


def _authority_maps(repo_root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "FUNCTION_ASSET": {row["canonical_id"]: row for row in read_jsonl(repo_root / FUNCTION_AUTHORITY_REL)},
        "NONFUNCTION_CLAIM": {row["canonical_id"]: row for row in read_jsonl(repo_root / NONFUNCTION_AUTHORITY_REL)},
    }

def _query_facets(query: dict[str, Any]) -> dict[str, set[str]]:
    return {key: _normalise_values(query, key) for key in FACET_KEYS}


def _asset_kind_filter(query: dict[str, Any]) -> set[str]:
    values = query.get("asset_kinds", ["FUNCTION_ASSET", "NONFUNCTION_CLAIM"])
    if isinstance(values, str):
        values = [values]
    allowed = {str(value) for value in values}
    invalid = allowed - {"FUNCTION_ASSET", "NONFUNCTION_CLAIM"}
    if invalid:
        raise ValueError(f"unsupported asset kinds: {sorted(invalid)}")
    return allowed


def _matched_facets(record: dict[str, Any], facets: dict[str, set[str]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for key, requested in facets.items():
        if not requested:
            continue
        matched = sorted(requested & set(record.get(key, [])))
        if matched:
            result[key] = matched
    return result


def _records_by_ref(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        _ref_key(row["asset_kind"], row["canonical_id"]): row
        for row in index.get("records", [])
    }


def _validate_selected(
    repo_root: Path,
    selected: list[dict[str, Any]],
    authorities: dict[str, dict[str, dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    for item in selected:
        kind = item["asset_kind"]
        canonical_id = item["canonical_id"]
        authority = authorities.get(kind, {}).get(canonical_id)
        if authority is None:
            invalid.append({"asset_kind": kind, "canonical_id": canonical_id, "reason": "MISSING_CURRENT_AUTHORITY"})
            continue
        if authority.get("record_sha256") != item.get("source_record_sha"):
            invalid.append({"asset_kind": kind, "canonical_id": canonical_id, "reason": "AUTHORITY_FINGERPRINT_MISMATCH"})
            continue
        valid.append(item)
    return valid, invalid


def retrieve_candidates(repo_root: Path, query: dict[str, Any], top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
    """Return a transparent, bounded, exact-validated routing result."""
    if top_k <= 0 or top_k > 1000:
        raise ValueError("top_k must be in the range 1..1000")
    index = load_index(repo_root)
    records = _records_by_ref(index)
    facets = _query_facets(query)
    allowed_kinds = _asset_kind_filter(query)
    requested_facets = {key: sorted(values) for key, values in facets.items() if values}

    facet_sets: list[set[str]] = []
    for key, values in facets.items():
        if not values:
            continue
        facet_index = index.get("facets", {}).get(FACET_KEYS[key], {})
        refs = set().union(*(set(facet_index.get(value, [])) for value in values))
        refs = {ref for ref in refs if records.get(ref, {}).get("asset_kind") in allowed_kinds}
        facet_sets.append(refs)

    if facet_sets:
        exact_universe = set.intersection(*facet_sets)
        union_universe = set.union(*facet_sets)
    else:
        exact_universe = set()
        union_universe = set()

    fallback = False
    fallback_reason = None
    if requested_facets and exact_universe:
        candidate_universe = exact_universe
    elif requested_facets and union_universe:
        fallback = True
        fallback_reason = "EXACT_FACET_INTERSECTION_EMPTY"
        candidate_universe = union_universe
    else:
        fallback = True
        fallback_reason = "NO_BOUNDED_FACETS"
        candidate_universe = {ref for ref, row in records.items() if row.get("asset_kind") in allowed_kinds}

    lexical_terms = {str(term).casefold() for term in query.get("lexical_terms", []) if str(term).strip()}
    authorities = _authority_maps(repo_root)

    scored: list[tuple[int, str, dict[str, Any], dict[str, list[str]]]] = []
    for ref in candidate_universe:
        record = records[ref]
        matched = _matched_facets(record, facets)
        score = sum(WEIGHTS[key] * len(values) for key, values in matched.items())
        if lexical_terms:
            authority = authorities[record["asset_kind"]].get(record["canonical_id"], {})
            title = str(authority.get("title", authority.get("canonical_title", ""))).casefold()
            if any(term in title for term in lexical_terms):
                score += 1
                matched["lexical_terms"] = sorted(term for term in lexical_terms if term in title)
        scored.append((score, ref, record, matched))

    scored.sort(key=lambda item: (-item[0], item[1]))
    selected_rows = [
        {
            "asset_kind": record["asset_kind"],
            "canonical_id": record["canonical_id"],
            "source_record_sha": record["source_record_sha"],
            "score": score,
            "matched_facets": matched,
        }
        for score, _ref, record, matched in scored[:top_k]
    ]
    valid, invalid = _validate_selected(repo_root, selected_rows, authorities)
    return {
        "schema_version": "task172-step07-routing-result-v1",
        "operation_id": "knowledge.collide_object",
        "run_mode": "READ_ONLY_RUN",
        "derived_query_facets": requested_facets,
        "candidate_universe_size": len(candidate_universe),
        "selected_count": len(valid),
        "selected_canonical_ids": [
            {"asset_kind": row["asset_kind"], "canonical_id": row["canonical_id"]}
            for row in valid
        ],
        "selected": valid,
        "exact_validation_status": "ALL_SELECTED_EXACT" if not invalid else "INVALID_SELECTIONS_REJECTED",
        "invalid_selection_count": len(invalid),
        "invalid_selections": invalid,
        "fallback": {
            "occurred": fallback,
            "reason": fallback_reason,
            "explicit": True,
        },
        "coverage_warning": None if not fallback else "Bounded facet intersection was insufficient; inspect fallback reason before treating recall as complete.",
        "top_k": top_k,
        "side_effects": {"repository_mutation": False, "external_action": False, "registry_write": False},
    }
