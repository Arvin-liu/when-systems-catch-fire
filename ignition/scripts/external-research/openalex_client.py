#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenAlex 学术检索客户端（免 key，polite pool）。

OpenAlex 是完全免费的开放学术数据库，无需 API key。
加入 mailto 参数可进入 polite pool，获得更高速率限制。

用法：
  python3 openalex_client.py "query" [limit]
  python3 openalex_client.py "query" 10 --mailto your@email.com
  python3 openalex_client.py --doi 10.48550/arxiv.2106.09685
  python3 openalex_client.py "query" 5 --json

输出 JSON 数组，每条包含：
  id, doi, title, year, authors, venue, type,
  abstract, open_access, oa_url, cited_by_count,
  is_retracted, concepts, relevance_score

合规：
  - 本工具返回元数据和摘要，不返回全文
  - DOI 需再用 Crossref 验真（与 anysearch_client 协议一致）
  - 摘要通过 abstract_inverted_index 还原，非模型生成
  - is_retracted 字段可用于撤稿预警
"""

from __future__ import annotations

import sys
import hashlib
import json
import time
import urllib.error
import urllib.request
import urllib.parse
from datetime import datetime, timezone

API = "https://api.openalex.org/works"
DEFAULT_MAILTO = "research@ignition.local"
DEFAULT_LIMIT = 5
MAX_LIMIT = 25  # OpenAlex 单页最大 200，但默认限制 25 避免过大输出

TOOLBOX_SEARCH_VERSION = "0.1.0"
TOOLBOX_SEARCH_HOST = "api.openalex.org"
TOOLBOX_SEARCH_SELECT = "id,doi,display_name,publication_year,type,relevance_score,authorships,primary_location"
TOOLBOX_SEARCH_MAX_RESULTS = 10
TOOLBOX_SEARCH_MAX_RESPONSE_BYTES = 512 * 1024
TOOLBOX_SEARCH_TIMEOUT_SECONDS = 5
TOOLBOX_SEARCH_MAX_RESPONSE_SECONDS = 7


def _restore_abstract(inverted_index: dict | None) -> str | None:
    """从 OpenAlex 的 inverted index 还原摘要文本。"""
    if not inverted_index:
        return None
    max_pos = 0
    for positions in inverted_index.values():
        if positions:
            max_pos = max(max_pos, max(positions))
    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            if 0 <= pos <= max_pos:
                words[pos] = word
    return " ".join(words)


def _canonical_work_sha256(work: dict) -> str:
    canonical = json.dumps(work, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _normalize_work(w: dict) -> dict:
    """Normalize one OpenAlex work using only fields in that raw record."""
    authors = []
    for authorship in w.get("authorships", []):
        name = authorship.get("author", {}).get("display_name", "")
        if name:
            authors.append(name)

    abstract = _restore_abstract(w.get("abstract_inverted_index"))
    open_access = w.get("open_access", {}) or {}
    primary = w.get("primary_location") or {}
    source = primary.get("source") or {}

    return {
        "openalex_id": w.get("id", ""),
        "doi": w.get("doi", ""),
        "title": w.get("title", "") or w.get("display_name", ""),
        "year": w.get("publication_year"),
        "authors": authors,
        "venue": source.get("display_name", ""),
        "type": w.get("type", ""),
        "abstract": abstract,
        "is_oa": open_access.get("is_oa", False),
        "oa_status": open_access.get("oa_status", ""),
        "oa_url": open_access.get("oa_url", ""),
        "any_repository_has_fulltext": open_access.get("any_repository_has_fulltext", False),
        "cited_by_count": w.get("cited_by_count", 0),
        "is_retracted": w.get("is_retracted", False),
        "concepts": [c.get("display_name", "") for c in w.get("concepts", [])[:8]],
        "relevance_score": w.get("relevance_score"),
        "language": w.get("language", ""),
    }


def parse_search_response(response_body: bytes) -> dict:
    """Derive normalized rows and per-record hashes from the same raw bytes.

    The record hashes use canonical JSON encoding of each raw work object. The
    complete original response bytes remain the authoritative captured artifact.
    """
    if not isinstance(response_body, bytes):
        raise TypeError("OpenAlex response body must be bytes")
    data = json.loads(response_body.decode("utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise ValueError("OpenAlex response must contain a results array")
    works = data["results"]
    if any(not isinstance(work, dict) for work in works):
        raise ValueError("OpenAlex results must contain only work objects")
    return {
        "results": [_normalize_work(work) for work in works],
        "raw_record_sha256": [_canonical_work_sha256(work) for work in works],
    }


class _ToolboxNoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """The bounded toolbox adapter never follows an API redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _toolbox_usage_headers(headers: object) -> dict[str, str | None]:
    names = (
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Credits-Used",
        "X-RateLimit-Reset",
    )
    result: dict[str, str | None] = {}
    for name in names:
        value = headers.get(name) if headers is not None and hasattr(headers, "get") else None
        if not isinstance(value, str) or len(value) > 64 or any(ord(char) < 32 for char in value):
            result[name] = None
        else:
            result[name] = value
    return result


