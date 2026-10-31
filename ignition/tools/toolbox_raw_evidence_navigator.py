#!/usr/bin/env python3
"""Navigate the checked-out Knowledge index, then reopen matching raw sources.

This is lexical navigation only. A match is not evidence that a claim is true
or that an evidence requirement has been satisfied.
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
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
INDEX_REL = "ignition/data/governance/knowledge-experience/search-index.jsonl"
TOOL_ID = "knowledge.navigate_raw_evidence"
TOOL_VERSION = "0.1.0"
MAX_REQUEST_BYTES = 32_000
MAX_INDEX_BYTES = 64 * 1024 * 1024
MAX_INDEX_RECORDS = 50_000
MAX_REQUIREMENTS = 8
MAX_TERMS_PER_REQUIREMENT = 12
MAX_SOURCES_PER_REQUIREMENT = 8
MAX_TOTAL_SOURCE_BYTES = 2_000_000
MAX_EXCERPT_CHARS = 2_000
MAX_HITS_PER_SOURCE = 8
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

CLAIM_CEILING = (
    "Lexical navigation through entries in the checked-out Knowledge search index, followed by "
    "reopening bounded current-checkout source files and reporting exact line matches and hashes. "
    "No new or unindexed source discovery, semantic relevance, evidence coverage, truth, proof, "
    "source authenticity, scientific acceptance, or publication readiness is established."
)


class RawEvidenceNavigationError(ValueError):
    """Raised when bounded local navigation cannot be performed safely."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RawEvidenceNavigationError("duplicate JSON input key: " + key)
        result[key] = value
    return result


def _normalize_source_path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise RawEvidenceNavigationError("indexed source path is blank or invalid")
    if value.startswith("/") or Path(value).is_absolute() or re.match(r"^[A-Za-z]:", value):
        raise RawEvidenceNavigationError("indexed source path must be repository-relative")
    if value.startswith("ignition/"):
        relative = value
    else:
        relative = "ignition/" + value
    parts = Path(relative).parts
    if Path(relative).is_absolute() or any(part in {"", ".", ".."} for part in parts):
        raise RawEvidenceNavigationError("indexed source path contains traversal")
    if not relative.startswith("ignition/"):
        raise RawEvidenceNavigationError("indexed source path must remain under ignition/")
    return relative


