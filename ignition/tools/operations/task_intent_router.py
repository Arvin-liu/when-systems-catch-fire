"""Resolve task-intent candidates against caller-typed input and the Current registry."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Mapping


HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[2]
REPO_ROOT = IGNITION_ROOT.parent
INDEX_PATH = REPO_ROOT / "ignition/data/operations/task-intent-index-r1.json"
REGISTRY_PATH = REPO_ROOT / "ignition/data/operations/ignition-operation-capability-registry-r1.json"
CALLABLE_STATUSES = frozenset({"CURRENT", "CURRENT_BOUNDED"})
CALLABILITIES = frozenset({"PUBLIC", "PUBLIC_BOUNDED"})


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_task_intent(
    query: str,
    input_type: str | None,
    *,
    intent_index: Mapping[str, Any] | None = None,
    operation_registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return discovery candidates only; never select, invoke, or authorize an operation.

    ``input_type`` must come from a separately checked typed input. This resolver does
    not infer an object's type from the query text or from a keyword match.
    """
    if intent_index is None:
        intent_index = _load(INDEX_PATH)
    if operation_registry is None:
        operation_registry = _load(REGISTRY_PATH)

    if not isinstance(query, str) or not query.strip() or not isinstance(input_type, str) or not input_type.strip():
        return {
            "status": "UNSUPPORTED",
            "reason": "A non-empty query and caller-verified input_type are required.",
            "candidates": [],
            "authority_boundary": "DISCOVERY_ONLY_NO_EXECUTION_OR_AUTHORIZATION",
        }

    operations = {item["operation_id"]: item for item in operation_registry.get("operations", [])}
    eligible: dict[str, dict[str, Any]] = {}
    for entry in intent_index.get("entries", []):
        operation = operations.get(entry.get("operation_id"))
        if not operation:
            continue
        if operation.get("current_status") not in CALLABLE_STATUSES:
            continue
        if operation.get("ai_callability") not in CALLABILITIES:
            continue
        if input_type not in operation.get("accepted_input_types", []):
            continue
        eligible[operation["operation_id"]] = entry

    if not eligible:
        return {
            "status": "UNSUPPORTED",
            "input_type": input_type,
            "reason": "No indexed Current capability accepts this caller-verified input type.",
            "candidates": [],
            "authority_boundary": "DISCOVERY_ONLY_NO_EXECUTION_OR_AUTHORIZATION",
        }

    normalized_query = _normalize(query)
    matched: list[dict[str, Any]] = []
    for operation_id, entry in sorted(eligible.items()):
        terms = []
        for field in ("aliases_zh", "aliases_en", "keywords_zh", "keywords_en"):
            terms.extend(entry.get(field, []))
        reasons = sorted({term for term in terms if term and _normalize(term) in normalized_query})
        if reasons:
            matched.append({
                "operation_id": operation_id,
                "component_ids": list(entry.get("component_ids", [])),
                "matched_terms": reasons,
                "input_type_source_ref": entry["input_type_source_ref"],
            })

    if not matched:
        return {
            "status": "UNSUPPORTED",
            "input_type": input_type,
            "reason": "No indexed intent phrase matched after Current and input-type filtering.",
            "candidates": [],
            "authority_boundary": "DISCOVERY_ONLY_NO_EXECUTION_OR_AUTHORIZATION",
        }
    if len(matched) > 1:
        return {
            "status": "UNRESOLVED",
            "input_type": input_type,
            "reason": "Multiple Current operations match; the resolver does not rank or force a unique result.",
            "candidates": matched,
            "authority_boundary": "DISCOVERY_ONLY_NO_EXECUTION_OR_AUTHORIZATION",
        }
    return {
        "status": "CANDIDATE",
        "input_type": input_type,
        "reason": "One discovery candidate matched; verify its complete contract in the operation registry before any action.",
        "candidates": matched,
        "authority_boundary": "DISCOVERY_ONLY_NO_EXECUTION_OR_AUTHORIZATION",
    }
