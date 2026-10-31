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
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_europe_pmc_query_search.py"
SPEC = importlib.util.spec_from_file_location("toolbox_europe_pmc_query_search", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


QUERY = '"CRISPR off-target"'
SAMPLE_RESPONSE = {
    "hitCount": "1",
    "request": {"queryString": "must not be echoed"},
    "resultList": {"result": [{
        "source": "MED",
        "id": "12345678",
        "pmid": "12345678",
        "pmcid": "PMC1234567",
        "doi": "10.1234/example",
        "title": "Example title",
        "authorString": "Author One, Author Two",
        "journalTitle": "Example Journal",
        "pubYear": "2025",
        "abstractText": "This field must not be returned.",
    }]},
}


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, content_type: str = "application/json") -> None:
        self.body = body
        self.offset = 0
        self.read_calls = 0
        self.status = status
        self.headers = {"Content-Type": content_type}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        self.read_calls += 1
        end = len(self.body) if size < 0 else min(len(self.body), self.offset + size)
        value = self.body[self.offset:end]
        self.offset = end
        return value


class FakeOpener:
    def __init__(self, response: FakeResponse | None = None, error: Exception | None = None) -> None:
        self.response = response or FakeResponse(json.dumps(SAMPLE_RESPONSE).encode("utf-8"))
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


def request_bytes(query: str = QUERY, max_results: int = 3) -> bytes:
    return json.dumps({"query": query, "max_results": max_results}).encode("utf-8")


class EuropePmcQuerySearchTests(unittest.TestCase):
    def test_search_uses_one_fixed_host_lite_json_request_and_returns_bounded_fields(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            receipt = TOOL.search(QUERY, 3)

        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        self.assertEqual(len(opener.calls), 1)
        request, timeout = opener.calls[0]
        parsed = urlsplit(request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "www.ebi.ac.uk")
        self.assertEqual(parsed.path, "/europepmc/webservices/rest/search")
        self.assertEqual(parse_qs(parsed.query), {
            "query": [QUERY], "format": ["json"], "resultType": ["lite"], "pageSize": ["3"],
        })
        self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(receipt["status"], "FOUND")
        self.assertEqual(receipt["hit_count"], 1)
        self.assertEqual(receipt["returned_count"], 1)
        self.assertEqual(receipt["records"][0]["source"], "MED")
        self.assertEqual(receipt["records"][0]["pmid"], "12345678")
        self.assertNotIn("abstract", json.dumps(receipt).casefold())
        self.assertNotIn(QUERY, json.dumps(receipt))
        self.assertEqual(len(receipt["query_sha256"]), 64)
        self.assertEqual(len(receipt["response_sha256"]), 64)

    def test_public_network_requires_explicit_per_invocation_flag(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(opener.calls, [])
        self.assertIn("--allow-public-network", stderr.getvalue())

    def test_cli_explicit_opt_in_emits_one_json_receipt(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin", "--allow-public-network"])
        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(json.loads(stdout.getvalue())["tool_id"], TOOL.TOOL_ID)

    def test_rejects_duplicate_keys_controls_bad_limits_and_overlong_queries(self) -> None:
        bad_requests = [
            b'{"query":"topic","query":"other","max_results":1}',
            b'{"query":"topic","max_results":true}',
            b'{"query":"topic","max_results":0}',
            b'{"query":"topic","max_results":11}',
            b'{"query":"topic\\nother","max_results":1}',
            json.dumps({"query": "x" * (TOOL.MAX_QUERY_CHARS + 1), "max_results": 1}).encode(),
            json.dumps({"query": "topic", "max_results": 1, "extra": "no"}).encode(),
            b" " * (TOOL.MAX_REQUEST_BYTES + 1),
        ]
        for raw in bad_requests:
            with self.subTest(raw=raw[:48]), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)
        with self.assertRaisesRegex(TOOL.ToolInputError, "trimmed"):
            TOOL.parse_request(request_bytes(" topic "))

    def test_no_match_and_invalid_provider_response_remain_explicit(self) -> None:
        empty = {"hitCount": "0", "resultList": {"result": []}}
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(json.dumps(empty).encode()))):
            receipt = TOOL.search(QUERY, 3)
        self.assertEqual(receipt["status"], "NO_MATCH")
        self.assertEqual(receipt["hit_count"], 0)
        self.assertEqual(receipt["records"], [])

        malformed = FakeOpener(FakeResponse(b'{"hitCount":"not-a-number","resultList":{"result":[]}}'))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=malformed):
            receipt = TOOL.search(QUERY, 3)
        self.assertEqual(receipt["acquisition_status"], "INVALID_PROVIDER_RESPONSE")
        self.assertIsNone(receipt["hit_count"])
        self.assertEqual(receipt["records"], [])
        self.assertIsNotNone(receipt["response_sha256"])

    def test_redirect_oversize_non_json_and_network_failures_are_bounded(self) -> None:
        redirect = FakeOpener(error=HTTPError(TOOL.API_BASE, 302, "redirect", {}, None))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=redirect):
            self.assertEqual(TOOL.search(QUERY, 2)["acquisition_status"], "REDIRECT_BLOCKED")

        oversized = FakeOpener(FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=oversized):
            self.assertEqual(TOOL.search(QUERY, 2)["acquisition_status"], "RESPONSE_TOO_LARGE")

        non_json = FakeOpener(FakeResponse(b"<html/>", content_type="text/html"))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=non_json):
            self.assertEqual(TOOL.search(QUERY, 2)["acquisition_status"], "NON_JSON_RESPONSE")

        offline = FakeOpener(error=OSError("offline"))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=offline):
            self.assertEqual(TOOL.search(QUERY, 2)["acquisition_status"], "NETWORK_ERROR")

        slow = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=slow), patch.object(
            TOOL.time, "monotonic", side_effect=[0.0, 8.0],
        ):
            self.assertEqual(TOOL.search(QUERY, 2)["acquisition_status"], "RESPONSE_TIMEOUT")


if __name__ == "__main__":
    unittest.main()
