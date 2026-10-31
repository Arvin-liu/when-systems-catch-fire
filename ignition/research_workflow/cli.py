#!/usr/bin/env python3
"""Create a source-backed research brief from a question and search queries.

The workflow can capture OpenAlex responses or import offline source snapshots,
validate citations in an optional agent-authored synthesis, and write a Markdown
report plus machine-readable manifests and a hash receipt. It never claims that
citation syntax, metadata, or exact excerpt anchors validate source contents.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import os
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


IGNITION_DIR = Path(__file__).resolve().parents[1]
_EXTERNAL_RESEARCH = IGNITION_DIR / "scripts" / "external-research"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


openalex_client = _load_module("ignition_openalex_client", _EXTERNAL_RESEARCH / "openalex_client.py")
crossref_runner = _load_module(
    "ignition_crossref_runner", IGNITION_DIR / "evidence-program" / "tools" / "run_crossref_verification.py"
)

MAX_QUERIES = 12
MAX_RESULTS_PER_QUERY = 25
MAX_SOURCES = 50
CITATION_RE = re.compile(r"\[(S[0-9]+)\]")
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^<>]*>")
CLAIM_REVIEW_JUDGMENTS = {"SUPPORTS", "CONTRADICTS", "CONTEXT_ONLY", "INSUFFICIENT", "NOT_REVIEWED"}
CLAIM_EVIDENCE_FIELDS = {"title", "abstract", "captured_text"}
MAX_SOURCE_SNAPSHOT_BYTES = 10_000_000
MAX_SOURCE_SNAPSHOT_MANIFEST_BYTES = 1_000_000
MAX_SNAPSHOT_SOURCES_PER_QUESTION = 5
SOURCE_SNAPSHOT_KINDS = {"web_run_observation", "official_api_json"}


class EvidenceIntegrityError(ValueError):
    """A provider/test adapter returned normalized data detached from raw bytes."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    data = b"".join(_json_bytes(row) for row in rows)
    _write_bytes(path, data)


def _source_key(item: dict[str, Any]) -> str:
    if item.get("openalex_id"):
        return str(item["openalex_id"]).casefold()
    if item.get("doi"):
        return str(item["doi"]).casefold()
    return f"{crossref_runner.norm(item.get('title'))}:{item.get('year')}"


def _normalized_title(value: Any) -> str:
    """Normalize title text after removing Crossref's inline markup tags."""
    text = HTML_TAG_RE.sub(" ", html.unescape(str(value or "")))
    return crossref_runner.norm(text)


def _select_candidates_round_robin(
    candidates: dict[str, dict[str, Any]],
    query_ids: list[str],
    limit: int,
) -> list[dict[str, Any]]:
    """Select unique records fairly across queries, preserving each query's ranks."""
    ranked_by_query: dict[str, list[tuple[int, str, dict[str, Any]]]] = {
        query_id: [] for query_id in query_ids
    }
    for key, candidate in candidates.items():
        for query_id, rank in candidate["rank_by_query"].items():
            if query_id in ranked_by_query:
                ranked_by_query[query_id].append((int(rank), key, candidate))
    for ranked in ranked_by_query.values():
        ranked.sort(key=lambda entry: (entry[0], entry[1]))

    selected: list[dict[str, Any]] = []
    selected_keys: set[str] = set()
    positions = {query_id: 0 for query_id in query_ids}
    while len(selected) < limit:
        added_this_round = False
        for query_id in query_ids:
            ranked = ranked_by_query[query_id]
            position = positions[query_id]
            while position < len(ranked) and ranked[position][1] in selected_keys:
                position += 1
            positions[query_id] = position
            if position >= len(ranked):
                continue
            _, key, candidate = ranked[position]
            positions[query_id] += 1
            selected_keys.add(key)
            selected.append(candidate)
            added_this_round = True
            if len(selected) >= limit:
                break
        if not added_this_round:
            break
    return selected


def _redact_request_url(raw_url: str | None) -> str | None:
    if not raw_url:
        return raw_url
    parts = urlsplit(raw_url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key.casefold() != "mailto"]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _redact_command(command: list[str]) -> list[str]:
    redacted = []
    redact_next = False
    for token in command:
        if redact_next:
            redacted.append("<provided>")
            redact_next = False
            continue
        redacted.append(token)
        if token in {"--mailto", "--draft", "--output-dir", "--claim-reviews", "--source-snapshots"}:
            redact_next = True
    return redacted


def _markdown_escape(text: str) -> str:
    """Keep caller-supplied source metadata from changing Markdown structure."""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|>])", r"\\\1", text)