def _safe_repo_file(repo_root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path.startswith("ignition/"):
        raise RawEvidenceNavigationError("source paths must remain under ignition/")
    root = Path(repo_root)
    if root.is_symlink():
        raise RawEvidenceNavigationError("repository root must not be a symlink")
    root = root.resolve()
    candidate = root
    for part in Path(relative_path).parts:
        if part in {"", ".", ".."}:
            raise RawEvidenceNavigationError("source path contains traversal")
        candidate = candidate / part
        if candidate.is_symlink():
            raise RawEvidenceNavigationError("source path contains a symlink")
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise RawEvidenceNavigationError("source path escapes the repository") from exc
    return candidate


def _validate_request(request: Any) -> dict[str, Any]:
    required = {
        "requirements",
        "max_sources_per_requirement",
        "max_total_source_bytes",
        "max_excerpt_chars",
    }
    if not isinstance(request, dict) or set(request) != required:
        raise RawEvidenceNavigationError("request must contain exactly " + ", ".join(sorted(required)))
    requirements = request["requirements"]
    if not isinstance(requirements, list) or not requirements or len(requirements) > MAX_REQUIREMENTS:
        raise RawEvidenceNavigationError("requirements must contain 1 to 8 entries")
    max_sources = request["max_sources_per_requirement"]
    max_bytes = request["max_total_source_bytes"]
    max_excerpt = request["max_excerpt_chars"]
    if isinstance(max_sources, bool) or not isinstance(max_sources, int) or not 1 <= max_sources <= MAX_SOURCES_PER_REQUIREMENT:
        raise RawEvidenceNavigationError("max_sources_per_requirement must be an integer from 1 to 8")
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or not 1 <= max_bytes <= MAX_TOTAL_SOURCE_BYTES:
        raise RawEvidenceNavigationError("max_total_source_bytes must be an integer from 1 to 2000000")
    if isinstance(max_excerpt, bool) or not isinstance(max_excerpt, int) or not 80 <= max_excerpt <= MAX_EXCERPT_CHARS:
        raise RawEvidenceNavigationError("max_excerpt_chars must be an integer from 80 to 2000")

    seen_ids: set[str] = set()
    clean_requirements: list[dict[str, Any]] = []
    for item in requirements:
        if not isinstance(item, dict) or set(item) != {"requirement_id", "query_terms"}:
            raise RawEvidenceNavigationError("each requirement must contain exactly requirement_id and query_terms")
        requirement_id = item["requirement_id"]
        terms = item["query_terms"]
        if not isinstance(requirement_id, str) or not _ID_RE.fullmatch(requirement_id):
            raise RawEvidenceNavigationError("requirement_id must be a bounded stable identifier")
        if requirement_id in seen_ids:
            raise RawEvidenceNavigationError("requirement_id values must be unique")
        seen_ids.add(requirement_id)
        if not isinstance(terms, list) or not terms or len(terms) > MAX_TERMS_PER_REQUIREMENT:
            raise RawEvidenceNavigationError("query_terms must contain 1 to 12 strings")
        normalized: list[str] = []
        for term in terms:
            if not isinstance(term, str) or not term.strip() or len(term.strip()) > 80:
                raise RawEvidenceNavigationError("query terms must be nonblank strings of at most 80 characters")
            folded = term.strip().casefold()
            if folded not in normalized:
                normalized.append(folded)
        if not normalized:
            raise RawEvidenceNavigationError("query_terms must contain at least one unique term")
        clean_requirements.append({"requirement_id": requirement_id, "query_terms": normalized})
    return {
        "requirements": clean_requirements,
        "max_sources_per_requirement": max_sources,
        "max_total_source_bytes": max_bytes,
        "max_excerpt_chars": max_excerpt,
    }


def _load_index(repo_root: Path) -> tuple[list[dict[str, Any]], str, int]:
    index_path = _safe_repo_file(repo_root, INDEX_REL)
    if not index_path.is_file():
        raise RawEvidenceNavigationError("checked-out Knowledge search index is missing")
    size = index_path.stat().st_size
    if size > MAX_INDEX_BYTES:
        raise RawEvidenceNavigationError("Knowledge search index exceeds the 64 MiB safety limit")
    raw = index_path.read_bytes()
    rows: list[dict[str, Any]] = []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RawEvidenceNavigationError("Knowledge search index is not UTF-8") from exc
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line, object_pairs_hook=_reject_duplicate_keys)
        except (json.JSONDecodeError, RawEvidenceNavigationError) as exc:
            raise RawEvidenceNavigationError("malformed Knowledge search index at line %d" % line_number) from exc
        if not isinstance(row, dict):
            raise RawEvidenceNavigationError("Knowledge search index row is not an object at line %d" % line_number)
        if not isinstance(row.get("search_id"), str) or not isinstance(row.get("canonical_source"), str):
            raise RawEvidenceNavigationError("Knowledge search index identity is incomplete at line %d" % line_number)
        rows.append(row)
        if len(rows) > MAX_INDEX_RECORDS:
            raise RawEvidenceNavigationError("Knowledge search index exceeds the 50000-record safety limit")
    return rows, hashlib.sha256(raw).hexdigest(), len(raw)


