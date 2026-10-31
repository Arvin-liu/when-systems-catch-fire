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


TOOL_VERSION = "0.2.0"
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
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\Z")


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


def parse_request_with_options(raw: bytes) -> tuple[list[str], str | None]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    try:
        document = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON") from exc
    if not isinstance(document, dict) or set(document) not in ({"pmids"}, {"pmids", "expected_doi"}):
        raise ToolInputError("request must contain pmids and may contain expected_doi")
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
    expected_doi = document.get("expected_doi")
    if "expected_doi" in document:
        if not isinstance(expected_doi, str) or len(expected_doi) > 128 or not DOI_RE.fullmatch(expected_doi):
            raise ToolInputError("expected_doi must be one bare DOI identifier")
        if len(result) != 1:
            raise ToolInputError("expected_doi may be supplied only with exactly one PMID")
    return result, expected_doi


def parse_request(raw: bytes) -> list[str]:
    """Backward-compatible PMID-only view of the typed request parser."""
    return parse_request_with_options(raw)[0]


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


def _doi_values(article: ET.Element) -> list[str]:
    values: list[str] = []
    doi_nodes = article.findall("./MedlineCitation/Article/ELocationID")
    doi_nodes.extend(article.findall("./PubmedData/ArticleIdList/ArticleId"))
    for node in doi_nodes:
        id_type = node.attrib.get("EIdType", node.attrib.get("IdType", ""))
        value = node.text.strip() if isinstance(node.text, str) else ""
        if id_type.casefold() == "doi":
            values.append(value)
    return values


def _record_relations(
    body: bytes,
    requested_pmid: str,
    expected_doi: str | None = None,
) -> dict[str, Any]:
    # ElementTree does not fetch external DTDs, and explicit entity declarations
    # are rejected so an upstream response cannot expand internal entities.
    if b"<!ENTITY" in body.upper():
        result = {"acquisition_status": "XML_ENTITY_DECLARATION_REJECTED", "record_status": "NOT_AVAILABLE", "relations": []}
        if expected_doi is not None:
            result.update({"expected_doi": expected_doi, "doi_binding_status": "NOT_EVALUATED"})
        return result
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        result = {"acquisition_status": "INVALID_XML_RESPONSE", "record_status": "NOT_AVAILABLE", "relations": []}
        if expected_doi is not None:
            result.update({"expected_doi": expected_doi, "doi_binding_status": "NOT_EVALUATED"})
        return result
    articles = root.findall(".//PubmedArticle")
    matches = []
    for article in articles:
        value = article.findtext("./MedlineCitation/PMID")
        if isinstance(value, str) and value.strip() == requested_pmid:
            matches.append(article)
    if len(matches) != 1:
        result = {
            "acquisition_status": "OK",
            "record_status": "NO_RECORD" if not articles else "UPSTREAM_RECORD_MISMATCH",
            "relations": [],
        }
        if expected_doi is not None:
            result.update({"expected_doi": expected_doi, "doi_binding_status": "NOT_EVALUATED"})
        return result

    doi_binding_status: str | None = None
    if expected_doi is not None:
        observed_dois = _doi_values(matches[0])
        if not observed_dois:
            doi_binding_status = "NOT_REPORTED"
        elif any(not DOI_RE.fullmatch(value) for value in observed_dois):
            doi_binding_status = "INVALID_VALUE"
        elif len({value.casefold() for value in observed_dois}) > 1:
            doi_binding_status = "MULTIPLE_VALUES"
        elif expected_doi.casefold() not in {value.casefold() for value in observed_dois}:
            doi_binding_status = "MISMATCH"
        else:
            doi_binding_status = "EXACT_MATCH"
        if doi_binding_status != "EXACT_MATCH":
            return {
                "acquisition_status": "OK",
                "record_status": "DOI_IDENTITY_NOT_CONFIRMED",
                "relations": [],
                "relations_truncated": False,
                "expected_doi": expected_doi,
                "doi_binding_status": doi_binding_status,
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
    result = {
        "acquisition_status": "OK",
        "record_status": "RECORD_FOUND_WITH_RECORDED_RELATIONS" if relations else "RECORD_FOUND_NO_RECORDED_RELATIONS",
        "relations": relations,
        "relations_truncated": truncated,
    }
    if expected_doi is not None:
        result.update({"expected_doi": expected_doi, "doi_binding_status": "EXACT_MATCH"})
    return result


def _inspect_row(pmid: str, expected_doi: str | None = None) -> dict[str, Any]:
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
        if expected_doi is not None:
            row.update({"expected_doi": expected_doi, "doi_binding_status": "NOT_EVALUATED"})
        return row
    body = fetched["body"]
    row["response_sha256"] = hashlib.sha256(body).hexdigest()
    parsed = _record_relations(body, pmid, expected_doi)
    row.update(parsed)
    return row


def inspect(pmids: list[str], *, expected_doi: str | None = None) -> dict[str, Any]:
    if expected_doi is not None:
        if not isinstance(expected_doi, str) or len(expected_doi) > 128 or not DOI_RE.fullmatch(expected_doi):
            raise ToolInputError("expected_doi must be one bare DOI identifier")
        if len(pmids) != 1:
            raise ToolInputError("expected_doi may be supplied only when inspecting exactly one PMID")
    rows: list[dict[str, Any]] = []
    for index, pmid in enumerate(pmids):
        rows.append(_inspect_row(pmid, expected_doi))
        if index + 1 < len(pmids):
            time.sleep(INTER_REQUEST_DELAY_SECONDS)
    failures = sum(row["acquisition_status"] != "OK" for row in rows)
    found = sum(row["record_status"] in {
        "RECORD_FOUND_WITH_RECORDED_RELATIONS",
        "RECORD_FOUND_NO_RECORDED_RELATIONS",
        "DOI_IDENTITY_NOT_CONFIRMED",
    } for row in rows)
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
        "claim_ceiling": "Raw Comments/Corrections relation fields returned for exact PubMed records at retrieval time only. When an expected DOI is supplied by a composing caller, relations are returned only if the same EFetch record reports exactly that DOI; this does not authenticate the source. No completeness claim is made and an empty relation list does not prove that no correction, expression of concern, or retraction exists.",
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
        pmids, expected_doi = parse_request_with_options(raw)
    except ToolInputError as exc:
        print(f"INVALID_REQUEST: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(inspect(pmids, expected_doi=expected_doi), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
