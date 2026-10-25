from __future__ import annotations

import importlib.util
import io
import json
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_europe_pmc_fulltext_locator.py"
SPEC = importlib.util.spec_from_file_location("toolbox_europe_pmc_fulltext_locator", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


DOI = "10.1371/journal.pone.0005403"
PMID = "19404397"
PMCID = "PMC2671458"
SAMPLE_RESPONSE = {
    "hitCount": "1",
    "resultList": {"result": [{
        "source": "PMC",
        "id": "2671458",
        "pmid": "19404397",
        "pmcid": "PMC2671458",
        "doi": DOI,
        "title": "This title must not be returned.",
        "abstractText": "This abstract must not be returned.",
        "isOpenAccess": "Y",
        "fullTextUrlList": {"fullTextUrl": [{
            "availability": "Open access",
            "availabilityCode": "OA",
            "documentStyle": "doi",
            "site": "PLOS",
            "license": "CC BY",
            "url": "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0005403",
        }]},
    }]},
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
    return json.dumps({"dois": dois or [DOI]}).encode("utf-8")


def provider_body(document: object = SAMPLE_RESPONSE) -> bytes:
    return json.dumps(document).encode("utf-8")


class EuropePmcFullTextLocatorTests(unittest.TestCase):
    def test_request_is_exact_doi_core_query_to_fixed_host_and_returns_only_location_fields(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            receipt = TOOL.locate([DOI])

        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        self.assertEqual(len(opener.calls), 1)
        request, timeout = opener.calls[0]
        parsed = urlsplit(request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, TOOL.API_HOST)
        self.assertEqual(parsed.path, "/europepmc/webservices/rest/search")
        self.assertEqual(parse_qs(parsed.query), {
            "query": ["DOI:" + DOI], "format": ["json"], "resultType": ["core"], "pageSize": ["5"],
        })
        self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(receipt["status"], "OK")
        self.assertEqual(receipt["successful_acquisition_count"], 1)
        self.assertEqual(receipt["valid_provider_response_count"], 1)
        self.assertEqual(receipt["records"][0]["match_status"], "EXACT_RECORD_WITH_LOCATIONS")
        record = receipt["records"][0]["records"][0]
        self.assertEqual(record["doi"], DOI)
        self.assertEqual(record["full_text_locations"][0]["url"], SAMPLE_RESPONSE["resultList"]["result"][0]["fullTextUrlList"]["fullTextUrl"][0]["url"])
        self.assertEqual(record["full_text_locations"][0]["license"], "CC BY")
        serialized = json.dumps(receipt)
        self.assertNotIn("abstract", serialized.casefold())
        self.assertNotIn("title", serialized.casefold())
        self.assertNotIn("This abstract", serialized)
        self.assertNotIn("This title", serialized)
        self.assertEqual(len(receipt["records"][0]["response_sha256"]), 64)

    def test_typed_pmid_and_pmcid_queries_match_their_exact_provider_fields(self) -> None:
        for identifier, expected_query, expected_type in [
            ({"type": "PMID", "value": PMID}, "EXT_ID:" + PMID, "PMID"),
            ({"type": "PMCID", "value": PMCID}, "PMCID:" + PMCID, "PMCID"),
        ]:
            with self.subTest(identifier=identifier):
                opener = FakeOpener()
                with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                    receipt = TOOL.locate([identifier])
                parsed = urlsplit(opener.calls[0][0].full_url)
                self.assertEqual(parse_qs(parsed.query)["query"], [expected_query])
                row = receipt["records"][0]
                self.assertEqual(row["requested_identifier"], identifier)
                self.assertEqual(row["match_status"], "EXACT_RECORD_WITH_LOCATIONS")
                self.assertEqual(row["records"][0][expected_type.lower()], identifier["value"])
                self.assertEqual(row["full_text_location_count"], 1)

    def test_pmid_match_can_return_a_record_without_a_doi(self) -> None:
        record = {
            "source": "MED",
            "id": PMID,
            "pmid": PMID,
            "pmcid": PMCID,
            "fullTextUrlList": SAMPLE_RESPONSE["resultList"]["result"][0]["fullTextUrlList"],
        }
        opener = FakeOpener(FakeResponse(provider_body({"hitCount": "1", "resultList": {"result": [record]}})))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            row = TOOL.locate([{"type": "PMID", "value": PMID}])["records"][0]
        self.assertEqual(row["match_status"], "EXACT_RECORD_WITH_LOCATIONS")
        self.assertIsNone(row["records"][0]["doi"])
        self.assertIsNone(row["requested_doi"])

    def test_returned_article_url_is_never_requested(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            TOOL.locate([DOI])
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(urlsplit(opener.calls[0][0].full_url).hostname, TOOL.API_HOST)

    def test_multiple_exact_records_are_reported_without_selecting_one(self) -> None:
        document = {
            "hitCount": "2",
            "resultList": {"result": [
                SAMPLE_RESPONSE["resultList"]["result"][0],
                {"source": "MED", "id": "duplicate", "doi": DOI},
            ]},
        }
        opener = FakeOpener(FakeResponse(provider_body(document)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            row = TOOL.locate([DOI])["records"][0]
        self.assertEqual(row["match_status"], "MULTIPLE_EXACT_RECORDS")
        self.assertEqual(row["record_count"], 2)

    def test_no_exact_match_is_distinguished_from_no_provider_hits(self) -> None:
        document = {"hitCount": "1", "resultList": {"result": [{"source": "MED", "id": "1", "doi": "10.9999/other"}]}}
        opener = FakeOpener(FakeResponse(provider_body(document)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            row = TOOL.locate([DOI])["records"][0]
        self.assertEqual(row["match_status"], "NO_EXACT_MATCH")
        self.assertEqual(row["provider_hit_count"], 1)

        empty = {"hitCount": "0", "resultList": {"result": []}}
        opener = FakeOpener(FakeResponse(provider_body(empty)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            row = TOOL.locate([DOI])["records"][0]
        self.assertEqual(row["match_status"], "NO_EXACT_MATCH")
        self.assertEqual(row["provider_hit_count"], 0)

    def test_unsafe_locations_are_omitted_and_counted(self) -> None:
        record = dict(SAMPLE_RESPONSE["resultList"]["result"][0])
        record["fullTextUrlList"] = {"fullTextUrl": [
            {"url": "https://valid.example/article"},
            {"url": "http://insecure.example/article"},
            {"url": "https://user:secret@private.example/article"},
            {"url": "https://example.org/article#fragment"},
            {"url": "not a URL"},
        ]}
        document = {"hitCount": "1", "resultList": {"result": [record]}}
        opener = FakeOpener(FakeResponse(provider_body(document)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            result = TOOL.locate([DOI])
        output_record = result["records"][0]["records"][0]
        self.assertEqual(len(output_record["full_text_locations"]), 1)
        self.assertEqual(output_record["omitted_unsafe_location_count"], 4)

    def test_bad_provider_document_is_not_reported_as_top_level_success(self) -> None:
        opener = FakeOpener(FakeResponse(b'{"hitCount":"NaN","resultList":{"result":[]}}'))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.locate([DOI])
        self.assertEqual(receipt["status"], "NOT_AVAILABLE")
        self.assertEqual(receipt["successful_acquisition_count"], 1)
        self.assertEqual(receipt["valid_provider_response_count"], 0)
        self.assertEqual(receipt["records"][0]["acquisition_status"], "INVALID_PROVIDER_RESPONSE")

        duplicate_keys = FakeOpener(FakeResponse(b'{"hitCount":"1","hitCount":"2","resultList":{"result":[]}}'))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=duplicate_keys):
            receipt = TOOL.locate([DOI])
        self.assertEqual(receipt["records"][0]["acquisition_status"], "INVALID_PROVIDER_RESPONSE")
        self.assertEqual(receipt["status"], "NOT_AVAILABLE")

    def test_each_doi_causes_only_one_fixed_api_request(self) -> None:
        first = FakeOpener()
        second = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", side_effect=[first, second]):
            receipt = TOOL.locate([DOI, "10.1111/example.2"])
        self.assertEqual(receipt["requested_count"], 2)
        self.assertEqual(first.calls[0][0].full_url.split("?", 1)[0], TOOL.API_BASE)
        self.assertEqual(second.calls[0][0].full_url.split("?", 1)[0], TOOL.API_BASE)

    def test_request_rejects_duplicate_json_keys_duplicate_identifiers_and_invalid_identifiers(self) -> None:
        for raw in [
            b'{"dois":["10.1000/x"],"dois":["10.2000/y"]}',
            json.dumps({"dois": [DOI, DOI.upper()]}).encode(),
            json.dumps({"dois": ["https://doi.org/" + DOI]}).encode(),
            json.dumps({"dois": ["10.123/example"]}).encode(),
            json.dumps({"dois": ["10.1234/a\n"]}).encode(),
            json.dumps({"dois": [DOI] * (TOOL.MAX_DOIS + 1)}).encode(),
            json.dumps({"identifiers": [{"type": "PMID", "value": PMID}, {"type": "PMID", "value": PMID}]}).encode(),
            json.dumps({"identifiers": [{"type": "PMID", "value": "019404397"}]}).encode(),
            json.dumps({"identifiers": [{"type": "PMCID", "value": "PMC"}]}).encode(),
            json.dumps({"identifiers": [{"type": "pmid", "value": PMID}]}).encode(),
            json.dumps({"identifiers": [{"type": "PMCID", "value": PMCID, "extra": "rejected"}]}).encode(),
            json.dumps({"dois": [DOI], "identifiers": [{"type": "PMID", "value": PMID}]}).encode(),
            b" " * (TOOL.MAX_REQUEST_BYTES + 1),
        ]:
            with self.subTest(request=raw[:60]), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)

        self.assertEqual(TOOL.parse_request(request_bytes()), [{"type": "DOI", "value": DOI}])
        typed = TOOL.parse_request(json.dumps({"identifiers": [
            {"type": "PMID", "value": PMID}, {"type": "PMCID", "value": "pmc2671458"},
        ]}).encode())
        self.assertEqual(typed, [
            {"type": "PMID", "value": PMID}, {"type": "PMCID", "value": PMCID},
        ])

    def test_receipt_matches_machine_schema_and_body_timeout_is_bounded(self) -> None:
        schema = json.loads((IGNITION_ROOT / "schemas/operations/toolbox-europe-pmc-fulltext-locator-r0.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate({"dois": [DOI]})
        Draft202012Validator(schema).validate({"identifiers": [{"type": "PMID", "value": PMID}]})
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.locate([DOI])
        Draft202012Validator(schema).validate(receipt)

        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener), patch.object(
            TOOL.time, "monotonic", side_effect=[0.0, 8.0],
        ):
            row = TOOL.locate([DOI])["records"][0]
        self.assertEqual(row["acquisition_status"], "RESPONSE_TIMEOUT")

    def test_public_network_requires_per_invocation_flag(self) -> None:
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

    def test_http_errors_redirect_rate_limit_non_json_and_oversize_are_explicit(self) -> None:
        cases = [
            (FakeOpener(error=HTTPError(TOOL.API_BASE, 302, "redirect", {}, None)), "REDIRECT_BLOCKED"),
            (FakeOpener(error=HTTPError(TOOL.API_BASE, 429, "rate limited", {}, None)), "RATE_LIMITED"),
            (FakeOpener(FakeResponse(b"<html/>", content_type="text/html")), "NON_JSON_RESPONSE"),
            (FakeOpener(FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1))), "RESPONSE_TOO_LARGE"),
            (FakeOpener(error=OSError("offline")), "NETWORK_ERROR"),
        ]
        for opener, expected in cases:
            with self.subTest(expected=expected), patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                row = TOOL.locate([DOI])["records"][0]
                self.assertEqual(row["acquisition_status"], expected)


if __name__ == "__main__":
    unittest.main()