def _metadata_text(row: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("title", "aliases", "subjects", "canonical_source", "destination"):
        value = row.get(key)
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            values.extend(item for item in value if isinstance(item, str))
    return "\n".join(values).casefold()


def _candidate_sources(
    rows: list[dict[str, Any]], query_terms: list[str]
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        metadata = _metadata_text(row)
        matches = [term for term in query_terms if term in metadata]
        if not matches:
            continue
        try:
            path = _normalize_source_path(row["canonical_source"])
        except RawEvidenceNavigationError:
            path = "REJECTED:" + str(row["canonical_source"])
        digest = row.get("source_sha256")
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            digest = None
        candidate = grouped.get(path)
        item = {
            "path": path,
            "search_id": row["search_id"],
            "title": row.get("title") if isinstance(row.get("title"), str) else "",
            "indexed_source_sha256": digest,
            "matched_index_terms": matches,
            "match_count": len(matches),
        }
        if candidate is None:
            grouped[path] = item
        elif (item["match_count"], item["search_id"]) > (candidate["match_count"], candidate["search_id"]):
            grouped[path] = item
    return sorted(
        grouped.values(),
        key=lambda item: (-item["match_count"], item["path"].casefold(), item["search_id"]),
    )


def _source_result(
    candidate: dict[str, Any],
    query_terms: list[str],
    repo_root: Path,
    max_bytes: int,
    bytes_already_read: int,
    max_excerpt_chars: int,
) -> tuple[dict[str, Any], int, bool]:
    path_value = candidate["path"]
    if path_value.startswith("REJECTED:"):
        return (
            {
                **candidate,
                "source_status": "RAW_SOURCE_PATH_REJECTED",
                "line_matches": [],
                "indexed_digest_relation": "NOT_CHECKED",
            },
            0,
            False,
        )
    try:
        path = _safe_repo_file(repo_root, path_value)
    except RawEvidenceNavigationError:
        return (
            {
                **candidate,
                "source_status": "RAW_SOURCE_PATH_REJECTED",
                "line_matches": [],
                "indexed_digest_relation": "NOT_CHECKED",
            },
            0,
            False,
        )
    if not path.is_file():
        return (
            {
                **candidate,
                "source_status": "RAW_SOURCE_MISSING",
                "line_matches": [],
                "indexed_digest_relation": "NOT_CHECKED",
            },
            0,
            False,
        )
    size = path.stat().st_size
    if size > max_bytes - bytes_already_read:
        return (
            {
                **candidate,
                "source_status": "RAW_SOURCE_NOT_OPENED_BUDGET",
                "source_bytes": size,
                "line_matches": [],
                "indexed_digest_relation": "NOT_CHECKED",
            },
            0,
            True,
        )
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return (
            {
                **candidate,
                "source_status": "RAW_SOURCE_NOT_UTF8",
                "current_source_sha256": digest,
                "source_bytes": len(raw),
                "line_matches": [],
                "indexed_digest_relation": "NOT_CHECKED",
            },
            len(raw),
            False,
        )
    indexed_digest = candidate["indexed_source_sha256"]
    digest_relation = (
        "INDEXED_DIGEST_UNAVAILABLE"
        if indexed_digest is None
        else "MATCHES_INDEXED_DIGEST"
        if indexed_digest == digest
        else "DIFFERS_FROM_INDEXED_DIGEST"
    )
    hits: list[dict[str, Any]] = []
    matched_line_count = 0
    all_matched_terms: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        matched = [term for term in query_terms if term in line.casefold()]
        if not matched:
            continue
        matched_line_count += 1
        all_matched_terms.update(matched)
        if len(hits) < MAX_HITS_PER_SOURCE:
            excerpt = line[:max_excerpt_chars]
            hits.append(
                {
                    "line": line_number,
                    "matched_terms": matched,
                    "excerpt": excerpt,
                    "truncated": len(line) > len(excerpt),
                }
            )
    missing_terms = sorted(set(query_terms) - all_matched_terms)
    if not missing_terms:
        source_status = "CURRENT_RAW_MATCHES_ALL_QUERY_TERMS"
    elif all_matched_terms:
        source_status = "CURRENT_RAW_PARTIAL_QUERY_TERM_MATCH"
    else:
        source_status = "CURRENT_RAW_NO_TERM_MATCH"
    return (
        {
            **candidate,
            "source_status": source_status,
            "current_source_sha256": digest,
            "source_bytes": len(raw),
            "indexed_digest_relation": digest_relation,
            "matched_current_terms": sorted(all_matched_terms),
            "missing_current_terms": missing_terms,
            "matched_line_count": matched_line_count,
            "line_matches_truncated": matched_line_count > len(hits),
            "line_matches": hits,
        },
        len(raw),
        False,
    )


def build_navigation_result(request: Any, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Return bounded lexical candidates and current raw line matches."""
    clean = _validate_request(request)
    rows, index_digest, index_bytes = _load_index(Path(repo_root))
    total_budget = clean["max_total_source_bytes"]
    bytes_read = 0
    source_reads = 0
    requirements: list[dict[str, Any]] = []
    for requirement in clean["requirements"]:
        terms = requirement["query_terms"]
        candidates = _candidate_sources(rows, terms)
        selected = candidates[: clean["max_sources_per_requirement"]]
        result_sources: list[dict[str, Any]] = []
        budget_blocked = False
        for candidate in selected:
            result, consumed, blocked = _source_result(
                candidate,
                terms,
                Path(repo_root),
                total_budget,
                bytes_read,
                clean["max_excerpt_chars"],
            )
            if consumed:
                bytes_read += consumed
                source_reads += 1
            if blocked:
                budget_blocked = True
            result_sources.append(result)
        matches = sum(item.get("source_status") == "CURRENT_RAW_MATCHES_ALL_QUERY_TERMS" for item in result_sources)
        partial_matches = sum(item.get("source_status") == "CURRENT_RAW_PARTIAL_QUERY_TERM_MATCH" for item in result_sources)
        unopened_sources = sum(item.get("source_status") == "RAW_SOURCE_NOT_OPENED_BUDGET" for item in result_sources)
        if not candidates:
            status = "NO_INDEX_CANDIDATE"
            gap = "No indexed metadata entry matched the supplied literal query terms."
        elif matches:
            status = "RAW_MATCHES_FOUND_WITH_BUDGET_GAP" if unopened_sources else "RAW_MATCHES_FOUND"
            gap = (
                "All literal query terms occur in at least one reopened source; %d prioritized candidate source(s) "
                "were not opened within budget, and requirement coverage was not evaluated." % unopened_sources
                if unopened_sources
                else "All literal query terms occur in at least one reopened source; requirement coverage was not evaluated."
            )
        elif partial_matches:
            status = "PARTIAL_RAW_MATCHES_FOUND"
            gap = "Only some literal query terms occur in reopened sources; missing terms remain explicit."
        elif budget_blocked:
            status = "BUDGET_EXHAUSTED"
            gap = "At least one prioritized raw source was not reopened within the byte budget."
        else:
            status = "NO_CURRENT_RAW_MATCH"
            gap = "No selected current raw source produced a literal line match."
        requirements.append(
            {
                "requirement_id": requirement["requirement_id"],
                "query_terms": terms,
                "navigation_status": status,
                "candidate_source_count": len(candidates),
                "selected_source_count": len(selected),
                "current_raw_match_count": matches,
                "partial_raw_source_count": partial_matches,
                "unopened_source_count": unopened_sources,
                "sufficiency_decision": "NOT_EVALUATED",
                "unresolved_gap": gap,
                "sources": result_sources,
            }
        )
    return {
        "schema_version": "toolbox-raw-evidence-navigation-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "result_status": "NAVIGATION_HINTS_ONLY",
        "search_index": {
            "path": INDEX_REL,
            "sha256": index_digest,
            "record_count": len(rows),
            "bytes": index_bytes,
            "role": "NONAUTHORITATIVE_NAVIGATION_PRIOR",
        },
        "budgets": {
            "max_sources_per_requirement": clean["max_sources_per_requirement"],
            "max_total_source_bytes": total_budget,
            "source_bytes_read": bytes_read,
            "source_files_read": source_reads,
            "max_excerpt_chars": clean["max_excerpt_chars"],
            "max_line_matches_per_source": MAX_HITS_PER_SOURCE,
        },
        "requirements": requirements,
        "execution_authorized": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON navigation request")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    if len(raw) > MAX_REQUEST_BYTES:
        print("RAW_EVIDENCE_NAVIGATION_NOT_AVAILABLE: request exceeds the 32000-byte limit", file=sys.stderr)
        return 2
    try:
        request = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
        result = build_navigation_result(request)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RawEvidenceNavigationError, RecursionError) as exc:
        print("RAW_EVIDENCE_NAVIGATION_NOT_AVAILABLE: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