def _toolbox_search_url(query: str, max_results: int) -> str:
    params = urllib.parse.urlencode({
        "search": query,
        "per_page": str(max_results),
        "select": TOOLBOX_SEARCH_SELECT,
    })
    url = API + "?" + params
    target = urllib.parse.urlsplit(url)
    if (
        target.scheme != "https"
        or target.hostname != TOOLBOX_SEARCH_HOST
        or target.port is not None
        or target.username
        or target.password
        or target.path != "/works"
        or target.fragment
        or len(url.encode("ascii")) > 4094
    ):
        raise ValueError("OpenAlex toolbox search endpoint is not the fixed bounded HTTPS target")
    return url


def search_for_toolbox(query: str, max_results: int) -> dict:
    """Run one no-key, bounded OpenAlex works search for the toolbox adapter.

    The legacy `search()` and CLI keep their existing output contract. This
    separate entry point reuses this module's OpenAlex response parser while
    omitting the legacy placeholder mailto, selecting metadata-only fields,
    rejecting redirects, and capping request and response work.
    """
    if (
        not isinstance(query, str)
        or not query
        or query != query.strip()
        or len(query) > 512
        or len(query.encode("utf-8")) > 2048
        or any(ord(char) < 0x20 or 0x7F <= ord(char) <= 0x9F for char in query)
    ):
        raise ValueError("query must be a bounded, trimmed, control-free string")
    if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= TOOLBOX_SEARCH_MAX_RESULTS:
        raise ValueError("max_results must be an integer from 1 through 10")
    url = _toolbox_search_url(query, max_results)
    request_sha256 = hashlib.sha256(url.encode("ascii")).hexdigest()
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "IgnitionToolboxOpenAlexSearch/{}".format(TOOLBOX_SEARCH_VERSION),
            "Accept": "application/json",
        },
    )
    opener = urllib.request.build_opener(_ToolboxNoRedirectHandler())
    try:
        with opener.open(request, timeout=TOOLBOX_SEARCH_TIMEOUT_SECONDS) as response:
            status = int(response.status)
            usage = _toolbox_usage_headers(response.headers)
            if status != 200:
                return {"acquisition_status": "HTTP_ERROR", "http_status": status, "body": None, "usage_headers": usage, "request_sha256": request_sha256}
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
            if content_type != "application/json" and not content_type.endswith("+json"):
                return {"acquisition_status": "NON_JSON_RESPONSE", "http_status": status, "body": None, "usage_headers": usage, "request_sha256": request_sha256}

            deadline = time.monotonic() + TOOLBOX_SEARCH_MAX_RESPONSE_SECONDS
            chunks: list[bytes] = []
            total_bytes = 0
            while total_bytes <= TOOLBOX_SEARCH_MAX_RESPONSE_BYTES:
                if time.monotonic() >= deadline:
                    return {"acquisition_status": "RESPONSE_TIMEOUT", "http_status": status, "body": None, "usage_headers": usage, "request_sha256": request_sha256}
                chunk = response.read(min(8192, TOOLBOX_SEARCH_MAX_RESPONSE_BYTES + 1 - total_bytes))
                if time.monotonic() > deadline:
                    return {"acquisition_status": "RESPONSE_TIMEOUT", "http_status": status, "body": None, "usage_headers": usage, "request_sha256": request_sha256}
                if not chunk:
                    break
                chunks.append(chunk)
                total_bytes += len(chunk)
            if total_bytes > TOOLBOX_SEARCH_MAX_RESPONSE_BYTES:
                return {"acquisition_status": "RESPONSE_TOO_LARGE", "http_status": status, "body": None, "usage_headers": usage, "request_sha256": request_sha256}
            return {
                "acquisition_status": "OK",
                "http_status": status,
                "body": b"".join(chunks),
                "usage_headers": usage,
                "request_sha256": request_sha256,
            }
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        if 300 <= status < 400:
            outcome = "REDIRECT_BLOCKED"
        elif status == 429:
            outcome = "RATE_LIMITED"
        else:
            outcome = "HTTP_ERROR"
        return {"acquisition_status": outcome, "http_status": status, "body": None, "usage_headers": _toolbox_usage_headers(exc.headers), "request_sha256": request_sha256}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"acquisition_status": "NETWORK_ERROR", "http_status": None, "body": None, "usage_headers": {}, "request_sha256": request_sha256}


