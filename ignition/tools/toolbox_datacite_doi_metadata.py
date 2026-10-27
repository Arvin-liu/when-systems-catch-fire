#!/usr/bin/env python3
"""Retrieve one bounded DataCite DOI metadata projection; stdout only.

This opt-in adapter makes one HTTPS GET to the fixed DataCite Public API host.
It never follows redirects, stores provider responses, fetches landing pages,
or changes repository/provider state.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


TOOL_VERSION = "0.1.0"
API_BASE = "https://api.datacite.org/dois/"
API_HOST = "api.datacite.org"
MAX_REQUEST_BYTES = 4096
MAX_DOI_LENGTH = 128
MAX_RESPONSE_BYTES = 128 * 1024
MAX_RESPONSE_DURATION_SECONDS = 7
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 8192
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\Z")
CLAIM_CEILING = (
    "One exact-DOI-matched record returned by the unauthenticated DataCite Public API at retrieval time. "
    "The Public API exposes Findable records only. A no-record response does not establish that the DOI "
    "does not exist, and returned state, resource type, identifiers, rights, or dates do not establish "
    "content, scientific truth, legal reuse permission, data availability, or provider-wide coverage."
)


class ToolInputError(ValueError):
    """Raised when caller input violates the bounded input contract."""


class ToolResponseError(ValueError):
    """Raised when a provider response cannot be safely interpreted."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Keep the request on its fixed host; redirects are evidence, not a route."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ToolResponseError("duplicate JSON object key")
        value[key] = item
    return value


def _reject_json_constant(value: str) -> None:
    raise ToolResponseError("non-standard JSON constant")


def parse_request(raw: bytes) -> str:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError("request exceeds the byte limit")
    try:
        document = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ToolResponseError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON with unique keys") from exc
    if not isinstance(document, dict) or set(document) != {"doi"}:
        raise ToolInputError("request must contain exactly one key: doi")
    doi = document["doi"]
    if (
        not isinstance(doi, str)
        or not 1 <= len(doi) <= MAX_DOI_LENGTH
        or doi != doi.strip()
        or not DOI_RE.fullmatch(doi)
    ):
        raise ToolInputError("doi must be one bare DOI identifier")
    return doi


def _fixed_url(doi: str) -> str:
    url = API_BASE + urllib.parse.quote(doi, safe="")
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != API_HOST
        or parsed.port is not None
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("DataCite endpoint is not the fixed HTTPS Public API host")
    return url


def _read_limited(stream: Any) -> tuple[bytes | None, int, str | None]:
    deadline = time.monotonic() + MAX_RESPONSE_DURATION_SECONDS
    chunks: list[bytes] = []
    total = 0
    while total <= MAX_RESPONSE_BYTES:
        if time.monotonic() >= deadline:
            return None, total, "RESPONSE_TIMEOUT"
        try:
            chunk = stream.read(min(RESPONSE_CHUNK_BYTES, MAX_RESPONSE_BYTES + 1 - total))
        except (OSError, TimeoutError):
            return None, total, "RESPONSE_READ_ERROR"
        if time.monotonic() > deadline:
            return None, total + len(chunk), "RESPONSE_TIMEOUT"
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
    if total > MAX_RESPONSE_BYTES:
        return None, total, "RESPONSE_TOO_LARGE"
    return b"".join(chunks), total, None


