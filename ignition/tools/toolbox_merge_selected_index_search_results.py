#!/usr/bin/env python3
"""Group selected literature-search results by exact normalized DOI, offline."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


TOOL_ID = "research.merge_selected_index_search_results"
TOOL_VERSION = "0.1.0"
MAX_INPUT_BYTES = 1_600_000
MAX_RESULTS_PER_PROVIDER = 10
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+\Z", re.IGNORECASE)
SHA256_RE = re.compile(r"[a-f0-9]{64}\Z")
PROVIDERS = {
    "crossref": {
        "schema_version": "ignition.crossref-query-search-r0",
        "tool_id": "research.search_crossref_query",
        "endpoint": "https://api.crossref.org/v1/works",
        "hit_count_key": "provider_hit_count",
    },
    "openalex": {
        "schema_version": "ignition.openalex-query-search-r0",
        "tool_id": "research.search_openalex_query",
        "endpoint": "https://api.openalex.org/works",
        "hit_count_key": "provider_hit_count",
    },
    "europe_pmc": {
        "schema_version": "ignition.europe-pmc-query-search-r0",
        "tool_id": "research.search_europe_pmc_query",
        "endpoint": "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        "hit_count_key": "hit_count",
    },
}
CLAIM_CEILING = (
    "This offline tool summarizes caller-supplied bounded Crossref, OpenAlex, and Europe PMC search receipts. "
    "Provider query languages, corpora, ranking, timestamps, and hit counts are not comparable. Only exact normalized "
    "DOI equality creates a cross-index group; title similarity is never used. Results do not establish relevance, "
    "completeness, source authenticity, article status, scientific support, or scientific validity."
)


class ToolInputError(ValueError):
    """Raised when source receipts do not satisfy the declared input contract."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ToolInputError("non-standard JSON constants are not accepted")