def _verify_doi(
    source: dict[str, Any],
    fetch: Callable[[str], dict[str, Any]],
    raw_dir: Path | None = None,
) -> dict[str, Any]:
    doi = crossref_runner.bare_doi(source.get("doi"))
    row: dict[str, Any] = {
        "source_id": source["source_id"],
        "doi": doi,
        "checked_at_utc": utc_now(),
        "provider": "Crossref REST API",
    }
    if not doi:
        row.update({"acquisition_status": "NO_DOI", "metadata_match_status": "NOT_APPLICABLE"})
        return row

    try:
        response = fetch(doi)
    except Exception as exc:
        response = {"http_ok": False, "status": -1, "error_type": type(exc).__name__}
    if not response.get("http_ok"):
        status = response.get("status")
        row.update({
            "acquisition_status": "RESOLUTION_FAILED" if status == 404 else "NETWORK_ERROR",
            "metadata_match_status": "UNDETERMINED",
            "http_status": status,
            "error_type": response.get("error_type"),
        })
        return row

    body = response["body"]
    row["response_sha256"] = sha256(body)
    if raw_dir is not None:
        raw_path = raw_dir / f"crossref-{source['source_id']}.json"
        _write_bytes(raw_path, body)
        row["raw_response_path"] = raw_path.relative_to(raw_dir.parent).as_posix()
    try:
        message = json.loads(body.decode("utf-8"))["message"]
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
        row.update({"acquisition_status": "INVALID_RESPONSE", "metadata_match_status": "UNDETERMINED"})
        return row

    observed_title = (message.get("title") or [None])[0]
    observed_year = crossref_runner.extract_year(message)
    expected_title = source.get("title")
    expected_year = source.get("year")
    title_match = (
        _normalized_title(observed_title) == _normalized_title(expected_title)
        if observed_title and expected_title else None
    )
    try:
        year_match = int(observed_year) == int(expected_year) if observed_year and expected_year else None
    except (TypeError, ValueError):
        year_match = None
    if title_match is True and year_match is True:
        match_status = "MATCH"
    elif title_match is False or year_match is False:
        match_status = "MISMATCH"
    else:
        match_status = "PARTIAL_OR_MISSING_METADATA"
    row.update({
        "acquisition_status": "OK",
        "metadata_match_status": match_status,
        "observed_title": observed_title,
        "observed_year": observed_year,
        "title_match": title_match,
        "year_match": year_match,
        "retraction_signal": crossref_runner.retraction_signal(message),
    })
    return row


def _validate_draft(draft: str, source_ids: set[str]) -> None:
    references = set(CITATION_RE.findall(draft))
    if not references:
        raise ValueError("draft must cite at least one captured source using [S1], [S2], ...")
    unknown = sorted(references - source_ids)
    if unknown:
        raise ValueError(f"draft cites unknown source IDs: {', '.join(unknown)}")


