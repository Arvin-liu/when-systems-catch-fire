from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import toolbox_arxiv_query_search as TOOL  # noqa: E402


def entry(identifier: str, title: str, *, authors: int = 1, abstract: str = "abstract must not be returned") -> str:
    author_xml = "".join(f"<author><name>Author {n}</name></author>" for n in range(authors))
    return (
        "<entry>"
        f"<id>https://arxiv.org/abs/{identifier}</id>"
        f"<title>{title}</title>{author_xml}"
        "<published>2026-10-20T00:00:00Z</published><updated>2026-10-21T00:00:00Z</updated>"
        "<arxiv:primary_category term=\"cs.AI\"/><category term=\"cs.AI\"/>"
        "<arxiv:journal_ref>Journal ref</arxiv:journal_ref><arxiv:doi>10.1234/example</arxiv:doi>"
        f"<summary>{abstract}</summary></entry>"
    )


def feed(entries: list[str], total: int | None = None) -> bytes:
    total = len(entries) if total is None else total
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:arxiv="http://arxiv.org/schemas/atom" '
        'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
        f"<opensearch:totalResults>{total}</opensearch:totalResults>"
        + "".join(entries)
        + "</feed>"
    )
    return body.encode("utf-8")


ENTRY = feed([
    entry("2610.04074v2", "Example title", authors=12),
    entry("hep-th/9901001v1", "Legacy result"),
], total=19)


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, content_type: str = "application/atom+xml") -> None:
        self.body = body
        self.offset = 0
        self.status = status
        self.headers = {"Content-Type": content_type}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        end = len(self.body) if size < 0 else min(len(self.body), self.offset + size)
        chunk = self.body[self.offset:end]
        self.offset = end
        return chunk


class FakeOpener:
    def __init__(self, response: FakeResponse | None = None, error: Exception | None = None) -> None:
        self.response = response or FakeResponse(ENTRY)
        self.error = error
        self.calls: list[tuple[object, int]] = []

    def open(self, request: object, timeout: int) -> FakeResponse:
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


class FakeStdin:
    def __init__(self, payload: bytes) -> None:
        self.buffer = io.BytesIO(payload)


def request_bytes(query: str = 'all:"artificial intelligence"', max_results: int = 2) -> bytes:
    return json.dumps({"query": query, "max_results": max_results}).encode("utf-8")


