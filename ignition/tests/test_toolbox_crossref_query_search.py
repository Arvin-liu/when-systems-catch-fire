from __future__ import annotations

import io
import json
import sys
import urllib.error
import urllib.parse
import unittest
from pathlib import Path
from unittest.mock import patch


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_crossref_query_search as TOOL  # noqa: E402


def work(doi: str = "10.1234/example", title: str = "A Crossref result") -> dict:
    return {
        "DOI": doi,
        "title": [title],
        "author": [{"given": "Ada", "family": "Writer"}, {"name": "Grace Editor"}],
        "issued": {"date-parts": [[2024, 2, 3]]},
        "type": "journal-article",
        "publisher": "Example Publisher",
        "container-title": ["Example Journal"],
        "is-referenced-by-count": 17,
        "abstract": "This copyrighted abstract must not be projected.",
        "reference": [{"DOI": "10.1234/another"}],
    }


def response_body(items: list[dict] | None = None, total: int = 1) -> bytes:
    return json.dumps({"status": "ok", "message": {"total-results": total, "items": items or []}}).encode()


def request_bytes(query: str = "artificial intelligence healthcare", max_results: int = 2) -> bytes:
    return json.dumps({"query": query, "max_results": max_results}).encode("utf-8")


class FakeResponse:
    def __init__(self, body: bytes, content_type: str = "application/json", status: int = 200) -> None:
        self.body = body
        self.offset = 0
        self.status = status
        self.headers = {
            "Content-Type": content_type,
            "x-rate-limit-limit": "1",
            "x-rate-limit-interval": "1s",
            "x-rate-limit-type": "list",
        }

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
        self.response = response or FakeResponse(response_body([work()], total=7))
        self.error = error
        self.calls: list[tuple[object, int]] = []

    def open(self, request: object, timeout: int) -> FakeResponse:
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


