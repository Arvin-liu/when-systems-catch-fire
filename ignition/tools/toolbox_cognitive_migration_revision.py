#!/usr/bin/env python3
"""Propose a verbatim paragraph reordering with bounded editorial diagnostics.

Derived from the bounded post-generation editorial-revision principles in
Formal PR #189 at 046570c6b69c3817b53167bebf8cf09cbf75e6d0. This optional,
offline adapter does not rewrite paragraph text or evaluate the evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


sys.dont_write_bytecode = True

TOOL_ID = "writing.preflight_cognitive_migration_revision"
TOOL_VERSION = "0.1.0"
MAX_INPUT_BYTES = 1_000_000
MAX_PARAGRAPHS = 80
MAX_PARAGRAPH_CHARS = 20_000
MAX_ANCHORS = 300
MOVE_TYPES = {
    "RECURSIVE_QUESTIONING",
    "PROGRESSIVE_DEEPENING",
    "PERSPECTIVE_SWITCHING",
}
PARAGRAPH_ROLES = {
    "LEDE",
    "BODY",
    "CLOSING",
    "EVIDENCE",
    "COUNTERARGUMENT",
    "AFFECTED_PERSON",
    "OTHER",
}
PROTECTED_ROLES = {"EVIDENCE", "COUNTERARGUMENT", "AFFECTED_PERSON"}
CLAIM_CEILING = (
    "Deterministic editorial structure proposal over caller-supplied paragraphs only. "
    "Selected text is copied verbatim and reordered; caller-supplied source anchors, "
    "claim limits, factual accuracy, causal meaning, literary quality, and publication "
    "readiness are not independently verified."
)

_PATTERNS = {
    "not_x_but_y": re.compile(r"(?:不是|并非|不再是).{0,100}(?:而是|而在于|而成为)"),
    "you_think_but": re.compile(r"你以为.{0,100}(?:其实|实际上|却|真正)"),
    "deepening_marker": re.compile(r"远不止|不止于"),
}


class ToolInputError(ValueError):
    """Raised when the request is malformed or outside the bounded contract."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ToolInputError(f"non-standard JSON constant is not allowed: {value}")