def _parse_timestamp(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 64:
        raise ToolInputError("provider timestamp must be an ISO date-time string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ToolInputError("provider timestamp must be an ISO date-time string") from exc
    if parsed.tzinfo is None:
        raise ToolInputError("provider timestamp must include a timezone")
    return value


def _normalize_doi(value: Any) -> str | None:
    if not isinstance(value, str) or len(value) > 1200:
        return None
    candidate = value.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/"):
        if candidate.casefold().startswith(prefix):
            candidate = candidate[len(prefix):]
            break
    if not DOI_RE.fullmatch(candidate):
        return None
    return candidate.casefold()


def _year(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and 0 <= value <= 3000:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1,4}", value):
        parsed = int(value)
        return parsed if parsed <= 3000 else None
    return None


def _record(provider: str, row: Any, index: int) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise ToolInputError("provider receipt contains a non-object record")
    if provider == "crossref":
        identifier = row.get("doi") or f"row:{index}"
        title = row.get("title")
        year = row.get("publication_year")
    elif provider == "openalex":
        identifier = row.get("openalex_id") or f"row:{index}"
        title = row.get("title")
        year = row.get("publication_year")
    else:
        source, local_id = row.get("source"), row.get("id")
        identifier = f"{source}:{local_id}" if isinstance(source, str) and isinstance(local_id, str) else f"row:{index}"
        title = row.get("title")
        year = row.get("publication_year")
    doi = row.get("doi")
    if doi is not None and (not isinstance(doi, str) or len(doi) > 1200):
        raise ToolInputError("provider receipt contains an invalid DOI field")
    if not isinstance(identifier, str) or len(identifier) > 1200:
        raise ToolInputError("provider receipt contains an invalid record identifier")
    if title is not None and (not isinstance(title, str) or len(title) > 4096):
        raise ToolInputError("provider receipt contains an invalid title")
    return {
        "provider": provider,
        "record_index": index,
        "provider_record_id": identifier,
        "doi": doi,
        "normalized_doi": _normalize_doi(doi),
        "title": title,
        "publication_year": _year(year),
    }


def _validate_source_receipt(receipt: Any) -> tuple[str, dict[str, Any]]:
    if not isinstance(receipt, dict):
        raise ToolInputError("source_results entries must be objects")
    tool_id = receipt.get("tool_id")
    providers = [name for name, config in PROVIDERS.items() if config["tool_id"] == tool_id]
    if len(providers) != 1:
        raise ToolInputError("source result must come from a supported topic-search adapter")
    provider = providers[0]
    config = PROVIDERS[provider]
    required = {
        "schema_version", "tool_id", "tool_version", "status", "acquisition_status", "source_endpoint",
        "retrieval_timestamp_utc", "max_results", "query_sha256", "response_sha256", "returned_count", "records",
    }
    if not required <= set(receipt):
        raise ToolInputError("source receipt is missing required provider fields")
    if receipt.get("schema_version") != config["schema_version"] or receipt.get("source_endpoint") != config["endpoint"]:
        raise ToolInputError("source receipt version or fixed endpoint does not match its provider")
    if not isinstance(receipt.get("tool_version"), str) or len(receipt["tool_version"]) > 32:
        raise ToolInputError("source receipt has an invalid adapter version")
    if not isinstance(receipt.get("status"), str) or len(receipt["status"]) > 64:
        raise ToolInputError("source receipt has an invalid adapter status")
    if not isinstance(receipt.get("acquisition_status"), str) or len(receipt["acquisition_status"]) > 64:
        raise ToolInputError("source receipt has an invalid acquisition status")
    if not SHA256_RE.fullmatch(str(receipt.get("query_sha256", ""))):
        raise ToolInputError("source receipt query_sha256 is invalid")
    response_sha = receipt.get("response_sha256")
    if response_sha is not None and (not isinstance(response_sha, str) or not SHA256_RE.fullmatch(response_sha)):
        raise ToolInputError("source receipt response_sha256 is invalid")
    if receipt["acquisition_status"] == "OK" and response_sha is None:
        raise ToolInputError("successful source receipt must carry a response SHA-256")
    timestamp = _parse_timestamp(receipt.get("retrieval_timestamp_utc"))
    limit = receipt.get("max_results")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_RESULTS_PER_PROVIDER:
        raise ToolInputError("source receipt max_results must be from one through ten")
    rows = receipt.get("records")
    if not isinstance(rows, list) or len(rows) > limit:
        raise ToolInputError("source receipt records exceed its declared result limit")
    returned_count = receipt.get("returned_count")
    if isinstance(returned_count, bool) or not isinstance(returned_count, int) or returned_count != len(rows):
        raise ToolInputError("source receipt returned_count does not match its records")
    hit_count = receipt.get(config["hit_count_key"])
    if hit_count is not None and (isinstance(hit_count, bool) or not isinstance(hit_count, int) or hit_count < 0):
        raise ToolInputError("source receipt provider hit count is invalid")
    records = [_record(provider, row, index) for index, row in enumerate(rows)]
    summary = {
        "provider": provider,
        "adapter_tool_id": tool_id,
        "adapter_version": receipt["tool_version"],
        "adapter_status": receipt["status"],
        "acquisition_status": receipt["acquisition_status"],
        "source_endpoint": config["endpoint"],
        "retrieval_timestamp_utc": timestamp,
        "max_results": limit,
        "query_sha256": receipt["query_sha256"],
        "response_sha256": response_sha,
        "provider_hit_count": hit_count,
        "returned_count": returned_count,
        "records": records,
    }
    return provider, summary


def parse_request(raw: bytes) -> tuple[list[dict[str, Any]], bytes]:
    if len(raw) > MAX_INPUT_BYTES:
        raise ToolInputError("request exceeds the declared byte limit")
    try:
        payload = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be UTF-8 JSON with unique keys") from exc
    if not isinstance(payload, dict) or set(payload) != {"source_results"}:
        raise ToolInputError("request must contain exactly source_results")
    source_results = payload["source_results"]
    if not isinstance(source_results, list) or not 2 <= len(source_results) <= len(PROVIDERS):
        raise ToolInputError("source_results must contain two or three provider receipts")
    summaries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in source_results:
        provider, summary = _validate_source_receipt(source)
        if provider in seen:
            raise ToolInputError("source_results must contain at most one receipt per provider")
        seen.add(provider)
        summaries.append(summary)
    summaries.sort(key=lambda row: list(PROVIDERS).index(row["provider"]))
    return summaries, raw


def merge(raw: bytes) -> dict[str, Any]:
    sources, exact_input = parse_request(raw)
    records = [record for source in sources for record in source["records"]]
    by_doi: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        normalized = record["normalized_doi"]
        if normalized is not None:
            by_doi.setdefault(normalized, []).append(record)
    clusters = []
    clustered: set[tuple[str, int]] = set()
    for doi in sorted(by_doi):
        members = by_doi[doi]
        if len({row["provider"] for row in members}) < 2:
            continue
        clusters.append({
            "normalized_doi": doi,
            "members": [{"provider": row["provider"], "record_index": row["record_index"], "provider_record_id": row["provider_record_id"]} for row in members],
        })
        clustered.update((row["provider"], row["record_index"]) for row in members)
    successful = sum(source["acquisition_status"] == "OK" for source in sources)
    status = "COMPLETE" if successful == len(sources) else ("PARTIAL" if successful else "FAILED")
    return {
        "schema_version": "ignition.selected-index-search-result-merge-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": status,
        "source_results": sources,
        "record_count_total": len(records),
        "exact_normalized_doi_clusters": clusters,
        "unclustered_record_count": len(records) - len(clustered),
        "match_basis": "EXACT_NORMALIZED_DOI_ONLY",
        "input_sha256": hashlib.sha256(exact_input).hexdigest(),
        "claim_ceiling": CLAIM_CEILING,
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args != ["--stdin"]:
        sys.stderr.write("Selected-index search result merge requires exactly --stdin.\n")
        return 2
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        result = merge(raw)
    except ToolInputError as exc:
        sys.stderr.write("Invalid selected-index search receipts: {}\n".format(exc))
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
