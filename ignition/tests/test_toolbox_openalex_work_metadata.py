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
import toolbox_openalex_work_metadata as TOOL  # noqa: E402

MAX_DOIS = TOOL.MAX_DOIS
MAX_RESPONSE_BYTES = TOOL.MAX_RESPONSE_BYTES
REQUEST_TIMEOUT_SECONDS = TOOL.REQUEST_TIMEOUT_SECONDS
_NoRedirectHandler = TOOL._NoRedirectHandler
lookup = TOOL.lookup
main = TOOL.main
parse_request = TOOL.parse_request


DOI = "10.3982/ecta15732"
WORK = {
    "id": "https://openalex.org/W3083006799",
    "doi": "https://doi.org/10.3982/ecta15732",
    "display_name": "Policy Learning With Observational Data",
    "publication_year": 2021,
    "type": "article",
    "is_retracted": False,
    "open_access": {
        "is_oa": True,
        "oa_status": "green",
        "oa_url": "https://repository.example.org/paper.pdf",
        "any_repository_has_fulltext": True,
    },
    "best_oa_location": {
        "id": "https://openalex.org/locations/L123",
        "is_oa": True,
        "landing_page_url": "https://repository.example.org/paper",
        "pdf_url": "https://repository.example.org/paper.pdf",
        "source": {
            "id": "https://openalex.org/S123",
            "display_name": "Example Repository",
            "type": "repository",
        },
        "license": "cc-by",
        "version": "acceptedVersion",
    },
    "locations": [
        {
            "id": "https://openalex.org/locations/L123",
            "is_oa": True,
            "landing_page_url": "https://repository.example.org/paper",
            "pdf_url": "https://repository.example.org/paper.pdf",
            "source": {
                "id": "https://openalex.org/S123",
                "display_name": "Example Repository",
                "type": "repository",
            },
            "license": "cc-by",
            "version": "acceptedVersion",
        }
    ],
}


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, content_type: str = "application/json") -> None:
        self.body = body
        self.offset = 0
        self.status = status
        self.headers = {
            "Content-Type": content_type,
            "X-RateLimit-Limit": "0.1",
            "X-RateLimit-Remaining": "0.0999",
            "X-RateLimit-Credits-Used": "0.0001",
            "X-RateLimit-Reset": "10",
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
        payload = {"meta": {"count": 1, "cost": 0.0001, "db_response_time_ms": 3}, "results": [WORK]}
        self.response = response or FakeResponse(json.dumps(payload).encode("utf-8"))
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


def request_bytes(dois: list[str] | None = None) -> bytes:
    return json.dumps({"dois": dois or [DOI]}).encode("utf-8")


class OpenAlexWorkMetadataTests(unittest.TestCase):
    def test_live_lookup_uses_one_fixed_host_request_and_returns_only_selected_fields(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            result = lookup(parse_request(request_bytes()))

        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], _NoRedirectHandler)
        request, timeout = opener.calls[0]
        parsed = urlsplit(request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "api.openalex.org")
        self.assertEqual(parsed.path, "/works")
        self.assertEqual(timeout, REQUEST_TIMEOUT_SECONDS)
        query = parse_qs(parsed.query)
        self.assertEqual(query["filter"], ["doi:" + DOI])
        self.assertEqual(query["select"], [TOOL.SELECT_FIELDS])
        self.assertEqual(result["request_count"], 1)
        self.assertEqual(result["status"], "EXACT_DOI_WORKS_RESOLVED")
        self.assertEqual(result["rows"][0]["status"], "EXACT_PRIMARY_DOI_MATCH")
        self.assertEqual(result["rows"][0]["openalex_id"], WORK["id"])
        self.assertFalse(result["rows"][0]["is_retracted"])
        row = result["rows"][0]
        self.assertEqual(row["location_metadata_status"], "PROVIDER_REPORTED")
        self.assertEqual(row["openalex_locations_count"], 1)
        self.assertEqual(row["openalex_locations_returned_count"], 1)
        self.assertFalse(row["openalex_locations_truncated"])
        self.assertEqual(row["openalex_locations"][0]["pdf_url"], "https://repository.example.org/paper.pdf")
        self.assertEqual(row["openalex_best_oa_location"]["source"]["display_name"], "Example Repository")
        self.assertEqual(row["openalex_open_access"]["oa_status"], "green")
        self.assertEqual(row["omitted_unsafe_location_url_count"], 0)
        self.assertEqual(len(result["response_sha256"]), 64)
        self.assertEqual(result["api_usage"]["meta"]["cost"], 0.0001)
        self.assertNotIn("abstract", json.dumps(result))

    def test_location_projection_drops_non_https_and_credential_urls_without_fetching_them(self) -> None:
        work = json.loads(json.dumps(WORK))
        work["locations"][0]["landing_page_url"] = "http://repository.example.org/paper"
        work["locations"][0]["pdf_url"] = "https://user:secret@repository.example.org/paper.pdf"
        work["best_oa_location"]["pdf_url"] = "http://repository.example.org/paper.pdf"
        work["open_access"]["oa_url"] = "http://repository.example.org/paper.pdf"
        body = json.dumps({"meta": {"count": 1}, "results": [work]}).encode("utf-8")
        opener = FakeOpener(FakeResponse(body))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            result = lookup([DOI])
        row = result["rows"][0]
        self.assertIsNone(row["openalex_locations"][0]["landing_page_url"])
        self.assertIsNone(row["openalex_locations"][0]["pdf_url"])
        self.assertIsNone(row["openalex_best_oa_location"]["pdf_url"])
        self.assertIsNone(row["openalex_open_access"]["oa_url"])
        self.assertEqual(row["omitted_unsafe_location_url_count"], 4)
        self.assertEqual(len(opener.calls), 1)

    def test_location_projection_caps_returned_records_and_preserves_provider_count(self) -> None:
        work = json.loads(json.dumps(WORK))
        work["locations"] = [dict(WORK["locations"][0], id="https://openalex.org/locations/L{}".format(i)) for i in range(30)]
        body = json.dumps({"meta": {"count": 1}, "results": [work]}).encode("utf-8")
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(body))):
            result = lookup([DOI])
        row = result["rows"][0]
        self.assertEqual(row["openalex_locations_count"], 30)
        self.assertEqual(row["openalex_locations_returned_count"], TOOL.MAX_LOCATIONS_PER_WORK)
        self.assertTrue(row["openalex_locations_truncated"])

    def test_malformed_location_projection_fails_closed_and_missing_fields_remain_explicit(self) -> None:
        malformed = json.loads(json.dumps(WORK))
        malformed["locations"] = {"unexpected": "not-an-array"}
        body = json.dumps({"meta": {"count": 1}, "results": [malformed]}).encode("utf-8")
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(body))):
            invalid = lookup([DOI])
        self.assertEqual(invalid["status"], "COMPLETED_WITH_EXPLICIT_FAILURES")
        self.assertEqual(invalid["rows"][0]["status"], "INVALID_OPENALEX_WORK_RECORD")

        work_without_locations = {key: value for key, value in WORK.items() if key not in {"locations", "best_oa_location", "open_access"}}
        body = json.dumps({"meta": {"count": 1}, "results": [work_without_locations]}).encode("utf-8")
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(body))):
            missing = lookup([DOI])
        row = missing["rows"][0]
        self.assertEqual(row["location_metadata_status"], "NOT_RETURNED")
        self.assertIsNone(row["openalex_locations"])
        self.assertIsNone(row["openalex_open_access"])

    def test_no_network_occurs_without_per_call_flag(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(sys, "stdin", FakeStdin(request_bytes())):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = main(["--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(opener.calls, [])
        self.assertIn("--allow-public-network", stderr.getvalue())

    def test_cli_requires_explicit_network_flag_and_returns_json(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(sys, "stdin", FakeStdin(request_bytes())):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = main(["--stdin", "--allow-public-network"])
        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(json.loads(stdout.getvalue())["tool_id"], "research.lookup_openalex_work_metadata")

    def test_rejects_url_duplicate_keys_duplicate_dois_and_oversized_batches(self) -> None:
        bad_inputs = [
            b'{"dois":["https://doi.org/10.3982/ecta15732"]}',
            b'{"dois":[],"dois":[]}',
            request_bytes([DOI, DOI.upper()]),
            request_bytes(["10.1234/test-{}".format(index) for index in range(MAX_DOIS + 1)]),
        ]
        for raw in bad_inputs:
            with self.subTest(raw=raw[:48]), self.assertRaises(TOOL.ToolInputError):
                parse_request(raw)

    def test_ambiguous_exact_matches_fail_closed_without_selecting_a_work(self) -> None:
        second = dict(WORK, id="https://openalex.org/W9999999999")
        body = json.dumps({"meta": {"count": 2, "cost": 0.0001}, "results": [WORK, second]}).encode("utf-8")
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(body))):
            result = lookup([DOI])
        row = result["rows"][0]
        self.assertEqual(result["status"], "COMPLETED_WITH_INCONCLUSIVE_ROWS")
        self.assertEqual(row["status"], "AMBIGUOUS_MULTIPLE_EXACT_MATCHES")
        self.assertEqual(row["candidate_work_ids"], [WORK["id"], second["id"]])
        self.assertNotIn("openalex_id", row)

    def test_location_filter_hit_without_exact_primary_doi_is_inconclusive(self) -> None:
        work = dict(WORK, doi="https://doi.org/10.1000/another-primary-doi")
        body = json.dumps({"meta": {"count": 1, "cost": 0.0001}, "results": [work]}).encode("utf-8")
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(body))):
            result = lookup([DOI])
        self.assertEqual(result["rows"][0]["status"], "INCONCLUSIVE_NO_PRIMARY_DOI_MATCH")
        self.assertNotIn("openalex_id", result["rows"][0])

    def test_truncated_result_set_does_not_claim_a_unique_match(self) -> None:
        body = json.dumps({"meta": {"count": MAX_RESPONSE_BYTES, "cost": 0.0001}, "results": [WORK]}).encode("utf-8")
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(body))):
            result = lookup([DOI])
        self.assertEqual(result["rows"][0]["status"], "RESULT_LIMIT_REACHED")
        self.assertNotIn("openalex_id", result["rows"][0])

    def test_redirect_is_not_followed_and_is_reported(self) -> None:
        error = HTTPError("https://api.openalex.org/works", 302, "redirect", {}, None)
        opener = FakeOpener(error=error)
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            result = lookup([DOI])
        self.assertIsInstance(build_opener.call_args.args[0], _NoRedirectHandler)
        self.assertEqual(result["acquisition_status"], "REDIRECT_BLOCKED")
        self.assertEqual(result["http_status"], 302)
        self.assertEqual(result["rows"][0]["status"], "REDIRECT_BLOCKED")

    def test_response_size_and_non_json_fail_explicitly(self) -> None:
        oversized = b"{" + b" " * (MAX_RESPONSE_BYTES + 1)
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(oversized))):
            too_large = lookup([DOI])
        self.assertEqual(too_large["acquisition_status"], "RESPONSE_TOO_LARGE")

        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(b"<html/>", content_type="text/html"))):
            non_json = lookup([DOI])
        self.assertEqual(non_json["acquisition_status"], "NON_JSON_RESPONSE")


if __name__ == "__main__":
    unittest.main()
