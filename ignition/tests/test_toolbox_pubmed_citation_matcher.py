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
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_pubmed_citation_matcher.py"
SPEC = importlib.util.spec_from_file_location("toolbox_pubmed_citation_matcher", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)

INPUT = {
    "journal_title": "proc natl acad sci u s a",
    "year": "1991",
    "volume": "88",
    "first_page": "3248",
    "first_author": "mann bj",
}
MATCHED_RESPONSE = b"proc natl acad sci u s a|1991|88|3248|mann bj|IgnitionToolbox0|2014248\n"


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, content_type: str = "text/plain") -> None:
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


def request_bytes(value: object = INPUT) -> bytes:
    return json.dumps(value).encode("utf-8")


class PubMedCitationMatcherTests(unittest.TestCase):
    def test_checked_in_public_example_matches_input_schema(self) -> None:
        fixture = json.loads((IGNITION_ROOT / "tests/fixtures/toolbox-pubmed-citation-matcher/valid-input-r0.json").read_text(encoding="utf-8"))
        schema = json.loads((IGNITION_ROOT / "schemas/operations/pubmed-citation-matcher-input-r0.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(fixture)
        self.assertEqual(TOOL.parse_request(request_bytes(fixture)), fixture)

    def test_one_fixed_host_request_reports_provider_pmid_and_digest_only(self) -> None:
        opener = FakeOpener([FakeResponse(MATCHED_RESPONSE)])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            receipt = TOOL.match(TOOL.parse_request(request_bytes()))
        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        self.assertEqual(len(opener.calls), 1)
        request, timeout = opener.calls[0]
        self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        target = urlsplit(request.full_url)
        self.assertEqual((target.scheme, target.hostname, target.path), (
            "https", TOOL.API_HOST, "/entrez/eutils/ecitmatch.cgi",
        ))
        params = parse_qs(target.query)
        self.assertEqual(params, {
            "db": ["pubmed"],
            "bdata": ["proc natl acad sci u s a|1991|88|3248|mann bj|IgnitionToolbox0|"],
            "retmode": ["xml"],
            "rettype": ["xml"],
            "tool": [TOOL.TOOL_CONTACT],
        })
        self.assertEqual(receipt["match_status"], "PROVIDER_MATCH_REPORTED")
        self.assertEqual(receipt["returned_pmid"], "2014248")
        self.assertEqual(receipt["request_count"], 1)
        self.assertEqual(receipt["response_binding_status"], "REQUEST_KEY_AND_NORMALIZED_CITATION_ECHO")
        self.assertEqual(receipt["email_sent_to_provider"], False)
        self.assertNotIn("mann bj", json.dumps(receipt))
        self.assertNotIn("proc natl", json.dumps(receipt))
        self.assertNotIn("abstract", json.dumps(receipt).casefold())

    def test_no_match_is_a_limited_provider_observation(self) -> None:
        body = b"proc natl acad sci u s a|1991|88|3248|mann bj|IgnitionToolbox0|\n"
        opener = FakeOpener([FakeResponse(body)])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.match(INPUT)
        self.assertEqual(receipt["acquisition_status"], "OK")
        self.assertEqual(receipt["match_status"], "NO_MATCH_REPORTED")
        self.assertIsNone(receipt["returned_pmid"])
        self.assertEqual(receipt["request_count"], 1)

    def test_cli_requires_public_network_flag_before_any_request(self) -> None:
        opener = FakeOpener([FakeResponse(MATCHED_RESPONSE)])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    with self.assertRaises(SystemExit) as exc:
                        TOOL.main(["--stdin"])
        self.assertEqual(exc.exception.code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(opener.calls, [])
        self.assertIn("--allow-public-network is required", stderr.getvalue())

    def test_cli_opt_in_emits_one_json_receipt(self) -> None:
        opener = FakeOpener([FakeResponse(MATCHED_RESPONSE)])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin", "--allow-public-network"])
        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(json.loads(stdout.getvalue())["tool_id"], TOOL.TOOL_ID)

    def test_strict_input_rejects_duplicate_keys_controls_injection_and_oversize(self) -> None:
        invalid = [
            b'{"journal_title":"a","journal_title":"b","year":"1991","volume":"88","first_page":"1","first_author":"x"}',
            json.dumps({**INPUT, "year": 199}).encode(),
            json.dumps({**INPUT, "year": "199A"}).encode(),
            json.dumps({**INPUT, "first_author": "mann|bj"}).encode(),
            json.dumps({**INPUT, "first_author": "mann\nbj"}).encode(),
            json.dumps({**INPUT, "extra": "no"}).encode(),
            b" " * (TOOL.MAX_REQUEST_BYTES + 1),
            b"\xff",
        ]
        for raw in invalid:
            with self.subTest(raw=raw[:80]), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)

    def test_key_echo_and_citation_echo_are_required(self) -> None:
        wrong_key = MATCHED_RESPONSE.replace(b"IgnitionToolbox0", b"OtherCaller0")
        wrong_fields = MATCHED_RESPONSE.replace(b"3248", b"3249")
        for body, expected in ((wrong_key, "INVALID_RESPONSE_SHAPE"), (wrong_fields, "CITATION_ECHO_MISMATCH")):
            opener = FakeOpener([FakeResponse(body)])
            with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                receipt = TOOL.match(INPUT)
            self.assertEqual(receipt["acquisition_status"], expected)
            self.assertEqual(receipt["match_status"], "NOT_EVALUATED")
            self.assertIsNone(receipt["returned_pmid"])
            self.assertEqual(receipt["response_binding_status"], "NOT_ESTABLISHED")

    def test_ambiguous_malformed_and_bad_encoding_results_fail_closed(self) -> None:
        bodies = [
            MATCHED_RESPONSE + MATCHED_RESPONSE,
            MATCHED_RESPONSE.replace(b"2014248", b"2014248,3026048"),
            b"\xff",
            b"unexpected provider payload",
        ]
        for body in bodies:
            opener = FakeOpener([FakeResponse(body)])
            with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                receipt = TOOL.match(INPUT)
            self.assertIn(receipt["acquisition_status"], {
                "INVALID_RESPONSE_ENCODING", "INVALID_RESPONSE_SHAPE", "UNRECOGNIZED_MATCH_VALUE",
            })
            self.assertIsNone(receipt["returned_pmid"])

    def test_redirect_rate_limit_wrong_content_type_oversize_and_offline_are_explicit(self) -> None:
        cases = [
            (HTTPError(TOOL.API_BASE, 302, "redirect", {}, None), "REDIRECT_BLOCKED"),
            (HTTPError(TOOL.API_BASE, 429, "rate limited", {}, None), "RATE_LIMITED"),
            (FakeResponse(b"<html/>", content_type="text/html"), "NON_TEXT_RESPONSE"),
            (FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1)), "RESPONSE_TOO_LARGE"),
            (OSError("offline"), "NETWORK_ERROR"),
        ]
        for response, expected in cases:
            opener = FakeOpener([response])
            with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                receipt = TOOL.match(INPUT)
            self.assertEqual(receipt["acquisition_status"], expected)
            self.assertEqual(receipt["match_status"], "NOT_AVAILABLE")
            self.assertIsNone(receipt["returned_pmid"])
            self.assertEqual(len(opener.calls), 1)

    def test_output_matches_schema_and_contains_ncbi_notice(self) -> None:
        opener = FakeOpener([FakeResponse(MATCHED_RESPONSE)])
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            receipt = TOOL.match(INPUT)
        schema = json.loads((IGNITION_ROOT / "schemas/operations/pubmed-citation-matcher-output-r0.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(receipt)
        self.assertEqual(receipt["provider_disclaimer"], "https://www.ncbi.nlm.nih.gov/About/disclaimer.html")
        self.assertEqual(receipt["provider_usage_policy"], "https://www.ncbi.nlm.nih.gov/home/about/policies/")


if __name__ == "__main__":
    unittest.main()