class ArxivQuerySearchTests(unittest.TestCase):
    def test_one_fixed_host_request_returns_bounded_metadata_without_query_or_abstract(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            result = TOOL.search(request_bytes())
        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        self.assertEqual(len(opener.calls), 1)
        request, timeout = opener.calls[0]
        parsed = urlsplit(request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "export.arxiv.org")
        self.assertEqual(parsed.path, "/api/query")
        self.assertEqual(parse_qs(parsed.query), {
            "search_query": ['all:"artificial intelligence"'],
            "start": ["0"],
            "max_results": ["2"],
            "sortBy": ["relevance"],
            "sortOrder": ["descending"],
        })
        self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(result["status"], "FOUND")
        self.assertEqual(result["hit_count"], 19)
        self.assertEqual(result["returned_count"], 2)
        self.assertEqual(result["request_count"], 1)
        self.assertEqual(result["records"][0]["author_count"], 12)
        self.assertTrue(result["records"][0]["authors_truncated"])
        self.assertEqual(result["records"][1]["arxiv_id"], "hep-th/9901001v1")
        encoded = json.dumps(result)
        self.assertNotIn('all:"artificial intelligence"', encoded)
        self.assertNotIn("abstract must not be returned", encoded)
        self.assertNotIn("summary", encoded)
        self.assertEqual(result["source_endpoint"], TOOL.API_BASE)
        self.assertEqual(len(result["query_sha256"]), 64)
        self.assertEqual(len(result["response_sha256"]), 64)

    def test_network_requires_per_call_flag_and_exact_stdin_mode(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(opener.calls, [])
        self.assertIn("--allow-public-network", stderr.getvalue())

    def test_cli_explicit_opt_in_emits_one_receipt_without_raw_query(self) -> None:
        opener = FakeOpener()
        query = "private test phrase"
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(sys, "stdin", FakeStdin(request_bytes(query))):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin", "--allow-public-network"])
        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(len(opener.calls), 1)
        receipt = json.loads(stdout.getvalue())
        self.assertEqual(receipt["tool_id"], TOOL.TOOL_ID)
        self.assertNotIn(query, stdout.getvalue())

    def test_rejects_ambiguous_or_oversized_requests_before_network(self) -> None:
        bad = [
            b'{"query":"x"}',
            b'{"query":"x","max_results":1,"extra":true}',
            b'{"query":" ","max_results":1}',
            b'{"query":" x","max_results":1}',
            b'{"query":"x\\ny","max_results":1}',
            b'{"query":"x","max_results":true}',
            b'{"query":"x","max_results":0}',
            b'{"query":"x","max_results":11}',
            b'{"query":"x","max_results":1,"max_results":2}',
            b'{"query":"\xff","max_results":1}',
            b" " * (TOOL.MAX_REQUEST_BYTES + 1),
            json.dumps({"query": "x" * (TOOL.MAX_QUERY_CHARS + 1), "max_results": 1}).encode(),
        ]
        for raw in bad:
            with self.subTest(raw=raw[:40]), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)

    def test_no_match_provider_error_dtd_and_invalid_feed_are_explicit(self) -> None:
        cases = [
            (feed([], total=0), "NO_MATCH"),
            (b'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"><opensearch:totalResults>1</opensearch:totalResults><entry><id>http://arxiv.org/api/errors#bad</id></entry></feed>', "PROVIDER_ERROR_ENTRY"),
            (b'<!DOCTYPE feed [<!ENTITY x "x">]><feed/>', "INVALID_XML_RESPONSE"),
            (b"<not-feed/>", "INVALID_PROVIDER_RESPONSE"),
            (feed([], total=1), "INVALID_PROVIDER_RESPONSE"),
        ]
        for body, expected in cases:
            opener = FakeOpener(FakeResponse(body))
            with self.subTest(status=expected), patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                result = TOOL.search(request_bytes())
            self.assertEqual(result["status"], expected)
            self.assertEqual(result["records"], [])

    def test_rejects_unsafe_provider_entry_and_more_rows_than_requested(self) -> None:
        unsafe = feed([entry("2610.04074", "Unsafe").replace(
            "https://arxiv.org/abs/2610.04074", "https://evil.example/abs/2610.04074"
        )])
        too_many = feed([entry("2610.04074", "One"), entry("2610.04075", "Two"), entry("2610.04076", "Three")], total=3)
        duplicated = feed([entry("2610.04074", "One"), entry("2610.04074", "Duplicate")], total=2)
        for body in (unsafe, too_many, duplicated):
            opener = FakeOpener(FakeResponse(body))
            with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                result = TOOL.search(request_bytes(max_results=2))
            self.assertEqual(result["status"], "INVALID_PROVIDER_RESPONSE")
            self.assertEqual(result["records"], [])

    def test_rejects_wrong_content_type_redirects_network_errors_and_oversized_body(self) -> None:
        cases = [
            (FakeOpener(FakeResponse(ENTRY, content_type="text/html")), "NON_ATOM_RESPONSE"),
            (FakeOpener(error=HTTPError("https://export.arxiv.org", 302, "redirect", {}, None)), "REDIRECT_BLOCKED"),
            (FakeOpener(error=HTTPError("https://export.arxiv.org", 429, "limited", {}, None)), "RATE_LIMITED"),
            (FakeOpener(error=OSError("offline")), "NETWORK_ERROR"),
            (FakeOpener(FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1))), "RESPONSE_TOO_LARGE"),
        ]
        for opener, expected in cases:
            with self.subTest(status=expected), patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                result = TOOL.search(request_bytes())
            self.assertEqual(result["status"], expected)
            self.assertEqual(len(opener.calls), 1)
            self.assertEqual(result["records"], [])


if __name__ == "__main__":
    unittest.main()
