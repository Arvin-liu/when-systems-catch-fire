from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from unittest.mock import patch
from jsonschema import Draft202012Validator, FormatChecker


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_datacite_doi_metadata as TOOL  # noqa: E402


DOI = "10.25491/3v3x-tj13"
ATTRIBUTES = {
    "doi": DOI,
    "state": "findable",
    "schemaVersion": "http://datacite.org/schema/kernel-4",
    "publisher": "GTEx",
    "publicationYear": 2017,
    "types": {"resourceTypeGeneral": "Dataset", "resourceType": "CRAI index file"},
    "titles": [{"title": "GTEX-ZTSS-0003-SM-6WBSU", "lang": "en"}],
    "creators": [{"name": "GTEx Consortium", "nameType": "Organizational"}],
    "rightsList": [],
    "relatedIdentifiers": [
        {
            "relatedIdentifier": "10.1234/example",
            "relatedIdentifierType": "DOI",
            "relationType": "IsPartOf",
            "relatedMetadataScheme": "DataCite",
        }
    ],
    "identifiers": [{"identifier": "GTEX-ZTSS-0003-SM-6WBSU", "identifierType": "Other"}],
    "dates": [{"date": "2017", "dateType": "Issued"}],
    "url": "https://example.org/data",
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
    def __init__(self, response: FakeResponse | None = None, error: Exception | None = None) -> None:
        payload = {"data": {"type": "dois", "id": DOI, "attributes": ATTRIBUTES}}
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


def request_bytes(doi: str = DOI) -> bytes:
    return json.dumps({"doi": doi}).encode("utf-8")


class DataCiteDoiMetadataTests(unittest.TestCase):
    def test_exact_metadata_lookup_is_one_fixed_host_get_and_returns_selected_fields(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            result = TOOL.lookup(DOI)

        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        request, timeout = opener.calls[0]
        parsed = urlsplit(request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "api.datacite.org")
        self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(unquote(parsed.path.rsplit("/", 1)[-1]), DOI)
        self.assertEqual(result["request_count"], 1)
        self.assertEqual(result["status"], "EXACT_DOI_MATCH")
        self.assertEqual(result["record"]["resource_type_general"], "Dataset")
        self.assertEqual(result["record"]["resource_type"], "CRAI index file")
        self.assertEqual(result["record"]["rights"], [])
        self.assertEqual(result["record"]["related_identifiers"][0]["relation_type"], "IsPartOf")
        self.assertEqual(result["record"]["state"], "findable")
        self.assertEqual(len(result["response_sha256"]), 64)
        self.assertNotIn("url", json.dumps(result))

    def test_provider_record_must_exactly_match_requested_doi(self) -> None:
        altered = dict(ATTRIBUTES, doi="10.1234/other")
        body = json.dumps({"data": {"type": "dois", "id": DOI, "attributes": altered}}).encode("utf-8")
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(body))):
            result = TOOL.lookup(DOI)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["acquisition_status"], "INVALID_DATACITE_RESPONSE")
        self.assertIsNone(result["record"])

    def test_missing_optional_fields_are_not_reported_as_empty_provider_values(self) -> None:
        minimal = {"doi": DOI, "types": {"resourceTypeGeneral": "Dataset"}}
        body = json.dumps({"data": {"type": "dois", "id": DOI, "attributes": minimal}}).encode("utf-8")
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(body))):
            result = TOOL.lookup(DOI)
        record = result["record"]
        self.assertEqual(record["field_statuses"]["rightsList"], "NOT_REPORTED")
        self.assertEqual(record["rights"], [])
        self.assertIsNone(record["field_counts"]["rightsList"]["reported_count"])

    def test_input_and_output_schemas_accept_the_declared_request_and_result(self) -> None:
        schema_dir = IGNITION_ROOT / "schemas/operations"
        input_schema = json.loads((schema_dir / "toolbox-datacite-doi-metadata-input-r0.schema.json").read_text())
        output_schema = json.loads((schema_dir / "toolbox-datacite-doi-metadata-output-r0.schema.json").read_text())
        Draft202012Validator(input_schema, format_checker=FormatChecker()).validate({"doi": DOI})
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener()):
            result = TOOL.lookup(DOI)
        Draft202012Validator(output_schema, format_checker=FormatChecker()).validate(result)

    def test_malformed_optional_array_is_explicit_and_bounded_lists_report_omissions(self) -> None:
        altered = dict(ATTRIBUTES, rightsList="not-an-array", relatedIdentifiers=[
            {"relatedIdentifier": "10.1234/{}".format(i), "relatedIdentifierType": "DOI", "relationType": "References"}
            for i in range(30)
        ])
        body = json.dumps({"data": {"type": "dois", "id": DOI, "attributes": altered}}).encode("utf-8")
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(body))):
            result = TOOL.lookup(DOI)
        record = result["record"]
        self.assertEqual(record["field_statuses"]["rightsList"], "MALFORMED")
        self.assertEqual(record["field_counts"]["rightsList"]["invalid_count"], 1)
        self.assertEqual(len(record["related_identifiers"]), 25)
        self.assertEqual(record["field_counts"]["relatedIdentifiers"]["omitted_count"], 5)

    def test_cli_does_not_call_network_without_per_invocation_permission(self) -> None:
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

    def test_cli_explicitly_permitted_request_prints_json(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin", "--allow-public-network"])
        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(json.loads(stdout.getvalue())["tool_id"], "research.lookup_datacite_doi_metadata")

    def test_rejects_urls_duplicate_keys_whitespace_and_oversized_input(self) -> None:
        bad_inputs = [
            b'{"doi":"https://doi.org/10.25491/3v3x-tj13"}',
            b'{"doi":"10.25491/3v3x-tj13","doi":"10.25491/3v3x-tj13"}',
            request_bytes(" 10.25491/3v3x-tj13"),
            b" " * (TOOL.MAX_REQUEST_BYTES + 1),
        ]
        for raw in bad_inputs:
            with self.subTest(raw=raw[:48]), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)

    def test_404_is_only_a_no_findable_record_observation(self) -> None:
        error = HTTPError("https://api.datacite.org/dois/" + DOI, 404, "not found", {}, io.BytesIO(b"not found"))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(error=error)):
            result = TOOL.lookup(DOI)
        self.assertEqual(result["acquisition_status"], "NOT_FOUND")
        self.assertEqual(result["status"], "NO_FINDABLE_DATACITE_RECORD")
        self.assertIsNone(result["record"])

    def test_redirect_is_not_followed_and_is_reported(self) -> None:
        error = HTTPError("https://api.datacite.org/dois/" + DOI, 302, "redirect", {}, io.BytesIO(b""))
        opener = FakeOpener(error=error)
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            result = TOOL.lookup(DOI)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(result["acquisition_status"], "REDIRECT_BLOCKED")

    def test_non_json_and_oversized_responses_fail_explicitly(self) -> None:
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(b"<html/>", content_type="text/html"))):
            non_json = TOOL.lookup(DOI)
        self.assertEqual(non_json["acquisition_status"], "NON_JSON_RESPONSE")
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(b"{" + b" " * TOOL.MAX_RESPONSE_BYTES))):
            oversized = TOOL.lookup(DOI)
        self.assertEqual(oversized["acquisition_status"], "RESPONSE_TOO_LARGE")
        self.assertIsNone(oversized["response_sha256"])

    def test_duplicate_key_and_malformed_provider_json_fail_closed(self) -> None:
        duplicate_keys = b'{"data":{"type":"dois","id":"' + DOI.encode() + b'","attributes":{"doi":"' + DOI.encode() + b'","doi":"10.1234/wrong"}}}'
        malformed = b'{"data":'
        for body in (duplicate_keys, malformed):
            with self.subTest(body=body[:30]), patch.object(
                TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(body))
            ):
                result = TOOL.lookup(DOI)
            self.assertEqual(result["status"], "UNRESOLVED")
            self.assertEqual(result["acquisition_status"], "INVALID_DATACITE_RESPONSE")
            self.assertIsNone(result["record"])

    def test_rate_limit_network_and_response_timeout_remain_explicit(self) -> None:
        rate_limit = HTTPError("https://api.datacite.org/dois/" + DOI, 429, "rate limited", {}, io.BytesIO(b""))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(error=rate_limit)):
            limited = TOOL.lookup(DOI)
        self.assertEqual(limited["acquisition_status"], "RATE_LIMITED")

        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(error=URLError("offline"))):
            offline = TOOL.lookup(DOI)
        self.assertEqual(offline["acquisition_status"], "NETWORK_ERROR")

        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener), patch.object(
            TOOL.time, "monotonic", side_effect=[0.0, 8.0]
        ):
            timed_out = TOOL.lookup(DOI)
        self.assertEqual(timed_out["acquisition_status"], "RESPONSE_TIMEOUT")

    def test_body_read_error_is_not_reported_as_missing_data(self) -> None:
        class ReadFailure(FakeResponse):
            def read(self, size: int = -1) -> bytes:
                raise OSError("simulated response read failure")

        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(ReadFailure(b""))):
            result = TOOL.lookup(DOI)
        self.assertEqual(result["acquisition_status"], "RESPONSE_READ_ERROR")
        self.assertEqual(result["status"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
