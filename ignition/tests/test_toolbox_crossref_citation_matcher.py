from __future__ import annotations

import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = IGNITION_ROOT / "tools/toolbox_crossref_citation_matcher.py"
SPEC = importlib.util.spec_from_file_location("toolbox_crossref_citation_matcher", SCRIPT)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


CITATION = "Causal inference in the medical domain: a survey. 2024."


def item(doi: str, score: float, title: str = "A matched Crossref work") -> dict:
    return {
        "DOI": doi,
        "score": score,
        "title": [title],
        "author": [{"given": "Ada", "family": "Writer"}, {"name": "Grace Editor"}],
        "issued": {"date-parts": [[2024, 2, 3]]},
        "type": "journal-article",
        "publisher": "Example Publisher",
        "container-title": ["Example Journal"],
        "volume": "42",
        "issue": "3",
        "page": "12-21",
        "abstract": "Do not project this possibly copyrighted abstract.",
        "reference": [{"DOI": "10.1000/other"}],
    }


def body(items: list[dict] | None = None, total: int = 1) -> bytes:
    return json.dumps({"status": "ok", "message": {"total-results": total, "items": items or []}}).encode("utf-8")


def request_bytes(citation: str = CITATION) -> bytes:
    return json.dumps({"citation": citation}, ensure_ascii=False).encode("utf-8")


class FakeResponse:
    def __init__(self, payload: bytes, *, content_type: str = "application/json", status: int = 200) -> None:
        self.payload = payload
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
        end = len(self.payload) if size < 0 else min(len(self.payload), self.offset + size)
        value = self.payload[self.offset:end]
        self.offset = end
        return value


class FakeOpener:
    def __init__(self, result: FakeResponse | Exception) -> None:
        self.result = result
        self.calls: list[tuple[object, int]] = []

    def open(self, request: object, timeout: int) -> FakeResponse:
        self.calls.append((request, timeout))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakeStdin:
    def __init__(self, payload: bytes) -> None:
        self.buffer = io.BytesIO(payload)