def _object(value: Any, required: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != required:
        raise ToolInputError(f"{label} must be an object with exactly: {', '.join(sorted(required))}")
    return value


def _nonblank(value: Any, label: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or "\x00" in value:
        raise ToolInputError(f"{label} must be a nonblank string of at most {maximum} characters")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise ToolInputError(f"{label} must contain valid Unicode scalar values") from exc
    return value


def _string_list(value: Any, label: str, *, maximum_items: int, maximum_length: int) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum_items:
        raise ToolInputError(f"{label} must be an array of at most {maximum_items} strings")
    result = [_nonblank(item, f"{label}[{index}]", maximum=maximum_length) for index, item in enumerate(value)]
    if len(result) != len(set(result)):
        raise ToolInputError(f"{label} values must be unique")
    return result


def parse_request(raw: bytes) -> dict[str, Any]:
    """Parse and validate one closed JSON request before producing any output."""

    if len(raw) > MAX_INPUT_BYTES:
        raise ToolInputError(f"request exceeds {MAX_INPUT_BYTES} bytes")
    try:
        request = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except ToolInputError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ToolInputError("request must be bounded, valid UTF-8 JSON") from exc

    top = _object(
        request,
        {"schema_version", "genre", "reader_shift", "claim_ceiling", "anchors", "paragraphs", "selected_paragraph_ids"},
        "request",
    )
    if top["schema_version"] != "ignition.cognitive-migration-revision-request.v1":
        raise ToolInputError("unsupported schema_version")
    if not isinstance(top["genre"], str) or top["genre"] not in {"MEDIUM_LENGTH_PUBLIC_ARTICLE", "OTHER"}:
        raise ToolInputError("genre must be MEDIUM_LENGTH_PUBLIC_ARTICLE or OTHER")
    top["claim_ceiling"] = _nonblank(top["claim_ceiling"], "claim_ceiling", maximum=2_000)

    shift = _object(top["reader_shift"], {"before", "after"}, "reader_shift")
    shift["before"] = _nonblank(shift["before"], "reader_shift.before", maximum=2_000)
    shift["after"] = _nonblank(shift["after"], "reader_shift.after", maximum=2_000)

    if not isinstance(top["anchors"], list) or len(top["anchors"]) > MAX_ANCHORS:
        raise ToolInputError(f"anchors must be an array of at most {MAX_ANCHORS} entries")
    anchors: dict[str, dict[str, str]] = {}
    for index, raw_anchor in enumerate(top["anchors"]):
        anchor = _object(raw_anchor, {"id", "exact_text", "source_ref"}, f"anchors[{index}]")
        anchor_id = _nonblank(anchor["id"], f"anchors[{index}].id", maximum=80)
        if anchor_id in anchors:
            raise ToolInputError(f"duplicate anchor id: {anchor_id}")
        anchors[anchor_id] = {
            "id": anchor_id,
            "exact_text": _nonblank(anchor["exact_text"], f"anchors[{index}].exact_text", maximum=1_000),
            "source_ref": _nonblank(anchor["source_ref"], f"anchors[{index}].source_ref", maximum=500),
        }

    paragraphs = top["paragraphs"]
    if not isinstance(paragraphs, list) or not 1 <= len(paragraphs) <= MAX_PARAGRAPHS:
        raise ToolInputError(f"paragraphs must contain between 1 and {MAX_PARAGRAPHS} entries")
    normalized: list[dict[str, Any]] = []
    paragraph_by_id: dict[str, dict[str, Any]] = {}
    used_anchor_ids: set[str] = set()
    for index, raw_paragraph in enumerate(paragraphs):
        paragraph = _object(
            raw_paragraph,
            {"id", "text", "role", "moves", "concepts", "anchor_ids"},
            f"paragraphs[{index}]",
        )
        paragraph_id = _nonblank(paragraph["id"], f"paragraphs[{index}].id", maximum=80)
        if paragraph_id in paragraph_by_id:
            raise ToolInputError(f"duplicate paragraph id: {paragraph_id}")
        text = _nonblank(paragraph["text"], f"paragraphs[{index}].text", maximum=MAX_PARAGRAPH_CHARS)
        if not isinstance(paragraph["role"], str) or paragraph["role"] not in PARAGRAPH_ROLES:
            raise ToolInputError(f"paragraphs[{index}].role is not a declared role")
        moves = _string_list(paragraph["moves"], f"paragraphs[{index}].moves", maximum_items=3, maximum_length=80)
        if not set(moves) <= MOVE_TYPES:
            raise ToolInputError(f"paragraphs[{index}].moves contains an unknown cognitive-move type")
        anchor_ids = _string_list(paragraph["anchor_ids"], f"paragraphs[{index}].anchor_ids", maximum_items=MAX_ANCHORS, maximum_length=80)
        if paragraph["role"] == "EVIDENCE" and not anchor_ids:
            raise ToolInputError(f"evidence paragraph {paragraph_id} must carry at least one declared source anchor")
        for anchor_id in anchor_ids:
            anchor = anchors.get(anchor_id)
            if anchor is None:
                raise ToolInputError(f"paragraph {paragraph_id} references unknown anchor {anchor_id}")
            if anchor["exact_text"] not in text:
                raise ToolInputError(f"paragraph {paragraph_id} does not contain the exact text for anchor {anchor_id}")
            used_anchor_ids.add(anchor_id)

        concepts = paragraph["concepts"]
        if not isinstance(concepts, list) or len(concepts) > 80:
            raise ToolInputError(f"paragraphs[{index}].concepts must be an array of at most 80 entries")
        concept_labels: list[str] = []
        concept_anchor_ids: list[str] = []
        for concept_index, raw_concept in enumerate(concepts):
            concept = _object(raw_concept, {"label", "anchor_id"}, f"paragraphs[{index}].concepts[{concept_index}]")
            label = _nonblank(concept["label"], f"paragraphs[{index}].concepts[{concept_index}].label", maximum=200)
            anchor_id = _nonblank(concept["anchor_id"], f"paragraphs[{index}].concepts[{concept_index}].anchor_id", maximum=80)
            if label in concept_labels:
                raise ToolInputError(f"paragraph {paragraph_id} repeats concept label {label}")
            if anchor_id not in anchor_ids:
                raise ToolInputError(f"concept {label} must reference an anchor attached to paragraph {paragraph_id}")
            concept_labels.append(label)
            concept_anchor_ids.append(anchor_id)
        if len(concept_anchor_ids) != len(set(concept_anchor_ids)):
            raise ToolInputError(f"each concept in paragraph {paragraph_id} must have its own declared anchor")

        normalized_paragraph = {
            "id": paragraph_id,
            "text": text,
            "role": paragraph["role"],
            "moves": moves,
            "concepts": [{"label": concept_labels[i], "anchor_id": concept_anchor_ids[i]} for i in range(len(concept_labels))],
            "anchor_ids": anchor_ids,
        }
        normalized.append(normalized_paragraph)
        paragraph_by_id[paragraph_id] = normalized_paragraph

    unused_anchors = set(anchors) - used_anchor_ids
    if unused_anchors:
        raise ToolInputError("every declared anchor must be attached to a paragraph: " + ", ".join(sorted(unused_anchors)))
    if not anchors and any(paragraph["concepts"] for paragraph in normalized):
        raise ToolInputError("every declared concept requires a source-anchored example")

    selected_ids = _string_list(top["selected_paragraph_ids"], "selected_paragraph_ids", maximum_items=MAX_PARAGRAPHS, maximum_length=80)
    if not selected_ids:
        raise ToolInputError("selected_paragraph_ids must contain at least one paragraph id")
    unknown_ids = [paragraph_id for paragraph_id in selected_ids if paragraph_id not in paragraph_by_id]
    if unknown_ids:
        raise ToolInputError("selected_paragraph_ids contains unknown IDs: " + ", ".join(unknown_ids))

    total_paragraph_chars = sum(len(paragraph["text"]) for paragraph in normalized)
    if total_paragraph_chars > MAX_INPUT_BYTES:
        raise ToolInputError("combined paragraph text exceeds the request byte limit")
    top["paragraphs"] = normalized
    top["anchors"] = list(anchors.values())
    top["selected_paragraph_ids"] = selected_ids
    top["_paragraph_by_id"] = paragraph_by_id
    top["_anchor_by_id"] = anchors
    return top


def _pattern_counts(text: str) -> dict[str, int]:
    return {name: len(pattern.findall(text)) for name, pattern in _PATTERNS.items()}


def build_review(raw: bytes) -> dict[str, Any]:
    """Build a deterministic proposal receipt for one bounded input request."""

    request = parse_request(raw)
    source_path = Path(__file__)
    if source_path.is_symlink() or not source_path.is_file():
        raise ToolInputError("tool wrapper must be a regular, non-symlink source file")
    wrapper_source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    paragraphs = request["paragraphs"]
    paragraph_by_id = request["_paragraph_by_id"]
    anchor_by_id = request["_anchor_by_id"]
    selected_ids = request["selected_paragraph_ids"]
    selected_id_set = set(selected_ids)
    omitted_ids = [paragraph["id"] for paragraph in paragraphs if paragraph["id"] not in selected_id_set]
    selected = [paragraph_by_id[paragraph_id] for paragraph_id in selected_ids]

    protected_omissions = [
        paragraph["id"]
        for paragraph in paragraphs
        if paragraph["id"] in omitted_ids and (paragraph["role"] in PROTECTED_ROLES or paragraph["anchor_ids"])
    ]
    findings: list[dict[str, Any]] = []
    if protected_omissions:
        findings.append({
            "code": "PROTECTED_CONTENT_OMITTED",
            "severity": "BLOCKER",
            "paragraph_ids": protected_omissions,
            "detail": "The proposal is withheld because an evidence-anchored, counterargument, or affected-person paragraph was omitted.",
        })
    optional_omissions = [paragraph_id for paragraph_id in omitted_ids if paragraph_id not in protected_omissions]
    if optional_omissions:
        findings.append({
            "code": "UNANCHORED_PARAGRAPHS_OMITTED",
            "severity": "REVIEW",
            "paragraph_ids": optional_omissions,
            "detail": "These unanchored paragraphs were excluded only because the caller omitted them from the requested order; review the selection before use.",
        })

    selected_moves = sorted({move for paragraph in selected for move in paragraph["moves"]})
    selected_body_count = sum(paragraph["role"] == "BODY" for paragraph in selected)
    if request["genre"] == "MEDIUM_LENGTH_PUBLIC_ARTICLE":
        if not 3 <= selected_body_count <= 5:
            findings.append({
                "code": "MEDIUM_ARTICLE_BODY_COUNT_OUTSIDE_REFERENCE_RANGE",
                "severity": "ADVISORY",
                "paragraph_ids": [paragraph["id"] for paragraph in selected if paragraph["role"] == "BODY"],
                "detail": "The source module offers 3–5 main paragraphs as a bounded outline example, not a universal writing rule.",
            })
        missing_moves = sorted(MOVE_TYPES - set(selected_moves))
        if missing_moves:
            findings.append({
                "code": "COGNITIVE_MOVE_VARIETY_REVIEW",
                "severity": "ADVISORY",
                "paragraph_ids": [],
                "detail": "Declared move annotations do not cover every reference type: " + ", ".join(missing_moves) + ". This is a review prompt, not a pass/fail rule.",
            })

    proposed_draft = None if protected_omissions else "\n\n".join(paragraph["text"] for paragraph in selected)
    proposal_counts = _pattern_counts(proposed_draft or "")
    repeated_patterns = sorted(name for name, count in proposal_counts.items() if count > 1)
    if repeated_patterns:
        findings.append({
            "code": "REPEATED_SURFACE_PATTERN_REVIEW",
            "severity": "ADVISORY",
            "paragraph_ids": [paragraph["id"] for paragraph in selected],
            "detail": "Repeated language patterns may expose editorial scaffolding; no phrase is banned: " + ", ".join(repeated_patterns) + ".",
        })

    selected_concepts = [concept for paragraph in selected for concept in paragraph["concepts"]]
    selected_anchor_ids = sorted({anchor_id for paragraph in selected for anchor_id in paragraph["anchor_ids"]})
    concept_anchor_ratio = {
        "concept_count": len(selected_concepts),
        "distinct_anchor_count": len({concept["anchor_id"] for concept in selected_concepts}),
        "one_distinct_anchor_per_concept": (
            len(selected_concepts) == 0
            or len({concept["anchor_id"] for concept in selected_concepts}) >= len(selected_concepts)
        ),
        "source_relation_verified": False,
    }
    if selected_concepts and not concept_anchor_ratio["one_distinct_anchor_per_concept"]:
        findings.append({
            "code": "CONCEPT_ANCHOR_RATIO_REVIEW",
            "severity": "ADVISORY",
            "paragraph_ids": [paragraph["id"] for paragraph in selected if paragraph["concepts"]],
            "detail": "At least one distinct declared source anchor per concept is the reference ratio; a reused anchor is reported for human review.",
        })

    paragraph_audit = []
    for paragraph in selected:
        paragraph_audit.append({
            "id": paragraph["id"],
            "role": paragraph["role"],
            "word_count_whitespace_split": len(paragraph["text"].split()),
            "moves_declared_by_caller": paragraph["moves"],
            "concept_count": len(paragraph["concepts"]),
            "concept_anchor_pairs": paragraph["concepts"],
            "anchor_ids": paragraph["anchor_ids"],
            "formula_pattern_counts": _pattern_counts(paragraph["text"]),
        })

    source_payload = json.dumps(
        [{key: paragraph[key] for key in ("id", "text", "role", "moves", "concepts", "anchor_ids")} for paragraph in paragraphs],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    output: dict[str, Any] = {
        "schema": "ignition.toolbox.cognitive-migration-revision.receipt.v1",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "review_status": "BLOCKED_PROTECTED_CONTENT_OMITTED" if protected_omissions else "PROPOSAL_REQUIRES_HUMAN_REVIEW",
        "execution_authorized": False,
        "text_policy": "COPY_SELECTED_PARAGRAPHS_VERBATIM_IN_CALLER_ORDER; NO_SENTENCE_REWRITE_OR_FACT_CHECK",
        "reader_shift": request["reader_shift"],
        "claim_ceiling_supplied_by_caller": request["claim_ceiling"],
        "claim_ceiling_evaluated": False,
        "request_sha256": hashlib.sha256(raw).hexdigest(),
        "source_paragraphs_sha256": hashlib.sha256(source_payload).hexdigest(),
        "wrapper_source_sha256": wrapper_source_sha256,
        "source_paragraph_count": len(paragraphs),
        "selected_paragraph_ids": selected_ids,
        "omitted_paragraph_ids": omitted_ids,
        "protected_omission_ids": protected_omissions,
        "proposal_text": proposed_draft,
        "proposal_text_sha256": hashlib.sha256(proposed_draft.encode("utf-8")).hexdigest() if proposed_draft is not None else None,
        "proposal_is_verbatim_join_of_selected_paragraphs": proposed_draft == "\n\n".join(paragraph["text"] for paragraph in selected) if proposed_draft is not None else False,
        "selected_move_types_declared_by_caller": selected_moves,
        "concept_anchor_ratio": concept_anchor_ratio,
        "selected_source_refs": [anchor_by_id[anchor_id]["source_ref"] for anchor_id in selected_anchor_ids],
        "source_ref_relation_verified": False,
        "proposal_formula_pattern_counts": proposal_counts,
        "paragraph_audit": paragraph_audit,
        "findings": findings,
        "claim_ceiling": CLAIM_CEILING,
    }
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON request from stdin")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        receipt = build_review(raw)
    except (OSError, TypeError, ValueError, KeyError, RecursionError) as exc:
        print("COGNITIVE_MIGRATION_REVISION_INPUT_INVALID: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
