#!/usr/bin/env python3
"""Resolve one DOI, then read raw PubMed Comments/Corrections if a PMID exists.

This bounded composition keeps identifier resolution and update-link reading as
separate evidence stages. It never interprets missing relations as absence of an
update and performs no repository writes or article-content review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


TOOL_VERSION = "0.2.0"
MAX_REQUEST_BYTES = 16 * 1024
TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
import toolbox_pubmed_identifier_resolver as identifier_resolver  # noqa: E402
import toolbox_pubmed_update_link_reader as update_reader  # noqa: E402


class ToolInputError(ValueError):
    """Raised when input falls outside the one-DOI composition contract."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_request(raw: bytes) -> list[str]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    try:
        dois = identifier_resolver.parse_request(raw)
    except identifier_resolver.ToolInputError as exc:
        raise ToolInputError(str(exc)) from exc
    if len(dois) != 1:
        raise ToolInputError("this composed route accepts exactly one DOI per invocation")
    return dois


def audit(dois: list[str]) -> dict[str, Any]:
    """Run the fixed identifier stage and conditionally the fixed PMID stage."""
    normalized = parse_request(json.dumps({"dois": dois}, ensure_ascii=False).encode("utf-8"))
    resolution = identifier_resolver.resolve(normalized)
    resolution_row = resolution["rows"][0]
    resolved_pmid = resolution_row.get("pmid") if resolution_row.get("identifier_status") == "IDENTIFIER_RESOLVED" else None
    pmid = resolved_pmid if isinstance(resolved_pmid, str) and update_reader.PMID_RE.fullmatch(resolved_pmid) else None

    inspection = update_reader.inspect([pmid], expected_doi=normalized[0]) if isinstance(pmid, str) else None
    inspection_rows = inspection.get("rows") if isinstance(inspection, dict) else None
    inspection_row = inspection_rows[0] if isinstance(inspection_rows, list) and inspection_rows else None
    if pmid is None:
        update_status = "SKIPPED_NO_VALID_PMID"
    elif not isinstance(inspection_row, dict):
        update_status = "INSPECTION_UNAVAILABLE"
    elif inspection_row.get("acquisition_status") != "OK":
        update_status = "INSPECTION_UNAVAILABLE"
    elif inspection_row.get("record_status") == "DOI_IDENTITY_NOT_CONFIRMED" or (
        inspection_row.get("record_status") in {
            "RECORD_FOUND_WITH_RECORDED_RELATIONS",
            "RECORD_FOUND_NO_RECORDED_RELATIONS",
        }
        and inspection_row.get("doi_binding_status") != "EXACT_MATCH"
    ):
        update_status = "RECORD_IDENTITY_NOT_CONFIRMED"
    elif inspection_row.get("record_status") not in {
        "RECORD_FOUND_WITH_RECORDED_RELATIONS",
        "RECORD_FOUND_NO_RECORDED_RELATIONS",
    }:
        update_status = "RECORD_NOT_CONFIRMED"
    elif inspection_row.get("relations"):
        update_status = "RECORDED_RELATIONS_RETURNED"
    else:
        update_status = "NO_RELATIONS_RETURNED_IN_THIS_RESPONSE"

    return {
        "schema_version": "ignition.pubmed-doi-update-audit-r0",
        "tool_id": "research.audit_pubmed_updates_from_doi",
        "tool_version": TOOL_VERSION,
        "status": "COMPLETED_WITH_EXPLICIT_STAGE_OUTCOMES",
        "doi": normalized[0],
        "identifier_resolution": resolution,
        "update_link_inspection": inspection,
        "update_link_status": update_status,
        "source_code_sha256": {
            "composition_wrapper": _sha256(Path(__file__).resolve()),
            "identifier_resolver": _sha256(Path(identifier_resolver.__file__).resolve()),
            "update_link_reader": _sha256(Path(update_reader.__file__).resolve()),
        },
        "claim_ceiling": (
            "One DOI-to-PMID resolution response followed, only when an exact PMID is returned, by raw PubMed Comments/Corrections fields for that exact record and the same EFetch response reports exactly the input DOI. "
            "An absent PMID, unavailable response, or empty relation list does not establish that no update exists; no source authenticity, completeness, retraction-status, article-content, or scientific-validity claim is made."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read the bounded one-DOI JSON contract from stdin")
    parser.add_argument("--allow-public-network", action="store_true", help="authorize fixed-host public HTTPS GET requests for both stages")
    args = parser.parse_args(argv)
    if not args.allow_public_network:
        print("PUBLIC_NETWORK_CALL_REQUIRES --allow-public-network", file=sys.stderr)
        return 2
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    try:
        dois = parse_request(raw)
    except ToolInputError as exc:
        print(f"INVALID_REQUEST: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(audit(dois), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