def search_with_evidence(query: str, limit: int = DEFAULT_LIMIT, mailto: str = DEFAULT_MAILTO) -> dict:
    """搜索 OpenAlex 并同时保留原始响应，供可复现工作流记录来源。

    Args:
        query: 搜索词
        limit: 返回条数（1-25）
        mailto: polite pool 邮箱
    Returns:
        dict containing request_url, response_body (bytes), and normalized results
    """
    limit = max(1, min(int(limit), MAX_LIMIT))
    params = urllib.parse.urlencode({
        "search": query,
        "per-page": limit,
        "mailto": mailto,
    })
    url = f"{API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "OpenAlex-Client/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        response_body = r.read()
    parsed = parse_search_response(response_body)
    return {
        "request_url": url,
        "response_body": response_body,
        "results": parsed["results"],
        "raw_record_sha256": parsed["raw_record_sha256"],
    }


def search(query: str, limit: int = DEFAULT_LIMIT, mailto: str = DEFAULT_MAILTO) -> list[dict]:
    """搜索 OpenAlex，返回标准化的结果列表（兼容原调用方）。"""
    return search_with_evidence(query, limit=limit, mailto=mailto)["results"]


def fetch_by_doi(doi: str, mailto: str = DEFAULT_MAILTO) -> dict | None:
    """通过 DOI 直接获取单篇文献信息。

    Args:
        doi: DOI 字符串（带或不带 https://doi.org/ 前缀）
        mailto: polite pool 邮箱
    Returns:
        标准化的文献 dict 或 None
    """
    doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
    url = f"{API}/doi:{urllib.parse.quote(doi)}?mailto={urllib.parse.quote(mailto)}"
    req = urllib.request.Request(url, headers={"User-Agent": "OpenAlex-Client/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            w = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

    authors = []
    for a in w.get("authorships", []):
        name = a.get("author", {}).get("display_name", "")
        if name:
            authors.append(name)

    abstract = _restore_abstract(w.get("abstract_inverted_index"))
    oa = w.get("open_access", {})
    primary = w.get("primary_location") or {}
    source = primary.get("source") or {}

    return {
        "openalex_id": w.get("id", ""),
        "doi": w.get("doi", ""),
        "title": w.get("title", "") or w.get("display_name", ""),
        "year": w.get("publication_year"),
        "authors": authors,
        "venue": source.get("display_name", ""),
        "type": w.get("type", ""),
        "abstract": abstract,
        "is_oa": oa.get("is_oa", False),
        "oa_status": oa.get("oa_status", ""),
        "oa_url": oa.get("oa_url", ""),
        "any_repository_has_fulltext": oa.get("any_repository_has_fulltext", False),
        "cited_by_count": w.get("cited_by_count", 0),
        "is_retracted": w.get("is_retracted", False),
        "concepts": [c.get("display_name", "") for c in w.get("concepts", [])[:8]],
        "language": w.get("language", ""),
    }


def fetch_by_openalex_id(openalex_id: str, mailto: str = DEFAULT_MAILTO) -> dict | None:
    """通过 OpenAlex ID (W开头) 获取单篇文献。

    Args:
        openalex_id: OpenAlex ID，如 W3168867926 或 https://openalex.org/W3168867926
        mailto: polite pool 邮箱
    Returns:
        标准化的文献 dict 或 None
    """
    oid = openalex_id.replace("https://openalex.org/", "")
    if not oid.startswith("W"):
        raise ValueError(f"Invalid OpenAlex ID: {openalex_id} (must start with W)")
    url = f"{API}/{oid}?mailto={urllib.parse.quote(mailto)}"
    req = urllib.request.Request(url, headers={"User-Agent": "OpenAlex-Client/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            w = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

    authors = []
    for a in w.get("authorships", []):
        name = a.get("author", {}).get("display_name", "")
        if name:
            authors.append(name)

    abstract = _restore_abstract(w.get("abstract_inverted_index"))
    oa = w.get("open_access", {})
    primary = w.get("primary_location") or {}
    source = primary.get("source") or {}

    return {
        "openalex_id": w.get("id", ""),
        "doi": w.get("doi", ""),
        "title": w.get("title", "") or w.get("display_name", ""),
        "year": w.get("publication_year"),
        "authors": authors,
        "venue": source.get("display_name", ""),
        "type": w.get("type", ""),
        "abstract": abstract,
        "is_oa": oa.get("is_oa", False),
        "oa_status": oa.get("oa_status", ""),
        "oa_url": oa.get("oa_url", ""),
        "any_repository_has_fulltext": oa.get("any_repository_has_fulltext", False),
        "cited_by_count": w.get("cited_by_count", 0),
        "is_retracted": w.get("is_retracted", False),
        "concepts": [c.get("display_name", "") for c in w.get("concepts", [])[:8]],
        "language": w.get("language", ""),
    }


# === 撤稿检查 ===
def check_retraction(doi: str | None = None, openalex_id: str | None = None,
                     mailto: str = DEFAULT_MAILTO) -> dict:
    """检查文献是否被撤稿。

    可以通过 DOI 或 OpenAlex ID 查询。
    返回 {is_retracted, retraction_notice_url (if any)}。
    """
    if doi:
        record = fetch_by_doi(doi, mailto)
    elif openalex_id:
        record = fetch_by_openalex_id(openalex_id, mailto)
    else:
        raise ValueError("Must provide doi or openalex_id")

    if record is None:
        return {"found": False, "is_retracted": None, "error": "NOT_FOUND"}

    return {
        "found": True,
        "openalex_id": record["openalex_id"],
        "doi": record["doi"],
        "is_retracted": record["is_retracted"],
        "title": record["title"],
    }


# === 批量 DOI 验证 ===
def batch_verify_dois(dois: list[str], mailto: str = DEFAULT_MAILTO) -> list[dict]:
    """批量验证 DOI 列表，返回每条 DOI 的 OpenAlex 状态。

    用于 088/104/106 协议中的 DOI 交叉核验。
    每条返回 {doi, found, openalex_id, title, year, is_retracted, is_oa}。
    """
    results = []
    for doi in dois:
        doi_clean = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
        record = fetch_by_doi(doi_clean, mailto)
        if record:
            results.append({
                "doi": doi_clean,
                "found": True,
                "openalex_id": record["openalex_id"],
                "title": record["title"],
                "year": record["year"],
                "is_retracted": record["is_retracted"],
                "is_oa": record["is_oa"],
            })
        else:
            results.append({
                "doi": doi_clean,
                "found": False,
                "openalex_id": None,
                "title": None,
                "year": None,
                "is_retracted": None,
                "is_oa": None,
            })
    return results


if __name__ == "__main__":
    args = sys.argv[1:]

    # 解析参数
    mailto = DEFAULT_MAILTO
    json_output = False
    doi_mode = False
    id_mode = False
    retraction_mode = False
    batch_mode = False
    positional = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--mailto" and i + 1 < len(args):
            mailto = args[i + 1]
            i += 2
        elif arg == "--json":
            json_output = True
            i += 1
        elif arg == "--doi":
            doi_mode = True
            i += 1
        elif arg == "--id":
            id_mode = True
            i += 1
        elif arg == "--retraction":
            retraction_mode = True
            i += 1
        elif arg == "--batch-doi":
            batch_mode = True
            i += 1
        else:
            positional.append(arg)
            i += 1

    # DOI 模式
    if doi_mode and positional:
        record = fetch_by_doi(positional[0], mailto)
        if record:
            print(json.dumps(record, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"found": False}, ensure_ascii=False))
        sys.exit(0)

    # OpenAlex ID 模式
    if id_mode and positional:
        record = fetch_by_openalex_id(positional[0], mailto)
        if record:
            print(json.dumps(record, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"found": False}, ensure_ascii=False))
        sys.exit(0)

    # 撤稿检查模式
    if retraction_mode and positional:
        result = check_retraction(doi=positional[0], mailto=mailto)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    # 批量 DOI 验证模式
    if batch_mode and positional:
        dois = positional[0].split(",")
        results = batch_verify_dois([d.strip() for d in dois], mailto)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        sys.exit(0)

    # 默认搜索模式
    if not positional:
        print("Usage: python3 openalex_client.py \"query\" [limit] [--mailto email] [--json]")
        print("       python3 openalex_client.py --doi 10.48550/arxiv.2106.09685")
        print("       python3 openalex_client.py --id W3168867926")
        print("       python3 openalex_client.py --retraction 10.48550/arxiv.2106.09685")
        print("       python3 openalex_client.py --batch-doi 'doi1,doi2,doi3'")
        sys.exit(1)

    q = positional[0]
    lim = DEFAULT_LIMIT
    if len(positional) > 1 and positional[1].isdigit():
        lim = int(positional[1])

    results = search(q, lim, mailto)
    print(json.dumps(results, ensure_ascii=False, indent=2))