class CrossrefQuerySearchTests(unittest.TestCase):
    def test_input_contract_is_exact_and_bounded(self) -> None:
        self.assertEqual(TOOL.parse_request(request_bytes()), ("artificial intelligence healthcare", 2))
        for raw in (
            b'{"query":"x","query":"y","max_results":1}',
            b'{"query":"x","max_results":true}',
            b'{"query":" x","max_results":1}',
            b'{"query":"x\\n y","max_results":1}',
            b'{"query":"x","max_results":11}',
            b'{"query":"x","max_results":1,"mailto":"person@example.org"}',
            b'{"query":"x","max_results":1,"api_key":"secret"}',
            b'{"query":"x","max_results":1.0}',
        ):
            with self.subTest(raw=raw), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)

    def test_bounded_crossref_projection_omits_query_abstract_and_references(self) -> None:
        opener = FakeOpener(FakeResponse(response_body([work()], total=7)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.search(request_bytes())
        encoded = json.dumps(receipt, ensure_ascii=False)
        self.assertEqual(receipt["status"], "FOUND")
        self.assertEqual(receipt["provider_hit_count"], 7)
        self.assertEqual(receipt["returned_count"], 1)
        self.assertEqual(receipt["records"][0]["doi"], "10.1234/example")
        self.assertEqual(receipt["records"][0]["publication_year"], 2024)
        self.assertEqual(receipt["records"][0]["author_names"], ["Ada Writer", "Grace Editor"])
        self.assertEqual(receipt["usage_headers"]["x-rate-limit-limit"], "1")
        self.assertNotIn("abstract", encoded)
        self.assertNotIn("reference", encoded)
        self.assertNotIn("artificial intelligence healthcare", encoded)
        self.assertEqual(receipt["request_count"], 1)
        self.assertEqual(len(opener.calls), 1)

    def test_request_uses_only_fixed_versioned_endpoint_and_one_public_query(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            fetched = TOOL._fetch("a public query", 3)
        self.assertEqual(fetched["acquisition_status"], "OK")
        self.assertEqual(len(opener.calls), 1)
        request, timeout = opener.calls[0]
        self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        parsed = urllib.parse.urlsplit(request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "api.crossref.org")
        self.assertEqual(parsed.path, "/v1/works")
        params = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(params["query"], ["a public query"])
        self.assertEqual(params["rows"], ["3"])
        self.assertIn("DOI", params["select"][0])
        self.assertNotIn("abstract", params["select"][0])
        self.assertNotIn("mailto", params)
        self.assertNotIn("Authorization", request.headers)
        self.assertIsNotNone(fetched["request_sha256"])

    def test_empty_results_are_not_a_request_failure(self) -> None:
        opener = FakeOpener(FakeResponse(response_body([], total=0)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.search(request_bytes())
        self.assertEqual(receipt["status"], "NOT_FOUND")
        self.assertEqual(receipt["acquisition_status"], "OK")
        self.assertEqual(receipt["records"], [])

    def test_duplicate_doi_invalid_year_and_over_limit_rows_fail_closed(self) -> None:
        scenarios = (
            ([work("10.1234/same"), work("10.1234/same")], 2),
            ([{**work(), "issued": {"date-parts": [[True]]}}], 1),
            ([work(), work("10.1234/second"), work("10.1234/third")], 2),
        )
        for items, requested_limit in scenarios:
            with self.subTest(items=len(items), requested=requested_limit):
                opener = FakeOpener(FakeResponse(response_body(items, total=len(items))))
                raw = request_bytes(max_results=requested_limit)
                with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                    receipt = TOOL.search(raw)
                self.assertEqual(receipt["status"], "FAILED")
                self.assertEqual(receipt["acquisition_status"], "INVALID_RESPONSE")
                self.assertEqual(receipt["records"], [])

    def test_missing_doi_is_retained_as_incomplete_provider_metadata(self) -> None:
        item = work()
        item.pop("DOI")
        opener = FakeOpener(FakeResponse(response_body([item], total=1)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.search(request_bytes())
        self.assertEqual(receipt["status"], "FOUND")
        self.assertIsNone(receipt["records"][0]["doi"])

    def test_provider_null_year_is_retained_as_unreported(self) -> None:
        item = work()
        item["issued"] = {"date-parts": [[None]]}
        opener = FakeOpener(FakeResponse(response_body([item], total=1)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.search(request_bytes())
        self.assertEqual(receipt["status"], "FOUND")
        self.assertIsNone(receipt["records"][0]["publication_year"])

    def test_rate_limit_is_reported_without_retry(self) -> None:
        error = urllib.error.HTTPError("https://api.crossref.org/v1/works", 429, "rate limit", {}, None)
        opener = FakeOpener(error=error)
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            fetched = TOOL._fetch("topic", 1)
        self.assertEqual(fetched["acquisition_status"], "RATE_LIMITED")
        self.assertEqual(fetched["http_status"], 429)
        self.assertEqual(len(opener.calls), 1)

    def test_redirect_is_rejected_without_following(self) -> None:
        error = urllib.error.HTTPError("https://api.crossref.org/v1/works", 302, "redirect", {}, None)
        opener = FakeOpener(error=error)
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            fetched = TOOL._fetch("topic", 1)
        self.assertEqual(fetched["acquisition_status"], "REDIRECT_BLOCKED")
        self.assertEqual(len(opener.calls), 1)

    def test_wrong_content_type_and_oversized_response_fail_closed(self) -> None:
        for response, expected in (
            (FakeResponse(b"<html>no</html>", content_type="text/html"), "NON_JSON_RESPONSE"),
            (FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1)), "RESPONSE_TOO_LARGE"),
        ):
            opener = FakeOpener(response)
            with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                receipt = TOOL.search(request_bytes())
            self.assertEqual(receipt["status"], "FAILED")
            self.assertEqual(receipt["acquisition_status"], expected)
            self.assertEqual(receipt["records"], [])
            self.assertEqual(len(opener.calls), 1)

    def test_network_cli_requires_both_explicit_flags(self) -> None:
        error = io.StringIO()
        with patch.object(TOOL.sys, "stderr", error), patch.object(TOOL, "_fetch") as fetch:
            code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        fetch.assert_not_called()
        self.assertIn("--allow-public-network", error.getvalue())


if __name__ == "__main__":
    unittest.main()
