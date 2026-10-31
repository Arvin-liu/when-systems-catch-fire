#!/usr/bin/env python3
"""Bounded, explicit OpenAlex works-query adapter for the Ignition toolbox."""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


IGNITION_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_RESEARCH = IGNITION_ROOT / "scripts" / "external-research"
if str(EXTERNAL_RESEARCH) not in sys.path:
    sys.path.insert(0, str(EXTERNAL_RESEARCH))

import openalex_client as OPENALEX  # noqa: E402


TOOL_ID = "research.search_openalex_query"
TOOL_VERSION = "0.1.0"
API_ENDPOINT = "https://api.openalex.org/works"
MAX_REQUEST_BYTES = 4096
MAX_QUERY_CHARS = 512
MAX_QUERY_UTF8_BYTES = 2048
MAX_RESULTS = 10
OPENALEX_WORK_ID_RE = re.compile(r"^https://openalex\.org/W[0-9]{1,20}$")
CLAIM_CEILING = (
    "At most ten OpenAlex-ranked Works metadata rows returned for one caller-supplied query at retrieval time. "
    "The search is not exhaustive and establishes no relevance, source authenticity, scientific support, "
    "publication status, or scientific validity."
)


class ToolInputError(ValueError):
    """Raised when the exact bounded JSON input contract is violated."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ToolInputError("non-standard JSON constants are not accepted")


def parse_request(raw: bytes) -> tuple[str, int]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError("request exceeds the declared byte limit")
    try:
        payload = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be UTF-8 JSON with unique keys") from exc
    if not isinstance(payload, dict) or set(payload) != {"query", "max_results"}:
        raise ToolInputError("request must contain exactly query and max_results")
    query = payload["query"]
    if not isinstance(query, str) or not query or query != query.strip():
        raise ToolInputError("query must be a non-empty, already-trimmed string")
    if len(query) > MAX_QUERY_CHARS or len(query.encode("utf-8")) > MAX_QUERY_UTF8_BYTES:
        raise ToolInputError("query exceeds its character or UTF-8 byte limit")
    if any(ord(char) < 0x20 or 0x7F <= ord(char) <= 0x9F for char in query):
        raise ToolInputError("query must not contain control characters")
    limit = payload["max_results"]
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_RESULTS:
        raise ToolInputError("max_results must be an integer from 1 through 10")
    return query, limit


def _text(value: Any, max_chars: int, field: str) -> str | None:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or len(value) > max_chars
        or any(ord(char) < 0x20 or 0x7F <= ord(char) <= 0x9F for char in value)
    ):
        raise ValueError("invalid {} field".format(field))
    return value


def _parse_records(body: bytes, max_results: int) -> tuple[int, list[dict[str, Any]]]:
    try:
        data = json.loads(body.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("response is not valid UTF-8 JSON") from exc
    if not isinstance(data, dict) or not isinstance(data.get("meta"), dict) or not isinstance(data.get("results"), list):
        raise ValueError("response does not match the OpenAlex Works list shape")
    total = data["meta"].get("count")
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ValueError("response has an invalid provider count")
    works = data["results"]
    if len(works) > max_results:
        raise ValueError("response exceeded the requested result limit")

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for work in works:
        if not isinstance(work, dict):
            raise ValueError("response contains a non-object Work")
        work_id = work.get("id")
        if not isinstance(work_id, str) or not OPENALEX_WORK_ID_RE.fullmatch(work_id) or work_id in seen:
            raise ValueError("response contains an invalid or duplicate OpenAlex Work ID")
        seen.add(work_id)
        doi = _text(work.get("doi"), 1024, "doi")
        title = _text(work.get("display_name"), 4096, "display_name")
        work_type = _text(work.get("type"), 256, "type")
        year = work.get("publication_year")
        if year is not None and (isinstance(year, bool) or not isinstance(year, int) or not 0 <= year <= 3000):
            raise ValueError("response contains an invalid publication year")
        score = work.get("relevance_score")
        if score is not None:
            try:
                score_is_finite = (
                    not isinstance(score, bool)
                    and isinstance(score, (int, float))
                    and math.isfinite(float(score))
                )
            except (OverflowError, TypeError, ValueError):
                score_is_finite = False
            if not score_is_finite:
                raise ValueError("response contains an invalid relevance score")

        authorships = work.get("authorships")
        if authorships is None:
            authorships = []
        if not isinstance(authorships, list) or len(authorships) > 1000:
            raise ValueError("response contains malformed authorships")
        authors: list[str] = []
        for authorship in authorships:
            if not isinstance(authorship, dict):
                raise ValueError("response contains a malformed authorship")
            author = authorship.get("author")
            if author is None:
                continue
            if not isinstance(author, dict):
                raise ValueError("response contains a malformed author")
            name = _text(author.get("display_name"), 512, "author.display_name")
            if name:
                authors.append(name)

        primary = work.get("primary_location")
        if primary is not None and not isinstance(primary, dict):
            raise ValueError("response contains a malformed primary location")
        source = primary.get("source") if isinstance(primary, dict) else None
        if source is not None and not isinstance(source, dict):
            raise ValueError("response contains a malformed primary source")
        venue = _text(source.get("display_name") if isinstance(source, dict) else None, 512, "source.display_name")
        records.append({
            "openalex_id": work_id,
            "doi": doi,
            "title": title,
            "publication_year": year,
            "type": work_type,
            "author_names": authors[:10],
            "author_count": len(authors),
            "authors_truncated": len(authors) > 10,
            "primary_venue": venue,
            "relevance_score": score,
        })
    return total, records


def search(raw: bytes) -> dict[str, Any]:
    query, max_results = parse_request(raw)
    fetched = OPENALEX.search_for_toolbox(query, max_results)
    body = fetched.get("body")
    acquisition = fetched.get("acquisition_status")
    receipt: dict[str, Any] = {
        "schema_version": "ignition.openalex-query-search-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": "FAILED",
        "acquisition_status": acquisition,
        "http_status": fetched.get("http_status"),
        "source_endpoint": API_ENDPOINT,
        "retrieval_timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "max_results": max_results,
        "request_count": 1,
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "request_sha256": fetched.get("request_sha256"),
        "response_sha256": None,
        "response_bytes": 0,
        "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "shared_client_source_sha256": hashlib.sha256(Path(OPENALEX.__file__).read_bytes()).hexdigest(),
        "provider_hit_count": None,
        "returned_count": 0,
        "usage_headers": fetched.get("usage_headers", {}),
        "records": [],
        "claim_ceiling": CLAIM_CEILING,
    }
    if acquisition != "OK" or not isinstance(body, bytes):
        return receipt

    receipt["response_sha256"] = hashlib.sha256(body).hexdigest()
    receipt["response_bytes"] = len(body)
    try:
        total, records = _parse_records(body, max_results)
    except (OverflowError, TypeError, ValueError):
        receipt["acquisition_status"] = "INVALID_RESPONSE"
        return receipt
    receipt["provider_hit_count"] = total
    receipt["records"] = records
    receipt["returned_count"] = len(records)
    receipt["status"] = "FOUND" if records else "NOT_FOUND"
    if records:
        receipt["acquisition_status"] = "OK"
    return receipt


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or set(args) != {"--stdin", "--allow-public-network"}:
        sys.stderr.write("OpenAlex toolbox search requires exactly --stdin --allow-public-network.\n")
        return 2
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    try:
        result = search(raw)
    except ToolInputError as exc:
        sys.stderr.write("Invalid OpenAlex toolbox search input: {}\n".format(exc))
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    return 0 if result["acquisition_status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
