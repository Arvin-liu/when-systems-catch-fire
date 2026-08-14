#!/usr/bin/env python3
"""fulltext_resolver.py — Discover and select legitimate OA full-text URLs.

This module does NOT download large files; it returns a ranked list of candidate
locations for fulltext_fetcher.py to retrieve. Each attempt is logged as a JSON
object to `121-fulltext-resolution-log.jsonl`.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_MAILTO = os.environ.get("OPENALEX_MAILTO", "research@ignition.local")
USER_AGENT = os.environ.get(
    "FULLTEXT_USER_AGENT",
    f"ignition-fulltext-resolver/1.0 (mailto:{DEFAULT_MAILTO})",
)


@dataclass
class ResolutionAttempt:
    source_id: str
    provider: str
    step: str
    url: str
    status: str
    http_status: int | None = None
    content_type: str | None = None
    content_length: int | None = None
    redirect_url: str | None = None
    error: str | None = None
    timestamp_utc: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    extra: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def _head(url: str, timeout: int = 30) -> tuple[int, dict[str, str]]:
    """Return HTTP status and lower-cased headers."""
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, {k.lower(): v for k, v in r.headers.items()}


def _probe(url: str) -> ResolutionAttempt:
    """Probe a URL and return a ResolutionAttempt with basic metadata."""
    try:
        status, headers = _head(url)
        return ResolutionAttempt(
            source_id="",
            provider="probe",
            step="HEAD",
            url=url,
            status="SUCCESS" if status == 200 else f"HTTP_{status}",
            http_status=status,
            content_type=headers.get("content-type"),
            content_length=int(headers.get("content-length", 0)) or None,
        )
    except urllib.error.HTTPError as e:
        return ResolutionAttempt(
            source_id="",
            provider="probe",
            step="HEAD",
            url=url,
            status=f"HTTP_ERROR_{e.code}",
            http_status=e.code,
            error=str(e.reason)[:200],
        )
    except Exception as e:
        return ResolutionAttempt(
            source_id="",
            provider="probe",
            step="HEAD",
            url=url,
            status="EXCEPTION",
            error=str(e)[:200],
        )


def arxiv_candidates(arxiv_id: str) -> list[tuple[str, str]]:
    """Return provider-name, URL tuples for arXiv IDs in priority order."""
    clean = arxiv_id.strip().lower().replace("arxiv:", "").replace("arxiv/", "").replace(" ", "")
    return [
        ("arxiv_html", f"https://arxiv.org/html/{clean}"),
        ("arxiv_pdf", f"https://arxiv.org/pdf/{clean}.pdf"),
        ("arxiv_api", f"https://export.arxiv.org/api/query?search_query=id:{clean}"),
        ("ar5iv_html", f"https://ar5iv.labs.arxiv.org/html/{clean}"),
    ]


def resolve_arxiv(arxiv_id: str, source_id: str = "") -> list[ResolutionAttempt]:
    """Probe all arXiv channels and return attempts."""
    attempts = []
    for provider, url in arxiv_candidates(arxiv_id):
        time.sleep(0.5)
        att = _probe(url)
        att.source_id = source_id
        att.provider = provider
        att.step = "ARXIV_PATH"
        attempts.append(att)
    return attempts


def resolve_openalex(
    doi: str | None = None,
    openalex_id: str | None = None,
    title: str | None = None,
    source_id: str = "",
) -> list[ResolutionAttempt]:
    """Query OpenAlex for OA locations and return candidate attempts."""
    attempts = []
    if not any([doi, openalex_id, title]):
        return attempts

    if openalex_id:
        oid = openalex_id.replace("https://openalex.org/", "")
        url = f"https://api.openalex.org/works/{oid}?mailto={urllib.parse.quote(DEFAULT_MAILTO)}"
    elif doi:
        d = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
        url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(d)}?mailto={urllib.parse.quote(DEFAULT_MAILTO)}"
    elif title:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(title)}&per-page=5&mailto={urllib.parse.quote(DEFAULT_MAILTO)}"
    else:
        return attempts

    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except Exception as e:
        attempts.append(
            ResolutionAttempt(
                source_id=source_id,
                provider="openalex_api",
                step="QUERY",
                url=url,
                status="API_ERROR",
                error=str(e)[:200],
            )
        )
        return attempts

    works = data.get("results", [data]) if "results" in data else [data]
    for w in works:
        oa = w.get("open_access", {})
        oa_url = oa.get("oa_url")
        if oa_url:
            time.sleep(0.5)
            att = _probe(oa_url)
            att.source_id = source_id
            att.provider = "openalex_oa_url"
            att.step = "OPENALEX_OA"
            att.extra = {
                "oa_status": oa.get("oa_status"),
                "is_oa": oa.get("is_oa"),
                "any_repository_has_fulltext": oa.get("any_repository_has_fulltext"),
            }
            attempts.append(att)
        for loc in w.get("locations", []) or []:
            landing = loc.get("landing_page_url")
            pdf = loc.get("pdf_url")
            for u in [pdf, landing]:
                if u and u != oa_url:
                    time.sleep(0.5)
                    att = _probe(u)
                    att.source_id = source_id
                    att.provider = "openalex_location"
                    att.step = "OPENALEX_LOCATION"
                    att.extra = {"source_type": loc.get("source", {}).get("type")}
                    attempts.append(att)
    return attempts


def resolve_doi_oa(doi: str, source_id: str = "") -> list[ResolutionAttempt]:
    """Use Crossref and Unpaywall (polite) to discover OA locations."""
    attempts = []
    d = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")

    # Crossref
    cr_url = f"https://api.crossref.org/works/{urllib.parse.quote(d)}"
    try:
        req = urllib.request.Request(cr_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            cr = json.load(r)
        link = (cr.get("message", {}).get("link", []) or [{}])[0]
        url = link.get("URL")
        if url:
            time.sleep(0.5)
            att = _probe(url)
            att.source_id = source_id
            att.provider = "crossref"
            att.step = "CROSSREF_LINK"
            attempts.append(att)
    except Exception as e:
        attempts.append(
            ResolutionAttempt(
                source_id=source_id,
                provider="crossref",
                step="CROSSREF_LINK",
                url=cr_url,
                status="API_ERROR",
                error=str(e)[:200],
            )
        )

    # Unpaywall
    email = os.environ.get("UNPAYWALL_EMAIL", DEFAULT_MAILTO)
    up_url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(d)}?email={urllib.parse.quote(email)}"
    try:
        req = urllib.request.Request(up_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            up = json.load(r)
        for key in ["best_oa_location", "first_oa_location"]:
            loc = up.get(key)
            if loc:
                url = loc.get("url_for_pdf") or loc.get("url")
                if url:
                    time.sleep(0.5)
                    att = _probe(url)
                    att.source_id = source_id
                    att.provider = "unpaywall"
                    att.step = key.upper()
                    att.extra = {"license": loc.get("license"), "version": loc.get("version")}
                    attempts.append(att)
    except Exception as e:
        attempts.append(
            ResolutionAttempt(
                source_id=source_id,
                provider="unpaywall",
                step="UNPAYWALL_QUERY",
                url=up_url,
                status="API_ERROR",
                error=str(e)[:200],
            )
        )
    return attempts


def resolve_source(source: dict) -> list[ResolutionAttempt]:
    """Resolve a single source registry entry using the ordered protocol."""
    attempts = []
    sid = source.get("source_id", "")
    doi = source.get("doi_or_identifier", "")
    url = source.get("url", "")
    arxiv_id = ""

    # Detect arXiv ID
    if doi.lower().startswith("arxiv:") or re.match(r"^\d{4}\.\d{4,5}$", doi, re.I):
        arxiv_id = doi.replace("arXiv:", "").replace("arxiv:", "")
    elif url and "arxiv.org" in url:
        m = re.search(r"arxiv\.org/(?:abs|html|pdf)/(\d+\.\d+)", url, re.I)
        if m:
            arxiv_id = m.group(1)

    # A/B: arXiv path
    if arxiv_id:
        attempts.extend(resolve_arxiv(arxiv_id, sid))

    # C: OpenAlex
    attempts.extend(resolve_openalex(doi=doi, title=source.get("title"), source_id=sid))

    # D: DOI path if not arXiv and has DOI-like identifier
    if not arxiv_id and doi.startswith("10."):
        attempts.extend(resolve_doi_oa(doi, sid))

    # E: direct registered URL if no OA found yet (probe once)
    if url and not any(a.status == "SUCCESS" for a in attempts):
        time.sleep(0.5)
        att = _probe(url)
        att.source_id = sid
        att.provider = "source_registry_url"
        att.step = "REGISTERED_URL"
        attempts.append(att)

    return attempts


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 fulltext_resolver.py '<source-json>'")
        sys.exit(1)
    source = json.loads(sys.argv[1])
    for att in resolve_source(source):
        print(att.to_json())
