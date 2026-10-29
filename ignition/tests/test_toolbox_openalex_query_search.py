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
import toolbox_openalex_query_search as TOOL  # noqa: E402


def work(identifier: str = "W123", title: str = "A bounded result") -> dict:
    return {
        "id": f"https://openalex.org/{identifier}",
        "doi": "https://doi.org/10.1234/example",
        "display_name": title,
        "publication_year": 2025,
        "type": "article",
        "relevance_score": 0.72,
        "authorships": [
            {"author": {"display_name": "Author One"}},
            {"author": {"display_name": "Author Two"}},
        ],
        "primary_location": {"source": {"display_name": "Example Journal"}},
        "abstract_inverted_index": {"private": [0]},
    }


def response_body(results: list[dict] | None = None, count: int = 1) -> bytes:
    return json.dumps({"meta": {"count": count, "per_page": len(results or [])}, "results": results or []}).encode()


def request_bytes(query: str = "artificial intelligence healthcare", max_results: int = 2) -> bytes:
    return json.dumps({"query": query, "max_results": max_results}).encode("utf-8")


class FakeResponse:
    def __init__(self, body: bytes, content_type: str = "application/json", status: int = 200) -> None:
        self.body = body
        self.offset = 0
        self.status = status
        self.headers = {
            "Content-Type": content_type,
            "X-RateLimit-Limit": "100000",
            "X-RateLimit-Remaining": "99999",
            "X-RateLimit-Credits-Used": "10",
            "X-RateLimit-Reset": "0",
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
        self.response = response or FakeResponse(response_body([work()], count=7))
        self.error = error
        self.calls: list[tuple[object, int]] = []

    def open(self, request: object, timeout: int) -> FakeResponse:
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


class OpenAlexQuerySearchTests(unittest.TestCase):
    def test_input_contract_is_exact_and_bounded(self) -> None:
        self.assertEqual(TOOL.parse_request(request_bytes()), ("artificial intelligence healthcare", 2))
        for raw in (
            b'{"query":"x","query":"y","max_results":1}',
            b'{"query":"x","max_results":true}',
            b'{"query":" x","max_results":1}',
            b'{"query":"x\\n y","max_results":1}',
            b'{"query":"x","max_results":11}',
            b'{"query":"x","max_results":1,"api_key":"secret"}',
        ):
            with self.subTest(raw=raw), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)

    def test_toolbox_output_is_bounded_and_does_not_echo_query_or_abstract(self) -> None:
        opener = FakeOpener(FakeResponse(response_body([work()], count=7)))
        with patch.object(TOOL.OPENALEX.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.search(request_bytes())
        self.assertEqual(receipt["status"], "FOUND")
        self.assertEqual(receipt["provider_hit_count"], 7)
        self.assertEqual(receipt["returned_count"], 1)
        self.assertEqual(receipt["records"][0]["openalex_id"], "https://openalex.org/W123")
        self.assertEqual(receipt["records"][0]["author_names"], ["Author One", "Author Two"])
        self.assertNotIn("abstract", json.dumps(receipt))
        self.assertNotIn("artificial intelligence healthcare", json.dumps(receipt))
        self.assertEqual(receipt["usage_headers"]["X-RateLimit-Credits-Used"], "10")
        self.assertEqual(receipt["request_count"], 1)
        self.assertEqual(len(opener.calls), 1)

    def test_empty_results_are_not_a_request_failure(self) -> None:
        opener = FakeOpener(FakeResponse(response_body([], count=0)))
        with patch.object(TOOL.OPENALEX.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.search(request_bytes())
        self.assertEqual(receipt["status"], "NOT_FOUND")
        self.assertEqual(receipt["acquisition_status"], "OK")
        self.assertEqual(receipt["records"], [])

    def test_work_ids_must_be_unique_and_bound_to_openalex(self) -> None:
        for records in ([work("W1"), work("W1")], [work("https://example.org/W1")]):
            opener = FakeOpener(FakeResponse(response_body(records, count=len(records))))
            with patch.object(TOOL.OPENALEX.urllib.request, "build_opener", return_value=opener):
                receipt = TOOL.search(request_bytes())
            self.assertEqual(receipt["status"], "FAILED")
            self.assertEqual(receipt["acquisition_status"], "INVALID_RESPONSE")
            self.assertEqual(receipt["records"], [])

    def test_shared_client_uses_one_fixed_no_key_query_without_mailto(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.OPENALEX.urllib.request, "build_opener", return_value=opener):
            fetched = TOOL.OPENALEX.search_for_toolbox("topic phrase", 2)
        self.assertEqual(fetched["acquisition_status"], "OK")
        self.assertEqual(len(opener.calls), 1)
        request, timeout = opener.calls[0]
        self.assertEqual(timeout, TOOL.OPENALEX.TOOLBOX_SEARCH_TIMEOUT_SECONDS)
        parsed = urllib.parse.urlsplit(request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "api.openalex.org")
        params = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(params["search"], ["topic phrase"])
        self.assertEqual(params["per_page"], ["2"])
        self.assertIn("display_name", params["select"][0])
        self.assertNotIn("mailto", params)
        self.assertNotIn("api_key", params)
        self.assertNotIn("Authorization", request.headers)
        self.assertIsNotNone(fetched["request_sha256"])

    def test_redirect_is_rejected_without_following(self) -> None:
        error = urllib.error.HTTPError("https://api.openalex.org/works", 302, "redirect", {}, None)
        opener = FakeOpener(error=error)
        with patch.object(TOOL.OPENALEX.urllib.request, "build_opener", return_value=opener):
            fetched = TOOL.OPENALEX.search_for_toolbox("topic", 1)
        self.assertEqual(fetched["acquisition_status"], "REDIRECT_BLOCKED")
        self.assertEqual(len(opener.calls), 1)

    def test_wrong_content_type_and_oversized_response_fail_closed(self) -> None:
        for fake_response, expected in (
            (FakeResponse(b"<html>not json</html>", content_type="text/html"), "NON_JSON_RESPONSE"),
            (FakeResponse(b"x" * (TOOL.OPENALEX.TOOLBOX_SEARCH_MAX_RESPONSE_BYTES + 1)), "RESPONSE_TOO_LARGE"),
        ):
            opener = FakeOpener(fake_response)
            with patch.object(TOOL.OPENALEX.urllib.request, "build_opener", return_value=opener):
                receipt = TOOL.search(request_bytes())
            self.assertEqual(receipt["status"], "FAILED")
            self.assertEqual(receipt["acquisition_status"], expected)
            self.assertEqual(receipt["records"], [])
            self.assertEqual(len(opener.calls), 1)

    def test_rate_limit_is_reported_without_retry(self) -> None:
        error = urllib.error.HTTPError("https://api.openalex.org/works", 429, "rate limit", {}, None)
        opener = FakeOpener(error=error)
        with patch.object(TOOL.OPENALEX.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.search(request_bytes())
        self.assertEqual(receipt["acquisition_status"], "RATE_LIMITED")
        self.assertEqual(receipt["http_status"], 429)
        self.assertEqual(len(opener.calls), 1)

    def test_toolbox_mode_requires_explicit_network_flag(self) -> None:
        error = io.StringIO()
        with patch.object(TOOL.sys, "stderr", error), patch.object(TOOL.OPENALEX, "search_for_toolbox") as search:
            code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        search.assert_not_called()
        self.assertIn("--allow-public-network", error.getvalue())


if __name__ == "__main__":
    unittest.main()
