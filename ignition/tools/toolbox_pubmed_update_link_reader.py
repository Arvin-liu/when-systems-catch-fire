#!/usr/bin/env python3
"""Read raw Comments/Corrections relations from fixed PubMed records.

The optional adapter accepts exact PMIDs and queries NCBI EFetch over one
fixed HTTPS host. It emits only PubMed relation metadata, not titles or
abstracts, and never interprets a missing relation as evidence of absence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


TOOL_VERSION = "0.1.0"
API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
API_HOST = "eutils.ncbi.nlm.nih.gov"
MAX_REQUEST_BYTES = 16 * 1024
MAX_RECORDS = 10
MAX_RESPONSE_BYTES = 256 * 1024
MAX_RESPONSE_DURATION_SECONDS = 7
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 8 * 1024
INTER_REQUEST_DELAY_SECONDS = 0.34
MAX_RELATIONS_PER_RECORD = 100
MAX_RELATION_SOURCE_LENGTH = 2000
PMID_RE = re.compile(r"[1-9][0-9]{0,11}\Z")


class ToolInputError(ValueError):
    """Raised when input falls outside the bounded PMID contract."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent a fixed-host request from following a redirect elsewhere."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def parse_request(raw: bytes) -> list[str]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    try:
        document = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON") from exc
    if not isinstance(document, dict) or set(document) != {"pmids"}:
        raise ToolInputError("request must be an object with exactly one key: pmids")
    pmids = document["pmids"]
    if not isinstance(pmids, list) or not 1 <= len(pmids) <= MAX_RECORDS:
        raise ToolInputError(f"pmids must contain between 1 and {MAX_RECORDS} entries")
    seen: set[str] = set()
    result: list[str] = []
    for index, pmid in enumerate(pmids):
        if not isinstance(pmid, str) or not PMID_RE.fullmatch(pmid):
            raise ToolInputError(f"pmids[{index}] must be a positive numeric PMID")
        if pmid in seen:
            raise ToolInputError("PMID values must be unique within one request")
        seen.add(pmid)
        result.append(pmid)
    return result


def _request_url(pmid: str) -> str:
    return API_BASE + "?" + urllib.parse.urlencode({
        "db": "pubmed", "id": pmid, "retmode": "xml", "tool": "IgnitionToolbox",
    })


def _fetch_one(pmid: str) -> dict[str, Any]:
    url = _request_url(pmid)
    target = urllib.parse.urlsplit(url)
    if (
        target.scheme != "https" or target.hostname != API_HOST or target.port is not None
        or target.username or target.password or target.fragment
    ):
        raise RuntimeError("NCBI EFetch endpoint is not the fixed HTTPS host")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"IgnitionToolboxPubMedUpdates/{TOOL_VERSION}", "Accept": "application/xml, text/xml"},
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status = int(response.status)
            if status != 200:
                return {"acquisition_status": "HTTP_ERROR", "http_status": status, "body": None}
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type not in {"application/xml", "text/xml"} and not content_type.endswith("+xml"):
                return {"acquisition_status": "NON_XML_RESPONSE", "http_status": status, "body": None}
            deadline = time.monotonic() + MAX_RESPONSE_DURATION_SECONDS
            chunks: list[bytes] = []
            total_bytes = 0
            while total_bytes <= MAX_RESPONSE_BYTES:
                if time.monotonic() >= deadline:
                    return {"acquisition_status": "RESPONSE_TIMEOUT", "http_status": status, "body": None}
                chunk = response.read(min(RESPONSE_CHUNK_BYTES, MAX_RESPONSE_BYTES + 1 - total_bytes))
                if time.monotonic() > deadline:
                    return {"acquisition_status": "RESPONSE_TIMEOUT", "http_status": status, "body": None}
                if not chunk:
                    break
                chunks.append(chunk)
                total_bytes += len(chunk)
            if total_bytes > MAX_RESPONSE_BYTES:
                return {"acquisition_status": "RESPONSE_TOO_LARGE", "http_status": status, "body": None}
            return {"acquisition_status": "OK", "http_status": status, "body": b"".join(chunks)}
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        outcome = "REDIRECT_BLOCKED" if 300 <= status < 400 else ("NOT_FOUND" if status == 404 else ("RATE_LIMITED" if status == 429 else "HTTP_ERROR"))
        return {"acquisition_status": outcome, "http_status": status, "body": None}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"acquisition_status": "NETWORK_ERROR", "http_status": None, "body": None}