def _read_claim_reviews(path: str | Path | bytes | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    rows = []
    seen_claim_sources = set()
    raw_text = path.decode("utf-8") if isinstance(path, bytes) else Path(path).read_text(encoding="utf-8")
    for line_number, line in enumerate(raw_text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid claim-review JSON on line {line_number}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"claim-review line {line_number} must be a JSON object")
        for field in ("claim_id", "claim_text", "source_id", "review_judgment"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"claim-review line {line_number} requires non-empty {field}")
        if row["review_judgment"] not in CLAIM_REVIEW_JUDGMENTS:
            raise ValueError(f"claim-review line {line_number} has an unsupported review_judgment")
        reviewer_type = row.get("reviewer_type", "NOT_REVIEWED")
        if not isinstance(reviewer_type, str) or reviewer_type not in {"HUMAN", "NOT_REVIEWED"}:
            raise ValueError(f"claim-review line {line_number} has an unsupported reviewer_type")
        if reviewer_type == "HUMAN":
            required = ("reviewer", "reviewed_at_utc", "evidence_field", "evidence_quote")
            missing = [field for field in required if not isinstance(row.get(field), str) or not row[field].strip()]
            if missing:
                raise ValueError(f"claim-review line {line_number} requires {', '.join(missing)} for HUMAN review")
            if row["review_judgment"] == "NOT_REVIEWED":
                raise ValueError(f"claim-review line {line_number} cannot pair HUMAN with NOT_REVIEWED")
            if row["evidence_field"] not in CLAIM_EVIDENCE_FIELDS:
                raise ValueError(f"claim-review line {line_number} evidence_field must be title, abstract, or captured_text")
        elif row["review_judgment"] != "NOT_REVIEWED":
            raise ValueError(f"claim-review line {line_number} requires reviewer_type HUMAN for a judgment")
        if "evidence_quote" in row and not isinstance(row["evidence_quote"], str):
            raise ValueError(f"claim-review line {line_number} evidence_quote must be a string")
        if "evidence_field" in row and (
            not isinstance(row["evidence_field"], str) or row["evidence_field"] not in CLAIM_EVIDENCE_FIELDS
        ):
            raise ValueError(f"claim-review line {line_number} evidence_field must be title, abstract, or captured_text")
        for field in ("reviewer", "reviewed_at_utc", "review_note"):
            if field in row and row[field] is not None and not isinstance(row[field], str):
                raise ValueError(f"claim-review line {line_number} {field} must be a string")
        key = (row["claim_id"], row["source_id"])
        if key in seen_claim_sources:
            raise ValueError(f"claim-review line {line_number} duplicates claim_id/source_id")
        seen_claim_sources.add(key)
        rows.append(row)
    return rows


def _read_source_snapshots(path: str | Path, query_count: int) -> tuple[list[dict[str, Any]], bytes]:
    """Read offline UTF-8 source captures and reject detached or unsafe inputs."""
    manifest_path = Path(path)
    manifest_bytes = manifest_path.read_bytes()
    if len(manifest_bytes) > MAX_SOURCE_SNAPSHOT_MANIFEST_BYTES:
        raise ValueError("source-snapshot manifest exceeds the 1 MB limit")
    rows: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    api_snapshot_count = 0
    for line_number, line in enumerate(manifest_bytes.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        if len(rows) >= MAX_SNAPSHOT_SOURCES_PER_QUESTION:
            raise ValueError("at most five source snapshots are allowed per research question")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"source-snapshot JSON is invalid on line {line_number}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"source-snapshot line {line_number} must be a JSON object")
        for field in ("title", "source_url", "capture_path", "capture_kind", "captured_at_utc", "locator"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"source-snapshot line {line_number} requires non-empty {field}")
        if row["capture_kind"] not in SOURCE_SNAPSHOT_KINDS:
            raise ValueError(f"source-snapshot line {line_number} has an unsupported capture_kind")
        source_url = row["source_url"].strip()
        url = urlsplit(source_url)
        if (
            url.scheme != "https" or not url.netloc or url.username or url.password
            or any(character.isspace() or ord(character) < 32 for character in source_url)
            or any(character in source_url for character in "<>\\")
        ):
            raise ValueError(f"source-snapshot line {line_number} source_url must be an HTTPS URL without credentials")
        normalized_url = urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path.rstrip("/"), url.query, ""))
        if normalized_url in seen_urls:
            raise ValueError(f"source-snapshot line {line_number} duplicates a source_url")
        seen_urls.add(normalized_url)
        capture_rel = Path(row["capture_path"])
        if capture_rel.is_absolute() or ".." in capture_rel.parts:
            raise ValueError(f"source-snapshot line {line_number} capture_path must stay under the manifest directory")
        capture_path = manifest_path.parent / capture_rel
        try:
            resolved_capture = capture_path.resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"source-snapshot line {line_number} capture_path cannot be read") from exc
        try:
            resolved_capture.relative_to(manifest_path.parent.resolve())
        except ValueError as exc:
            raise ValueError(f"source-snapshot line {line_number} capture_path escapes the manifest directory") from exc
        try:
            if resolved_capture.stat().st_size > MAX_SOURCE_SNAPSHOT_BYTES:
                raise ValueError(f"source-snapshot line {line_number} exceeds the 10 MB capture limit")
        except OSError as exc:
            raise ValueError(f"source-snapshot line {line_number} capture_path cannot be read") from exc
        try:
            raw = resolved_capture.read_bytes()
        except OSError as exc:
            raise ValueError(f"source-snapshot line {line_number} capture_path cannot be read") from exc
        if not raw:
            raise ValueError(f"source-snapshot line {line_number} capture is empty")
        if len(raw) > MAX_SOURCE_SNAPSHOT_BYTES:
            raise ValueError(f"source-snapshot line {line_number} exceeds the 10 MB capture limit")
        try:
            captured_text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"source-snapshot line {line_number} capture must be UTF-8") from exc
        if row["capture_kind"] == "official_api_json":
            api_snapshot_count += 1
            if api_snapshot_count > 1:
                raise ValueError("at most one official_api_json source snapshot is allowed per run")
            try:
                json.loads(captured_text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"source-snapshot line {line_number} official_api_json capture is invalid JSON") from exc
        captured_at_utc = row["captured_at_utc"].strip()
        try:
            parsed_captured_at = datetime.fromisoformat(captured_at_utc.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"source-snapshot line {line_number} captured_at_utc must be ISO-8601") from exc
        offset = parsed_captured_at.utcoffset()
        if parsed_captured_at.tzinfo is None or offset is None or offset.total_seconds() != 0:
            raise ValueError(f"source-snapshot line {line_number} captured_at_utc must include a UTC timezone")
        query_ids = row.get("query_ids", [])
        if not isinstance(query_ids, list) or any(not isinstance(value, str) for value in query_ids):
            raise ValueError(f"source-snapshot line {line_number} query_ids must be a list of strings")
        if len(set(query_ids)) != len(query_ids):
            raise ValueError(f"source-snapshot line {line_number} contains duplicate query_ids")
        known_query_ids = {f"Q{index}" for index in range(1, query_count + 1)}
        if any(value not in known_query_ids for value in query_ids):
            raise ValueError(f"source-snapshot line {line_number} references an unknown query_id")
        default_content_type = (
            "application/json" if row["capture_kind"] == "official_api_json"
            else "text/plain; charset=utf-8"
        )
        content_type = row.get("content_type", default_content_type)
        if not isinstance(content_type, str) or not content_type.strip():
            raise ValueError(f"source-snapshot line {line_number} content_type must be a non-empty string")
        rows.append({
            "title": re.sub(r"\s+", " ", row["title"]).strip(),
            "source_url": source_url,
            "capture_path": capture_rel.as_posix(),
            "capture_kind": row["capture_kind"],
            "captured_at_utc": captured_at_utc,
            "locator": re.sub(r"\s+", " ", row["locator"]).strip(),
            "query_ids": query_ids,
            "content_type": content_type,
            "raw_bytes": raw,
            "captured_text": captured_text,
        })
    if not rows:
        raise ValueError("source-snapshot manifest must contain at least one source")
    return rows, manifest_bytes


