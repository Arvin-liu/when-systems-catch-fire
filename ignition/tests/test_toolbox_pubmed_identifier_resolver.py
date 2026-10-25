from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_pubmed_identifier_resolver.py"
SPEC = importlib.util.spec_from_file_location("toolbox_pubmed_identifier_resolver", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


DOI = "10.1016/j.ajhg.2010.04.006"
SAMPLE_RESPONSE = {
    "status": "ok",
    "records": [{
        "doi": DOI,
        "pmid": 20466091,
        "pmcid": "PMC2885863",
        "requested-id": DOI,
        "idtype": "doi",
        "live": True,
    }],
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


def request_bytes(dois: list[str] | None = None) -> bytes:
    return json.dumps({"dois": [DOI] if dois is None else dois}).encode("utf-8")


class PubMedIdentifierResolverTests(unittest.TestCase):
    def test_lookup_uses_fixed_host_and_returns_hashed_identifier_mapping(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            result = TOOL.resolve(TOOL.parse_request(request_bytes()))

        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        request, timeout = opener.calls[0]
        parsed = urlsplit(request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "pmc.ncbi.nlm.nih.gov")
        self.assertEqual(parsed.path, "/tools/idconv/api/v1/articles/")
        self.assertEqual(parse_qs(parsed.query), {"ids": [DOI], "format": ["json"]})
        self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        result_row = result["rows"][0]
        self.assertEqual(result["status"], "IDENTIFIERS_RESOLVED")
        self.assertEqual(result_row["identifier_status"], "IDENTIFIER_RESOLVED")
        self.assertEqual(result_row["matched_doi"], DOI)
        self.assertEqual(result_row["pmid"], "20466091")
        self.assertEqual(result_row["pmcid"], "PMC2885863")
        self.assertEqual(len(result_row["response_sha256"]), 64)
        self.assertIn("no article-content", result["claim_ceiling"])

    def test_live_cli_requires_explicit_network_flag_before_reading_or_requesting(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(opener.calls, [])
        self.assertIn("--allow-public-network", stderr.getvalue())

    def test_rejects_url_like_or_duplicate_dois_and_duplicate_json_keys(self) -> None:
        for bad in (
            "https://doi.org/" + DOI,
            "doi:" + DOI,
            " " + DOI,
        ):
            with self.subTest(bad=bad), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(request_bytes([bad]))
        with self.assertRaisesRegex(TOOL.ToolInputError, "unique"):
            TOOL.parse_request(request_bytes([DOI, DOI.upper()]))
        with self.assertRaisesRegex(TOOL.ToolInputError, "duplicate JSON"):
            TOOL.parse_request(b'{"dois":[],"dois":[]}')

    def test_rejects_empty_and_over_limit_batches_before_network(self) -> None:
        with self.assertRaisesRegex(TOOL.ToolInputError, "between 1 and"):
            TOOL.parse_request(request_bytes([]))
        with self.assertRaisesRegex(TOOL.ToolInputError, "between 1 and"):
            TOOL.parse_request(request_bytes([f"10.1234/item-{i}" for i in range(TOOL.MAX_RECORDS + 1)]))

    def test_preserves_no_match_without_inventing_identifiers(self) -> None:
        opener = FakeOpener(FakeResponse(b'{"status":"ok","records":[]}'))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            row = TOOL.resolve([DOI])["rows"][0]
        self.assertEqual(row["acquisition_status"], "OK")
        self.assertEqual(row["identifier_status"], "NO_MATCH")
        self.assertIsNone(row["pmid"])
        self.assertIsNone(row["pmcid"])

    def test_rejects_mismatched_upstream_record_and_invalid_identifiers(self) -> None:
        mismatched = {"status": "ok", "records": [{"doi": "10.1234/other", "pmid": "123"}]}
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(json.dumps(mismatched).encode()))):
            row = TOOL.resolve([DOI])["rows"][0]
        self.assertEqual(row["identifier_status"], "UPSTREAM_RECORD_MISMATCH")
        self.assertIsNone(row["pmid"])

        invalid_ids = {"status": "ok", "records": [{"doi": DOI, "pmid": "123x", "pmcid": "PMCbad"}]}
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(json.dumps(invalid_ids).encode()))):
            row = TOOL.resolve([DOI])["rows"][0]
        self.assertEqual(row["identifier_status"], "MATCHED_WITHOUT_PUBMED_OR_PMC_ID")
        self.assertIsNone(row["pmid"])
        self.assertIsNone(row["pmcid"])

    def test_accepts_ncbi_integer_pmid_and_keeps_string_compatibility(self) -> None:
        for pmid in (20466091, "20466091"):
            with self.subTest(pmid=pmid):
                response = {"status": "ok", "records": [{"doi": DOI, "pmid": pmid}]}
                with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(json.dumps(response).encode()))):
                    row = TOOL.resolve([DOI])["rows"][0]
                self.assertEqual(row["identifier_status"], "IDENTIFIER_RESOLVED")
                self.assertEqual(row["pmid"], "20466091")

    def test_rejects_invalid_numeric_pmid_values(self) -> None:
        for pmid in (0, -1, 1_000_000_000_000, True):
            with self.subTest(pmid=pmid):
                response = {"status": "ok", "records": [{"doi": DOI, "pmid": pmid}]}
                with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(json.dumps(response).encode()))):
                    row = TOOL.resolve([DOI])["rows"][0]
                self.assertEqual(row["identifier_status"], "MATCHED_WITHOUT_PUBMED_OR_PMC_ID")
                self.assertIsNone(row["pmid"])

    def test_redirect_oversize_timeout_and_non_json_are_explicit(self) -> None:
        redirect = FakeOpener(error=HTTPError(TOOL.API_BASE, 302, "redirect", {}, None))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=redirect):
            self.assertEqual(TOOL._fetch_one(DOI)["acquisition_status"], "REDIRECT_BLOCKED")

        oversized = FakeOpener(FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=oversized):
            self.assertEqual(TOOL._fetch_one(DOI)["acquisition_status"], "RESPONSE_TOO_LARGE")

        non_json = FakeOpener(FakeResponse(b"<html/>", content_type="text/html"))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=non_json):
            self.assertEqual(TOOL._fetch_one(DOI)["acquisition_status"], "NON_JSON_RESPONSE")

        slow = FakeOpener(FakeResponse(json.dumps(SAMPLE_RESPONSE).encode()))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=slow), patch.object(TOOL.time, "monotonic", side_effect=[0.0, 8.0]):
            self.assertEqual(TOOL._fetch_one(DOI)["acquisition_status"], "RESPONSE_TIMEOUT")
        self.assertEqual(slow.response.read_calls, 0)

    def test_invalid_json_and_network_errors_are_recorded(self) -> None:
        malformed = FakeOpener(FakeResponse(b"not json"))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=malformed):
            row = TOOL.resolve([DOI])["rows"][0]
        self.assertEqual(row["acquisition_status"], "INVALID_JSON_RESPONSE")
        self.assertEqual(row["identifier_status"], "NOT_AVAILABLE")
        self.assertIsNotNone(row["response_sha256"])

        failed = FakeOpener(error=TimeoutError("timeout"))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=failed):
            result = TOOL.resolve([DOI])
        self.assertEqual(result["status"], "COMPLETED_WITH_EXPLICIT_FAILURES")
        self.assertEqual(result["rows"][0]["acquisition_status"], "NETWORK_ERROR")

    def test_rejects_multiple_upstream_records_for_one_doi(self) -> None:
        duplicated = {"status": "ok", "records": [SAMPLE_RESPONSE["records"][0], SAMPLE_RESPONSE["records"][0]]}
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(json.dumps(duplicated).encode()))):
            row = TOOL.resolve([DOI])["rows"][0]
        self.assertEqual(row["identifier_status"], "UPSTREAM_RECORD_MISMATCH")


if __name__ == "__main__":
    unittest.main()