def _record_relations(body: bytes, requested_pmid: str) -> dict[str, Any]:
    # ElementTree does not fetch external DTDs, and explicit entity declarations
    # are rejected so an upstream response cannot expand internal entities.
    if b"<!ENTITY" in body.upper():
        return {"acquisition_status": "XML_ENTITY_DECLARATION_REJECTED", "record_status": "NOT_AVAILABLE", "relations": []}
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return {"acquisition_status": "INVALID_XML_RESPONSE", "record_status": "NOT_AVAILABLE", "relations": []}
    articles = root.findall(".//PubmedArticle")
    matches = []
    for article in articles:
        value = article.findtext("./MedlineCitation/PMID")
        if isinstance(value, str) and value.strip() == requested_pmid:
            matches.append(article)
    if len(matches) != 1:
        return {
            "acquisition_status": "OK",
            "record_status": "NO_RECORD" if not articles else "UPSTREAM_RECORD_MISMATCH",
            "relations": [],
        }

    relations: list[dict[str, str | None]] = []
    relation_list = matches[0].find("./MedlineCitation/CommentsCorrectionsList")
    if relation_list is not None:
        for node in relation_list.findall("./CommentsCorrections")[:MAX_RELATIONS_PER_RECORD]:
            ref_type = node.attrib.get("RefType")
            ref_source = " ".join((node.findtext("./RefSource") or "").split())[:MAX_RELATION_SOURCE_LENGTH]
            related_pmid = node.findtext("./PMID")
            relations.append({
                "ref_type": ref_type[:100] if isinstance(ref_type, str) else None,
                "related_pmid": related_pmid.strip() if isinstance(related_pmid, str) and PMID_RE.fullmatch(related_pmid.strip()) else None,
                "reference_source": ref_source or None,
            })
    truncated = relation_list is not None and len(relation_list.findall("./CommentsCorrections")) > MAX_RELATIONS_PER_RECORD
    return {
        "acquisition_status": "OK",
        "record_status": "RECORD_FOUND_WITH_RECORDED_RELATIONS" if relations else "RECORD_FOUND_NO_RECORDED_RELATIONS",
        "relations": relations,
        "relations_truncated": truncated,
    }


def _inspect_row(pmid: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "pmid": pmid,
        "retrieval_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_url": _request_url(pmid),
        "pubmed_record_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "acquisition_status": None,
        "http_status": None,
        "response_sha256": None,
        "record_status": None,
        "relations": [],
        "relations_truncated": False,
    }
    fetched = _fetch_one(pmid)
    row["acquisition_status"] = fetched["acquisition_status"]
    row["http_status"] = fetched["http_status"]
    if fetched["acquisition_status"] != "OK":
        row["record_status"] = "NOT_AVAILABLE"
        return row
    body = fetched["body"]
    row["response_sha256"] = hashlib.sha256(body).hexdigest()
    parsed = _record_relations(body, pmid)
    row.update(parsed)
    return row


def inspect(pmids: list[str]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index, pmid in enumerate(pmids):
        rows.append(_inspect_row(pmid))
        if index + 1 < len(pmids):
            time.sleep(INTER_REQUEST_DELAY_SECONDS)
    failures = sum(row["acquisition_status"] != "OK" for row in rows)
    found = sum(row["record_status"] in {"RECORD_FOUND_WITH_RECORDED_RELATIONS", "RECORD_FOUND_NO_RECORDED_RELATIONS"} for row in rows)
    return {
        "schema_version": "ignition.pubmed-update-link-inspection-r0",
        "tool_id": "research.inspect_pubmed_update_links",
        "tool_version": TOOL_VERSION,
        "status": "COMPLETED_WITH_EXPLICIT_FAILURES" if failures else ("RECORDS_INSPECTED" if found else "NO_RECORDS_FOUND"),
        "pmid_count": len(rows),
        "records_found": found,
        "acquisition_failure_count": failures,
        "rows": rows,
        "source_code_sha256": {"wrapper": _sha256(Path(__file__).resolve())},
        "claim_ceiling": "Raw Comments/Corrections relation fields returned for exact PubMed records at retrieval time only; no completeness claim is made and an empty relation list does not prove that no correction, expression of concern, or retraction exists.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read the bounded JSON contract from stdin")
    parser.add_argument("--allow-public-network", action="store_true", help="authorize this invocation to make fixed-host public HTTPS GET requests")
    args = parser.parse_args(argv)
    if not args.allow_public_network:
        print("PUBLIC_NETWORK_CALL_REQUIRES --allow-public-network", file=sys.stderr)
        return 2
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    try:
        pmids = parse_request(raw)
    except ToolInputError as exc:
        print(f"INVALID_REQUEST: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(inspect(pmids), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