class CrossrefCitationMatcherTests(unittest.TestCase):
    def test_fixture_and_exact_input_contract(self) -> None:
        fixture = json.loads((IGNITION_ROOT / "tests/fixtures/toolbox-crossref-citation-matcher/valid-input-r0.json").read_text(encoding="utf-8"))
        input_schema = json.loads((IGNITION_ROOT / "schemas/operations/toolbox-crossref-citation-matcher-input-r0.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(input_schema).validate(fixture)
        self.assertEqual(TOOL.parse_request(request_bytes()), CITATION)
        invalid = [
            b'{"citation":"x","citation":"y"}',
            b'{"citation":" x "}',
            b'{"citation":"x\\ny"}',
            b'{"citation":"x","mailto":"person@example.org"}',
            b'{"citation":"x","api_key":"secret"}',
            b'{"citation":true}',
            b"\xff",
            b" " * (TOOL.MAX_REQUEST_BYTES + 1),
            json.dumps({"citation": "é" * 2049}, ensure_ascii=False).encode("utf-8"),
        ]
        for raw in invalid:
            with self.subTest(raw=raw[:80]), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)

    def test_request_uses_bibliographic_endpoint_two_rows_and_no_email(self) -> None:
        opener = FakeOpener(FakeResponse(body([item("10.1234/example", 3.2)])))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build:
            receipt = TOOL.match(request_bytes(), opener=opener)
        self.assertEqual(build.call_count, 0)
        self.assertEqual(len(opener.calls), 1)
        request, timeout = opener.calls[0]
        self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        self.assertIn("IgnitionCrossrefCitationMatcher/0.1.0", request.get_header("User-agent"))
        target = urlsplit(request.full_url)
        self.assertEqual((target.scheme, target.hostname, target.path), ("https", TOOL.API_HOST, "/v1/works"))
        params = parse_qs(target.query)
        self.assertEqual(params["query.bibliographic"], [CITATION])
        self.assertEqual(params["rows"], ["2"])
        self.assertIn("DOI", params["select"][0])
        self.assertNotIn("abstract", params["select"][0])
        self.assertNotIn("mailto", params)
        self.assertNotIn("email", params)
        self.assertNotIn("api_key", params)
        self.assertEqual(receipt["status"], "CANDIDATES_REPORTED")
        self.assertEqual(receipt["candidates"][0]["doi"], "10.1234/example")

    def test_results_preserve_provider_rank_and_score_but_never_claim_match(self) -> None:
        payload = body([item("10.1234/first", 9.5), item("10.1234/second", 7.25)], total=7)
        opener = FakeOpener(FakeResponse(payload))
        receipt = TOOL.match(request_bytes(), opener=opener)
        encoded = json.dumps(receipt, ensure_ascii=False)
        self.assertEqual(receipt["provider_hit_count"], 7)
        self.assertEqual(receipt["returned_count"], 2)
        self.assertEqual(receipt["top_two_score_status"], "TOP_SCORES_DIFFER_AS_REPORTED")
        self.assertEqual([row["doi"] for row in receipt["candidates"]], ["10.1234/first", "10.1234/second"])
        self.assertEqual([row["provider_rank"] for row in receipt["candidates"]], [1, 2])
        self.assertEqual([row["crossref_relevance_score"] for row in receipt["candidates"]], [9.5, 7.25])
        self.assertNotIn("Causal inference in the medical domain", encoded)
        self.assertNotIn("abstract", encoded)
        self.assertNotIn("reference", encoded)
        self.assertEqual(receipt["request_count"], 1)
        self.assertEqual(len(opener.calls), 1)

    def test_equal_scores_report_provider_tie_without_selecting_a_winner(self) -> None:
        opener = FakeOpener(FakeResponse(body([item("10.1234/one", 4.0), item("10.1234/two", 4.0)], total=2)))
        receipt = TOOL.match(request_bytes(), opener=opener)
        self.assertEqual(receipt["top_two_score_status"], "TOP_SCORES_EQUAL_AS_REPORTED")
        self.assertEqual(receipt["returned_count"], 2)

    def test_finite_negative_provider_score_is_preserved_without_interpreting_its_scale(self) -> None:
        receipt = TOOL.match(request_bytes(), opener=FakeOpener(FakeResponse(body([item("10.1234/one", -0.25)]))))
        self.assertEqual(receipt["status"], "CANDIDATES_REPORTED")
        self.assertEqual(receipt["candidates"][0]["crossref_relevance_score"], -0.25)

    def test_malformed_or_ambiguous_provider_payload_fails_closed(self) -> None:
        for payload in (
            b"not json",
            b'{"status":"ok","message":{"total-results":1,"items":[{"DOI":"not-a-doi"}]}}',
            b'{"status":"ok","message":{"total-results":1,"items":[{"DOI":"10.1234/a","score":NaN}]}}',
            body([item("10.1234/duplicate", 1), item("10.1234/duplicate", 2)], total=2),
            body([item("10.1234/one", 1), item("10.1234/two", True)], total=2),
            body([item("10.1234/one", 1), item("10.1234/two", 2), item("10.1234/three", 3)], total=3),
        ):
            receipt = TOOL.match(request_bytes(), opener=FakeOpener(FakeResponse(payload)))
            with self.subTest(payload=payload[:50]):
                self.assertEqual(receipt["status"], "INVALID_RESPONSE")
                self.assertEqual(receipt["acquisition_status"], "INVALID_RESPONSE")
                self.assertEqual(receipt["candidates"], [])
                self.assertIsNone(receipt["provider_hit_count"])

    def test_no_result_and_missing_scores_remain_uncertain(self) -> None:
        no_result = TOOL.match(request_bytes(), opener=FakeOpener(FakeResponse(body([], total=0))))
        self.assertEqual(no_result["status"], "NO_CANDIDATE_REPORTED")
        self.assertEqual(no_result["top_two_score_status"], "INSUFFICIENT_CANDIDATES")
        missing_scores = [item("10.1234/one", 1), item("10.1234/two", 2)]
        for row in missing_scores:
            del row["score"]
        receipt = TOOL.match(request_bytes(), opener=FakeOpener(FakeResponse(body(missing_scores, total=2))))
        self.assertEqual(receipt["top_two_score_status"], "SCORE_NOT_RETURNED")
        self.assertIsNone(receipt["candidates"][0]["crossref_relevance_score"])

    def test_http_redirect_rate_limit_response_size_and_offline_are_explicit(self) -> None:
        cases = [
            (HTTPError(TOOL.API_ENDPOINT, 302, "redirect", {}, None), "REDIRECT_BLOCKED"),
            (HTTPError(TOOL.API_ENDPOINT, 429, "rate limited", {}, None), "RATE_LIMITED"),
            (FakeResponse(b"<html/>", content_type="text/html"), "NON_JSON_RESPONSE"),
            (FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1)), "RESPONSE_TOO_LARGE"),
            (OSError("offline"), "NETWORK_ERROR"),
        ]
        for value, expected in cases:
            opener = FakeOpener(value)
            receipt = TOOL.match(request_bytes(), opener=opener)
            with self.subTest(expected=expected):
                self.assertEqual(receipt["acquisition_status"], expected)
                self.assertEqual(receipt["status"], "UNAVAILABLE")
                self.assertEqual(receipt["request_count"], 1)
                self.assertEqual(len(opener.calls), 1)

    def test_cli_refuses_network_without_explicit_flag_before_reading_or_requesting(self) -> None:
        opener = FakeOpener(FakeResponse(body([item("10.1234/one", 1)])))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                with patch("sys.stdout", io.StringIO()), patch("sys.stderr", io.StringIO()):
                    self.assertEqual(TOOL.main(["--stdin"]), 2)
        self.assertEqual(opener.calls, [])

    def test_cli_emits_one_json_receipt_after_explicit_network_opt_in(self) -> None:
        opener = FakeOpener(FakeResponse(body([item("10.1234/one", 1)])))
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin", "--allow-public-network"])
        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(json.loads(stdout.getvalue())["tool_id"], TOOL.TOOL_ID)

    def test_output_matches_schema(self) -> None:
        receipt = TOOL.match(request_bytes(), opener=FakeOpener(FakeResponse(body([item("10.1234/one", 1)]))))
        schema = json.loads((IGNITION_ROOT / "schemas/operations/toolbox-crossref-citation-matcher-output-r0.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(receipt)

    def test_route_is_default_off_and_allowlist_does_not_authorize_execution(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "research.match_crossref_citation")
        profile = {
            "task_id": "GAP001-01-crossref-citation-matcher-c1-01",
            "current_ref": "codex/toolbox-growth-20261025",
            "input_types": card["accepted_input_types"],
            "required_outputs": card["output_types"],
            "allowed_execution_modes": ["READ_ONLY_RUN"],
            "allowed_network_hosts": ["api.crossref.org"],
        }
        default = planner.plan_tool_route(profile)
        opted_in = planner.plan_tool_route(profile, include_experimental_tool_ids=[card["tool_id"]])
        hostless = planner.plan_tool_route(
            {**profile, "allowed_network_hosts": []},
            include_experimental_tool_ids=[card["tool_id"]],
        )
        overbroad = planner.plan_tool_route(
            {**profile, "allowed_network_hosts": ["api.crossref.org", "example.org"]},
            include_experimental_tool_ids=[card["tool_id"]],
        )
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(opted_in["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opted_in["selected_tools"]], [card["tool_id"]])
        self.assertFalse(opted_in["execution_authorized"])
        self.assertFalse(opted_in["selected_tools"][0]["permissions"]["write_paths"])
        self.assertEqual(opted_in["selected_tools"][0]["permissions"]["network_hosts"], ["api.crossref.org"])
        self.assertEqual(hostless["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": card["tool_id"], "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            hostless["rejected_candidates"],
        )
        self.assertEqual(overbroad["decision"], "COMPLETE")
        self.assertEqual(overbroad["selected_tools"][0]["permissions"]["network_hosts"], ["api.crossref.org"])
        self.assertFalse(overbroad["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
