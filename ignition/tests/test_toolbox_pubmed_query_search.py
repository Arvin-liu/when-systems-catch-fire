from __future__ import annotations

import importlib.util
import io
import json
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_pubmed_query_search.py"
SPEC = importlib.util.spec_from_file_location("toolbox_pubmed_query_search", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)

QUERY = "microplastics"
EMAIL = "researcher@example.org"
ESEARCH = {"esearchresult": {"count": "2", "idlist": ["12345678", "87654321"], "querytranslation": "ignored"}}
ESUMMARY = {
    "result": {
        "uids": ["12345678", "87654321"],
        "12345678": {
            "uid": "12345678",
            "title": "Example title",
            "pubdate": "2025 Jan",
            "fulljournalname": "Example Journal",
            "authors": [{"name": "Author One"}, {"name": "Author Two"}],
            "articleids": [{"idtype": "pubmed", "value": "12345678"}, {"idtype": "doi", "value": "10.1234/example"}],
            "abstract": "Must not be returned.",
        },
        "87654321": {
            "uid": "87654321",
            "title": "Second title",
            "authors": [],
            "articleids": [],
        },
    }
}


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, content_type: str = "application/json") -> None:
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
        value = self.body[self.offset:end]
        self.offset = end
        return value


class FakeOpener:
    def __init__(self, responses: list[FakeResponse | Exception]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[object, int]] = []

    def open(self, request: object, timeout: int) -> FakeResponse:
        self.calls.append((request, timeout))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeStdin:
    def __init__(self, payload: bytes) -> None:
        self.buffer = io.BytesIO(payload)


def request_bytes(query: str = QUERY, max_results: int = 2, email: str = EMAIL) -> bytes:
    return json.dumps({"query": query, "max_results": max_results, "contact_email": email}).encode("utf-8")


def json_response(value: object) -> FakeResponse:
    return FakeResponse(json.dumps(value).encode("utf-8"))