def _build_claim_review_ledger(
    reviews: list[dict[str, Any]], sources: list[dict[str, Any]],
    evidence_text_by_source: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    source_by_id = {source["source_id"]: source for source in sources}
    ledger = []
    for review in reviews:
        source = source_by_id.get(review["source_id"])
        evidence_quote = review.get("evidence_quote")
        evidence_field = review.get("evidence_field")
        if source is None:
            anchor_status = "UNKNOWN_SOURCE"
        elif not evidence_quote:
            anchor_status = "NOT_PROVIDED"
        elif evidence_quote in (
            (evidence_text_by_source or {}).get(review["source_id"], "")
            if evidence_field == "captured_text" else (source.get(evidence_field) or "")
        ):
            anchor_status = "EXACT_MATCH"
        else:
            anchor_status = "NOT_FOUND"
        if review.get("reviewer_type") == "HUMAN" and anchor_status == "EXACT_MATCH":
            row_status = "REVIEWED_AND_ANCHORED"
        elif review.get("review_judgment") == "NOT_REVIEWED":
            row_status = "NOT_REVIEWED"
        else:
            row_status = "UNANCHORED_OR_SOURCE_UNAVAILABLE"
        ledger.append({
            "claim_id": review["claim_id"],
            "claim_text": review["claim_text"],
            "source_id": review["source_id"],
            "source_title": source.get("title") if source else None,
            "source_openalex_id": source.get("openalex_id") if source else None,
            "source_url": source.get("source_url") if source else None,
            "source_raw_evidence": source.get("raw_evidence", []) if source else [],
            "evidence_field": evidence_field,
            "evidence_quote": evidence_quote,
            "evidence_quote_sha256": sha256(evidence_quote.encode("utf-8")) if evidence_quote else None,
            "evidence_anchor_status": anchor_status,
            "review_judgment": review["review_judgment"],
            "reviewer_type": review.get("reviewer_type", "NOT_REVIEWED"),
            "reviewer": review.get("reviewer"),
            "reviewed_at_utc": review.get("reviewed_at_utc"),
            "review_note": review.get("review_note"),
            "row_status": row_status,
        })
    if not ledger:
        status = "NOT_VALIDATED"
    elif any(row["evidence_anchor_status"] in {"UNKNOWN_SOURCE", "NOT_FOUND"} for row in ledger):
        status = "FAILED"
    elif all(row["row_status"] == "REVIEWED_AND_ANCHORED" for row in ledger):
        status = "COMPLETED"
    else:
        status = "PARTIAL"
    return ledger, status


def _acquisition_status(query_rows: list[dict[str, Any]], sources: list[dict[str, Any]]) -> str:
    successful = sum(row.get("status") == "OK" for row in query_rows)
    failed = len(query_rows) - successful
    if successful == 0:
        return "FAILED"
    if failed:
        return "PARTIAL"
    if not sources:
        return "NOT_VALIDATED"
    return "COMPLETED"


def _overall_run_status(
    acquisition_status: str,
    claim_review_status: str,
    draft_error: str | None,
) -> str:
    """Keep acquisition success distinct from citation-review completion."""
    if draft_error:
        return "INVALID_DRAFT"
    if acquisition_status in {"FAILED", "PARTIAL", "INVALID_RESPONSE", "NETWORK_ERROR", "RESOLUTION_FAILED"}:
        return acquisition_status
    if claim_review_status == "FAILED":
        return "CLAIM_REVIEW_FAILED"
    if claim_review_status == "PARTIAL":
        return "CLAIM_REVIEW_INCOMPLETE"
    return "COMPLETED" if acquisition_status in {"COMPLETED", "IMPORTED", "NORMALIZED_RECORDS_RECEIVED"} else acquisition_status


def _markdown_report(
    question: str,
    queries: list[str],
    sources: list[dict[str, Any]],
    verifications: list[dict[str, Any]],
    draft: str | None,
    status: str,
    acquisition_status: str,
    claim_review_status: str,
    claim_review_count: int,
    ingestion_mode: str = "OPENALEX_LIVE_SEARCH",
) -> str:
    matched = sum(row.get("metadata_match_status") == "MATCH" for row in verifications)
    mismatch = sum(row.get("metadata_match_status") == "MISMATCH" for row in verifications)
    lines = [
        f"# Research report: {question}",
        "",
        f"- Run status: `{status}`",
        (
            f"- Source capture import status: `{acquisition_status}`"
            if ingestion_mode == "OFFLINE_SOURCE_SNAPSHOTS"
            else f"- Source acquisition status: `{acquisition_status}`"
        ),
        f"- Claim review ledger status: `{claim_review_status}` ({claim_review_count} rows)",
        f"- Sources captured: {len(sources)}",
        "- Evidence ceiling: this workflow checks acquisition integrity, citation IDs, and exact excerpt anchors; it does not decide whether claims are true or supported.",
        "",
        "## Search method",
        "",
        (
            "Query strings are recorded as arm-provided inputs; this CLI did not execute or verify those searches. "
            "Source capture files are copied byte-for-byte into the run directory. A web_run_observation is the "
            "saved tool observation, not the original publisher HTTP response."
            if ingestion_mode == "OFFLINE_SOURCE_SNAPSHOTS"
            else "Searches used OpenAlex works metadata. The query set and original response bytes are preserved in the run directory."
        ),
    ]
    if ingestion_mode != "OFFLINE_SOURCE_SNAPSHOTS":
        lines[6:6] = [
            f"- DOI title/year metadata matches: {matched}",
            f"- DOI metadata mismatches: {mismatch}",
        ]
    lines.extend(f"- `{query}`" for query in queries)
    lines += ["", "## Synthesis", ""]
    if status == "INVALID_DRAFT":
        lines += ["The supplied synthesis was rejected because its citation markers did not resolve to sources in this run. Details are recorded in receipt.json."]
    elif draft is not None:
        lines += [
            "The following synthesis was supplied by the research agent. Citation IDs were checked syntactically against this run; the workflow does not judge whether each claim follows from its cited source.",
            "",
            draft.strip(),
        ]
    elif sources:
        lines += [
            "No agent-authored synthesis was supplied. The source notes below are retrieval evidence, not a conclusion about the research question.",
        ]
    else:
        lines += ["No sources were captured; no conclusion is supported by this run."]

    lines += ["", "## Source notes", ""]
    if not sources:
        lines.append("No source records were returned by the search provider.")
    for source in sources:
        title = source.get("title") or "Untitled record"
        safe_title = _markdown_escape(str(title))
        authors = ", ".join(source.get("authors") or []) or "Author metadata unavailable"
        year = source.get("year") or "Year unavailable"
        venue = source.get("venue") or "Venue unavailable"
        url = source.get("source_url") or source.get("doi_url") or source.get("openalex_id") or ""
        lines += [f"### [{source['source_id']}] {safe_title}", ""]
        if ingestion_mode == "OFFLINE_SOURCE_SNAPSHOTS":
            evidence = (source.get("raw_evidence") or [{}])[0]
            lines += [
                f"- Capture kind: `{source.get('capture_kind')}`; locator: {_markdown_escape(source.get('locator') or 'not supplied')}.",
                f"- Capture bytes: `{evidence.get('path')}`; SHA-256: `{evidence.get('capture_sha256') or evidence.get('response_sha256')}`.",
            ]
        else:
            lines += [
                f"- Bibliography: {authors} ({year}). {venue}.",
                f"- OpenAlex work type: {source.get('type') or 'unavailable'}; cited-by count: {source.get('cited_by_count') if source.get('cited_by_count') is not None else 'unavailable'}.",
            ]
        if url:
            lines.append(f"- Source: {url}")
        verification = next((v for v in verifications if v["source_id"] == source["source_id"]), None)
        if verification and verification.get("provider") != "OFFLINE_SOURCE_SNAPSHOT":
            lines.append(
                f"- Crossref check: `{verification['acquisition_status']}` / `{verification['metadata_match_status']}`."
            )
        if ingestion_mode == "OFFLINE_SOURCE_SNAPSHOTS":
            pass
        elif source.get("abstract"):
            lines += ["", "> Abstract (OpenAlex metadata):", ">", *(f"> {line}" for line in source["abstract"].splitlines()), ""]
        else:
            lines.append("- Abstract: unavailable in the captured OpenAlex record.")

    for source in sources:
        url = source.get("source_url") or source.get("doi_url") or source.get("openalex_id")
        if url:
            target = f"<{url}>" if ingestion_mode == "OFFLINE_SOURCE_SNAPSHOTS" else url
            lines += ["", f"[{source['source_id']}]: {target}"]

    lines += [
        "",
        "## Claim review handoff",
        "",
        (
            "Human review judgments and quoted excerpts are recorded in `claim-review.jsonl`. Exact excerpt matching "
            "only confirms that the quote occurs in the saved capture bytes and is linked to their hash; it does not "
            "establish that the claim is true or that the excerpt semantically supports it."
            if ingestion_mode == "OFFLINE_SOURCE_SNAPSHOTS"
            else "Human review judgments and quoted excerpts are recorded in `claim-review.jsonl`. Exact excerpt matching only confirms that the quote occurs in the captured title or abstract and is linked to raw response evidence; it does not establish that the claim is true or that the excerpt semantically supports it."
        ),
    ]

    lines += [
        "",
        "## Limits",
        "",
        (
            "Snapshot hashes establish the saved capture bytes used by this run, not the authenticity or completeness of "
            "the originating web observation. The workflow does not perform semantic claim verification."
            if ingestion_mode == "OFFLINE_SOURCE_SNAPSHOTS"
            else "OpenAlex and Crossref checks cover bibliographic metadata only. They do not establish that a paper's findings are correct, that an abstract fully represents the paper, or that any synthesis claim is supported. Full-text access, study quality, causal interpretation, and independent replication require separate review."
        ),
        "",
    ]
    return "\n".join(lines)


def _run_snapshot_research(
    *,
    question: str,
    queries: list[str],
    output_dir: str | Path,
    source_snapshots_path: str | Path,
    max_sources: int,
    draft_path: str | Path | None,
    claim_reviews: list[dict[str, Any]],
    command: list[str] | None,
) -> dict[str, Any]:
    """Import saved source observations without network access or search claims."""
    snapshots, manifest_bytes = _read_source_snapshots(source_snapshots_path, len(queries))
    if len(snapshots) > max_sources:
        raise ValueError("source-snapshot count exceeds max_sources")
    out = Path(output_dir)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise FileExistsError(f"output directory must be absent or empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    started = utc_now()

    query_source_counts = {f"Q{index}": 0 for index in range(1, len(queries) + 1)}
    for snapshot in snapshots:
        for query_id in snapshot["query_ids"]:
            query_source_counts[query_id] += 1
    query_rows = [
        {
            "query_id": f"Q{index}",
            "query": query,
            "status": "DECLARED_EXTERNALLY_NOT_VERIFIED",
            "search_provider": "NOT_VERIFIED_BY_CLI",
            "source_capture_count": query_source_counts[f"Q{index}"],
            "response_capture_status": "NOT_CAPTURED_BY_CLI",
        }
        for index, query in enumerate(queries, 1)
    ]

    sources: list[dict[str, Any]] = []
    evidence_text_by_source: dict[str, str] = {}
    for index, snapshot in enumerate(snapshots, 1):
        source_id = f"S{index}"
        suffix = "json" if snapshot["capture_kind"] == "official_api_json" else "txt"
        raw_path = f"raw/source-{source_id}.{suffix}"
        _write_bytes(out / raw_path, snapshot["raw_bytes"])
        capture_sha256 = sha256(snapshot["raw_bytes"])
        evidence_text_by_source[source_id] = snapshot["captured_text"]
        sources.append({
            "source_id": source_id,
            "provider": "OFFLINE_SOURCE_SNAPSHOT",
            "capture_kind": snapshot["capture_kind"],
            "source_url": snapshot["source_url"],
            "title": snapshot["title"],
            "locator": snapshot["locator"],
            "content_type": snapshot["content_type"],
            "captured_at_utc": snapshot["captured_at_utc"],
            "query_ids": snapshot["query_ids"],
            "capture_sha256": capture_sha256,
            "capture_bytes": len(snapshot["raw_bytes"]),
            "raw_evidence": [{
                "path": raw_path,
                "capture_sha256": capture_sha256,
                "capture_kind": snapshot["capture_kind"],
                "manifest_capture_path": snapshot["capture_path"],
                "query_ids": snapshot["query_ids"],
            }],
        })

    claim_ledger, claim_review_status = _build_claim_review_ledger(
        claim_reviews, sources, evidence_text_by_source=evidence_text_by_source,
    )
    draft = Path(draft_path).read_text(encoding="utf-8") if draft_path else None
    draft_error = None
    if draft is not None:
        try:
            _validate_draft(draft, {source["source_id"] for source in sources})
        except ValueError as exc:
            draft_error = str(exc)
            draft = None

    verifications = [{
        "source_id": source["source_id"],
        "provider": "OFFLINE_SOURCE_SNAPSHOT",
        "acquisition_status": "IMPORTED",
        "metadata_match_status": "NOT_APPLICABLE",
        "capture_sha256": source["capture_sha256"],
        "source_url": source["source_url"],
    } for source in sources]
    _write_jsonl(out / "query-manifest.jsonl", query_rows)
    _write_jsonl(out / "sources.jsonl", sources)
    _write_jsonl(out / "verification.jsonl", verifications)
    _write_jsonl(out / "claim-review.jsonl", claim_ledger)

    acquisition_status = "IMPORTED"
    status = _overall_run_status(acquisition_status, claim_review_status, draft_error)
    report = _markdown_report(
        question, queries, sources, verifications, draft, status,
        acquisition_status, claim_review_status, len(claim_ledger),
        ingestion_mode="OFFLINE_SOURCE_SNAPSHOTS",
    )
    _write_bytes(out / "report.md", report.encode("utf-8"))
    artifact_paths = sorted(
        path for path in out.rglob("*") if path.is_file() and path.name != "receipt.json"
    )
    receipt = {
        "workflow": "ignition-research-workflow-r1",
        "ingestion_mode": "OFFLINE_SOURCE_SNAPSHOTS",
        "query_execution_status": "NOT_VERIFIED_BY_CLI",
        "status": status,
        "acquisition_status": acquisition_status,
        "claim_review_status": claim_review_status,
        "claim_ceiling": "capture_integrity_and_human_review_handoff; no_search_verification_or_semantic_claim_verification",
        "question": question,
        "queries": queries,
        "source_snapshot_manifest_sha256": sha256(manifest_bytes),
        "started_at_utc": started,
        "finished_at_utc": utc_now(),
        "runtime": {"python": platform.python_version(), "platform": platform.platform()},
        "budget": {
            "query_count": len(queries),
            "max_sources": max_sources,
            "direct_api_cost_usd": 0,
            "network_requests_by_cli": 0,
        },
        "counts": {
            "query_ok": 0,
            "query_error": 0,
            "queries_declared": len(query_rows),
            "sources_captured": len(sources),
            "claim_review_rows": len(claim_ledger),
            "claim_review_anchored": sum(row["row_status"] == "REVIEWED_AND_ANCHORED" for row in claim_ledger),
            "claim_review_unanchored": sum(row["evidence_anchor_status"] in {"UNKNOWN_SOURCE", "NOT_FOUND"} for row in claim_ledger),
            "crossref_matches": 0,
            "crossref_mismatches": 0,
            "crossref_unresolved": 0,
        },
        "draft_mode": (
            "rejected_agent_authored_synthesis" if draft_error
            else "agent_authored_citations_syntax_checked" if draft is not None
            else "evidence_brief_only"
        ),
        "draft_error": draft_error,
        "command": _redact_command(command or []),
        "mailto_configured": False,
        "artifacts": [
            {"path": path.relative_to(out).as_posix(), "sha256": sha256(path.read_bytes()), "bytes": path.stat().st_size}
            for path in artifact_paths
        ],
        "limitations": [
            "The CLI imports source captures and does not execute or verify the listed search queries.",
            "web_run_observation is the saved tool observation, not the publisher's original HTTP response.",
            "Source URL, title, locator, capture timestamp, and query associations are caller-supplied manifest metadata.",
            "Capture hashes prove which saved bytes were used, not the authenticity or completeness of their origin.",
            "Claim-review judgments are human-supplied and self-reported; exact quote anchoring is not semantic support verification.",
        ],
    }
    _write_bytes(out / "receipt.json", _json_bytes(receipt))
    return receipt


def run_research(
    *,
    question: str,
    queries: list[str],
    output_dir: str | Path,
    max_sources: int = 12,
    mailto: str = openalex_client.DEFAULT_MAILTO,
    draft_path: str | Path | None = None,
    claim_review_path: str | Path | None = None,
    source_snapshots_path: str | Path | None = None,
    searcher: Callable[..., dict[str, Any]] | None = None,
    crossref_fetch: Callable[[str], dict[str, Any]] | None = None,
    command: list[str] | None = None,
) -> dict[str, Any]:
    """Run source collection, DOI metadata checks, report assembly, and receipt.

    The supplied draft (when present) must cite captured sources as ``[S1]`` etc.
    Claim-review judgments are supplied by a human; the workflow only anchors
    quoted text and source bytes, and never infers semantic support.
    """
    question = (question or "").strip()
    queries = [str(query).strip() for query in queries if str(query).strip()]
    if not question:
        raise ValueError("question is required")
    if not queries:
        raise ValueError("at least one non-empty --query is required")
    if len(queries) > MAX_QUERIES:
        raise ValueError(f"at most {MAX_QUERIES} queries are allowed")
    if not 1 <= max_sources <= MAX_SOURCES:
        raise ValueError(f"max_sources must be between 1 and {MAX_SOURCES}")
    claim_reviews = _read_claim_reviews(claim_review_path)

    if source_snapshots_path is not None:
        return _run_snapshot_research(
            question=question,
            queries=queries,
            output_dir=output_dir,
            source_snapshots_path=source_snapshots_path,
            max_sources=max_sources,
            draft_path=draft_path,
            claim_reviews=claim_reviews,
            command=command,
        )

    out = Path(output_dir)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise FileExistsError(f"output directory must be absent or empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    started = utc_now()
    searcher = searcher or openalex_client.search_with_evidence
    crossref_fetch = crossref_fetch or crossref_runner.fetch
    query_rows: list[dict[str, Any]] = []
    candidates: dict[str, dict[str, Any]] = {}

    for index, query in enumerate(queries, 1):
        row: dict[str, Any] = {"query_id": f"Q{index}", "query": query, "retrieved_at_utc": utc_now()}
        try:
            evidence = searcher(query, limit=MAX_RESULTS_PER_QUERY, mailto=mailto)
            raw = evidence.get("response_body")
            if not isinstance(raw, bytes):
                raise TypeError("search response did not include original response bytes")
            raw_path = f"raw/openalex-query-{index:02d}.json"
            _write_bytes(out / raw_path, raw)
            row.update({
                "request_url": _redact_request_url(evidence.get("request_url")),
                "raw_response_path": raw_path,
                "raw_response_sha256": sha256(raw),
            })
            parsed = openalex_client.parse_search_response(raw)
            results = parsed["results"]
            provided_results = evidence.get("results")
            if provided_results is not None and provided_results != results:
                raise EvidenceIntegrityError("normalized source records do not match the captured raw response")
            row["normalized_output_status"] = (
                "MATCHES_RAW_RESPONSE" if provided_results is not None else "DERIVED_FROM_RAW_RESPONSE"
            )
            for rank, item in enumerate(results, 1):
                key = _source_key(item)
                if key not in candidates:
                    candidates[key] = {**item, "query_ids": [], "rank_by_query": {}, "raw_evidence": []}
                record = candidates[key]
                if row["query_id"] not in record["query_ids"]:
                    record["query_ids"].append(row["query_id"])
                record["rank_by_query"].setdefault(row["query_id"], rank)
                if raw_path not in [entry["path"] for entry in record["raw_evidence"]]:
                    record["raw_evidence"].append({
                        "query_id": row["query_id"],
                        "path": raw_path,
                        "response_sha256": sha256(raw),
                        "record_index": rank,
                        "raw_record_sha256": parsed["raw_record_sha256"][rank - 1],
                    })
            row["result_count"] = len(results)
            row["status"] = "OK"
        except Exception as exc:  # preserve failed acquisition as an explicit row
            row.update({
                "status": "ERROR",
                "error_type": type(exc).__name__,
                "error_summary": (
                    str(exc) if isinstance(exc, EvidenceIntegrityError)
                    else "provider request failed or returned an invalid evidence envelope; exception details omitted from the public receipt"
                ),
            })
        query_rows.append(row)

    selected = _select_candidates_round_robin(
        candidates,
        [row["query_id"] for row in query_rows],
        max_sources,
    )
    sources: list[dict[str, Any]] = []
    for index, candidate in enumerate(selected, 1):
        doi = crossref_runner.bare_doi(candidate.get("doi"))
        openalex_id = candidate.get("openalex_id") or ""
        sources.append({
            "source_id": f"S{index}",
            "provider": "OpenAlex",
            "openalex_id": openalex_id,
            "doi": doi,
            "doi_url": f"https://doi.org/{doi}" if doi else None,
            "title": candidate.get("title"),
            "year": candidate.get("year"),
            "type": candidate.get("type"),
            "authors": candidate.get("authors") or [],
            "venue": candidate.get("venue"),
            "abstract": candidate.get("abstract"),
            "concepts": candidate.get("concepts") or [],
            "cited_by_count": candidate.get("cited_by_count"),
            "relevance_score": candidate.get("relevance_score"),
            "language": candidate.get("language"),
            "is_retracted": candidate.get("is_retracted"),
            "oa_url": candidate.get("oa_url"),
            "query_ids": candidate["query_ids"],
            "rank_by_query": candidate["rank_by_query"],
            "raw_evidence": candidate["raw_evidence"],
            "captured_at_utc": started,
        })

    claim_ledger, claim_review_status = _build_claim_review_ledger(claim_reviews, sources)

    draft = Path(draft_path).read_text(encoding="utf-8") if draft_path else None
    draft_error = None
    if draft is not None:
        try:
            _validate_draft(draft, {source["source_id"] for source in sources})
        except ValueError as exc:
            draft_error = str(exc)
            draft = None

    verifications = [_verify_doi(source, crossref_fetch, raw_dir=out / "raw") for source in sources]
    _write_jsonl(out / "query-manifest.jsonl", query_rows)
    _write_jsonl(out / "sources.jsonl", sources)
    _write_jsonl(out / "verification.jsonl", verifications)
    _write_jsonl(out / "claim-review.jsonl", claim_ledger)

    acquisition_status = _acquisition_status(query_rows, sources)
    status = _overall_run_status(acquisition_status, claim_review_status, draft_error)
    report = _markdown_report(
        question, queries, sources, verifications, draft, status,
        acquisition_status, claim_review_status, len(claim_ledger),
    )
    _write_bytes(out / "report.md", report.encode("utf-8"))

    artifact_paths = sorted(
        path for path in out.rglob("*") if path.is_file() and path.name != "receipt.json"
    )
    receipt = {
        "workflow": "ignition-research-workflow-r1",
        "status": status,
        "acquisition_status": acquisition_status,
        "claim_review_status": claim_review_status,
        "claim_ceiling": "source_capture_and_human_review_handoff; no_semantic_claim_verification",
        "question": question,
        "queries": queries,
        "started_at_utc": started,
        "finished_at_utc": utc_now(),
        "runtime": {"python": platform.python_version(), "platform": platform.platform()},
        "budget": {"query_count": len(queries), "max_sources": max_sources, "direct_api_cost_usd": 0},
        "counts": {
            "query_ok": sum(row["status"] == "OK" for row in query_rows),
            "query_error": sum(row["status"] == "ERROR" for row in query_rows),
            "sources_captured": len(sources),
            "claim_review_rows": len(claim_ledger),
            "claim_review_anchored": sum(row["row_status"] == "REVIEWED_AND_ANCHORED" for row in claim_ledger),
            "claim_review_unanchored": sum(row["evidence_anchor_status"] in {"UNKNOWN_SOURCE", "NOT_FOUND"} for row in claim_ledger),
            "crossref_matches": sum(row["metadata_match_status"] == "MATCH" for row in verifications),
            "crossref_mismatches": sum(row["metadata_match_status"] == "MISMATCH" for row in verifications),
            "crossref_unresolved": sum(row["metadata_match_status"] in {"UNDETERMINED", "PARTIAL_OR_MISSING_METADATA"} for row in verifications),
        },
        "draft_mode": (
            "rejected_agent_authored_synthesis" if draft_error
            else "agent_authored_citations_syntax_checked" if draft is not None
            else "evidence_brief_only"
        ),
        "draft_error": draft_error,
        "command": _redact_command(command or []),
        "mailto_configured": bool(mailto),
        "artifacts": [
            {"path": path.relative_to(out).as_posix(), "sha256": sha256(path.read_bytes()), "bytes": path.stat().st_size}
            for path in artifact_paths
        ],
        "limitations": [
            "Crossref checks only DOI resolution, title, year, and available retraction metadata.",
            "Citation markers are checked for references to captured source IDs; factual support is not semantically validated.",
            "OpenAlex abstracts are metadata and may not represent the full paper.",
            "Normalized source rows are re-derived from captured response bytes; caller-supplied normalized rows that differ are rejected.",
            "Claim-review judgments are human-supplied and self-reported; exact quote anchoring is not semantic support verification.",
        ],
    }
    _write_bytes(out / "receipt.json", _json_bytes(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", required=True, help="Owner/research question")
    parser.add_argument("--query", action="append", required=True, help="recorded query; repeat up to 12 times")
    parser.add_argument("--output-dir", required=True, help="new or empty run directory")
    parser.add_argument("--max-sources", type=int, default=12, help=f"number of records to retain (1-{MAX_SOURCES})")
    parser.add_argument("--mailto", default=openalex_client.DEFAULT_MAILTO, help="OpenAlex polite-pool contact")
    parser.add_argument("--draft", help="optional UTF-8 Markdown synthesis that cites captured IDs such as [S1]")
    parser.add_argument("--claim-reviews", help="optional JSONL human claim-to-source review rows")
    parser.add_argument("--source-snapshots", help="offline JSONL manifest for saved source capture files")
    args = parser.parse_args(argv)
    try:
        receipt = run_research(
            question=args.question,
            queries=args.query,
            output_dir=args.output_dir,
            max_sources=args.max_sources,
            mailto=args.mailto,
            draft_path=args.draft,
            claim_review_path=args.claim_reviews,
            source_snapshots_path=args.source_snapshots,
            command=sys.argv,
        )
    except (ValueError, FileExistsError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "status": receipt["status"],
        "acquisition_status": receipt["acquisition_status"],
        "claim_review_status": receipt["claim_review_status"],
        "receipt": str(Path(args.output_dir) / "receipt.json"),
        "report": str(Path(args.output_dir) / "report.md"),
        "sources": receipt["counts"]["sources_captured"],
    }, ensure_ascii=False))
    return 0 if (
        receipt["status"] == "COMPLETED"
        and receipt["claim_review_status"] in {"COMPLETED", "NOT_VALIDATED"}
    ) else 2


if __name__ == "__main__":
    raise SystemExit(main())