def _fetch_one(doi: str) -> dict[str, Any]:
    request = urllib.request.Request(
        _fixed_url(doi),
        headers={
            "Accept": "application/vnd.api+json, application/json",
            "User-Agent": "IgnitionToolboxDataCite/{}".format(TOOL_VERSION),
        },
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        response = opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        body, size, read_error = _read_limited(exc)
        outcome = (
            "REDIRECT_BLOCKED" if 300 <= status < 400
            else "NOT_FOUND" if status == 404
            else "RATE_LIMITED" if status == 429
            else "HTTP_ERROR"
        )
        return {
            "acquisition_status": read_error or outcome,
            "http_status": status,
            "content_type": _content_type(exc.headers),
            "body": body,
            "response_bytes": size,
        }
    except (urllib.error.URLError, TimeoutError, OSError):
        return {
            "acquisition_status": "NETWORK_ERROR",
            "http_status": None,
            "content_type": None,
            "body": None,
            "response_bytes": None,
        }

    with response:
        status = int(response.status)
        content_type = _content_type(response.headers)
        body, size, read_error = _read_limited(response)
    if read_error:
        outcome = read_error
    elif status != 200:
        outcome = "HTTP_ERROR"
    elif content_type != "application/json" and not content_type.endswith("+json"):
        outcome = "NON_JSON_RESPONSE"
    else:
        outcome = "OK"
    return {
        "acquisition_status": outcome,
        "http_status": status,
        "content_type": content_type,
        "body": body,
        "response_bytes": size,
    }


def _content_type(headers: Any) -> str | None:
    if headers is None:
        return None
    value = headers.get("Content-Type", "")
    if not isinstance(value, str) or len(value) > 128 or any(ord(char) < 32 for char in value):
        return None
    return value.split(";", 1)[0].strip().lower() or None


def _digest(body: bytes | None) -> str | None:
    return hashlib.sha256(body).hexdigest() if body is not None else None


def _safe_text(value: Any, *, limit: int = 1024) -> str | None:
    if not isinstance(value, str) or len(value) > limit or value != value.strip():
        return None
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return None
    return value or None


def _project_list(
    attributes: dict[str, Any],
    field: str,
    limit: int,
    projector: Any,
) -> tuple[list[dict[str, Any]], str, int | None, int, int]:
    if field not in attributes:
        return [], "NOT_REPORTED", None, 0, 0
    source = attributes[field]
    if not isinstance(source, list):
        return [], "MALFORMED", None, 0, 1
    rows: list[dict[str, Any]] = []
    invalid = 0
    for item in source[:limit]:
        if not isinstance(item, dict):
            invalid += 1
            continue
        projected = projector(item)
        if projected is None:
            invalid += 1
            continue
        rows.append(projected)
    omitted = max(0, len(source) - limit)
    return rows, "REPORTED", len(source), omitted, invalid


def _project_record(data: Any, requested_doi: str) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("type") != "dois":
        raise ToolResponseError("response data is not a DataCite DOI record")
    attributes = data.get("attributes")
    if not isinstance(attributes, dict):
        raise ToolResponseError("response DOI attributes are malformed")
    record_id = data.get("id")
    attribute_doi = attributes.get("doi")
    if (
        _normalize_doi(record_id) != requested_doi.casefold()
        or _normalize_doi(attribute_doi) != requested_doi.casefold()
    ):
        raise ToolResponseError("response DOI does not exactly match the requested DOI")

    titles = _project_list(
        attributes, "titles", 10,
        lambda item: ({
            "title": _safe_text(item.get("title")),
            "lang": _safe_text(item.get("lang"), limit=64),
        } if _safe_text(item.get("title")) is not None else None),
    )
    creators = _project_list(
        attributes, "creators", 20,
        lambda item: ({
            "name": _safe_text(item.get("name")),
            "name_type": _safe_text(item.get("nameType"), limit=64),
        } if _safe_text(item.get("name")) is not None else None),
    )
    rights = _project_list(
        attributes, "rightsList", 20,
        lambda item: ({
            "rights": _safe_text(item.get("rights")),
            "rights_uri": _safe_text(item.get("rightsUri"), limit=2048),
            "rights_identifier": _safe_text(item.get("rightsIdentifier"), limit=128),
            "rights_identifier_scheme": _safe_text(item.get("rightsIdentifierScheme"), limit=128),
        } if _safe_text(item.get("rights")) is not None or _safe_text(item.get("rightsUri"), limit=2048) is not None else None),
    )
    related = _project_list(
        attributes, "relatedIdentifiers", 25,
        lambda item: ({
            "related_identifier": _safe_text(item.get("relatedIdentifier"), limit=2048),
            "related_identifier_type": _safe_text(item.get("relatedIdentifierType"), limit=128),
            "relation_type": _safe_text(item.get("relationType"), limit=128),
            "related_metadata_scheme": _safe_text(item.get("relatedMetadataScheme"), limit=128),
        } if _safe_text(item.get("relatedIdentifier"), limit=2048) is not None else None),
    )
    identifiers = _project_list(
        attributes, "identifiers", 25,
        lambda item: ({
            "identifier": _safe_text(item.get("identifier"), limit=2048),
            "identifier_type": _safe_text(item.get("identifierType"), limit=128),
        } if _safe_text(item.get("identifier"), limit=2048) is not None else None),
    )
    dates = _project_list(
        attributes, "dates", 25,
        lambda item: ({
            "date": _safe_text(item.get("date"), limit=128),
            "date_type": _safe_text(item.get("dateType"), limit=128),
        } if _safe_text(item.get("date"), limit=128) is not None else None),
    )
    types = attributes.get("types")
    if types is not None and not isinstance(types, dict):
        raise ToolResponseError("response resource types are malformed")
    year = attributes.get("publicationYear")
    if type(year) is not int or not 1000 <= year <= 2200:
        year = None

    row_fields = (titles, creators, rights, related, identifiers, dates)
    field_names = ("titles", "creators", "rightsList", "relatedIdentifiers", "identifiers", "dates")
    return {
        "doi": requested_doi,
        "state": _safe_text(attributes.get("state"), limit=64),
        "schema_version": _safe_text(attributes.get("schemaVersion"), limit=256),
        "publisher": _safe_text(attributes.get("publisher"), limit=512),
        "publication_year": year,
        "resource_type_general": _safe_text(types.get("resourceTypeGeneral"), limit=128) if types else None,
        "resource_type": _safe_text(types.get("resourceType"), limit=512) if types else None,
        "titles": titles[0],
        "creators": creators[0],
        "rights": rights[0],
        "related_identifiers": related[0],
        "identifiers": identifiers[0],
        "dates": dates[0],
        "field_statuses": {name: row[1] for name, row in zip(field_names, row_fields)},
        "field_counts": {
            name: {
                "reported_count": row[2],
                "omitted_count": row[3],
                "invalid_count": row[4],
            }
            for name, row in zip(field_names, row_fields)
        },
    }


def _normalize_doi(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    result = value.strip()
    lowered = result.casefold()
    for prefix in ("https://doi.org/", "http://doi.org/"):
        if lowered.startswith(prefix):
            result = result[len(prefix):]
            break
    return result.casefold()


def lookup(doi: str) -> dict[str, Any]:
    fetched = _fetch_one(doi)
    result: dict[str, Any] = {
        "schema_version": "toolbox-datacite-doi-metadata-output-r0",
        "tool_id": "research.lookup_datacite_doi_metadata",
        "tool_version": TOOL_VERSION,
        "requested_doi": doi,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "request_count": 1,
        "acquisition_status": fetched["acquisition_status"],
        "http_status": fetched["http_status"],
        "content_type": fetched["content_type"],
        "response_bytes": fetched["response_bytes"],
        "response_sha256": _digest(fetched["body"]),
        "status": "UNRESOLVED",
        "record": None,
        "claim_ceiling": CLAIM_CEILING,
    }
    if fetched["acquisition_status"] == "NOT_FOUND":
        result["status"] = "NO_FINDABLE_DATACITE_RECORD"
        return result
    if fetched["acquisition_status"] != "OK":
        return result
    try:
        document = json.loads(
            fetched["body"].decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
        if not isinstance(document, dict) or "data" not in document:
            raise ToolResponseError("response is not a DataCite JSON:API document")
        record = _project_record(document["data"], doi)
    except (UnicodeDecodeError, json.JSONDecodeError, ToolResponseError, TypeError):
        result["acquisition_status"] = "INVALID_DATACITE_RESPONSE"
        return result
    result["status"] = "EXACT_DOI_MATCH"
    result["record"] = record
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one JSON request from stdin")
    parser.add_argument("--allow-public-network", action="store_true", help="allow the one DataCite Public API GET for this invocation")
    args = parser.parse_args(argv)
    if not args.allow_public_network:
        print("network access is disabled; pass --allow-public-network for this invocation", file=sys.stderr)
        return 2
    try:
        request = parse_request(sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1))
    except ToolInputError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(lookup(request), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