class PubMedQuerySearchTests(unittest.TestCase):
    def test_two_fixed_host_requests_return_bounded_metadata_without_echoing_input(self) -> None:
        opener = FakeOpener([json_response(ESEARCH), json_response(ESUMMARY)])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            receipt = TOOL.search(QUERY, 2, EMAIL)
        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        self.assertEqual(len(opener.calls), 2)
        first, first_timeout = opener.calls[0]
        second, second_timeout = opener.calls[1]
        self.assertEqual(first_timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(second_timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        esearch = urlsplit(first.full_url)
        self.assertEqual(esearch.scheme, "https")
        self.assertEqual(esearch.hostname, TOOL.API_HOST)
        self.assertEqual(esearch.path, "/entrez/eutils/esearch.fcgi")
        self.assertEqual(parse_qs(esearch.query), {
            "db": ["pubmed"], "term": [QUERY], "retmax": ["2"], "retmode": ["json"],
            "sort": ["relevance"], "tool": [TOOL.TOOL_CONTACT], "email": [EMAIL],
        })
        esummary = urlsplit(second.full_url)
        self.assertEqual(esummary.hostname, TOOL.API_HOST)
        self.assertEqual(esummary.path, "/entrez/eutils/esummary.fcgi")
        self.assertEqual(parse_qs(esummary.query), {
            "db": ["pubmed"], "id": ["12345678,87654321"], "retmode": ["json"],
            "tool": [TOOL.TOOL_CONTACT], "email": [EMAIL],
        })
        self.assertEqual(receipt["status"], "FOUND")
        self.assertEqual(receipt["hit_count"], 2)
        self.assertEqual(receipt["search_returned_pmids"], ["12345678", "87654321"])
        self.assertEqual(receipt["returned_count"], 2)
        self.assertEqual(receipt["records"][0]["doi"], "10.1234/example")
        self.assertNotIn(QUERY, json.dumps(receipt))
        self.assertNotIn(EMAIL, json.dumps(receipt))
        self.assertNotIn("abstract", json.dumps(receipt).casefold())

    def test_network_flag_is_required_before_any_request(self) -> None:
        opener = FakeOpener([json_response(ESEARCH), json_response(ESUMMARY)])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(opener.calls, [])
        self.assertIn("--allow-public-network", stderr.getvalue())

    def test_cli_opt_in_emits_one_json_receipt_and_keeps_email_out(self) -> None:
        opener = FakeOpener([json_response(ESEARCH), json_response(ESUMMARY)])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin", "--allow-public-network"])
        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(len(opener.calls), 2)
        self.assertEqual(json.loads(stdout.getvalue())["tool_id"], TOOL.TOOL_ID)
        self.assertNotIn(EMAIL, stdout.getvalue())

    def test_no_match_makes_only_esearch_request(self) -> None:
        opener = FakeOpener([json_response({"esearchresult": {"count": "0", "idlist": []}})])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.search(QUERY, 2, EMAIL)
        self.assertEqual(receipt["status"], "NO_MATCH")
        self.assertEqual(receipt["hit_count"], 0)
        self.assertEqual(receipt["records"], [])
        self.assertEqual(receipt["request_count"], 1)
        self.assertEqual(len(opener.calls), 1)

    def test_partial_summary_and_malformed_search_are_not_hidden(self) -> None:
        partial = {"result": {"uids": ["12345678"], "12345678": ESUMMARY["result"]["12345678"]}}
        opener = FakeOpener([json_response(ESEARCH), json_response(partial)])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.search(QUERY, 2, EMAIL)
        self.assertEqual(receipt["status"], "PARTIAL")
        self.assertEqual(receipt["missing_summary_pmids"], ["87654321"])

        malformed = FakeOpener([json_response({"esearchresult": {"count": "many", "idlist": []}})])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=malformed):
            receipt = TOOL.search(QUERY, 2, EMAIL)
        self.assertEqual(receipt["acquisition_status"], "INVALID_ESEARCH_RESPONSE")
        self.assertIsNone(receipt["hit_count"])
        self.assertIsNotNone(receipt["response_sha256"]["esearch"])

    def test_rejects_duplicate_keys_controls_limits_extra_fields_and_bad_email(self) -> None:
        bad_requests = [
            b'{"query":"one","query":"two","max_results":1,"contact_email":"x@example.org"}',
            json.dumps({"query": QUERY, "max_results": True, "contact_email": EMAIL}).encode(),
            json.dumps({"query": QUERY, "max_results": 11, "contact_email": EMAIL}).encode(),
            json.dumps({"query": "x\nother", "max_results": 1, "contact_email": EMAIL}).encode(),
            json.dumps({"query": "x" * (TOOL.MAX_QUERY_CHARS + 1), "max_results": 1, "contact_email": EMAIL}).encode(),
            json.dumps({"query": QUERY, "max_results": 1, "contact_email": "bad@example.org\r\nX-Test:y"}).encode(),
            json.dumps({"query": QUERY, "max_results": 1, "contact_email": EMAIL, "extra": "no"}).encode(),
            b" " * (TOOL.MAX_REQUEST_BYTES + 1),
        ]
        for raw in bad_requests:
            with self.subTest(raw=raw[:40]), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)
        with self.assertRaisesRegex(TOOL.ToolInputError, "trimmed"):
            TOOL.parse_request(request_bytes(" microplastics "))

    def test_redirect_oversize_wrong_content_type_and_network_failures_are_bounded(self) -> None:
        redirect = FakeOpener([HTTPError(TOOL.ESEARCH_BASE, 302, "redirect", {}, None)])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=redirect):
            self.assertEqual(TOOL.search(QUERY, 2, EMAIL)["acquisition_status"], "REDIRECT_BLOCKED")

        oversized = FakeOpener([FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1))])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=oversized):
            self.assertEqual(TOOL.search(QUERY, 2, EMAIL)["acquisition_status"], "RESPONSE_TOO_LARGE")

        html = FakeOpener([FakeResponse(b"<html/>", content_type="text/html")])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=html):
            self.assertEqual(TOOL.search(QUERY, 2, EMAIL)["acquisition_status"], "NON_JSON_RESPONSE")

        offline = FakeOpener([OSError("offline")])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=offline):
            self.assertEqual(TOOL.search(QUERY, 2, EMAIL)["acquisition_status"], "NETWORK_ERROR")

    def test_summary_failure_is_explicit_and_keeps_the_search_observation(self) -> None:
        opener = FakeOpener([json_response(ESEARCH), HTTPError(TOOL.ESUMMARY_BASE, 503, "busy", {}, None)])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.search(QUERY, 2, EMAIL)
        self.assertEqual(receipt["acquisition_status"], "ESUMMARY_HTTP_ERROR")
        self.assertEqual(receipt["hit_count"], 2)
        self.assertEqual(receipt["search_returned_pmids"], ["12345678", "87654321"])
        self.assertEqual(receipt["records"], [])
        self.assertEqual(receipt["http_status"]["esummary"], 503)


if __name__ == "__main__":
    unittest.main()
